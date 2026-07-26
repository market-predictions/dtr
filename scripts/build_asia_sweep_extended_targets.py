from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.extended_targets import build_extended_target_ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    ledger = pd.read_csv(args.ledger)
    ledger = ledger.loc[ledger["instrument"].eq(args.symbol)].copy()
    targets = build_extended_target_ledger(ledger, args.source_root)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"extended_target_ledger_{args.symbol}.csv"
    targets.to_csv(path, index=False)
    summary = {
        "symbol": args.symbol,
        "rows": int(len(targets)),
        "events": int(targets["event_id"].nunique()),
        "landmarks": sorted(targets["landmark"].unique().tolist()),
        "years": sorted(pd.to_numeric(targets["year"]).astype(int).unique().tolist()),
    }
    (args.out / f"extended_target_ledger_{args.symbol}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
