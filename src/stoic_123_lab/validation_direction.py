from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np
import pandas as pd

from .config import SequenceConfig
from .detector import attach_map, detect_sequences

EntryModel = Literal["ema_break", "ema_break_retest", "full_123", "matched_time"]
DirectionMode = Literal["long_only", "short_only", "both"]


@dataclass(frozen=True)
class StageDetection:
    events: pd.DataFrame
    funnel: dict[str, int]
    bars: pd.DataFrame


def entry_config(base: SequenceConfig, mode: DirectionMode) -> SequenceConfig:
    if mode == "long_only":
        return replace(base, allow_long=True, allow_short=False)
    if mode == "short_only":
        return replace(base, allow_long=False, allow_short=True)
    if mode == "both":
        return replace(base, allow_long=True, allow_short=True)
    raise ValueError(f"Unsupported direction mode: {mode}")


def management_config(base: SequenceConfig) -> SequenceConfig:
    """Restrict entries independently while retaining both management directions."""

    return replace(base.management_config(), allow_long=True, allow_short=True)


def _selected_map_direction(
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
        return ema_direction if ema_direction == breakout_direction else 0
    raise ValueError(f"Unsupported map mode: {config.map_mode}")


def _map_allows_long(
    ema_direction: int,
    breakout_direction: int,
    config: SequenceConfig,
) -> bool:
    return config.map_mode == "none" or _selected_map_direction(
        ema_direction, breakout_direction, config
    ) == 1


def _long_step1(
    index: int,
    *,
    open_: np.ndarray,
    close: np.ndarray,
    ema_fast: np.ndarray,
    ema_slow: np.ndarray,
    atr: np.ndarray,
    body_fraction: np.ndarray,
    ema_map: np.ndarray,
    breakout_map: np.ndarray,
    config: SequenceConfig,
) -> bool:
    if not np.isfinite(atr[index]) or atr[index] <= 0:
        return False
    if close[index] <= open_[index]:
        return False
    if body_fraction[index] < config.step1_min_body_fraction:
        return False
    previous_zone_high = max(ema_fast[index - 1], ema_slow[index - 1])
    zone_high = max(ema_fast[index], ema_slow[index])
    buffer = config.step1_close_buffer_atr * atr[index]
    crossed = close[index - 1] <= previous_zone_high and close[index] > zone_high + buffer
    return bool(
        crossed
        and _map_allows_long(
            int(ema_map[index]),
            int(breakout_map[index]),
            config,
        )
    )


def _event_row(
    *,
    arm_id: str,
    model: EntryModel,
    step1_time: pd.Timestamp,
    retest_time: pd.Timestamp | None,
    signal_time: pd.Timestamp,
    base_lock_time: pd.Timestamp,
    protective_boundary: float,
    breakout_close: float,
    atr_at_signal: float,
    map_direction_step1: int,
    map_direction_signal: int,
) -> dict[str, object]:
    return {
        "arm_id": arm_id,
        "entry_model": model,
        "direction": 1,
        "step1_time": step1_time,
        "retest_time": retest_time,
        "base_lock_time": base_lock_time,
        "signal_time": signal_time,
        "protective_boundary": protective_boundary,
        "breakout_close": breakout_close,
        "atr_at_signal": atr_at_signal,
        "map_direction_step1": map_direction_step1,
        "map_direction_signal": map_direction_signal,
    }


def detect_long_stage_events(
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    config: SequenceConfig,
    *,
    model: Literal["ema_break", "ema_break_retest"],
) -> StageDetection:
    """Detect causal long controls using the frozen Step-1 and retest definitions."""

    if model not in {"ema_break", "ema_break_retest"}:
        raise ValueError(f"Unsupported stage model: {model}")
    config.validate()
    bars = attach_map(execution_bars, map_bars, config).reset_index(drop=True)
    funnel = {"bars": int(len(bars)), "gap_resets": 0, "step1": 0, "retests": 0}
    if len(bars) < 2:
        return StageDetection(pd.DataFrame(), funnel, bars)

    open_ = bars["open"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    ema_fast = bars["ema_fast"].to_numpy(float)
    ema_slow = bars["ema_slow"].to_numpy(float)
    atr = bars["atr"].to_numpy(float)
    body_fraction = bars["body_fraction"].to_numpy(float)
    ema_map = bars["ema_map_direction"].fillna(0).to_numpy(np.int8)
    breakout_map = bars["breakout_map_direction"].fillna(0).to_numpy(np.int8)
    gap_minutes = bars["gap_minutes"].fillna(0).to_numpy(float)
    bar_open = pd.to_datetime(bars["timestamp"]).to_numpy(dtype="datetime64[ns]")
    bar_end = pd.to_datetime(bars["bar_end"]).to_numpy(dtype="datetime64[ns]")

    waiting_retest = False
    step1_index = -1
    step1_timestamp: pd.Timestamp | None = None
    step1_map = 0
    events: list[dict[str, object]] = []

    for index in range(1, len(bars)):
        if gap_minutes[index] > config.gap_reset_minutes:
            waiting_retest = False
            step1_index = -1
            step1_timestamp = None
            funnel["gap_resets"] += 1

        if not waiting_retest:
            if not _long_step1(
                index,
                open_=open_,
                close=close,
                ema_fast=ema_fast,
                ema_slow=ema_slow,
                atr=atr,
                body_fraction=body_fraction,
                ema_map=ema_map,
                breakout_map=breakout_map,
                config=config,
            ):
                continue
            step1_timestamp = pd.Timestamp(bar_end[index])
            step1_map = _selected_map_direction(
                int(ema_map[index]), int(breakout_map[index]), config
            )
            funnel["step1"] += 1
            if model == "ema_break":
                events.append(
                    _event_row(
                        arm_id=f"{config.arm_id}__EMA_BREAK",
                        model="ema_break",
                        step1_time=step1_timestamp,
                        retest_time=None,
                        signal_time=step1_timestamp,
                        base_lock_time=pd.Timestamp(bar_open[index]),
                        protective_boundary=float(low[index]),
                        breakout_close=float(close[index]),
                        atr_at_signal=float(atr[index]),
                        map_direction_step1=step1_map,
                        map_direction_signal=step1_map,
                    )
                )
            else:
                waiting_retest = True
                step1_index = index
            continue

        if step1_timestamp is None or step1_index < 0:
            waiting_retest = False
            continue
        if index - step1_index > config.retest_max_bars:
            waiting_retest = False
            step1_index = -1
            step1_timestamp = None
            continue
        if not np.isfinite(atr[index]):
            continue
        tolerance = config.retest_tolerance_atr * atr[index]
        zone_high = max(ema_fast[index], ema_slow[index])
        zone_low = min(ema_fast[index], ema_slow[index])
        retest = low[index] <= zone_high + tolerance and close[index] >= zone_low - tolerance
        if not retest:
            continue
        signal_map = _selected_map_direction(
            int(ema_map[index]), int(breakout_map[index]), config
        )
        if config.require_map_at_step3 and not _map_allows_long(
            int(ema_map[index]), int(breakout_map[index]), config
        ):
            continue
        signal_time = pd.Timestamp(bar_end[index])
        events.append(
            _event_row(
                arm_id=f"{config.arm_id}__EMA_BREAK_RETEST",
                model="ema_break_retest",
                step1_time=step1_timestamp,
                retest_time=signal_time,
                signal_time=signal_time,
                base_lock_time=step1_timestamp,
                protective_boundary=float(np.min(low[step1_index : index + 1])),
                breakout_close=float(close[index]),
                atr_at_signal=float(atr[index]),
                map_direction_step1=step1_map,
                map_direction_signal=signal_map,
            )
        )
        funnel["retests"] += 1
        waiting_retest = False
        step1_index = -1
        step1_timestamp = None

    event_frame = pd.DataFrame(events)
    if not event_frame.empty:
        event_frame = event_frame.sort_values("signal_time").reset_index(drop=True)
    return StageDetection(event_frame, funnel, bars)


def full_sequence_events(
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    base: SequenceConfig,
    *,
    direction_mode: DirectionMode,
) -> pd.DataFrame:
    config = entry_config(base, direction_mode)
    result = detect_sequences(execution_bars, map_bars, config)
    events = result.events.copy()
    if not events.empty:
        events["entry_model"] = "full_123"
    return events
