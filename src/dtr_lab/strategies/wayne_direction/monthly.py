from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .calendar import NEW_YORK_TZ
from .structure_common import _validate_ohlc


def traditional_levels(high: float, low: float, close: float) -> dict[str, float]:
    if not all(np.isfinite(value) for value in (high, low, close)) or high <= low:
        raise ValueError("invalid prior-month OHLC")
    pivot = (high + low + close) / 3.0
    width = high - low
    r1 = 2.0 * pivot - low
    s1 = 2.0 * pivot - high
    r2 = pivot + width
    s2 = pivot - width
    return {
        "P": pivot,
        "R1": r1,
        "S1": s1,
        "R2": r2,
        "S2": s2,
        "M1": 0.5 * (s2 + s1),
        "M2": 0.5 * (s1 + pivot),
        "M3": 0.5 * (pivot + r1),
        "M4": 0.5 * (r1 + r2),
    }


def _trading_month_id(index: pd.DatetimeIndex) -> np.ndarray:
    if index.tz is None:
        raise ValueError("daily-bar index must be timezone-aware")
    local_start = index.tz_convert(NEW_YORK_TZ).tz_localize(None)
    trading_date = local_start.normalize() + pd.Timedelta(days=1)
    return (trading_date.year * 100 + trading_date.month).to_numpy(dtype=int)


def build_monthly_context(daily_bars: pd.DataFrame) -> pd.DataFrame:
    daily = _validate_ohlc(daily_bars)
    daily["month_id"] = _trading_month_id(daily.index)
    monthly = daily.groupby("month_id", sort=True).agg(
        month_open=("open", "first"),
        month_high=("high", "max"),
        month_low=("low", "min"),
        month_close=("close", "last"),
        trading_days=("close", "size"),
    )
    monthly["prior_high"] = monthly["month_high"].shift(1)
    monthly["prior_low"] = monthly["month_low"].shift(1)
    monthly["prior_close"] = monthly["month_close"].shift(1)

    names = ("P", "R1", "S1", "R2", "S2", "M1", "M2", "M3", "M4")
    level_rows: list[dict[str, float]] = []
    for row in monthly.itertuples():
        if not all(
            np.isfinite(value)
            for value in (row.prior_high, row.prior_low, row.prior_close)
        ):
            level_rows.append({name: math.nan for name in names})
            continue
        level_rows.append(
            traditional_levels(row.prior_high, row.prior_low, row.prior_close)
        )
    levels = pd.DataFrame(level_rows, index=monthly.index)
    monthly = pd.concat([monthly, levels], axis=1)

    locations: list[str] = []
    for row in monthly.itertuples():
        required = (row.month_open, row.M2, row.P, row.M3)
        if not all(np.isfinite(value) for value in required):
            locations.append("WARMUP")
        elif row.M2 <= row.month_open <= row.P:
            locations.append("BUY_ZONE")
        elif row.P <= row.month_open <= row.M3:
            locations.append("SELL_ZONE")
        elif row.month_open < row.M2:
            locations.append("BELOW_BUY_ZONE")
        elif row.month_open > row.M3:
            locations.append("ABOVE_SELL_ZONE")
        else:
            locations.append("CENTRAL_OTHER")
    monthly["month_open_location"] = locations

    context = daily.loc[:, ["month_id"]].join(monthly, on="month_id")
    context.index = daily.index
    return context


def _first_true(mask: np.ndarray) -> int | None:
    positions = np.flatnonzero(mask)
    return None if len(positions) == 0 else int(positions[0])


def build_monthly_reach_ledger(
    daily_bars: pd.DataFrame,
    structure_ledger: pd.DataFrame,
    monthly_context: pd.DataFrame | None = None,
) -> pd.DataFrame:
    daily = _validate_ohlc(daily_bars)
    if not daily.index.equals(structure_ledger.index):
        raise ValueError("daily bars and structure ledger indexes must match exactly")
    if "confirmed_direction" not in structure_ledger.columns:
        raise ValueError("structure ledger missing confirmed_direction")
    context = (
        build_monthly_context(daily)
        if monthly_context is None
        else monthly_context.copy()
    )
    if not daily.index.equals(context.index):
        raise ValueError("monthly context index must match daily bars")

    joined = daily.join(
        context[
            [
                "month_id",
                "month_open",
                "month_open_location",
                "M1",
                "M2",
                "M3",
                "M4",
                "R1",
                "R2",
                "S1",
                "S2",
            ]
        ]
    ).join(structure_ledger[["confirmed_direction"]])

    rows: list[dict[str, Any]] = []
    for month_id, month in joined.groupby("month_id", sort=True):
        first = month.iloc[0]
        direction = str(first["confirmed_direction"])
        location = str(first["month_open_location"])
        if direction == "BULL" and location == "BUY_ZONE":
            side = "BULL"
            targets = ("M4", "R2")
            path_values = month["high"].to_numpy(dtype=float)
            invalid = month["confirmed_direction"].ne("BULL").to_numpy(dtype=bool)
            comparator = np.greater_equal
        elif direction == "BEAR" and location == "SELL_ZONE":
            side = "BEAR"
            targets = ("M1", "S2")
            path_values = month["low"].to_numpy(dtype=float)
            invalid = month["confirmed_direction"].ne("BEAR").to_numpy(dtype=bool)
            comparator = np.less_equal
        else:
            continue

        invalidation_pos = _first_true(invalid)
        for target_name in targets:
            target = float(first[target_name])
            target_pos = _first_true(comparator(path_values, target))
            reached = target_pos is not None and (
                invalidation_pos is None or target_pos < invalidation_pos
            )
            rows.append(
                {
                    "month_id": int(month_id),
                    "month_start_timestamp": month.index[0],
                    "side": side,
                    "month_open": float(first["month_open"]),
                    "month_open_location": location,
                    "target_name": target_name,
                    "target": target,
                    "reached_before_invalidation": reached,
                    "target_pos": target_pos,
                    "invalidation_pos": invalidation_pos,
                    "days_to_target": target_pos if reached else math.nan,
                    "observed_days": int(len(month)),
                }
            )
    return pd.DataFrame(rows)
