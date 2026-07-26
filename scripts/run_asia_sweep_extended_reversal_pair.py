from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.extended_reversal_targets import (
    build_pair_extended_target_ledger,
    target_census,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--levels", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    landmark_ledger = pd.read_csv(args.ledger)
    levels = pd.read_csv(args.levels)
    result = build_pair_extended_target_ledger(
        landmark_ledger,
        levels,
        args.data,
        symbol=args.symbol,
    )
    census = target_census(result)
    result.to_csv(args.out / "extended_reversal_targets.csv", index=False)
    census.to_csv(args.out / "extended_reversal_target_census.csv", index=False)
    summary = {
        "symbol": args.symbol.upper(),
        "rows": int(len(result)),
        "event_landmarks": int(
            result[["event_id", "landmark"]].drop_duplicates().shape[0]
        ),
        "targets": sorted(result["extended_target"].unique().tolist()),
        "years": sorted(result["year"].unique().astype(int).tolist()),
    }
    (args.out / "pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
