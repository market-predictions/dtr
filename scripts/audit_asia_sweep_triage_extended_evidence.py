from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss


TOLERANCE = 1e-10


def _assert_close(name: str, actual: float, expected: float) -> None:
    if pd.isna(actual) and pd.isna(expected):
        return
    if not math.isclose(float(actual), float(expected), rel_tol=TOLERANCE, abs_tol=TOLERANCE):
        raise AssertionError(f"{name}: {actual} != {expected}")


def _triage_metrics(frame: pd.DataFrame) -> dict[str, float]:
    action = frame["action"].astype(str).to_numpy()
    outcome = frame["triage_outcome"].astype(str).to_numpy()
    take = action != "ABSTAIN"
    correct = action == outcome
    continuation = action == "CONTINUATION"
    reversal = action == "REVERSAL"
    true_reversal = outcome == "REVERSAL"
    return {
        "events": float(len(frame)),
        "resolved_events": float((outcome != "UNRESOLVED").sum()),
        "coverage": float(take.mean()),
        "continuation_coverage": float(continuation.mean()),
        "continuation_precision": (
            float(correct[continuation].mean()) if continuation.any() else 0.0
        ),
        "continuation_false_veto_rate": (
            float((continuation & true_reversal).sum() / true_reversal.sum())
            if true_reversal.any()
            else 0.0
        ),
        "reversal_calls": float(reversal.sum()),
        "reversal_precision": float(correct[reversal].mean()) if reversal.any() else 0.0,
        "selective_accuracy": float(correct[take].mean()) if take.any() else 0.0,
        "utility_per_event": float(
            (correct[take].sum() - 1.5 * (~correct[take]).sum()) / len(frame)
        ),
    }


def audit_triage(directory: Path) -> dict[str, Any]:
    summary = pd.read_csv(directory / "triage_candidate_summary.csv")
    audited = 0
    for path in sorted(directory.glob("triage_predictions_*.csv")):
        frame = pd.read_csv(path)
        if frame.duplicated(["event_id", "landmark"]).any():
            raise AssertionError(f"{path.name}: duplicate event-landmark keys")
        if set(frame["year"].astype(int)) != set(range(2015, 2020)):
            raise AssertionError(f"{path.name}: unexpected years")
        if set(frame["instrument"]) != {"EURUSD", "GBPUSD"}:
            raise AssertionError(f"{path.name}: unexpected instruments")
        row = summary.loc[
            summary["landmark"].eq(frame.iloc[0]["landmark"])
            & summary["family"].eq(frame.iloc[0]["family"])
        ].iloc[0]
        metrics = _triage_metrics(frame)
        for name, value in metrics.items():
            _assert_close(f"{path.name}/{name}", value, row[name])
        audited += 1
    if audited != 8:
        raise AssertionError(f"expected 8 triage candidates, audited {audited}")
    return {"candidates": audited, "rows": int(summary["events"].sum())}


def _extended_metrics(frame: pd.DataFrame) -> dict[str, float]:
    ranked = frame.copy()
    ranked["quintile"] = ranked.groupby("year")["probability"].transform(
        lambda values: pd.qcut(values.rank(method="first"), 5, labels=False) + 1
    )
    target = ranked["model_target"].to_numpy(dtype=int)
    probability = ranked["probability"].to_numpy(dtype=float)
    base_rate = float(target.mean())
    top = ranked.loc[ranked["quintile"].eq(5)].copy()
    bottom = ranked.loc[ranked["quintile"].eq(1)].copy()
    target_name = str(ranked.iloc[0]["target_name"])
    reward = top["target_reward_risk"].astype(float)
    slippage = top["entry_slippage_r"].astype(float)
    stressed_reward = reward - (
        2.0 if target_name == "LATE_TREND_HOLD_1600" else 1.0
    ) * slippage
    stressed_loss = 1.0 + 2.0 * slippage
    expected_value = (
        top["probability"] * stressed_reward
        - (1.0 - top["probability"]) * stressed_loss
    )
    pair = ranked.groupby("instrument").agg(
        positives=("model_target", "sum"),
        base_rate=("model_target", "mean"),
    )
    pair["top_rate"] = ranked.loc[ranked["quintile"].eq(5)].groupby(
        "instrument"
    )["model_target"].mean()
    year = ranked.groupby("year")["model_target"].mean().to_frame("base_rate")
    year["top_rate"] = ranked.loc[ranked["quintile"].eq(5)].groupby("year")[
        "model_target"
    ].mean()
    pr_auc = float(average_precision_score(target, probability))
    return {
        "events": float(len(ranked)),
        "positives": float(target.sum()),
        "minimum_pair_positives": float(pair["positives"].min()),
        "base_rate": base_rate,
        "pr_auc": pr_auc,
        "pr_auc_relative_lift": pr_auc / base_rate - 1.0,
        "brier": float(brier_score_loss(target, probability)),
        "constant_brier": base_rate * (1.0 - base_rate),
        "top_quintile_rate": float(top["model_target"].mean()),
        "top_quintile_lift": float(top["model_target"].mean() / base_rate),
        "bottom_quintile_rate": float(bottom["model_target"].mean()),
        "bottom_base_ratio": float(bottom["model_target"].mean() / base_rate),
        "pair_positive_lift_count": float((pair["top_rate"] > pair["base_rate"]).sum()),
        "year_positive_lift_count": float((year["top_rate"] > year["base_rate"]).sum()),
        "median_top_stressed_ev": float(expected_value.median()),
        "median_top_reward_risk": float(reward.median()),
    }


def audit_extended(directory: Path) -> dict[str, Any]:
    audited = 0
    total_rows = 0
    for summary_path in sorted(directory.rglob("extended_summary_*.json")):
        expected = json.loads(summary_path.read_text(encoding="utf-8"))
        prediction_paths = list(
            summary_path.parent.glob("extended_predictions_*.csv")
        )
        if len(prediction_paths) != 1:
            raise AssertionError(
                f"{summary_path.parent}: expected one prediction file"
            )
        frame = pd.read_csv(prediction_paths[0])
        if frame.duplicated(["event_id", "landmark"]).any():
            raise AssertionError(f"{prediction_paths[0].name}: duplicate keys")
        if set(frame["year"].astype(int)) != set(range(2015, 2020)):
            raise AssertionError(f"{prediction_paths[0].name}: unexpected years")
        if set(frame["instrument"]) != {"EURUSD", "GBPUSD"}:
            raise AssertionError(f"{prediction_paths[0].name}: unexpected pairs")
        metrics = _extended_metrics(frame)
        for name, value in metrics.items():
            _assert_close(
                f"{prediction_paths[0].name}/{name}",
                value,
                expected[name],
            )
        audited += 1
        total_rows += len(frame)
    if audited != 20:
        raise AssertionError(f"expected 20 extended candidates, audited {audited}")
    return {"candidates": audited, "prediction_rows": total_rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--extended", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = {
        "programme": "ASIAN_SWEEP_INDEPENDENT_EVIDENCE_AUDIT_V1",
        "triage": audit_triage(args.triage),
        "extended": audit_extended(args.extended),
        "decision": "PASS_INDEPENDENT_RECONCILIATION",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "independent_evidence_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
