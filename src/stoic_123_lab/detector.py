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


@dataclass
class _DirectionState:
    phase: str = "WAIT_BREAK"
    step1_index: int | None = None
    step1_time: pd.Timestamp | None = None
    retest_index: int | None = None
    retest_time: pd.Timestamp | None = None
    base_start_index: int | None = None
    base_lock_index: int | None = None
    base_lock_time: pd.Timestamp | None = None
    base_upper: float | None = None
    base_lower: float | None = None
    atr_anchor: float | None = None
    map_direction_step1: int = 0

    def reset(self) -> None:
        self.__dict__.update(_DirectionState().__dict__)


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
    work["ema_fast"] = work["close"].ewm(span=config.ema_fast, adjust=False).mean()
    work["ema_slow"] = work["close"].ewm(span=config.ema_slow, adjust=False).mean()
    work["atr"] = _true_range(work).ewm(
        alpha=1 / config.atr_length,
        adjust=False,
        min_periods=config.atr_length,
    ).mean()
    true_range = _true_range(work).replace(0, np.nan)
    work["body_fraction"] = (work["close"] - work["open"]).abs().div(true_range).fillna(0)
    return work


def _map_features(map_bars: pd.DataFrame, config: SequenceConfig) -> pd.DataFrame:
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
        active_direction.append(last_direction if age <= config.map_breakout_active_bars else 0)
        active_age.append(age)
    work["breakout_map_direction"] = active_direction
    work["breakout_map_age"] = active_age
    work["available_time"] = pd.to_datetime(work["bar_end"])
    return work[
        ["available_time", "ema_map_direction", "breakout_map_direction", "breakout_map_age"]
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
    merged[["ema_map_direction", "breakout_map_direction"]] = merged[
        ["ema_map_direction", "breakout_map_direction"]
    ].fillna(0)
    return merged


def _selected_map_direction(row: pd.Series, config: SequenceConfig) -> int:
    ema_direction = int(row.get("ema_map_direction", 0))
    breakout_direction = int(row.get("breakout_map_direction", 0))
    if config.map_mode == "none":
        return 0
    if config.map_mode == "ema_alignment":
        return ema_direction
    if config.map_mode == "recent_breakout":
        return breakout_direction
    if config.map_mode == "ema_plus_breakout":
        return ema_direction if ema_direction == breakout_direction else 0
    raise ValueError(f"Unsupported map mode: {config.map_mode}")


def _map_allows(row: pd.Series, direction: int, config: SequenceConfig) -> bool:
    if config.map_mode == "none":
        return True
    return _selected_map_direction(row, config) == direction


def _step1(row: pd.Series, previous: pd.Series, direction: int, config: SequenceConfig) -> bool:
    if pd.isna(row["atr"]) or row["atr"] <= 0:
        return False
    zone_now_high = max(float(row["ema_fast"]), float(row["ema_slow"]))
    zone_now_low = min(float(row["ema_fast"]), float(row["ema_slow"]))
    zone_prev_high = max(float(previous["ema_fast"]), float(previous["ema_slow"]))
    zone_prev_low = min(float(previous["ema_fast"]), float(previous["ema_slow"]))
    buffer = config.step1_close_buffer_atr * float(row["atr"])
    directional_body = row["close"] > row["open"] if direction == 1 else row["close"] < row["open"]
    if not directional_body or float(row["body_fraction"]) < config.step1_min_body_fraction:
        return False
    if direction == 1:
        crossed = previous["close"] <= zone_prev_high and row["close"] > zone_now_high + buffer
    else:
        crossed = previous["close"] >= zone_prev_low and row["close"] < zone_now_low - buffer
    return bool(crossed and _map_allows(row, direction, config))


def _retest(row: pd.Series, direction: int, config: SequenceConfig) -> bool:
    tolerance = config.retest_tolerance_atr * float(row["atr"])
    zone_high = max(float(row["ema_fast"]), float(row["ema_slow"]))
    zone_low = min(float(row["ema_fast"]), float(row["ema_slow"]))
    if direction == 1:
        return bool(row["low"] <= zone_high + tolerance and row["close"] >= zone_low - tolerance)
    return bool(row["high"] >= zone_low - tolerance and row["close"] <= zone_high + tolerance)


def _overlap_ratio(base: pd.DataFrame) -> float:
    if len(base) < 2:
        return 0.0
    overlaps = 0
    comparisons = 0
    rows = list(base[["high", "low"]].itertuples(index=False, name=None))
    for (prev_high, prev_low), (high, low) in zip(rows, rows[1:], strict=False):
        comparisons += 1
        if min(prev_high, high) >= max(prev_low, low):
            overlaps += 1
    return overlaps / comparisons if comparisons else 0.0


def _base_qualifies(
    bars: pd.DataFrame,
    start: int,
    end: int,
    atr_anchor: float,
    config: SequenceConfig,
) -> bool:
    base = bars.iloc[start : end + 1]
    count = len(base)
    if count < config.base_min_bars or count > config.base_max_bars:
        return False
    base_range = float(base["high"].max() - base["low"].min())
    return bool(
        base_range <= config.base_max_range_atr * atr_anchor
        and _overlap_ratio(base) >= config.base_min_overlap_ratio
    )


def _wrong_way_break(
    row: pd.Series,
    state: _DirectionState,
    direction: int,
    config: SequenceConfig,
) -> bool:
    if state.base_upper is None or state.base_lower is None:
        return False
    buffer = config.step3_close_buffer_atr * float(row["atr"])
    if direction == 1:
        return bool(row["close"] < state.base_lower - buffer)
    return bool(row["close"] > state.base_upper + buffer)


def _confirmed_break(
    row: pd.Series,
    state: _DirectionState,
    direction: int,
    config: SequenceConfig,
) -> bool:
    if state.base_upper is None or state.base_lower is None:
        return False
    buffer = config.step3_close_buffer_atr * float(row["atr"])
    if direction == 1:
        return bool(row["close"] > state.base_upper + buffer)
    return bool(row["close"] < state.base_lower - buffer)


def detect_sequences(
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    config: SequenceConfig,
) -> DetectionResult:
    config.validate()
    bars = attach_map(execution_bars, map_bars, config).reset_index(drop=True)
    states = {1: _DirectionState(), -1: _DirectionState()}
    events: list[SequenceEvent] = []
    funnel = {
        "bars": int(len(bars)),
        "gap_resets": 0,
        "step1": 0,
        "retests": 0,
        "bases_locked": 0,
        "wrong_way_invalidations": 0,
        "expired": 0,
        "step3": 0,
    }

    for index in range(1, len(bars)):
        row = bars.iloc[index]
        previous = bars.iloc[index - 1]
        if float(row.get("gap_minutes", 0)) > config.gap_reset_minutes:
            for state in states.values():
                state.reset()
            funnel["gap_resets"] += 1

        for direction, state in states.items():
            if direction == 1 and not config.allow_long:
                continue
            if direction == -1 and not config.allow_short:
                continue

            if state.phase == "WAIT_BREAK":
                if _step1(row, previous, direction, config):
                    state.phase = "WAIT_RETEST"
                    state.step1_index = index
                    state.step1_time = pd.Timestamp(row["bar_end"])
                    state.atr_anchor = float(row["atr"])
                    state.map_direction_step1 = _selected_map_direction(row, config)
                    funnel["step1"] += 1
                continue

            if state.step1_index is None:
                state.reset()
                continue

            if state.phase == "WAIT_RETEST":
                if index - state.step1_index > config.retest_max_bars:
                    state.reset()
                    funnel["expired"] += 1
                    continue
                if _retest(row, direction, config):
                    state.phase = "BUILD_BASE"
                    state.retest_index = index
                    state.retest_time = pd.Timestamp(row["bar_end"])
                    state.base_start_index = index + 1
                    funnel["retests"] += 1
                continue

            if state.phase == "BUILD_BASE":
                if state.base_start_index is None or state.atr_anchor is None:
                    state.reset()
                    continue
                count = index - state.base_start_index + 1
                if count > config.base_max_bars:
                    state.reset()
                    funnel["expired"] += 1
                    continue
                if _base_qualifies(
                    bars,
                    state.base_start_index,
                    index,
                    state.atr_anchor,
                    config,
                ):
                    base = bars.iloc[state.base_start_index : index + 1]
                    state.base_upper = float(base["high"].max())
                    state.base_lower = float(base["low"].min())
                    state.base_lock_index = index
                    state.base_lock_time = pd.Timestamp(row["bar_end"])
                    state.phase = "WAIT_BREAKOUT"
                    funnel["bases_locked"] += 1
                continue

            if state.phase == "WAIT_BREAKOUT":
                if state.base_lock_index is None:
                    state.reset()
                    continue
                if index - state.base_lock_index > config.breakout_expiry_bars:
                    state.reset()
                    funnel["expired"] += 1
                    continue
                if pd.isna(row["atr"]):
                    continue
                if _wrong_way_break(row, state, direction, config):
                    state.reset()
                    funnel["wrong_way_invalidations"] += 1
                    continue
                if not _confirmed_break(row, state, direction, config):
                    continue
                if config.require_map_at_step3 and not _map_allows(row, direction, config):
                    continue
                if None in (
                    state.step1_time,
                    state.retest_time,
                    state.base_lock_time,
                    state.base_upper,
                    state.base_lower,
                ):
                    state.reset()
                    continue
                breakout_boundary = state.base_upper if direction == 1 else state.base_lower
                protective_boundary = state.base_lower if direction == 1 else state.base_upper
                events.append(
                    SequenceEvent(
                        arm_id=config.arm_id,
                        direction=direction,
                        step1_time=pd.Timestamp(state.step1_time),
                        retest_time=pd.Timestamp(state.retest_time),
                        base_lock_time=pd.Timestamp(state.base_lock_time),
                        signal_time=pd.Timestamp(row["bar_end"]),
                        base_upper=float(state.base_upper),
                        base_lower=float(state.base_lower),
                        breakout_boundary=float(breakout_boundary),
                        protective_boundary=float(protective_boundary),
                        atr_at_signal=float(row["atr"]),
                        breakout_close=float(row["close"]),
                        map_direction_step1=state.map_direction_step1,
                        map_direction_step3=_selected_map_direction(row, config),
                    )
                )
                funnel["step3"] += 1
                state.reset()

    event_frame = pd.DataFrame([event.as_dict() for event in events])
    if not event_frame.empty:
        event_frame = event_frame.sort_values("signal_time").reset_index(drop=True)
    return DetectionResult(events=event_frame, funnel=funnel, bars=bars)


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
    times = events[["step1_time", "retest_time", "base_lock_time", "signal_time"]].apply(
        pd.to_datetime
    )
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
    if not bool(
        (events.loc[long_rows, "breakout_boundary"] == events.loc[long_rows, "base_upper"]).all()
        and (
            events.loc[long_rows, "protective_boundary"] == events.loc[long_rows, "base_lower"]
        ).all()
        and (
            events.loc[short_rows, "breakout_boundary"] == events.loc[short_rows, "base_lower"]
        ).all()
        and (
            events.loc[short_rows, "protective_boundary"] == events.loc[short_rows, "base_upper"]
        ).all()
    ):
        raise ValueError("Event boundary assignment failed")
