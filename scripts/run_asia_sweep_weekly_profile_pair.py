from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes
from dtr_lab.strategies.asia_sweep.weekly_profile_regime import (
    DEVELOPMENT_YEARS,
    enrich_pair_target_ledger,
    prepare_midpoint_minutes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build causal weekly-profile features for one Asian Sweep FX pair."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    symbol = args.symbol.upper()
    targets = pd.read_csv(args.targets)
    minute_parts: list[pd.DataFrame] = []
    for year in DEVELOPMENT_YEARS:
        minute_parts.append(
            prepare_midpoint_minutes(load_bid_ask_minutes(args.data, symbol, year))
        )
    minutes = pd.concat(minute_parts).sort_index()
    if minutes.index.duplicated().any():
        raise ValueError(f"{symbol}: duplicate minute timestamps across source years")

    source_events = targets.loc[
        targets["instrument"].eq(symbol)
        & targets["landmark"].eq("T0")
        & targets["year"].between(2015, 2019),
        "event_id",
    ].nunique()
    enriched = enrich_pair_target_ledger(targets, minutes, symbol=symbol)
    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(output / "weekly_profile_enriched.csv", index=False)

    role_census = (
        enriched.drop_duplicates("event_id")
        .groupby(["year", "trade_role"], sort=True)
        .size()
        .rename("events")
        .reset_index()
    )
    phase_census = (
        enriched.drop_duplicates("event_id")
        .groupby(["year", "weekly_phase"], sort=True)
        .size()
        .rename("events")
        .reset_index()
    )
    role_census.to_csv(output / "weekly_profile_role_census.csv", index=False)
    phase_census.to_csv(output / "weekly_profile_phase_census.csv", index=False)

    summary = {
        "symbol": symbol,
        "development_years": list(DEVELOPMENT_YEARS),
        "protected_years_opened": False,
        "source_t0_events": int(source_events),
        "enriched_t0_events": int(enriched["event_id"].nunique()),
        "skipped_t0_events": int(source_events - enriched["event_id"].nunique()),
        "enriched_target_rows": int(len(enriched)),
        "structural_trend_counts": {
            str(key): int(value)
            for key, value in enriched.drop_duplicates("event_id")[
                "structural_trend"
            ].value_counts().sort_index().items()
        },
        "trade_role_counts": {
            str(key): int(value)
            for key, value in enriched.drop_duplicates("event_id")[
                "trade_role"
            ].value_counts().sort_index().items()
        },
    }
    (output / "weekly_profile_pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
