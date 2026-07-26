from __future__ import annotations

import numpy as np
import pandas as pd

from .structure_common import _validate_ohlc

NEW_YORK_TZ = "America/New_York"


def pivot_day_start(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    if index.tz is None:
        raise ValueError("pivot-day assignment requires timezone-aware timestamps")
    local = index.tz_convert(NEW_YORK_TZ)
    local_naive = local.tz_localize(None)
    start_naive = local_naive.normalize() + pd.Timedelta(hours=17)
    start_naive = start_naive.where(
        local_naive >= start_naive,
        start_naive - pd.Timedelta(days=1),
    )
    return pd.DatetimeIndex(start_naive).tz_localize(NEW_YORK_TZ).tz_convert("UTC")


def h4_bar_start(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    if index.tz is None:
        raise ValueError("H4 assignment requires timezone-aware timestamps")
    local = index.tz_convert(NEW_YORK_TZ)
    local_naive = local.tz_localize(None)
    day_start_naive = local_naive.normalize() + pd.Timedelta(hours=17)
    day_start_naive = day_start_naive.where(
        local_naive >= day_start_naive,
        day_start_naive - pd.Timedelta(days=1),
    )
    wall_hours = (
        (local_naive - day_start_naive) / pd.Timedelta(hours=1)
    ).to_numpy(dtype=float)
    bucket = np.floor(wall_hours / 4.0).astype(int)
    if np.any((bucket < 0) | (bucket > 5)):
        raise ValueError("H4 wall-clock bucket outside expected pivot day")
    start_naive = day_start_naive + pd.to_timedelta(bucket * 4, unit="h")
    return (
        pd.DatetimeIndex(start_naive)
        .tz_localize(NEW_YORK_TZ, ambiguous=True, nonexistent="shift_forward")
        .tz_convert("UTC")
    )


def _aggregate(
    frame: pd.DataFrame,
    key: pd.DatetimeIndex,
    *,
    active_column: str | None,
) -> pd.DataFrame:
    bars = _validate_ohlc(frame)
    if active_column is not None:
        if active_column not in bars.columns:
            raise ValueError(f"missing activity column: {active_column}")
        active = bars[active_column].astype(bool)
    else:
        active = pd.Series(True, index=bars.index)

    work = bars.loc[:, ["open", "high", "low", "close"]].copy()
    work["bar_start"] = key
    work["active"] = active.to_numpy(dtype=bool)
    grouped = work.groupby("bar_start", sort=True)
    out = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        observed_minutes=("close", "size"),
        active_minutes=("active", "sum"),
    )
    out.index = pd.DatetimeIndex(out.index)
    out.index.name = "bar_start_utc"
    return out


def build_new_york_daily_bars(
    minutes: pd.DataFrame,
    *,
    active_column: str | None = None,
) -> pd.DataFrame:
    if not isinstance(minutes.index, pd.DatetimeIndex):
        raise TypeError("minute index must be a DatetimeIndex")
    key = pivot_day_start(minutes.index)
    return _aggregate(minutes, key, active_column=active_column)


def build_new_york_h4_bars(
    minutes: pd.DataFrame,
    *,
    active_column: str | None = None,
) -> pd.DataFrame:
    if not isinstance(minutes.index, pd.DatetimeIndex):
        raise TypeError("minute index must be a DatetimeIndex")
    key = h4_bar_start(minutes.index)
    return _aggregate(minutes, key, active_column=active_column)
