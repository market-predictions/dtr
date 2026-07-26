from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes
from dtr_lab.strategies.asia_sweep.weekly_profile_regime import prepare_midpoint_minutes
from dtr_lab.strategies.asia_sweep.weekly_transition_validation import (
    enrich_transition_target_ledger,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich one validation target ledger with causal weekly transition context."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--warmup-start-year", type=int, required=True)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.warmup_start_year > args.start_year:
        raise ValueError("warmup start must not exceed validation start")
    targets = pd.read_csv(args.targets)
    minute_parts = [
        prepare_midpoint_minutes(load_bid_ask_minutes(args.data, args.symbol, year))
        for year in range(args.warmup_start_year, args.end_year + 1)
    ]
    minutes = pd.concat(minute_parts).sort_index()
    if minutes.index.duplicated().any():
        raise ValueError(f"{args.symbol}: duplicate minute timestamps")
    enriched = enrich_transition_target_ledger(
        targets,
        minutes,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(args.out / "weekly_transition_enriched.csv", index=False)
    event_frame = enriched.drop_duplicates("event_id")
    population = event_frame.loc[event_frame["transition_population"].astype(bool)]
    reference = event_frame.loc[event_frame["transition_reference"].astype(bool)]
    summary = {
        "symbol": args.symbol,
        "warmup_start_year": args.warmup_start_year,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "protected_outside_partition_opened": False,
        "enriched_events": int(event_frame["event_id"].nunique()),
        "enriched_target_rows": int(len(enriched)),
        "transition_population_events": int(population["event_id"].nunique()),
        "transition_reference_events": int(reference["event_id"].nunique()),
        "transition_population_by_year": {
            str(key): int(value)
            for key, value in population.groupby("year").size().sort_index().items()
        },
    }
    (args.out / "weekly_transition_pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
