from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import (
    NEW_YORK_TZ,
    REPLICATION_PAIRS,
    build_h4_health,
    build_monthly_context,
    build_new_york_daily_bars,
    build_new_york_h4_bars,
    build_staged_monthly_sequence,
    build_structure_ledger,
    load_bid_ask_minutes,
    midpoint_minutes,
)

MIN_DAILY_ACTIVE_MINUTES = 1200
MIN_H4_ACTIVE_MINUTES = 180
LOCATION_RULES = ("CLOSE_IN_ZONE", "RANGE_TOUCH")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one unchanged Wayne independent-replication ledger."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", choices=REPLICATION_PAIRS, required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _stage_counts(
    opportunities: pd.DataFrame,
    *,
    column: str,
) -> list[dict[str, Any]]:
    if opportunities.empty:
        return []
    return (
        opportunities.groupby(
            ["location_rule", "side", column],
            dropna=False,
            sort=True,
        )
        .size()
        .rename("opportunities")
        .reset_index()
        .to_dict(orient="records")
    )


def _signal_reach(
    ledger: pd.DataFrame,
    *,
    max_day: int,
) -> list[dict[str, Any]]:
    signals = ledger.loc[ledger["health_pivot_day"].le(max_day)].copy()
    if signals.empty:
        return []
    grouped = (
        signals.groupby(
            ["location_rule", "target_tier", "side"],
            sort=True,
        )
        .agg(
            signals=("health_timestamp", "size"),
            available=("signal_target_available", "sum"),
            reached=("signal_reached_before_invalidation", "sum"),
            preconsumed=("signal_target_pre_start", "sum"),
            same_bar_ambiguous=("signal_target_same_bar", "sum"),
        )
        .reset_index()
    )
    grouped["reach_rate"] = grouped["reached"] / grouped["available"].replace(
        0,
        np.nan,
    )
    return grouped.to_dict(orient="records")


def main() -> None:
    args = parse_args()
    quotes = load_bid_ask_minutes(
        args.data,
        args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    minutes = midpoint_minutes(quotes)
    daily = build_new_york_daily_bars(minutes, active_column="active")
    daily = daily.loc[
        daily["active_minutes"].ge(MIN_DAILY_ACTIVE_MINUTES)
        & daily["high"].gt(daily["low"])
    ].copy()
    h4 = build_new_york_h4_bars(minutes, active_column="active")
    h4 = h4.loc[
        h4["active_minutes"].ge(MIN_H4_ACTIVE_MINUTES)
        & h4["high"].gt(h4["low"])
    ].copy()
    if daily.empty or h4.empty:
        raise ValueError(f"{args.symbol}: empty validated D1 or H4 bars")

    daily_year = daily.index.tz_convert(NEW_YORK_TZ).year
    daily = daily.loc[
        (daily_year >= args.start_year) & (daily_year <= args.end_year)
    ].copy()
    h4_year = h4.index.tz_convert(NEW_YORK_TZ).year
    h4 = h4.loc[
        (h4_year >= args.start_year) & (h4_year <= args.end_year)
    ].copy()

    d1_structure, _d1_swings = build_structure_ledger(daily)
    h4_structure, _h4_swings = build_structure_ledger(h4)
    h4_health = build_h4_health(h4)
    monthly_context = build_monthly_context(daily)

    ledgers = []
    for location_rule in LOCATION_RULES:
        ledger = build_staged_monthly_sequence(
            daily,
            monthly_context,
            d1_structure,
            h4,
            h4_structure,
            h4_health,
            location_rule=location_rule,
        )
        if not ledger.empty:
            ledgers.append(ledger)
    if not ledgers:
        raise ValueError(f"{args.symbol}: no staged monthly opportunities")
    ledger = pd.concat(ledgers, ignore_index=True)
    ledger.insert(0, "instrument", args.symbol)

    opportunities = ledger.drop_duplicates(
        ["instrument", "opportunity_id"]
    ).copy()
    primary = opportunities.loc[
        opportunities["location_rule"].eq("CLOSE_IN_ZONE")
    ]
    summary = {
        "instrument": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "source_minutes": int(len(minutes)),
        "active_minutes": int(minutes["active"].sum()),
        "daily_bars": int(len(daily)),
        "h4_bars": int(len(h4)),
        "opportunities": int(len(opportunities)),
        "primary_opportunities": int(len(primary)),
        "primary_active_day5": int(
            primary["sequence_active_primary"].astype(bool).sum()
        ),
        "primary_active_day10": int(
            primary["sequence_active_sensitivity"].astype(bool).sum()
        ),
        "primary_preexisting": int(
            primary["preexisting_aligned"].astype(bool).sum()
        ),
        "primary_dual_zone_months": int(
            primary.loc[primary["dual_zone_month"].astype(bool), "month_id"].nunique()
        ),
        "stage_primary": _stage_counts(
            opportunities,
            column="stage_primary",
        ),
        "stage_sensitivity": _stage_counts(
            opportunities,
            column="stage_sensitivity",
        ),
        "signal_reach_day5": _signal_reach(ledger, max_day=5),
        "signal_reach_day10": _signal_reach(ledger, max_day=10),
        "first_daily_close": daily.index.min(),
        "last_daily_close": daily.index.max(),
        "first_h4_close": h4.index.min(),
        "last_h4_close": h4.index.max(),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(
        args.out / "wayne_replication_sequence_ledger.csv",
        index=False,
    )
    safe = _json_safe(summary)
    (args.out / "wayne_replication_pair_summary.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
