from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

LANDMARKS = ("T0", "T1", "T2", "T3")
FAMILIES = ("elastic_net", "hgb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _load_candidates(directory: Path) -> pd.DataFrame:
    files = sorted(directory.rglob("candidate_summary.json"))
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    frame = pd.DataFrame(rows)
    expected = {(landmark, family) for landmark in LANDMARKS for family in FAMILIES}
    found = set(zip(frame["landmark"], frame["family"], strict=False))
    if found != expected:
        raise ValueError(f"expected candidate set {sorted(expected)}, found {sorted(found)}")
    if frame.duplicated(["landmark", "family"]).any():
        raise ValueError("candidate landmark-family keys must be unique")
    return frame


def _first_role_landmark(frame: pd.DataFrame, role: str) -> str | None:
    for landmark in ("T1", "T2", "T3"):
        row = frame.loc[frame["landmark"].eq(landmark)].iloc[0]
        if bool(row[f"{role}_role_pass"]):
            return landmark
    return None


def _family_sequence(frame: pd.DataFrame, family: str) -> dict[str, Any]:
    family_frame = frame.loc[frame["family"].eq(family)].copy()
    continuation_landmark = _first_role_landmark(family_frame, "continuation")
    reversal_landmark = _first_role_landmark(family_frame, "reversal")
    if continuation_landmark is None or reversal_landmark is None:
        return {
            "family": family,
            "passes": False,
            "continuation_landmark": continuation_landmark,
            "reversal_landmark": reversal_landmark,
            "failed_predicates": "missing_role_landmark",
        }
    selected_landmarks = sorted(
        {continuation_landmark, reversal_landmark}, key=LANDMARKS.index
    )
    selected = family_frame.loc[family_frame["landmark"].isin(selected_landmarks)]
    continuation_row = family_frame.loc[
        family_frame["landmark"].eq(continuation_landmark)
    ].iloc[0]
    reversal_row = family_frame.loc[
        family_frame["landmark"].eq(reversal_landmark)
    ].iloc[0]
    gates = {
        "mean_macro_lift": float(selected["macro_relative_pr_auc_lift"].mean())
        >= 0.35,
        "sample_size": bool(selected["events"].ge(400).all()),
        "abstain_coverage": bool(
            selected["abstain_coverage"].between(0.25, 0.75).all()
        ),
        "calibration": bool(selected["all_class_calibration_better"].all()),
        "concentration": bool(selected["max_action_concentration"].le(0.70).all()),
    }
    minimum_directional_precision = min(
        float(continuation_row["continuation_precision"]),
        float(reversal_row["reversal_precision"]),
    )
    return {
        "family": family,
        "passes": bool(all(gates.values())),
        "continuation_landmark": continuation_landmark,
        "reversal_landmark": reversal_landmark,
        "mean_macro_relative_pr_auc_lift": float(
            selected["macro_relative_pr_auc_lift"].mean()
        ),
        "continuation_precision": float(
            continuation_row["continuation_precision"]
        ),
        "reversal_precision": float(reversal_row["reversal_precision"]),
        "minimum_directional_precision": minimum_directional_precision,
        "continuation_coverage": float(continuation_row["continuation_coverage"]),
        "reversal_coverage": float(reversal_row["reversal_coverage"]),
        "gates": gates,
        "failed_predicates": ";".join(key for key, value in gates.items() if not value),
    }


def _select_family(sequences: list[dict[str, Any]]) -> str | None:
    elastic = next(row for row in sequences if row["family"] == "elastic_net")
    hgb = next(row for row in sequences if row["family"] == "hgb")
    if bool(elastic["passes"]):
        selected = "elastic_net"
        if bool(hgb["passes"]):
            macro_improvement = (
                float(hgb["mean_macro_relative_pr_auc_lift"])
                - float(elastic["mean_macro_relative_pr_auc_lift"])
            )
            no_precision_loss = float(hgb["minimum_directional_precision"]) >= float(
                elastic["minimum_directional_precision"]
            )
            if macro_improvement >= 0.10 and no_precision_loss:
                selected = "hgb"
        return selected
    if bool(hgb["passes"]):
        return "hgb"
    return None


def _copy_selected_evidence(
    inputs: Path,
    output: Path,
    sequence: dict[str, Any],
) -> None:
    family = str(sequence["family"])
    for role in ("continuation", "reversal"):
        landmark = str(sequence[f"{role}_landmark"])
        for kind in ("predictions", "thresholds", "tuning"):
            matches = list(inputs.rglob(f"{kind}_{landmark}_{family}.csv"))
            if len(matches) != 1:
                raise ValueError(
                    f"expected one {kind} file for {landmark}/{family}, found {matches}"
                )
            shutil.copyfile(matches[0], output / f"selected_{role}_{kind}.csv")


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    candidates = _load_candidates(args.inputs)
    sequences = [_family_sequence(candidates, family) for family in FAMILIES]
    selected_family = _select_family(sequences)
    decision_name = (
        "PASS_TRIAGE_AUTHORIZE_SEPARATE_STAGED_REVERSAL_AND_CONTINUATION_GEOMETRY"
        if selected_family is not None
        else "FAIL_TRIAGE_STOP_BEFORE_STAGED_PNL"
    )
    decision: dict[str, Any] = {
        "programme": "ASIAN_SWEEP_SEQUENTIAL_TRIAGE_PHASE_A_V6",
        "decision": decision_name,
        "selected_family": selected_family,
        "family_sequences": sequences,
        "development_years": [2015, 2016, 2017, 2018, 2019],
        "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "staged_reversal_pnl_opened": False,
        "continuation_execution_opened": False,
        "extended_reversal_execution_opened": False,
    }
    if selected_family is not None:
        selected_sequence = next(
            row for row in sequences if row["family"] == selected_family
        )
        decision["selected_sequence"] = selected_sequence
        _copy_selected_evidence(args.inputs, args.out, selected_sequence)
    candidates.to_csv(args.out / "candidate_summary.csv", index=False)
    pd.DataFrame(sequences).to_csv(
        args.out / "family_sequence_summary.csv", index=False
    )
    (args.out / "triage_phase_a_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    if selected_family is None:
        raise SystemExit(2)
    if not math.isfinite(float(decision["selected_sequence"]["mean_macro_relative_pr_auc_lift"])):
        raise SystemExit("selected sequence has non-finite macro lift")


if __name__ == "__main__":
    main()
