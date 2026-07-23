from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .config import SequenceConfig


@dataclass(frozen=True)
class SequenceEvent:
    arm_id: str
    direction: int
    step1_time: pd.Timestamp
    retest_time: pd.Timestamp
    base_lock_time: pd.Timestamp
    signal_time: pd.Timestamp
    base_upper: float
    base_lower: float
    breakout_boundary: float
    protective_boundary: float
    atr_at_signal: float
    breakout_close: float
    map_direction_step1: int
    map_direction_step3: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DetectionResult:
    events: pd.DataFrame
    funnel: dict[str, int]
    bars: pd.DataFrame


def _true_range(frame: pd.DataFrame) -> pd.Series:
    previous_close = frame["close"].shift(1)
    return pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def _indicators(frame: pd.DataFrame, config: SequenceConfig) -> pd.DataFrame:
    work = frame.copy()
    work["ema_fast"] = work["close"].ewm(
        span=config.ema_fast,
        adjust=False,
    ).mean()
    work["ema_slow"] = work["close"].ewm(
        span=config.ema_slow,
        adjust=False,
    ).mean()
    work["atr"] = _true_range(work).ewm(
        alpha=1 / config.atr_length,
        adjust=False,
        min_periods=config.atr_length,
    ).mean()
    true_range = _true_range(work).replace(0, np.nan)
    work["body_fraction"] = (
        (work["close"] - work["open"]).abs().div(true_range).fillna(0)
    )
    return work


def _map_features(
    map_bars: pd.DataFrame,
    config: SequenceConfig,
) -> pd.DataFrame:
    work = _indicators(map_bars, config)
    slow_slope = work["ema_slow"].diff()
    work["ema_map_direction"] = np.select(
        [
            (work["close"] > work["ema_fast"])
            & (work["ema_fast"] > work["ema_slow"])
            & (slow_slope > 0),
            (work["close"] < work["ema_fast"])
            & (work["ema_fast"] < work["ema_slow"])
            & (slow_slope < 0),
        ],
        [1, -1],
        default=0,
    )
    prior_high = work["high"].rolling(config.map_breakout_lookback).max().shift(1)
    prior_low = work["low"].rolling(config.map_breakout_lookback).min().shift(1)
    breakout = np.select(
        [work["close"] > prior_high, work["close"] < prior_low],
        [1, -1],
        default=0,
    )
    last_direction = 0
    age = config.map_breakout_active_bars + 1
    active_direction: list[int] = []
    active_age: list[int] = []
    for value in breakout:
        if value:
            last_direction = int(value)
            age = 0
        else:
            age += 1
        active = age <= config.map_breakout_active_bars
        active_direction.append(last_direction if active else 0)
        active_age.append(age)
    work["breakout_map_direction"] = active_direction
    work["breakout_map_age"] = active_age
    work["available_time"] = pd.to_datetime(work["bar_end"])
    return work[
        [
            "available_time",
            "ema_map_direction",
            "breakout_map_direction",
            "breakout_map_age",
        ]
    ]


def attach_map(
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    config: SequenceConfig,
) -> pd.DataFrame:
    execution = _indicators(execution_bars, config).sort_values("bar_end")
    map_features = _map_features(map_bars, config).sort_values("available_time")
    merged = pd.merge_asof(
        execution,
        map_features,
        left_on="bar_end",
        right_on="available_time",
        direction="backward",
        allow_exact_matches=True,
    )
    map_columns = ["ema_map_direction", "breakout_map_direction"]
    merged[map_columns] = merged[map_columns].fillna(0)
    return merged


def _map_direction(
    ema_direction: int,
    breakout_direction: int,
    config: SequenceConfig,
) -> int:
    if config.map_mode == "none":
        return 0
    if config.map_mode == "ema_alignment":
        return ema_direction
    if config.map_mode == "recent_breakout":
        return breakout_direction
    if config.map_mode == "ema_plus_breakout":
        if ema_direction == breakout_direction:
            return ema_direction
        return 0
    raise ValueError(f"Unsupported map mode: {config.map_mode}")


def _base_qualifies(
    high: np.ndarray,
    low: np.ndarray,
    start: int,
    end: int,
    atr_anchor: float,
    config: SequenceConfig,
) -> bool:
    count = end - start + 1
    if count < config.base_min_bars or count > config.base_max_bars:
        return False
    base_range = float(np.max(high[start : end + 1]) - np.min(low[start : end + 1]))
    if base_range > config.base_max_range_atr * atr_anchor:
        return False
    overlaps = 0
    for index in range(start + 1, end + 1):
        previous_high = high[index - 1]
        previous_low = low[index - 1]
        if min(previous_high, high[index]) >= max(previous_low, low[index]):
            overlaps += 1
    return overlaps / (count - 1) >= config.base_min_overlap_ratio


def detect_sequences(
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    config: SequenceConfig,
) -> DetectionResult:
    config.validate()
    bars = attach_map(execution_bars, map_bars, config).reset_index(drop=True)
    bar_count = len(bars)
    funnel = {
        "bars": int(bar_count),
        "gap_resets": 0,
        "step1": 0,
        "retests": 0,
        "bases_locked": 0,
        "wrong_way_invalidations": 0,
        "expired": 0,
        "step3": 0,
    }
    if bar_count < 2:
        return DetectionResult(pd.DataFrame(), funnel, bars)

    open_ = bars["open"].to_numpy(float)
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    ema_fast = bars["ema_fast"].to_numpy(float)
    ema_slow = bars["ema_slow"].to_numpy(float)
    atr = bars["atr"].to_numpy(float)
    body_fraction = bars["body_fraction"].to_numpy(float)
    gap_minutes = bars["gap_minutes"].fillna(0).to_numpy(float)
    ema_map = bars["ema_map_direction"].fillna(0).to_numpy(np.int8)
    breakout_map = bars["breakout_map_direction"].fillna(0).to_numpy(np.int8)
    bar_end = pd.to_datetime(bars["bar_end"]).to_numpy(dtype="datetime64[ns]")

    phase = {1: 0, -1: 0}
    step1_index = {1: -1, -1: -1}
    step1_time = {1: None, -1: None}
    retest_time = {1: None, -1: None}
    base_start = {1: -1, -1: -1}
    base_lock_index = {1: -1, -1: -1}
    base_lock_time = {1: None, -1: None}
    base_upper = {1: np.nan, -1: np.nan}
    base_lower = {1: np.nan, -1: np.nan}
    atr_anchor = {1: np.nan, -1: np.nan}
    map_step1 = {1: 0, -1: 0}
    events: list[SequenceEvent] = []

    def reset(direction: int) -> None:
        phase[direction] = 0
        step1_index[direction] = -1
        step1_time[direction] = None
        retest_time[direction] = None
        base_start[direction] = -1
        base_lock_index[direction] = -1
        base_lock_time[direction] = None
        base_upper[direction] = np.nan
        base_lower[direction] = np.nan
        atr_anchor[direction] = np.nan
        map_step1[direction] = 0

    for index in range(1, bar_count):
        if gap_minutes[index] > config.gap_reset_minutes:
            reset(1)
            reset(-1)
            funnel["gap_resets"] += 1

        for direction in (1, -1):
            if direction == 1 and not config.allow_long:
                continue
            if direction == -1 and not config.allow_short:
                continue

            selected_map = _map_direction(
                int(ema_map[index]),
                int(breakout_map[index]),
                config,
            )
            map_allows = config.map_mode == "none" or selected_map == direction

            if phase[direction] == 0:
                if not np.isfinite(atr[index]) or atr[index] <= 0:
                    continue
                zone_high = max(ema_fast[index], ema_slow[index])
                zone_low = min(ema_fast[index], ema_slow[index])
                previous_zone_high = max(ema_fast[index - 1], ema_slow[index - 1])
                previous_zone_low = min(ema_fast[index - 1], ema_slow[index - 1])
                buffer = config.step1_close_buffer_atr * atr[index]
                directional_body = (
                    close[index] > open_[index]
                    if direction == 1
                    else close[index] < open_[index]
                )
                if not directional_body:
                    continue
                if body_fraction[index] < config.step1_min_body_fraction:
                    continue
                if direction == 1:
                    crossed = (
                        close[index - 1] <= previous_zone_high
                        and close[index] > zone_high + buffer
                    )
                else:
                    crossed = (
                        close[index - 1] >= previous_zone_low
                        and close[index] < zone_low - buffer
                    )
                if crossed and map_allows:
                    phase[direction] = 1
                    step1_index[direction] = index
                    step1_time[direction] = bar_end[index]
                    atr_anchor[direction] = atr[index]
                    map_step1[direction] = selected_map
                    funnel["step1"] += 1
                continue

            if step1_index[direction] < 0:
                reset(direction)
                continue

            if phase[direction] == 1:
                if index - step1_index[direction] > config.retest_max_bars:
                    reset(direction)
                    funnel["expired"] += 1
                    continue
                tolerance = config.retest_tolerance_atr * atr[index]
                zone_high = max(ema_fast[index], ema_slow[index])
                zone_low = min(ema_fast[index], ema_slow[index])
                if direction == 1:
                    retest = (
                        low[index] <= zone_high + tolerance
                        and close[index] >= zone_low - tolerance
                    )
                else:
                    retest = (
                        high[index] >= zone_low - tolerance
                        and close[index] <= zone_high + tolerance
                    )
                if retest:
                    phase[direction] = 2
                    retest_time[direction] = bar_end[index]
                    base_start[direction] = index + 1
                    funnel["retests"] += 1
                continue

            if phase[direction] == 2:
                start = base_start[direction]
                if start < 0 or not np.isfinite(atr_anchor[direction]):
                    reset(direction)
                    continue
                if index - start + 1 > config.base_max_bars:
                    reset(direction)
                    funnel["expired"] += 1
                    continue
                if _base_qualifies(
                    high,
                    low,
                    start,
                    index,
                    atr_anchor[direction],
                    config,
                ):
                    base_upper[direction] = float(np.max(high[start : index + 1]))
                    base_lower[direction] = float(np.min(low[start : index + 1]))
                    base_lock_index[direction] = index
                    base_lock_time[direction] = bar_end[index]
                    phase[direction] = 3
                    funnel["bases_locked"] += 1
                continue

            if base_lock_index[direction] < 0:
                reset(direction)
                continue
            if index - base_lock_index[direction] > config.breakout_expiry_bars:
                reset(direction)
                funnel["expired"] += 1
                continue
            if not np.isfinite(atr[index]):
                continue
            buffer = config.step3_close_buffer_atr * atr[index]
            wrong_way = (
                close[index] < base_lower[direction] - buffer
                if direction == 1
                else close[index] > base_upper[direction] + buffer
            )
            if wrong_way:
                reset(direction)
                funnel["wrong_way_invalidations"] += 1
                continue
            confirmed = (
                close[index] > base_upper[direction] + buffer
                if direction == 1
                else close[index] < base_lower[direction] - buffer
            )
            if not confirmed:
                continue
            if config.require_map_at_step3 and not map_allows:
                continue
            required_times = (
                step1_time[direction],
                retest_time[direction],
                base_lock_time[direction],
            )
            if any(value is None for value in required_times):
                reset(direction)
                continue
            breakout_boundary = (
                base_upper[direction] if direction == 1 else base_lower[direction]
            )
            protective_boundary = (
                base_lower[direction] if direction == 1 else base_upper[direction]
            )
            events.append(
                SequenceEvent(
                    arm_id=config.arm_id,
                    direction=direction,
                    step1_time=pd.Timestamp(step1_time[direction]),
                    retest_time=pd.Timestamp(retest_time[direction]),
                    base_lock_time=pd.Timestamp(base_lock_time[direction]),
                    signal_time=pd.Timestamp(bar_end[index]),
                    base_upper=float(base_upper[direction]),
                    base_lower=float(base_lower[direction]),
                    breakout_boundary=float(breakout_boundary),
                    protective_boundary=float(protective_boundary),
                    atr_at_signal=float(atr[index]),
                    breakout_close=float(close[index]),
                    map_direction_step1=map_step1[direction],
                    map_direction_step3=selected_map,
                )
            )
            funnel["step3"] += 1
            reset(direction)

    event_frame = pd.DataFrame([event.as_dict() for event in events])
    if not event_frame.empty:
        event_frame = event_frame.sort_values("signal_time").reset_index(drop=True)
    return DetectionResult(event_frame, funnel, bars)


def validate_event_chronology(events: pd.DataFrame) -> None:
    if events.empty:
        return
    required = {
        "step1_time",
        "retest_time",
        "base_lock_time",
        "signal_time",
        "base_upper",
        "base_lower",
        "breakout_boundary",
        "protective_boundary",
        "direction",
    }
    missing = required.difference(events.columns)
    if missing:
        raise ValueError(f"Event audit missing columns: {sorted(missing)}")
    time_columns = [
        "step1_time",
        "retest_time",
        "base_lock_time",
        "signal_time",
    ]
    times = events[time_columns].apply(pd.to_datetime)
    valid_order = (
        (times["step1_time"] < times["retest_time"])
        & (times["retest_time"] <= times["base_lock_time"])
        & (times["base_lock_time"] < times["signal_time"])
    )
    if not bool(valid_order.all()):
        raise ValueError("Non-causal event chronology detected")
    if not bool((events["base_upper"] >= events["base_lower"]).all()):
        raise ValueError("Invalid base geometry")
    long_rows = events["direction"] == 1
    short_rows = events["direction"] == -1
    assignments_ok = (
        (
            events.loc[long_rows, "breakout_boundary"]
            == events.loc[long_rows, "base_upper"]
        ).all()
        and (
            events.loc[long_rows, "protective_boundary"]
            == events.loc[long_rows, "base_lower"]
        ).all()
        and (
            events.loc[short_rows, "breakout_boundary"]
            == events.loc[short_rows, "base_lower"]
        ).all()
        and (
            events.loc[short_rows, "protective_boundary"]
            == events.loc[short_rows, "base_upper"]
        ).all()
    )
    if not bool(assignments_ok):
        raise ValueError("Event boundary assignment failed")
