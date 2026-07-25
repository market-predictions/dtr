from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

AMSTERDAM_TZ = "Europe/Amsterdam"
NEW_YORK_TZ = "America/New_York"
ASIAN_START_MINUTE = 0
ASIAN_END_MINUTE = 8 * 60
SWEEP_START_MINUTE = 8 * 60
SWEEP_END_MINUTE = 10 * 60
FOLLOW_END_MINUTE = 11 * 60
MIN_ASIAN_ACTIVE_MINUTES = 456
ADVERSE_BARRIER_FRACTION = 0.20
REACTION_FRACTION = 0.25
PIP_SIZE = {"EURUSD": 0.0001, "GBPUSD": 0.0001}
EVENT_COLUMNS = [
    "event_id",
    "instrument",
    "trade_date",
    "week_key",
    "weekday",
    "week_of_month",
    "side",
    "sweep_timestamp_utc",
    "sweep_timestamp_amsterdam",
    "sweep_minute",
    "sweep_before_0900",
    "sweep_half_hour",
    "asian_high",
    "asian_low",
    "asian_midpoint",
    "asian_range_price",
    "asian_range_pips",
    "asian_active_minutes",
    "asian_range_atr20",
    "asian_range_adr20",
    "asian_range_vs_median20",
    "asian_range_percentile20",
    "asian_range_percentile60",
    "asian_range_zscore60",
    "asian_compression_bucket",
    "asian_range_under_20_pip_flag",
    "asian_range_20_30_pip_flag",
    "asian_range_over_30_pip_flag",
    "asian_close_location",
    "asian_return_range_fraction",
    "asian_realized_vol_range_fraction",
    "asian_high_formation_minute",
    "asian_low_formation_minute",
    "asian_high_zone_touches",
    "asian_low_zone_touches",
    "asian_direction_changes",
    "asian_first_half_range_fraction",
    "asian_second_half_range_fraction",
    "pre_sweep_return_range_fraction",
    "pre_sweep_reversal_signed_return",
    "pre_sweep_realized_vol_range_fraction",
    "pre_sweep_boundary_tests",
    "pre_sweep_minutes_from_0800",
    "pre_sweep_trailing_15m_range_fraction",
    "sweep_extreme",
    "sweep_depth_pips",
    "sweep_depth_range_fraction",
    "sweep_body_range_fraction",
    "sweep_wick_range_fraction",
    "sweep_close_beyond_boundary_fraction",
    "sweep_close_location_in_bar",
    "sweep_displacement_vs_trailing_vol",
    "t5_timestamp_utc",
    "t5_available",
    "t5_closes_outside",
    "t5_closes_inside",
    "t5_reclaim",
    "t5_reclaim_delay_minutes",
    "t5_reclaim_depth_range_fraction",
    "t5_return_range_fraction",
    "t5_mfe_range_fraction",
    "t5_mae_range_fraction",
    "t5_extreme_extension_range_fraction",
    "t5_retest_touch",
    "t5_retest_hold",
    "t5_reversal_swing_break",
    "prior_day_high",
    "prior_day_low",
    "prior_day_close",
    "prior_day_return_atr20",
    "prior_week_high",
    "prior_week_low",
    "current_week_pre08_high",
    "current_week_pre08_low",
    "previous_ny_high",
    "previous_ny_low",
    "same_side_level_count",
    "same_side_source_diversity",
    "nearest_same_side_distance_atr",
    "second_same_side_distance_atr",
    "third_same_side_distance_atr",
    "same_side_levels_within_0_05_atr",
    "same_side_levels_within_0_10_atr",
    "same_side_levels_within_0_20_atr",
    "same_side_levels_within_0_25_range",
    "same_side_source_families_within_0_10_atr",
    "same_side_weighted_density",
    "stack_present",
    "stack_member_count",
    "stack_source_diversity",
    "stack_centroid_distance_atr",
    "stack_span_atr",
    "stack_contains_equal_cluster",
    "levels_consumed_before_sweep",
    "levels_consumed_by_sweep",
    "levels_consumed_through_t5",
    "stack_fraction_consumed_t0",
    "stack_fraction_consumed_t5",
    "full_stack_exhausted_t0",
    "full_stack_exhausted_t5",
    "remaining_levels_beyond_t0",
    "remaining_levels_beyond_t5",
    "nearest_remaining_distance_atr_t0",
    "nearest_remaining_distance_atr_t5",
    "residual_density_t0",
    "residual_density_t5",
    "sweep_consumption_class",
    "sweep_stops_inside_stack",
    "opposite_level_count",
    "opposite_source_diversity",
    "nearest_opposite_distance_atr",
    "midpoint_before_nearest_opposite",
    "midpoint_success_09_10",
    "reaction_25",
    "full_range_success",
    "late_midpoint",
    "immediate_continuation",
    "false_reversal",
    "stalled_reaction",
    "two_sided_ambiguous",
    "primary_outcome",
    "midpoint_first_passage_utc",
    "barrier_first_passage_utc",
    "reaction_first_passage_utc",
    "opposite_first_passage_utc",
    "return_5m_range_fraction",
    "mfe_5m_range_fraction",
    "mae_5m_range_fraction",
    "return_15m_range_fraction",
    "mfe_15m_range_fraction",
    "mae_15m_range_fraction",
    "return_30m_range_fraction",
    "mfe_30m_range_fraction",
    "mae_30m_range_fraction",
    "return_60m_range_fraction",
    "mfe_60m_range_fraction",
    "mae_60m_range_fraction",
    "close_1000_range_fraction",
    "close_1100_range_fraction",
]
LEVEL_COLUMNS = [
    "event_id",
    "instrument",
    "trade_date",
    "side",
    "level_id",
    "level_family",
    "level_side",
    "level_price",
    "level_timestamp_utc",
    "member_count",
    "timeframe_diversity",
    "distance_boundary_pips",
    "distance_boundary_range",
    "distance_boundary_atr",
    "distance_pre_sweep_atr",
    "distance_t0_atr",
    "distance_t5_atr",
    "available_at_0800",
    "consumed_before_sweep",
    "consumed_by_sweep",
    "consumed_through_t5",
    "remaining_beyond_t0",
    "remaining_beyond_t5",
    "in_relevant_stack",
]


@dataclass(frozen=True)
class Level:
    level_id: str
    family: str
    side: str
    price: float
    timestamp: pd.Timestamp
    member_count: int = 1
    timeframe_diversity: int = 1


@dataclass(frozen=True)
class FirstPassage:
    timestamp: pd.Timestamp | None
    ambiguous: bool = False


def _minute_of_day(index: pd.DatetimeIndex) -> np.ndarray:
    return index.hour.to_numpy() * 60 + index.minute.to_numpy()


def _percentile(value: float, history: Iterable[float], minimum: int) -> float:
    sample = np.asarray(list(history), dtype=float)
    sample = sample[np.isfinite(sample)]
    if len(sample) < minimum:
        return math.nan
    below = float((sample < value).sum())
    equal = float((sample == value).sum())
    return (below + 0.5 * equal) / len(sample)


def _robust_zscore(value: float, history: Iterable[float], minimum: int = 20) -> float:
    sample = np.asarray(list(history), dtype=float)
    sample = sample[np.isfinite(sample)]
    if len(sample) < minimum:
        return math.nan
    median = float(np.median(sample))
    mad = float(np.median(np.abs(sample - median)))
    if mad <= 1e-12:
        return 0.0
    return 0.6744897501960817 * (value - median) / mad


def _compression_bucket(percentile60: float, history_count: int) -> str:
    if history_count < 20 or not np.isfinite(percentile60):
        return "WARMUP"
    if percentile60 <= 0.20:
        return "ULTRA_COMPRESSED"
    if percentile60 <= 0.50:
        return "LOW_NORMAL"
    if percentile60 < 0.80:
        return "HIGH_NORMAL"
    return "EXPANDED"


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator) or denominator <= 0:
        return math.nan
    return float(numerator / denominator)


def _local_clock(day: pd.Timestamp, hour: int, minute: int = 0) -> pd.Timestamp:
    stamp = pd.Timestamp(day)
    naive = pd.Timestamp(
        year=stamp.year,
        month=stamp.month,
        day=stamp.day,
        hour=hour,
        minute=minute,
    )
    return naive.tz_localize(AMSTERDAM_TZ, ambiguous="raise", nonexistent="raise")


def _local_bounds(day: pd.Timestamp) -> dict[str, pd.Timestamp]:
    base = _local_clock(day, 0)
    return {
        "day_start": base,
        "asian_end": _local_clock(day, 8),
        "sweep_end": _local_clock(day, 10),
        "follow_end": _local_clock(day, 11),
        "day_end": (pd.Timestamp(day) + pd.DateOffset(days=1)).tz_localize(
            AMSTERDAM_TZ, ambiguous="raise", nonexistent="raise"
        ),
    }


def _active_slice(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return frame.loc[
        (frame.index >= start)
        & (frame.index < end)
        & (frame["is_active_quote"] > 0)
    ]


def _validate_minutes(minutes: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "open", "high", "low", "close", "is_active_quote"}
    missing = required.difference(minutes.columns)
    if missing:
        raise ValueError(f"minute frame missing columns: {sorted(missing)}")
    out = minutes.loc[:, sorted(required)].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    if out["timestamp"].duplicated().any():
        raise ValueError("minute frame contains duplicate timestamps")
    for column in ("open", "high", "low", "close", "is_active_quote"):
        out[column] = pd.to_numeric(out[column], errors="raise")
    invalid = (
        (out["high"] < out[["open", "close"]].max(axis=1))
        | (out["low"] > out[["open", "close"]].min(axis=1))
        | (out["high"] < out["low"])
    )
    if invalid.any():
        raise ValueError("minute frame violates OHLC geometry")
    out["timestamp_local"] = out["timestamp"].dt.tz_convert(AMSTERDAM_TZ)
    out = out.set_index("timestamp_local").sort_index()
    return out


def _build_daily_table(frame: pd.DataFrame) -> pd.DataFrame:
    active = frame.loc[frame["is_active_quote"] > 0].copy()
    active["trade_date"] = active.index.date
    daily = active.groupby("trade_date", sort=True).agg(
        high=("high", "max"),
        low=("low", "min"),
        open=("open", "first"),
        close=("close", "last"),
        active_minutes=("close", "size"),
    )
    daily = daily.loc[daily["active_minutes"] >= 1200].copy()
    previous_close = daily["close"].shift(1)
    daily["true_range"] = np.maximum.reduce(
        [
            (daily["high"] - daily["low"]).to_numpy(float),
            (daily["high"] - previous_close).abs().to_numpy(float),
            (daily["low"] - previous_close).abs().to_numpy(float),
        ]
    )
    daily["adr20"] = (daily["high"] - daily["low"]).rolling(20, min_periods=20).mean().shift(1)
    daily["atr20"] = daily["true_range"].rolling(20, min_periods=20).mean().shift(1)
    daily["atr_percentile60"] = [
        _percentile(value, daily["true_range"].iloc[max(0, i - 60) : i], 20)
        for i, value in enumerate(daily["true_range"])
    ]
    return daily


def _build_asian_table(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["trade_date"] = work.index.date
    minute = _minute_of_day(work.index)
    asian = work.loc[
        (minute >= ASIAN_START_MINUTE)
        & (minute < ASIAN_END_MINUTE)
        & (work["is_active_quote"] > 0)
    ].copy()
    grouped = asian.groupby("trade_date", sort=True)
    table = grouped.agg(
        high=("high", "max"),
        low=("low", "min"),
        open=("open", "first"),
        close=("close", "last"),
        active_minutes=("close", "size"),
    )
    table["range"] = table["high"] - table["low"]
    table["median20"] = table["range"].rolling(20, min_periods=20).median().shift(1)
    ranges = table["range"].to_numpy(float)
    p20: list[float] = []
    p60: list[float] = []
    z60: list[float] = []
    for i, value in enumerate(ranges):
        p20.append(_percentile(value, ranges[max(0, i - 20) : i], 20))
        p60.append(_percentile(value, ranges[max(0, i - 60) : i], 20))
        z60.append(_robust_zscore(value, ranges[max(0, i - 60) : i], 20))
    table["percentile20"] = p20
    table["percentile60"] = p60
    table["zscore60"] = z60
    return table


def _resample_ohlc(frame: pd.DataFrame, rule: str) -> pd.DataFrame:
    active = frame.loc[frame["is_active_quote"] > 0, ["open", "high", "low", "close"]]
    expected = int(pd.Timedelta(rule) / pd.Timedelta(minutes=1))
    bars = active.resample(rule, label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        source_minutes=("close", "size"),
    )
    bars = bars.loc[bars["source_minutes"] >= max(1, int(expected * 0.80))].dropna()
    bars["bar_end"] = bars.index + pd.Timedelta(rule)
    return bars


def _confirmed_pivots(frame: pd.DataFrame, rule: str, family: str) -> list[Level]:
    bars = _resample_ohlc(frame, rule)
    high = bars["high"]
    low = bars["low"]
    pivot_high = (
        (high > high.shift(1))
        & (high > high.shift(2))
        & (high >= high.shift(-1))
        & (high >= high.shift(-2))
    )
    pivot_low = (
        (low < low.shift(1))
        & (low < low.shift(2))
        & (low <= low.shift(-1))
        & (low <= low.shift(-2))
    )
    levels: list[Level] = []
    for position in np.flatnonzero(pivot_high.fillna(False).to_numpy()):
        if position + 2 >= len(bars):
            continue
        confirmation = pd.Timestamp(bars.iloc[position + 2]["bar_end"])
        pivot_time = pd.Timestamp(bars.index[position])
        levels.append(
            Level(
                level_id=f"{family}_HIGH_{pivot_time.isoformat()}",
                family=family,
                side="HIGH",
                price=float(high.iloc[position]),
                timestamp=confirmation,
            )
        )
    for position in np.flatnonzero(pivot_low.fillna(False).to_numpy()):
        if position + 2 >= len(bars):
            continue
        confirmation = pd.Timestamp(bars.iloc[position + 2]["bar_end"])
        pivot_time = pd.Timestamp(bars.index[position])
        levels.append(
            Level(
                level_id=f"{family}_LOW_{pivot_time.isoformat()}",
                family=family,
                side="LOW",
                price=float(low.iloc[position]),
                timestamp=confirmation,
            )
        )
    return sorted(levels, key=lambda level: (level.timestamp, level.level_id))


def _previous_completed_ny_sessions(frame: pd.DataFrame) -> pd.DataFrame:
    ny = frame.copy()
    ny_index = ny.index.tz_convert(NEW_YORK_TZ)
    minute = ny_index.hour.to_numpy() * 60 + ny_index.minute.to_numpy()
    ny = ny.loc[
        (minute >= 8 * 60)
        & (minute < 17 * 60)
        & (ny["is_active_quote"] > 0)
    ].copy()
    if ny.empty:
        return pd.DataFrame(columns=["start", "end", "high", "low"])
    ny["ny_date"] = ny.index.tz_convert(NEW_YORK_TZ).date
    rows: list[dict[str, Any]] = []
    for ny_date, group in ny.groupby("ny_date", sort=True):
        start = pd.Timestamp(ny_date).tz_localize(NEW_YORK_TZ) + pd.Timedelta(hours=8)
        end = pd.Timestamp(ny_date).tz_localize(NEW_YORK_TZ) + pd.Timedelta(hours=17)
        if len(group) < 480:
            continue
        rows.append(
            {
                "ny_date": ny_date,
                "start": start.tz_convert(AMSTERDAM_TZ),
                "end": end.tz_convert(AMSTERDAM_TZ),
                "high": float(group["high"].max()),
                "low": float(group["low"].min()),
            }
        )
    return pd.DataFrame(rows).set_index("ny_date")


def _previous_week_table(daily: pd.DataFrame) -> pd.DataFrame:
    rows = daily.reset_index().copy()
    rows["date_ts"] = pd.to_datetime(rows["trade_date"])
    rows["week_start"] = rows["date_ts"] - pd.to_timedelta(rows["date_ts"].dt.weekday, unit="D")
    weekly = rows.groupby("week_start", sort=True).agg(high=("high", "max"), low=("low", "min"))
    weekly["previous_high"] = weekly["high"].shift(1)
    weekly["previous_low"] = weekly["low"].shift(1)
    return weekly


def _first_passage(
    path: pd.DataFrame,
    *,
    side: str,
    target: float,
    barrier: float,
) -> tuple[FirstPassage, FirstPassage]:
    target_time: pd.Timestamp | None = None
    barrier_time: pd.Timestamp | None = None
    target_ambiguous = False
    barrier_ambiguous = False
    for timestamp, row in path.iterrows():
        if side == "UP":
            target_hit = float(row["low"]) <= target
            barrier_hit = float(row["high"]) >= barrier
        else:
            target_hit = float(row["high"]) >= target
            barrier_hit = float(row["low"]) <= barrier
        if target_hit and barrier_hit:
            target_time = pd.Timestamp(timestamp)
            barrier_time = pd.Timestamp(timestamp)
            target_ambiguous = True
            barrier_ambiguous = True
            break
        if target_hit and target_time is None:
            target_time = pd.Timestamp(timestamp)
            break
        if barrier_hit and barrier_time is None:
            barrier_time = pd.Timestamp(timestamp)
            break
    return (
        FirstPassage(target_time, target_ambiguous),
        FirstPassage(barrier_time, barrier_ambiguous),
    )


def _single_first_passage(path: pd.DataFrame, side: str, price: float) -> pd.Timestamp | None:
    if path.empty:
        return None
    if side == "UP":
        hits = path.index[path["low"] <= price]
    else:
        hits = path.index[path["high"] >= price]
    return pd.Timestamp(hits[0]) if len(hits) else None


def _opposite_boundary_passage(path: pd.DataFrame, side: str, price: float) -> pd.Timestamp | None:
    if path.empty:
        return None
    if side == "UP":
        hits = path.index[path["low"] < price]
    else:
        hits = path.index[path["high"] > price]
    return pd.Timestamp(hits[0]) if len(hits) else None


def _path_metrics(
    path: pd.DataFrame,
    *,
    side: str,
    anchor: float,
    reference_range: float,
) -> tuple[float, float, float]:
    if path.empty:
        return math.nan, math.nan, math.nan
    direction = -1.0 if side == "UP" else 1.0
    signed_return = direction * (float(path.iloc[-1]["close"]) - anchor) / reference_range
    if side == "UP":
        mfe = (anchor - float(path["low"].min())) / reference_range
        mae = (float(path["high"].max()) - anchor) / reference_range
    else:
        mfe = (float(path["high"].max()) - anchor) / reference_range
        mae = (anchor - float(path["low"].min())) / reference_range
    return float(signed_return), float(mfe), float(mae)


def _touch_count(values: np.ndarray, level: float, tolerance: float) -> int:
    if len(values) == 0:
        return 0
    mask = np.abs(values - level) <= tolerance
    count = 0
    active = False
    for hit in mask:
        if hit and not active:
            count += 1
        active = bool(hit)
    return count


def _recent_eligible_cutoff(
    eligible_dates: list[object], trade_date: object, lookback: int
) -> object | None:
    try:
        position = eligible_dates.index(trade_date)
    except ValueError:
        return None
    if position <= 0:
        return None
    return eligible_dates[max(0, position - lookback)]


def _pivot_unswept(
    frame: pd.DataFrame,
    level: Level,
    snapshot: pd.Timestamp,
    tolerance: float,
) -> bool:
    if level.timestamp >= snapshot:
        return False
    path = _active_slice(frame, level.timestamp, snapshot)
    if path.empty:
        return True
    if level.side == "HIGH":
        return float(path["high"].max()) < level.price + tolerance
    return float(path["low"].min()) > level.price - tolerance


def _cluster_levels(levels: list[Level], tolerance: float, snapshot: pd.Timestamp) -> list[Level]:
    clusters: list[Level] = []
    for side in ("HIGH", "LOW"):
        candidates = sorted(
            [level for level in levels if level.side == side],
            key=lambda level: level.price,
        )
        current: list[Level] = []
        for level in candidates:
            if not current or abs(level.price - current[-1].price) <= tolerance:
                current.append(level)
                continue
            if len(current) >= 2:
                clusters.append(_make_cluster(current, side, snapshot))
            current = [level]
        if len(current) >= 2:
            clusters.append(_make_cluster(current, side, snapshot))
    return clusters


def _make_cluster(levels: list[Level], side: str, snapshot: pd.Timestamp) -> Level:
    families = {level.family for level in levels}
    price = float(np.mean([level.price for level in levels]))
    ids = "|".join(sorted(level.level_id for level in levels))
    return Level(
        level_id=(
            f"EQUAL_CLUSTER_{side}_{snapshot.isoformat()}_"
            f"{hashlib.sha256(ids.encode('utf-8')).hexdigest()[:12]}"
        ),
        family="EQUAL_CLUSTER",
        side=side,
        price=price,
        timestamp=max(level.timestamp for level in levels),
        member_count=len(levels),
        timeframe_diversity=len(families),
    )


def _session_levels(
    *,
    trade_date: object,
    asian_high: float,
    asian_low: float,
    day_start: pd.Timestamp,
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    ny_sessions: pd.DataFrame,
    frame: pd.DataFrame,
) -> list[Level]:
    levels: list[Level] = []
    dates = list(daily.index)
    if trade_date in daily.index:
        position = dates.index(trade_date)
        if position > 0:
            prior_date = dates[position - 1]
            prior = daily.loc[prior_date]
            prior_end = pd.Timestamp(prior_date).tz_localize(AMSTERDAM_TZ) + pd.DateOffset(days=1)
            levels.extend(
                [
                    Level("PRIOR_DAY_HIGH", "PRIOR_DAY", "HIGH", float(prior["high"]), prior_end),
                    Level("PRIOR_DAY_LOW", "PRIOR_DAY", "LOW", float(prior["low"]), prior_end),
                ]
            )
    week_start = pd.Timestamp(trade_date) - pd.Timedelta(days=pd.Timestamp(trade_date).weekday())
    if week_start in weekly.index:
        row = weekly.loc[week_start]
        if np.isfinite(row["previous_high"]):
            levels.append(
                Level(
                    "PRIOR_WEEK_HIGH",
                    "PRIOR_WEEK",
                    "HIGH",
                    float(row["previous_high"]),
                    week_start.tz_localize(AMSTERDAM_TZ),
                )
            )
        if np.isfinite(row["previous_low"]):
            levels.append(
                Level(
                    "PRIOR_WEEK_LOW",
                    "PRIOR_WEEK",
                    "LOW",
                    float(row["previous_low"]),
                    week_start.tz_localize(AMSTERDAM_TZ),
                )
            )
    current_week_path = _active_slice(
        frame,
        week_start.tz_localize(AMSTERDAM_TZ),
        day_start,
    )
    if not current_week_path.empty:
        levels.extend(
            [
                Level(
                    "CURRENT_WEEK_PRE08_HIGH",
                    "CURRENT_WEEK",
                    "HIGH",
                    float(current_week_path["high"].max()),
                    day_start,
                ),
                Level(
                    "CURRENT_WEEK_PRE08_LOW",
                    "CURRENT_WEEK",
                    "LOW",
                    float(current_week_path["low"].min()),
                    day_start,
                ),
            ]
        )
    if not ny_sessions.empty:
        completed = ny_sessions.loc[ny_sessions["end"] <= day_start]
        if not completed.empty:
            row = completed.iloc[-1]
            levels.extend(
                [
                    Level(
                        "PREVIOUS_NY_HIGH",
                        "PREVIOUS_NY",
                        "HIGH",
                        float(row["high"]),
                        pd.Timestamp(row["end"]),
                    ),
                    Level(
                        "PREVIOUS_NY_LOW",
                        "PREVIOUS_NY",
                        "LOW",
                        float(row["low"]),
                        pd.Timestamp(row["end"]),
                    ),
                ]
            )
    return [
        level
        for level in levels
        if not (
            (level.side == "HIGH" and abs(level.price - asian_high) <= 1e-12)
            or (level.side == "LOW" and abs(level.price - asian_low) <= 1e-12)
        )
    ]


def _select_pivots(
    *,
    pivots: list[Level],
    frame: pd.DataFrame,
    snapshot: pd.Timestamp,
    trade_date: object,
    eligible_dates: list[object],
    pip: float,
    atr20: float,
) -> list[Level]:
    selected: list[Level] = []
    for family, lookback, limit in (("M15_PIVOT", 5, 5), ("H1_PIVOT", 20, 3)):
        cutoff = _recent_eligible_cutoff(eligible_dates, trade_date, lookback)
        candidates = [
            level
            for level in pivots
            if level.family == family
            and level.timestamp < snapshot
            and (cutoff is None or level.timestamp.date() >= cutoff)
        ]
        tolerance = max(pip, 0.001 * atr20) if np.isfinite(atr20) else pip
        candidates = [
            level
            for level in candidates
            if _pivot_unswept(frame, level, snapshot, tolerance)
        ]
        candidates = sorted(candidates, key=lambda level: level.timestamp, reverse=True)[:limit]
        selected.extend(candidates)
    cluster_tolerance = max(pip, 0.03 * atr20) if np.isfinite(atr20) else pip
    selected.extend(_cluster_levels(selected, cluster_tolerance, snapshot))
    return selected


def _distance_for_side(side: str, level_price: float, reference: float) -> float:
    return level_price - reference if side == "UP" else reference - level_price


def _level_reached(path: pd.DataFrame, side: str, price: float) -> bool:
    if path.empty:
        return False
    if side == "UP":
        return bool((path["high"] >= price).any())
    return bool((path["low"] <= price).any())


def _relevant_levels(
    levels: list[Level],
    *,
    side: str,
    asian_high: float,
    asian_low: float,
    tolerance: float,
) -> tuple[list[Level], list[Level]]:
    if side == "UP":
        same = [
            level
            for level in levels
            if level.side == "HIGH" and level.price >= asian_high - tolerance
        ]
        opposite = [
            level
            for level in levels
            if level.side == "LOW" and level.price <= asian_low + tolerance
        ]
    else:
        same = [
            level
            for level in levels
            if level.side == "LOW" and level.price <= asian_low + tolerance
        ]
        opposite = [
            level
            for level in levels
            if level.side == "HIGH" and level.price >= asian_high - tolerance
        ]
    same = sorted(
        same,
        key=lambda level: _distance_for_side(
            side,
            level.price,
            asian_high if side == "UP" else asian_low,
        ),
    )
    return same, opposite


def _stack_members(
    levels: list[Level],
    *,
    side: str,
    boundary: float,
    atr20: float,
) -> list[Level]:
    if not levels or not np.isfinite(atr20) or atr20 <= 0:
        return []
    nearest_distance = _distance_for_side(side, levels[0].price, boundary) / atr20
    if nearest_distance > 0.15:
        return []
    candidate: list[Level] = [levels[0]]
    for level in levels[1:]:
        distance = abs(level.price - candidate[-1].price) / atr20
        if distance <= 0.10:
            candidate.append(level)
        else:
            break
    if len(candidate) < 2 or len({level.family for level in candidate}) < 2:
        return []
    return candidate


def _liquidity_features(
    *,
    event_id: str,
    instrument: str,
    trade_date: object,
    side: str,
    levels: list[Level],
    asian_high: float,
    asian_low: float,
    asian_range: float,
    pip: float,
    atr20: float,
    pre_sweep_price: float,
    sweep_extreme: float,
    t5_price: float,
    path_0800_pre: pd.DataFrame,
    sweep_bar: pd.DataFrame,
    path_sweep_t5: pd.DataFrame,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    boundary = asian_high if side == "UP" else asian_low
    tolerance = max(pip, 0.001 * atr20) if np.isfinite(atr20) else pip
    same, opposite = _relevant_levels(
        levels,
        side=side,
        asian_high=asian_high,
        asian_low=asian_low,
        tolerance=tolerance,
    )
    stack = _stack_members(same, side=side, boundary=boundary, atr20=atr20)
    stack_ids = {level.level_id for level in stack}
    records: list[dict[str, Any]] = []
    same_distances_atr: list[float] = []
    available_levels: list[Level] = []
    consumed_before: list[Level] = []
    consumed_sweep: list[Level] = []
    consumed_t5: list[Level] = []
    remaining_t0: list[Level] = []
    remaining_t5: list[Level] = []
    for level in same:
        distance_boundary = _distance_for_side(side, level.price, boundary)
        distance_pre = _distance_for_side(side, level.price, pre_sweep_price)
        distance_t0 = _distance_for_side(side, level.price, sweep_extreme)
        distance_t5 = _distance_for_side(side, level.price, t5_price)
        distance_boundary_atr = _safe_ratio(distance_boundary, atr20)
        same_distances_atr.append(distance_boundary_atr)
        available = distance_boundary >= -tolerance
        before = _level_reached(path_0800_pre, side, level.price)
        by_sweep = (not before) and _level_reached(sweep_bar, side, level.price)
        by_t5 = (not before) and _level_reached(path_sweep_t5, side, level.price)
        rem_t0 = distance_t0 > tolerance
        rem_t5 = distance_t5 > tolerance
        if available:
            available_levels.append(level)
        if before:
            consumed_before.append(level)
        if by_sweep:
            consumed_sweep.append(level)
        if by_t5:
            consumed_t5.append(level)
        if rem_t0:
            remaining_t0.append(level)
        if rem_t5:
            remaining_t5.append(level)
        records.append(
            {
                "event_id": event_id,
                "instrument": instrument,
                "trade_date": str(trade_date),
                "side": side,
                "level_id": level.level_id,
                "level_family": level.family,
                "level_side": level.side,
                "level_price": level.price,
                "level_timestamp_utc": level.timestamp.tz_convert("UTC").isoformat(),
                "member_count": level.member_count,
                "timeframe_diversity": level.timeframe_diversity,
                "distance_boundary_pips": distance_boundary / pip,
                "distance_boundary_range": _safe_ratio(distance_boundary, asian_range),
                "distance_boundary_atr": distance_boundary_atr,
                "distance_pre_sweep_atr": _safe_ratio(distance_pre, atr20),
                "distance_t0_atr": _safe_ratio(distance_t0, atr20),
                "distance_t5_atr": _safe_ratio(distance_t5, atr20),
                "available_at_0800": available,
                "consumed_before_sweep": before,
                "consumed_by_sweep": by_sweep,
                "consumed_through_t5": by_t5,
                "remaining_beyond_t0": rem_t0,
                "remaining_beyond_t5": rem_t5,
                "in_relevant_stack": level.level_id in stack_ids,
            }
        )
    distances = [value for value in same_distances_atr if np.isfinite(value) and value >= 0]
    distances_sorted = sorted(distances)
    families_010 = {
        level.family
        for level, distance in zip(same, same_distances_atr, strict=False)
        if np.isfinite(distance) and 0 <= distance <= 0.10
    }
    stack_consumed_t0 = sum(level in consumed_sweep or level in consumed_before for level in stack)
    stack_consumed_t5 = sum(level in consumed_t5 or level in consumed_before for level in stack)
    stack_fraction_t0 = stack_consumed_t0 / len(stack) if stack else math.nan
    stack_fraction_t5 = stack_consumed_t5 / len(stack) if stack else math.nan
    residual_t0_distances = [
        _safe_ratio(_distance_for_side(side, level.price, sweep_extreme), atr20)
        for level in remaining_t0
    ]
    residual_t5_distances = [
        _safe_ratio(_distance_for_side(side, level.price, t5_price), atr20)
        for level in remaining_t5
    ]
    opposing_distances = [
        _safe_ratio(abs(level.price - sweep_extreme), atr20) for level in opposite
    ]
    nearest_opposite = min(
        [value for value in opposing_distances if np.isfinite(value)],
        default=math.nan,
    )
    midpoint_distance = _safe_ratio(abs(((asian_high + asian_low) / 2.0) - sweep_extreme), atr20)
    if not consumed_sweep:
        consumption_class = "ASIAN_BOUNDARY_ONLY"
    elif len(consumed_sweep) == 1:
        consumption_class = "ONE_EXTERNAL_LEVEL"
    else:
        consumption_class = "MULTIPLE_EXTERNAL_LEVELS"
    stack_prices = [level.price for level in stack]
    if stack:
        stack_span = (max(stack_prices) - min(stack_prices)) / atr20
        stack_centroid = _distance_for_side(side, float(np.mean(stack_prices)), boundary) / atr20
        furthest = max(_distance_for_side(side, level.price, boundary) for level in stack)
        sweep_distance = _distance_for_side(side, sweep_extreme, boundary)
        stops_inside = sweep_distance < furthest - tolerance
    else:
        stack_span = math.nan
        stack_centroid = math.nan
        stops_inside = False
    features = {
        "same_side_level_count": len(same),
        "same_side_source_diversity": len({level.family for level in same}),
        "nearest_same_side_distance_atr": distances_sorted[0] if distances_sorted else math.nan,
        "second_same_side_distance_atr": distances_sorted[1]
        if len(distances_sorted) > 1
        else math.nan,
        "third_same_side_distance_atr": distances_sorted[2]
        if len(distances_sorted) > 2
        else math.nan,
        "same_side_levels_within_0_05_atr": sum(value <= 0.05 for value in distances),
        "same_side_levels_within_0_10_atr": sum(value <= 0.10 for value in distances),
        "same_side_levels_within_0_20_atr": sum(value <= 0.20 for value in distances),
        "same_side_levels_within_0_25_range": sum(
            0 <= _distance_for_side(side, level.price, boundary) <= 0.25 * asian_range
            for level in same
        ),
        "same_side_source_families_within_0_10_atr": len(families_010),
        "same_side_weighted_density": float(
            sum(math.exp(-value / 0.10) for value in distances)
        ),
        "stack_present": bool(stack),
        "stack_member_count": len(stack),
        "stack_source_diversity": len({level.family for level in stack}),
        "stack_centroid_distance_atr": stack_centroid,
        "stack_span_atr": stack_span,
        "stack_contains_equal_cluster": any(
            level.family == "EQUAL_CLUSTER" for level in stack
        ),
        "levels_consumed_before_sweep": len(consumed_before),
        "levels_consumed_by_sweep": len(consumed_sweep),
        "levels_consumed_through_t5": len(consumed_t5),
        "stack_fraction_consumed_t0": stack_fraction_t0,
        "stack_fraction_consumed_t5": stack_fraction_t5,
        "full_stack_exhausted_t0": bool(stack) and stack_fraction_t0 == 1.0,
        "full_stack_exhausted_t5": bool(stack) and stack_fraction_t5 == 1.0,
        "remaining_levels_beyond_t0": len(remaining_t0),
        "remaining_levels_beyond_t5": len(remaining_t5),
        "nearest_remaining_distance_atr_t0": min(
            [value for value in residual_t0_distances if np.isfinite(value)],
            default=math.nan,
        ),
        "nearest_remaining_distance_atr_t5": min(
            [value for value in residual_t5_distances if np.isfinite(value)],
            default=math.nan,
        ),
        "residual_density_t0": float(
            sum(
                math.exp(-value / 0.10)
                for value in residual_t0_distances
                if np.isfinite(value) and value >= 0
            )
        ),
        "residual_density_t5": float(
            sum(
                math.exp(-value / 0.10)
                for value in residual_t5_distances
                if np.isfinite(value) and value >= 0
            )
        ),
        "sweep_consumption_class": consumption_class,
        "sweep_stops_inside_stack": stops_inside,
        "opposite_level_count": len(opposite),
        "opposite_source_diversity": len({level.family for level in opposite}),
        "nearest_opposite_distance_atr": nearest_opposite,
        "midpoint_before_nearest_opposite": bool(
            np.isfinite(midpoint_distance)
            and np.isfinite(nearest_opposite)
            and midpoint_distance <= nearest_opposite
        ),
    }
    return features, records


def _event_outcomes(
    *,
    path_to_1000: pd.DataFrame,
    path_to_1100: pd.DataFrame,
    side: str,
    sweep_extreme: float,
    asian_high: float,
    asian_low: float,
    asian_range: float,
) -> dict[str, Any]:
    midpoint = (asian_high + asian_low) / 2.0
    barrier = (
        sweep_extreme + ADVERSE_BARRIER_FRACTION * asian_range
        if side == "UP"
        else sweep_extreme - ADVERSE_BARRIER_FRACTION * asian_range
    )
    reaction = (
        sweep_extreme - REACTION_FRACTION * asian_range
        if side == "UP"
        else sweep_extreme + REACTION_FRACTION * asian_range
    )
    midpoint_passage, barrier_passage = _first_passage(
        path_to_1100,
        side=side,
        target=midpoint,
        barrier=barrier,
    )
    reaction_passage = _single_first_passage(path_to_1100, side, reaction)
    opposite_passage = _opposite_boundary_passage(
        path_to_1100,
        side,
        asian_low if side == "UP" else asian_high,
    )
    resolution_times = [
        timestamp
        for timestamp in (midpoint_passage.timestamp, barrier_passage.timestamp)
        if timestamp is not None
    ]
    resolution = min(resolution_times) if resolution_times else None
    two_sided = (
        opposite_passage is not None
        and (resolution is None or opposite_passage <= resolution)
        and (
            midpoint_passage.timestamp is None
            or opposite_passage != midpoint_passage.timestamp
        )
    )
    ambiguous = midpoint_passage.ambiguous or barrier_passage.ambiguous or two_sided
    midpoint_by_1000 = (
        midpoint_passage.timestamp is not None
        and not path_to_1000.empty
        and midpoint_passage.timestamp < path_to_1000.index.max() + pd.Timedelta(minutes=1)
    )
    midpoint_before_barrier = (
        midpoint_passage.timestamp is not None
        and (
            barrier_passage.timestamp is None
            or midpoint_passage.timestamp < barrier_passage.timestamp
        )
    )
    success = bool(midpoint_by_1000 and midpoint_before_barrier and not ambiguous)
    reaction_before_barrier = (
        reaction_passage is not None
        and (
            barrier_passage.timestamp is None
            or reaction_passage < barrier_passage.timestamp
        )
    )
    barrier_before_reaction = (
        barrier_passage.timestamp is not None
        and (
            reaction_passage is None
            or barrier_passage.timestamp < reaction_passage
        )
    )
    late_midpoint = bool(
        midpoint_passage.timestamp is not None
        and not midpoint_by_1000
        and midpoint_before_barrier
        and not ambiguous
    )
    false_reversal = bool(
        reaction_before_barrier
        and not success
        and barrier_passage.timestamp is not None
        and reaction_passage is not None
        and reaction_passage < barrier_passage.timestamp
        and not ambiguous
    )
    immediate = bool(barrier_before_reaction and not ambiguous)
    stalled = bool(
        not success
        and not late_midpoint
        and not false_reversal
        and not immediate
        and not ambiguous
    )
    if ambiguous:
        primary = "TWO_SIDED_AMBIGUOUS"
    elif success:
        primary = "MIDPOINT_SUCCESS_09_10"
    elif immediate:
        primary = "IMMEDIATE_CONTINUATION"
    elif false_reversal:
        primary = "FALSE_REVERSAL"
    elif late_midpoint:
        primary = "LATE_MIDPOINT"
    else:
        primary = "STALLED_REACTION"
    full_range = bool(
        opposite_passage is not None
        and (
            barrier_passage.timestamp is None
            or opposite_passage < barrier_passage.timestamp
        )
        and not ambiguous
    )
    return {
        "midpoint_success_09_10": success,
        "reaction_25": bool(reaction_before_barrier and not ambiguous),
        "full_range_success": full_range,
        "late_midpoint": late_midpoint,
        "immediate_continuation": immediate,
        "false_reversal": false_reversal,
        "stalled_reaction": stalled,
        "two_sided_ambiguous": ambiguous,
        "primary_outcome": primary,
        "midpoint_first_passage_utc": (
            midpoint_passage.timestamp.tz_convert("UTC").isoformat()
            if midpoint_passage.timestamp is not None
            else None
        ),
        "barrier_first_passage_utc": (
            barrier_passage.timestamp.tz_convert("UTC").isoformat()
            if barrier_passage.timestamp is not None
            else None
        ),
        "reaction_first_passage_utc": (
            reaction_passage.tz_convert("UTC").isoformat()
            if reaction_passage is not None
            else None
        ),
        "opposite_first_passage_utc": (
            opposite_passage.tz_convert("UTC").isoformat()
            if opposite_passage is not None
            else None
        ),
    }


def _t5_features(
    *,
    side: str,
    boundary: float,
    asian_range: float,
    sweep_extreme: float,
    path: pd.DataFrame,
) -> dict[str, Any]:
    if path.empty:
        return {
            "t5_timestamp_utc": None,
            "t5_available": False,
            "t5_closes_outside": 0,
            "t5_closes_inside": 0,
            "t5_reclaim": False,
            "t5_reclaim_delay_minutes": math.nan,
            "t5_reclaim_depth_range_fraction": math.nan,
            "t5_return_range_fraction": math.nan,
            "t5_mfe_range_fraction": math.nan,
            "t5_mae_range_fraction": math.nan,
            "t5_extreme_extension_range_fraction": math.nan,
            "t5_retest_touch": False,
            "t5_retest_hold": False,
            "t5_reversal_swing_break": False,
        }
    closes_outside = (
        path["close"] > boundary if side == "UP" else path["close"] < boundary
    )
    closes_inside = ~closes_outside
    reclaim_positions = np.flatnonzero(closes_inside.to_numpy())
    reclaim = len(reclaim_positions) > 0
    reclaim_delay = float(reclaim_positions[0] + 1) if reclaim else math.nan
    final_close = float(path.iloc[-1]["close"])
    reclaim_depth = (
        (boundary - final_close) / asian_range
        if side == "UP"
        else (final_close - boundary) / asian_range
    )
    anchor = float(path.iloc[0]["open"])
    signed_return, mfe, mae = _path_metrics(
        path,
        side=side,
        anchor=anchor,
        reference_range=asian_range,
    )
    extreme_extension = (
        (float(path["high"].max()) - sweep_extreme) / asian_range
        if side == "UP"
        else (sweep_extreme - float(path["low"].min())) / asian_range
    )
    if side == "UP":
        retest_touch = bool((path["high"] >= boundary).any()) if reclaim else False
        retest_hold = bool(final_close < boundary) if retest_touch else False
        prior_swing = float(path.iloc[: max(1, len(path) - 1)]["low"].min())
        swing_break = float(path.iloc[-1]["close"]) < prior_swing
    else:
        retest_touch = bool((path["low"] <= boundary).any()) if reclaim else False
        retest_hold = bool(final_close > boundary) if retest_touch else False
        prior_swing = float(path.iloc[: max(1, len(path) - 1)]["high"].max())
        swing_break = float(path.iloc[-1]["close"]) > prior_swing
    return {
        "t5_timestamp_utc": path.index[-1].tz_convert("UTC").isoformat(),
        "t5_available": len(path) >= 5,
        "t5_closes_outside": int(closes_outside.sum()),
        "t5_closes_inside": int(closes_inside.sum()),
        "t5_reclaim": reclaim,
        "t5_reclaim_delay_minutes": reclaim_delay,
        "t5_reclaim_depth_range_fraction": float(reclaim_depth),
        "t5_return_range_fraction": signed_return,
        "t5_mfe_range_fraction": mfe,
        "t5_mae_range_fraction": mae,
        "t5_extreme_extension_range_fraction": float(extreme_extension),
        "t5_retest_touch": retest_touch,
        "t5_retest_hold": retest_hold,
        "t5_reversal_swing_break": swing_break,
    }


def _formation_minute(frame: pd.DataFrame, column: str, value: float) -> int:
    matches = frame.index[np.isclose(frame[column].to_numpy(float), value)]
    if len(matches) == 0:
        return -1
    timestamp = pd.Timestamp(matches[0])
    return timestamp.hour * 60 + timestamp.minute


def _prior_context(
    trade_date: object,
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    ny_sessions: pd.DataFrame,
    day_start: pd.Timestamp,
    frame: pd.DataFrame,
) -> dict[str, float]:
    result = {
        "prior_day_high": math.nan,
        "prior_day_low": math.nan,
        "prior_day_close": math.nan,
        "prior_day_return_atr20": math.nan,
        "prior_week_high": math.nan,
        "prior_week_low": math.nan,
        "current_week_pre08_high": math.nan,
        "current_week_pre08_low": math.nan,
        "previous_ny_high": math.nan,
        "previous_ny_low": math.nan,
    }
    dates = list(daily.index)
    if trade_date in daily.index:
        position = dates.index(trade_date)
        if position > 0:
            prior = daily.loc[dates[position - 1]]
            result["prior_day_high"] = float(prior["high"])
            result["prior_day_low"] = float(prior["low"])
            result["prior_day_close"] = float(prior["close"])
            if position > 1:
                prior_previous = daily.loc[dates[position - 2]]
                atr = float(daily.loc[trade_date, "atr20"])
                result["prior_day_return_atr20"] = _safe_ratio(
                    float(prior["close"] - prior_previous["close"]),
                    atr,
                )
    week_start = pd.Timestamp(trade_date) - pd.Timedelta(days=pd.Timestamp(trade_date).weekday())
    if week_start in weekly.index:
        row = weekly.loc[week_start]
        result["prior_week_high"] = float(row["previous_high"])
        result["prior_week_low"] = float(row["previous_low"])
    current = _active_slice(
        frame,
        week_start.tz_localize(AMSTERDAM_TZ),
        day_start,
    )
    if not current.empty:
        result["current_week_pre08_high"] = float(current["high"].max())
        result["current_week_pre08_low"] = float(current["low"].min())
    if not ny_sessions.empty:
        completed = ny_sessions.loc[ny_sessions["end"] <= day_start]
        if not completed.empty:
            row = completed.iloc[-1]
            result["previous_ny_high"] = float(row["high"])
            result["previous_ny_low"] = float(row["low"])
    return result


def build_fingerprint_ledgers(
    symbol: str,
    minutes: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    symbol = symbol.upper()
    if symbol not in PIP_SIZE:
        raise ValueError(f"unsupported symbol: {symbol}")
    if end_year < start_year:
        raise ValueError("end_year must be >= start_year")
    pip = PIP_SIZE[symbol]
    frame = _validate_minutes(minutes)
    daily = _build_daily_table(frame)
    asian_table = _build_asian_table(frame)
    weekly = _previous_week_table(daily)
    ny_sessions = _previous_completed_ny_sessions(frame)
    pivots = _confirmed_pivots(frame, "15min", "M15_PIVOT")
    pivots.extend(_confirmed_pivots(frame, "1h", "H1_PIVOT"))
    pivots = sorted(pivots, key=lambda level: (level.timestamp, level.level_id))
    eligible_dates = [
        date
        for date, row in asian_table.iterrows()
        if int(row["active_minutes"]) >= MIN_ASIAN_ACTIVE_MINUTES
        and float(row["range"]) > 0
    ]
    events: list[dict[str, Any]] = []
    level_records: list[dict[str, Any]] = []
    session_rows: list[dict[str, Any]] = []
    for trade_date in eligible_dates:
        year = pd.Timestamp(trade_date).year
        if year < start_year or year > end_year:
            continue
        bounds = _local_bounds(pd.Timestamp(trade_date))
        asian = _active_slice(frame, bounds["day_start"], bounds["asian_end"])
        sweep_window = _active_slice(frame, bounds["asian_end"], bounds["sweep_end"])
        row = asian_table.loc[trade_date]
        asian_high = float(row["high"])
        asian_low = float(row["low"])
        asian_range = float(row["range"])
        atr20 = float(daily.loc[trade_date, "atr20"]) if trade_date in daily.index else math.nan
        adr20 = float(daily.loc[trade_date, "adr20"]) if trade_date in daily.index else math.nan
        threshold = max(pip, 0.02 * asian_range)
        upper = sweep_window.loc[sweep_window["high"] >= asian_high + threshold]
        lower = sweep_window.loc[sweep_window["low"] <= asian_low - threshold]
        session_rows.append(
            {
                "instrument": symbol,
                "trade_date": str(trade_date),
                "week_key": pd.Timestamp(trade_date).strftime("%G-W%V"),
                "asian_active_minutes": int(row["active_minutes"]),
                "asian_range_pips": asian_range / pip,
                "asian_range_atr20": _safe_ratio(asian_range, atr20),
                "upper_candidate": not upper.empty,
                "lower_candidate": not lower.empty,
                "candidate_count": int(not upper.empty) + int(not lower.empty),
            }
        )
        candidates: list[tuple[str, pd.Timestamp]] = []
        if not upper.empty:
            candidates.append(("UP", pd.Timestamp(upper.index[0])))
        if not lower.empty:
            candidates.append(("DOWN", pd.Timestamp(lower.index[0])))
        for side, sweep_time in sorted(candidates, key=lambda item: (item[1], item[0])):
            sweep_bar = frame.loc[[sweep_time]]
            same_minute_double = bool(
                float(sweep_bar.iloc[0]["high"]) >= asian_high + threshold
                and float(sweep_bar.iloc[0]["low"]) <= asian_low - threshold
            )
            boundary = asian_high if side == "UP" else asian_low
            sweep_extreme = (
                float(sweep_bar.iloc[0]["high"])
                if side == "UP"
                else float(sweep_bar.iloc[0]["low"])
            )
            pre_sweep = _active_slice(frame, bounds["asian_end"], sweep_time)
            t5_end = min(sweep_time + pd.Timedelta(minutes=5), bounds["sweep_end"])
            path_t5 = _active_slice(frame, sweep_time, t5_end)
            path_to_1000 = _active_slice(frame, sweep_time, bounds["sweep_end"])
            path_to_1100 = _active_slice(frame, sweep_time, bounds["follow_end"])
            if path_to_1100.empty:
                continue
            event_id = f"{symbol}_{trade_date}_{side}_{sweep_time.tz_convert('UTC').strftime('%H%M')}"
            t5 = _t5_features(
                side=side,
                boundary=boundary,
                asian_range=asian_range,
                sweep_extreme=sweep_extreme,
                path=path_t5,
            )
            t5_price = (
                float(path_t5.iloc[-1]["close"])
                if not path_t5.empty
                else float(sweep_bar.iloc[-1]["close"])
            )
            levels = _session_levels(
                trade_date=trade_date,
                asian_high=asian_high,
                asian_low=asian_low,
                day_start=bounds["day_start"],
                daily=daily,
                weekly=weekly,
                ny_sessions=ny_sessions,
                frame=frame,
            )
            levels.extend(
                _select_pivots(
                    pivots=pivots,
                    frame=frame,
                    snapshot=sweep_time + pd.Timedelta(minutes=1),
                    trade_date=trade_date,
                    eligible_dates=eligible_dates,
                    pip=pip,
                    atr20=atr20,
                )
            )
            liquidity, event_level_records = _liquidity_features(
                event_id=event_id,
                instrument=symbol,
                trade_date=trade_date,
                side=side,
                levels=levels,
                asian_high=asian_high,
                asian_low=asian_low,
                asian_range=asian_range,
                pip=pip,
                atr20=atr20,
                pre_sweep_price=(
                    float(pre_sweep.iloc[-1]["close"])
                    if not pre_sweep.empty
                    else float(asian.iloc[-1]["close"])
                ),
                sweep_extreme=sweep_extreme,
                t5_price=t5_price,
                path_0800_pre=pre_sweep,
                sweep_bar=sweep_bar,
                path_sweep_t5=path_t5,
            )
            level_records.extend(event_level_records)
            outcomes = _event_outcomes(
                path_to_1000=path_to_1000,
                path_to_1100=path_to_1100,
                side=side,
                sweep_extreme=sweep_extreme,
                asian_high=asian_high,
                asian_low=asian_low,
                asian_range=asian_range,
            )
            if same_minute_double:
                outcomes.update(
                    {
                        "midpoint_success_09_10": False,
                        "full_range_success": False,
                        "two_sided_ambiguous": True,
                        "primary_outcome": "TWO_SIDED_AMBIGUOUS",
                    }
                )
            local_minute = sweep_time.hour * 60 + sweep_time.minute
            asian_close = float(asian.iloc[-1]["close"])
            asian_open = float(asian.iloc[0]["open"])
            asian_returns = asian["close"].pct_change().dropna()
            zone_tolerance = max(pip, 0.03 * asian_range)
            pre_returns = pre_sweep["close"].pct_change().dropna()
            trailing = _active_slice(
                frame,
                max(bounds["asian_end"], sweep_time - pd.Timedelta(minutes=15)),
                sweep_time,
            )
            trailing_vol = (
                float(trailing["close"].pct_change().std(ddof=0))
                if len(trailing) > 1
                else math.nan
            )
            sweep_body = abs(float(sweep_bar.iloc[0]["close"] - sweep_bar.iloc[0]["open"]))
            sweep_wick = float(sweep_bar.iloc[0]["high"] - sweep_bar.iloc[0]["low"]) - sweep_body
            bar_range = float(sweep_bar.iloc[0]["high"] - sweep_bar.iloc[0]["low"])
            close_beyond = (
                float(sweep_bar.iloc[0]["close"]) - boundary
                if side == "UP"
                else boundary - float(sweep_bar.iloc[0]["close"])
            )
            close_location_bar = (
                _safe_ratio(float(sweep_bar.iloc[0]["close"] - sweep_bar.iloc[0]["low"]), bar_range)
                if bar_range > 0
                else 0.5
            )
            pre_return = (
                float(pre_sweep.iloc[-1]["close"] - pre_sweep.iloc[0]["open"]) / asian_range
                if not pre_sweep.empty
                else 0.0
            )
            reversal_direction = -1.0 if side == "UP" else 1.0
            first_half = asian.iloc[: len(asian) // 2]
            second_half = asian.iloc[len(asian) // 2 :]
            direction_series = np.sign(asian["close"].diff()).replace(0, np.nan).ffill()
            event = {
                "event_id": event_id,
                "instrument": symbol,
                "trade_date": str(trade_date),
                "week_key": pd.Timestamp(trade_date).strftime("%G-W%V"),
                "weekday": pd.Timestamp(trade_date).weekday(),
                "week_of_month": int((pd.Timestamp(trade_date).day - 1) // 7 + 1),
                "side": side,
                "sweep_timestamp_utc": sweep_time.tz_convert("UTC").isoformat(),
                "sweep_timestamp_amsterdam": sweep_time.isoformat(),
                "sweep_minute": local_minute,
                "sweep_before_0900": local_minute < 9 * 60,
                "sweep_half_hour": "0900_0929"
                if 9 * 60 <= local_minute < 9 * 60 + 30
                else ("0930_0959" if local_minute >= 9 * 60 + 30 else "0800_0859"),
                "asian_high": asian_high,
                "asian_low": asian_low,
                "asian_midpoint": (asian_high + asian_low) / 2.0,
                "asian_range_price": asian_range,
                "asian_range_pips": asian_range / pip,
                "asian_active_minutes": int(row["active_minutes"]),
                "asian_range_atr20": _safe_ratio(asian_range, atr20),
                "asian_range_adr20": _safe_ratio(asian_range, adr20),
                "asian_range_vs_median20": _safe_ratio(asian_range, float(row["median20"])),
                "asian_range_percentile20": float(row["percentile20"]),
                "asian_range_percentile60": float(row["percentile60"]),
                "asian_range_zscore60": float(row["zscore60"]),
                "asian_compression_bucket": _compression_bucket(
                    float(row["percentile60"]), eligible_dates.index(trade_date)
                ),
                "asian_range_under_20_pip_flag": asian_range / pip < 20,
                "asian_range_20_30_pip_flag": 20 <= asian_range / pip <= 30,
                "asian_range_over_30_pip_flag": asian_range / pip > 30,
                "asian_close_location": _safe_ratio(asian_close - asian_low, asian_range),
                "asian_return_range_fraction": (asian_close - asian_open) / asian_range,
                "asian_realized_vol_range_fraction": _safe_ratio(
                    float(asian_returns.std(ddof=0)),
                    asian_range / max(abs(asian_close), 1e-12),
                ),
                "asian_high_formation_minute": _formation_minute(asian, "high", asian_high),
                "asian_low_formation_minute": _formation_minute(asian, "low", asian_low),
                "asian_high_zone_touches": _touch_count(
                    asian["high"].to_numpy(float), asian_high, zone_tolerance
                ),
                "asian_low_zone_touches": _touch_count(
                    asian["low"].to_numpy(float), asian_low, zone_tolerance
                ),
                "asian_direction_changes": int((direction_series.diff().fillna(0) != 0).sum()),
                "asian_first_half_range_fraction": _safe_ratio(
                    float(first_half["high"].max() - first_half["low"].min()), asian_range
                ),
                "asian_second_half_range_fraction": _safe_ratio(
                    float(second_half["high"].max() - second_half["low"].min()), asian_range
                ),
                "pre_sweep_return_range_fraction": pre_return,
                "pre_sweep_reversal_signed_return": reversal_direction * pre_return,
                "pre_sweep_realized_vol_range_fraction": _safe_ratio(
                    float(pre_returns.std(ddof=0)),
                    asian_range
                    / max(
                        abs(float(pre_sweep.iloc[-1]["close"]))
                        if not pre_sweep.empty
                        else 1.0,
                        1e-12,
                    ),
                ),
                "pre_sweep_boundary_tests": (
                    _touch_count(pre_sweep["high"].to_numpy(float), asian_high, threshold)
                    if side == "UP"
                    else _touch_count(pre_sweep["low"].to_numpy(float), asian_low, threshold)
                ),
                "pre_sweep_minutes_from_0800": int(
                    (sweep_time - bounds["asian_end"]).total_seconds() // 60
                ),
                "pre_sweep_trailing_15m_range_fraction": (
                    _safe_ratio(float(trailing["high"].max() - trailing["low"].min()), asian_range)
                    if not trailing.empty
                    else math.nan
                ),
                "sweep_extreme": sweep_extreme,
                "sweep_depth_pips": abs(sweep_extreme - boundary) / pip,
                "sweep_depth_range_fraction": abs(sweep_extreme - boundary) / asian_range,
                "sweep_body_range_fraction": sweep_body / asian_range,
                "sweep_wick_range_fraction": sweep_wick / asian_range,
                "sweep_close_beyond_boundary_fraction": close_beyond / asian_range,
                "sweep_close_location_in_bar": close_location_bar,
                "sweep_displacement_vs_trailing_vol": (
                    sweep_body / (trailing_vol * abs(float(sweep_bar.iloc[0]["close"])))
                    if np.isfinite(trailing_vol) and trailing_vol > 0
                    else math.nan
                ),
            }
            event.update(t5)
            event.update(
                _prior_context(
                    trade_date,
                    daily,
                    weekly,
                    ny_sessions,
                    bounds["day_start"],
                    frame,
                )
            )
            event.update(liquidity)
            event.update(outcomes)
            anchor = float(sweep_bar.iloc[0]["open"])
            for horizon in (5, 15, 30, 60):
                horizon_end = min(
                    sweep_time + pd.Timedelta(minutes=horizon),
                    bounds["follow_end"],
                )
                path = _active_slice(frame, sweep_time, horizon_end)
                signed_return, mfe, mae = _path_metrics(
                    path,
                    side=side,
                    anchor=anchor,
                    reference_range=asian_range,
                )
                event[f"return_{horizon}m_range_fraction"] = signed_return
                event[f"mfe_{horizon}m_range_fraction"] = mfe
                event[f"mae_{horizon}m_range_fraction"] = mae
            close_1000 = _active_slice(
                frame,
                max(sweep_time, bounds["sweep_end"] - pd.Timedelta(minutes=1)),
                bounds["sweep_end"],
            )
            close_1100 = _active_slice(
                frame,
                max(sweep_time, bounds["follow_end"] - pd.Timedelta(minutes=1)),
                bounds["follow_end"],
            )
            event["close_1000_range_fraction"] = (
                reversal_direction
                * (float(close_1000.iloc[-1]["close"]) - anchor)
                / asian_range
                if not close_1000.empty
                else math.nan
            )
            event["close_1100_range_fraction"] = (
                reversal_direction
                * (float(close_1100.iloc[-1]["close"]) - anchor)
                / asian_range
                if not close_1100.empty
                else math.nan
            )
            events.append(event)
    event_frame = pd.DataFrame(events, columns=EVENT_COLUMNS)
    level_frame = pd.DataFrame(level_records, columns=LEVEL_COLUMNS)
    session_frame = pd.DataFrame(session_rows)
    return event_frame, level_frame, session_frame


def write_fingerprint_outputs(
    output: Path,
    *,
    symbol: str,
    events: pd.DataFrame,
    levels: pd.DataFrame,
    sessions: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    events.to_csv(output / "fingerprint_events.csv", index=False)
    levels.to_csv(output / "fingerprint_levels.csv", index=False)
    sessions.to_csv(output / "fingerprint_sessions.csv", index=False)
    summary = {
        "programme": "ASIAN_SWEEP_FINGERPRINT_V1",
        "stage": "DEVELOPMENT_ANATOMY",
        "symbol": symbol,
        "start_year": start_year,
        "end_year": end_year,
        "candidate_events": int(len(events)),
        "midpoint_successes": int(events["midpoint_success_09_10"].sum())
        if not events.empty
        else 0,
        "success_rate": float(events["midpoint_success_09_10"].mean())
        if not events.empty
        else None,
        "weeks_with_candidates": int(events["week_key"].nunique()) if not events.empty else 0,
        "strategy_pnl_calculated": False,
        "validation_2022_2023_opened": False,
        "holdout_2024_2025_opened": False,
    }
    (output / "pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary
