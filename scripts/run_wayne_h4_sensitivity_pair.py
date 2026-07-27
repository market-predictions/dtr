from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import (
    NEW_YORK_TZ,
    PRIMARY_PAIRS,
    build_h4_health,
    build_h4_monthly_attribution,
    build_monthly_context,
    build_new_york_daily_bars,
    build_new_york_h4_bars,
    build_structure_ledger,
    load_bid_ask_minutes,
    midpoint_minutes,
)

MIN_DAILY_ACTIVE_MINUTES = 1200
MIN_H4_ACTIVE_MINUTES = 180


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one frozen Wayne H4 structural sensitivity ledger."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", choices=PRIMARY_PAIRS, required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
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


def _event_counts(events: pd.Series) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for value in events.fillna(""):
        counter.update(item for item in str(value).split(";") if item)
    return dict(sorted(counter.items()))


def _run_durations(direction: pd.Series) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current = "NONE"
    start = 0
    for position, value in enumerate(direction.astype(str)):
        if value == current:
            continue
        if current in {"BULL", "BEAR"}:
            rows.append(
                {
                    "side": current,
                    "start_pos": start,
                    "end_pos": position - 1,
                    "bars": position - start,
                }
            )
        current = value
        start = position
    if current in {"BULL", "BEAR"}:
        rows.append(
            {
                "side": current,
                "start_pos": start,
                "end_pos": len(direction) - 1,
                "bars": len(direction) - start,
            }
        )
    return rows


def _group_records(
    frame: pd.DataFrame,
    groups: list[str],
    value: str,
) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return (
        frame.groupby(groups, dropna=False, sort=True)[value]
        .size()
        .rename("observations")
        .reset_index()
        .to_dict(orient="records")
    )


def _reach_records(attribution: pd.DataFrame) -> list[dict[str, Any]]:
    if attribution.empty:
        return []
    return (
        attribution.groupby(
            ["h4_relation", "d1_relation", "side", "target_name"],
            dropna=False,
            sort=True,
        )
        .agg(
            observations=("reached_by_month_end", "size"),
            reached=("reached_by_month_end", "sum"),
            reach_rate=("reached_by_month_end", "mean"),
            median_days_to_target=("days_to_target", "median"),
        )
        .reset_index()
        .to_dict(orient="records")
    )


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
    h4 = h4.loc[(h4_year >= args.start_year) & (h4_year <= args.end_year)].copy()

    d1_structure, _d1_swings = build_structure_ledger(daily)
    h4_structure, h4_swings = build_structure_ledger(h4)
    h4_health = build_h4_health(h4)
    monthly_context = build_monthly_context(daily)
    attribution = build_h4_monthly_attribution(
        daily,
        monthly_context,
        d1_structure,
        h4_structure,
        h4_health,
    )

    h4_enriched = h4_structure.join(h4_health, rsuffix="_health")
    h4_enriched.insert(0, "instrument", args.symbol)
    h4_swings.insert(0, "instrument", args.symbol)
    if not attribution.empty:
        attribution.insert(0, "instrument", args.symbol)

    confirmations = h4_enriched.loc[
        h4_enriched["events"].str.contains("TREND_CONFIRMED", na=False)
    ].copy()
    confirmations["side"] = np.where(
        confirmations["events"].str.contains("BULL_TREND_CONFIRMED"),
        "BULL",
        "BEAR",
    )
    confirmation_health = (
        confirmations.groupby(["side", "health_state"], dropna=False, sort=True)
        .size()
        .rename("confirmations")
        .reset_index()
        .to_dict(orient="records")
    )
    unique_opportunities = (
        attribution.drop_duplicates(["instrument", "month_id", "side"])
        if not attribution.empty
        else attribution
    )
    aligned = (
        unique_opportunities.loc[
            unique_opportunities["h4_relation"].eq("ALIGNED_HEALTHY")
        ]
        if not unique_opportunities.empty
        else unique_opportunities
    )

    summary = {
        "instrument": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "source_minutes": int(len(minutes)),
        "active_minutes": int(minutes["active"].sum()),
        "daily_bars": int(len(daily)),
        "h4_bars": int(len(h4)),
        "h4_swing_points": int(len(h4_swings)),
        "h4_event_counts": _event_counts(h4_enriched["events"]),
        "h4_trend_confirmations": int(len(confirmations)),
        "h4_bull_confirmations": int(confirmations["side"].eq("BULL").sum()),
        "h4_bear_confirmations": int(confirmations["side"].eq("BEAR").sum()),
        "h4_confirmation_health": confirmation_health,
        "h4_run_durations": _run_durations(h4_enriched["confirmed_direction"]),
        "monthly_opportunities": int(len(unique_opportunities)),
        "aligned_healthy_months": int(len(aligned)),
        "monthly_category_counts": _group_records(
            unique_opportunities,
            ["h4_relation", "d1_relation", "side"],
            "month_id",
        ),
        "monthly_reach": _reach_records(attribution),
        "first_h4_close": h4.index.min(),
        "last_h4_close": h4.index.max(),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    h4_enriched.to_csv(
        args.out / "wayne_h4_structure_ledger.csv",
        index_label="timestamp_utc",
    )
    h4_swings.to_csv(args.out / "wayne_h4_swings.csv", index=False)
    attribution.to_csv(args.out / "wayne_h4_monthly_attribution.csv", index=False)
    safe = _json_safe(summary)
    (args.out / "wayne_h4_pair_summary.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
