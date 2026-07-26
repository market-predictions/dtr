from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.context_regime import (
    build_event_context,
    load_bid_ask_minutes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one causal Asian Sweep context and regime ledger."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    events = pd.read_csv(args.events)
    quotes = load_bid_ask_minutes(
        args.data,
        args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    ledger = build_event_context(events, quotes, symbol=args.symbol)
    ledger["year"] = pd.to_datetime(ledger["trade_date"], errors="raise").dt.year
    observed_years = sorted(ledger["year"].unique().astype(int).tolist())
    expected_years = list(range(args.start_year, args.end_year + 1))
    if observed_years != expected_years:
        raise ValueError(
            f"{args.symbol}: expected years {expected_years}, found {observed_years}"
        )
    if ledger["event_id"].duplicated().any():
        raise ValueError(f"{args.symbol}: duplicate event ids")
    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "context_regime_ledger.csv", index=False)
    summary = {
        "programme": "ASIAN_SWEEP_CONTEXT_REGIME_ATLAS_V10",
        "stage": "PAIR_CONTEXT_LEDGER",
        "symbol": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "events": int(len(ledger)),
        "economic_events": int(ledger["economic_proxy_eligible"].sum()),
        "positive_cases": int(ledger["target"].sum()),
        "dates": int(ledger["trade_date"].nunique()),
        "duplicate_event_ids": int(ledger["event_id"].duplicated().sum()),
        "strategy_pnl_calculated": False,
    }
    (args.out / "pair_context_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
