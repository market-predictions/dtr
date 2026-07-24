from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CANDIDATE_SUFFIXES = (
    "__RTH_LONG_FULL",
    "__RTH_LONG_FULL_COST_2T",
    "__RTH_LONG_FULL_DELAY_1M",
    "__RTH_LONG_FULL_DELAY_5M",
)
SUMMARY_COLUMNS = (
    "trades",
    "net_r",
    "expectancy_r",
    "profit_factor",
    "max_drawdown_r",
    "median_hold_minutes",
    "return_to_drawdown",
)


def _load_csv(directory: Path, name: str) -> pd.DataFrame:
    path = directory / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _candidate_summaries(directory: Path) -> pd.DataFrame:
    frame = _load_csv(directory, "scenario_summary.csv")
    arm = frame["arm_id"].astype(str)
    selected = arm.eq("USA500_RTH_FULL_123_COMBINED_2015_2025")
    for suffix in CANDIDATE_SUFFIXES:
        selected |= arm.str.endswith(suffix)
    return frame.loc[selected].sort_values(["partition", "arm_id"]).reset_index(drop=True)


def _assert_equal_numbers(
    expected: pd.DataFrame,
    observed: pd.DataFrame,
    columns: tuple[str, ...],
) -> None:
    for column in columns:
        left = pd.to_numeric(expected[column], errors="coerce").to_numpy(float)
        right = pd.to_numeric(observed[column], errors="coerce").to_numpy(float)
        if not np.allclose(left, right, atol=1e-12, rtol=0, equal_nan=True):
            difference = np.nanmax(np.abs(left - right))
            raise AssertionError(f"parity failure for {column}; max difference={difference}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare accelerated certification to frozen evidence")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    expected = _candidate_summaries(args.reference)
    observed = _candidate_summaries(args.observed)
    keys = ["partition", "arm_id"]
    if expected[keys].to_dict("records") != observed[keys].to_dict("records"):
        raise AssertionError("candidate summary keys differ")
    _assert_equal_numbers(expected, observed, SUMMARY_COLUMNS)

    expected_gates = _load_csv(args.reference, "promotion_gates.csv").sort_values("gate")
    observed_gates = _load_csv(args.observed, "promotion_gates.csv").sort_values("gate")
    if expected_gates[["gate", "passed"]].to_dict("records") != observed_gates[
        ["gate", "passed"]
    ].to_dict("records"):
        raise AssertionError("promotion gate outcomes differ")

    expected_decision = json.loads((args.reference / "decision.json").read_text(encoding="utf-8"))
    observed_decision = json.loads((args.observed / "decision.json").read_text(encoding="utf-8"))
    if expected_decision["status"] != observed_decision["status"]:
        raise AssertionError("decision status differs")

    report = {
        "status": "PASS",
        "candidate_summary_rows": int(len(observed)),
        "gate_count": int(len(observed_gates)),
        "decision": observed_decision["status"],
        "summary_tolerance": 1e-12,
        "reference": str(args.reference),
        "observed": str(args.observed),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
