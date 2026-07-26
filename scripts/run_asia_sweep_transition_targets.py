from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.extended_reversal_targets import (
    TARGET_ORDER,
    target_census,
)
from dtr_lab.strategies.asia_sweep.transition_target_builder import (
    build_partition_extended_target_ledger,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build frozen T0-T3 extended targets for one validation partition."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--levels", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    landmark_ledger = pd.read_csv(args.ledger)
    levels = pd.read_csv(args.levels)
    result = build_partition_extended_target_ledger(
        landmark_ledger,
        levels,
        args.data,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    present = set(result["extended_target"].unique())
    missing_targets = [target for target in TARGET_ORDER if target not in present]
    if missing_targets:
        raise ValueError(
            f"{args.symbol}: frozen validation targets missing: {missing_targets}"
        )
    args.out.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out / "transition_extended_targets.csv", index=False)
    target_census(result).to_csv(
        args.out / "transition_extended_target_census.csv", index=False
    )
    summary = {
        "symbol": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "rows": int(len(result)),
        "event_landmarks": int(
            result[["event_id", "landmark"]].drop_duplicates().shape[0]
        ),
        "targets": sorted(present),
        "opposing_liquidity_levels": int(len(levels)),
        "opposing_liquidity_events": int(levels["event_id"].nunique()),
    }
    (args.out / "transition_target_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
