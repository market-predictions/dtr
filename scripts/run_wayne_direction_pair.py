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
    attach_last_completed_h4,
    build_h4_health,
    build_monthly_context,
    build_monthly_reach_ledger,
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
        description="Build one frozen Wayne direction-first pair census."
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


def _confirmation_side(value: str) -> str | None:
    if "BULL_TREND_CONFIRMED" in value:
        return "BULL"
    if "BEAR_TREND_CONFIRMED" in value:
        return "BEAR"
    return None


def _reach_summary(reach: pd.DataFrame) -> list[dict[str, Any]]:
    if reach.empty:
        return []
    grouped = (
        reach.groupby(["side", "target_name"], sort=True)
        .agg(
            observations=("reached_before_invalidation", "size"),
            reached=("reached_before_invalidation", "sum"),
            reach_rate=("reached_before_invalidation", "mean"),
            median_days_to_target=("days_to_target", "median"),
        )
        .reset_index()
    )
    return grouped.to_dict(orient="records")


def _month_open_summary(
    context: pd.DataFrame,
    structure: pd.DataFrame,
) -> list[dict[str, Any]]:
    snapshot = context.groupby("month_id", sort=True).first().copy()
    direction_at_open = structure["confirmed_direction"].shift(1)
    snapshot["direction_at_open"] = direction_at_open.groupby(
        context["month_id"],
        sort=True,
    ).first()
    grouped = (
        snapshot.groupby(
            ["direction_at_open", "month_open_location"],
            dropna=False,
            sort=True,
        )
        .size()
        .rename("months")
        .reset_index()
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

    local_year = daily.index.tz_convert(NEW_YORK_TZ).year
    daily = daily.loc[
        (local_year >= args.start_year) & (local_year <= args.end_year)
    ].copy()
    structure, swings = build_structure_ledger(daily)
    h4_health = build_h4_health(h4)
    enriched = attach_last_completed_h4(structure, h4_health)
    monthly_context = build_monthly_context(daily)
    reach = build_monthly_reach_ledger(daily, structure, monthly_context)

    enriched = enriched.join(daily.add_prefix("d1_"), how="left")
    monthly_columns = [
        "month_id",
        "month_open",
        "month_open_location",
        "P",
        "M1",
        "M2",
        "M3",
        "M4",
        "R1",
        "R2",
        "S1",
        "S2",
    ]
    enriched = enriched.join(monthly_context[monthly_columns], how="left")
    enriched.insert(0, "instrument", args.symbol)
    swings.insert(0, "instrument", args.symbol)
    if not reach.empty:
        reach.insert(0, "instrument", args.symbol)

    confirmations = enriched.loc[
        enriched["events"].str.contains("TREND_CONFIRMED", na=False)
    ].copy()
    confirmations["side"] = confirmations["events"].map(_confirmation_side)
    confirmation_health = (
        confirmations.groupby(["side", "health_state"], dropna=False, sort=True)
        .size()
        .rename("confirmations")
        .reset_index()
        .to_dict(orient="records")
    )

    summary = {
        "instrument": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "source_minutes": int(len(minutes)),
        "active_minutes": int(minutes["active"].sum()),
        "daily_bars": int(len(daily)),
        "h4_bars": int(len(h4)),
        "swing_points": int(len(swings)),
        "event_counts": _event_counts(enriched["events"]),
        "trend_confirmations": int(len(confirmations)),
        "bull_confirmations": int(confirmations["side"].eq("BULL").sum()),
        "bear_confirmations": int(confirmations["side"].eq("BEAR").sum()),
        "confirmation_health": confirmation_health,
        "active_direction_bars": {
            str(key): int(value)
            for key, value in enriched["confirmed_direction"].value_counts().items()
        },
        "month_open_states": _month_open_summary(monthly_context, structure),
        "monthly_reach": _reach_summary(reach),
        "first_daily_close": daily.index.min(),
        "last_daily_close": daily.index.max(),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    daily.to_csv(args.out / "wayne_direction_daily_bars.csv", index_label="timestamp_utc")
    h4_health.to_csv(
        args.out / "wayne_direction_h4_health.csv",
        index_label="timestamp_utc",
    )
    enriched.to_csv(
        args.out / "wayne_direction_structure_ledger.csv",
        index_label="timestamp_utc",
    )
    swings.to_csv(args.out / "wayne_direction_swings.csv", index=False)
    reach.to_csv(args.out / "wayne_direction_monthly_reach.csv", index=False)
    safe = _json_safe(summary)
    (args.out / "wayne_direction_pair_summary.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
