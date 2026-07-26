from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.asia_sweep.extended_reversal_targets import (
    LANDMARKS,
    TARGET_ORDER,
)

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
    expected = {
        (target, landmark, family)
        for target in TARGET_ORDER
        for landmark in LANDMARKS
        for family in FAMILIES
    }
    found = set(
        zip(
            frame["extended_target"],
            frame["landmark"],
            frame["family"],
            strict=False,
        )
    )
    if found != expected:
        raise ValueError(f"expected {len(expected)} candidates, found {len(found)}")
    if frame.duplicated(["extended_target", "landmark", "family"]).any():
        raise ValueError("extended candidate keys must be unique")
    return frame


def _select_family_landmark(
    target_frame: pd.DataFrame,
    family: str,
) -> pd.Series | None:
    passing = target_frame.loc[
        target_frame["family"].eq(family) & target_frame["passes"].astype(bool)
    ].copy()
    if passing.empty:
        return None
    passing["landmark_order"] = passing["landmark"].map(
        {landmark: index for index, landmark in enumerate(LANDMARKS)}
    )
    passing = passing.sort_values("landmark_order", kind="mergesort")
    selected = passing.iloc[0]
    for _, challenger in passing.iloc[1:].iterrows():
        pr_improvement = float(challenger["pr_auc_relative_lift"]) - float(
            selected["pr_auc_relative_lift"]
        )
        rr_decline = float(
            selected["median_top_decile_reward_risk_stress_010"]
        ) - float(challenger["median_top_decile_reward_risk_stress_010"])
        if pr_improvement >= 0.20 and rr_decline <= 0.20:
            selected = challenger
    return selected


def _select_target_candidate(target_frame: pd.DataFrame) -> pd.Series | None:
    elastic = _select_family_landmark(target_frame, "elastic_net")
    hgb = _select_family_landmark(target_frame, "hgb")
    if elastic is None:
        return hgb
    if hgb is None:
        return elastic
    pr_improvement = float(hgb["pr_auc_relative_lift"]) - float(
        elastic["pr_auc_relative_lift"]
    )
    no_top_rate_loss = float(hgb["top_decile_rate"]) >= float(
        elastic["top_decile_rate"]
    )
    no_ev_loss = float(hgb["median_top_decile_ev_stress_010"]) >= float(
        elastic["median_top_decile_ev_stress_010"]
    )
    if pr_improvement >= 0.15 and no_top_rate_loss and no_ev_loss:
        return hgb
    return elastic


def _copy_selected(
    inputs: Path,
    output: Path,
    selected: pd.Series,
) -> None:
    target = str(selected["extended_target"])
    landmark = str(selected["landmark"])
    family = str(selected["family"])
    prefix = f"{target}_{landmark}_{family}"
    for kind in ("predictions", "tuning"):
        matches = list(inputs.rglob(f"{kind}_{prefix}.csv"))
        if len(matches) != 1:
            raise ValueError(f"expected one selected {kind} file, found {matches}")
        shutil.copyfile(matches[0], output / f"selected_{kind}.csv")


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    candidates = _load_candidates(args.inputs)
    selected_rows: list[dict[str, Any]] = []
    for target in TARGET_ORDER:
        selected = _select_target_candidate(
            candidates.loc[candidates["extended_target"].eq(target)]
        )
        if selected is None:
            selected_rows.append(
                {
                    "extended_target": target,
                    "selected_landmark": None,
                    "selected_family": None,
                    "passes": False,
                }
            )
        else:
            row = selected.to_dict()
            row["selected_landmark"] = row.pop("landmark")
            row["selected_family"] = row.pop("family")
            selected_rows.append(row)
    target_selection = pd.DataFrame(selected_rows)
    primary_target = None
    primary_row = None
    for target in TARGET_ORDER:
        row = target_selection.loc[target_selection["extended_target"].eq(target)].iloc[0]
        if bool(row.get("passes", False)):
            primary_target = target
            primary_row = row
            break
    if primary_row is not None:
        selected_source = candidates.loc[
            candidates["extended_target"].eq(primary_target)
            & candidates["landmark"].eq(primary_row["selected_landmark"])
            & candidates["family"].eq(primary_row["selected_family"])
        ].iloc[0]
        _copy_selected(args.inputs, args.out, selected_source)
    decision_name = (
        "PASS_EXTENDED_REVERSAL_MODEL_AUTHORIZE_POSITION_STRUCTURE_DISCOVERY"
        if primary_target is not None
        else "FAIL_EXTENDED_REVERSAL_MODEL_STOP_BEFORE_POSITION_STRUCTURE_PNL"
    )
    decision = {
        "programme": "ASIAN_SWEEP_EXTENDED_REVERSAL_MODEL_V7_0",
        "decision": decision_name,
        "primary_target": primary_target,
        "selected_landmark": (
            str(primary_row["selected_landmark"])
            if primary_row is not None
            else None
        ),
        "selected_family": (
            str(primary_row["selected_family"])
            if primary_row is not None
            else None
        ),
        "development_years": [2015, 2016, 2017, 2018, 2019],
        "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "position_structure_pnl_opened": False,
        "candidate_count": int(len(candidates)),
    }
    flattened_candidates: list[dict[str, Any]] = []
    for row in candidates.to_dict(orient="records"):
        flat = {key: value for key, value in row.items() if key != "gates"}
        flat["failed_predicates"] = ";".join(
            key for key, value in row["gates"].items() if not value
        )
        flattened_candidates.append(flat)
    pd.DataFrame(flattened_candidates).to_csv(
        args.out / "extended_candidate_summary.csv", index=False
    )
    target_selection.to_csv(
        args.out / "extended_target_selection.csv", index=False
    )
    (args.out / "extended_reversal_model_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
