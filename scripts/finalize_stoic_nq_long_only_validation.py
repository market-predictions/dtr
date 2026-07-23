from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply frozen matched-control promotion veto")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gates = pd.read_csv(args.out / "promotion_gates.csv")
    matched = pd.read_csv(args.out / "matched_time_control.csv")
    decision_path = args.out / "decision.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))

    required_matched = {
        "arm_id",
        "full_expectancy_r",
        "matched_p95_expectancy_r",
        "matched_to_full_hold_ratio",
        "hold_distribution_match_flag",
        "matched_min_event_match_fraction",
    }
    missing = required_matched.difference(matched.columns)
    if missing:
        raise ValueError(f"Matched-control output missing columns: {sorted(missing)}")
    if int(decision.get("matched_control_replicates", 0)) != 50:
        raise ValueError("Expected exactly 50 matched-control replicates")

    numerical = gates.groupby("arm_id")["passed"].all()
    rows: list[dict[str, object]] = []
    promoted: list[str] = []
    for row in matched.itertuples(index=False):
        hold_ratio = float(row.matched_to_full_hold_ratio)
        hold_comparable = bool(row.hold_distribution_match_flag) and (
            0.75 <= hold_ratio <= 1.25
        )
        coverage_passed = float(row.matched_min_event_match_fraction) >= 0.90
        comparable = hold_comparable and coverage_passed
        exceeds_p95 = float(row.full_expectancy_r) > float(row.matched_p95_expectancy_r)
        numerical_pass = bool(numerical.get(row.arm_id, False))
        vetoed = not comparable or not exceeds_p95
        promote = numerical_pass and not vetoed
        if promote:
            promoted.append(str(row.arm_id))
        rows.append(
            {
                "arm_id": row.arm_id,
                "numerical_gates_passed": numerical_pass,
                "hold_distribution_comparable": hold_comparable,
                "matched_control_coverage_passed": coverage_passed,
                "matched_control_comparable": comparable,
                "full_expectancy_exceeds_matched_p95": exceeds_p95,
                "matched_control_vetoed": vetoed,
                "promoted": promote,
            }
        )

    veto = pd.DataFrame(rows).sort_values("arm_id").reset_index(drop=True)
    veto.to_csv(args.out / "matched_control_veto.csv", index=False)
    decision["numerical_gate_passed_arms"] = sorted(
        arm for arm, passed in numerical.items() if bool(passed)
    )
    decision["matched_control_vetoed_arms"] = sorted(
        veto.loc[veto["matched_control_vetoed"], "arm_id"].astype(str).tolist()
    )
    decision["promoted_arms"] = sorted(promoted)
    decision["status"] = "PROMOTION_GATE_PASSED" if promoted else "NO_PROMOTION"
    decision["matched_control_veto_contract"] = {
        "median_hold_ratio_min": 0.75,
        "median_hold_ratio_max": 1.25,
        "full_expectancy_must_exceed_matched_p95": True,
        "minimum_event_match_fraction": 0.90,
    }
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(veto.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
