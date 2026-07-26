from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.wayne_pivots import (
    build_anatomy_ledger,
    load_bid_ask_minutes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one causal Wayne Pivots anatomy ledger."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    symbol = args.symbol.upper()
    quotes = load_bid_ask_minutes(
        args.data,
        symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    ledger, day_ledger = build_anatomy_ledger(
        quotes,
        symbol=symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "wayne_pivots_anatomy_ledger.csv", index=False)
    day_ledger.to_csv(args.out / "wayne_pivots_day_ledger.csv", index=False)
    summary = {
        "instrument": symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "quote_minutes": int(len(quotes)),
        "pivot_days": int(len(day_ledger)),
        "ledger_rows": int(len(ledger)),
        "fresh_rows": int(ledger["eligible_fresh"].sum()),
        "structures": sorted(ledger["structure"].unique().tolist()),
        "sides": sorted(ledger["side"].unique().tolist()),
        "targets": sorted(ledger["target_name"].unique().tolist()),
        "minimum_timestamp_utc": str(quotes.index.min()),
        "maximum_timestamp_utc": str(quotes.index.max()),
    }
    (args.out / "wayne_pivots_pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
