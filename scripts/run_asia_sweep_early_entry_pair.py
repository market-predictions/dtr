from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.early_entry_landmarks import (
    build_pair_landmark_ledger,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--levels", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2019)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    events = pd.read_csv(args.events)
    levels = pd.read_csv(args.levels)
    ledger = build_pair_landmark_ledger(
        events,
        levels,
        args.data,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "early_entry_landmarks.csv", index=False)
    summary = {
        "programme": "ASIAN_SWEEP_EARLY_ENTRY_INFORMATION_FRONTIER_V5",
        "symbol": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "rows": int(len(ledger)),
        "events": int(ledger["event_id"].nunique()),
        "landmark_counts": {
            str(key): int(value)
            for key, value in ledger["landmark"].value_counts().sort_index().items()
        },
    }
    (args.out / "pair_early_entry_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
