from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtest import (
    Trade,
    _append_trade,
    _first_index_at_or_after,
    _management_time_index,
    _opposite_exit_time,
    _single_stream_cost_points,
    simulate,
)
from .config import InstrumentSpec, SequenceConfig


@dataclass(frozen=True)
class _PreparedSingleStream:
    frame_id: int
    row_count: int
    first_timestamp: pd.Timestamp
    last_timestamp: pd.Timestamp
    times: pd.Series
    times_ns: np.ndarray
    open_: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    gaps: np.ndarray


_PREPARED_CACHE: dict[int, _PreparedSingleStream] = {}


def _prepare_single(one_minute: pd.DataFrame) -> _PreparedSingleStream:
    key = id(one_minute)
    cached = _PREPARED_CACHE.get(key)
    first = pd.Timestamp(one_minute["timestamp"].iloc[0])
    last = pd.Timestamp(one_minute["timestamp"].iloc[-1])
    if (
        cached is not None
        and cached.row_count == len(one_minute)
        and cached.first_timestamp == first
        and cached.last_timestamp == last
    ):
        return cached

    if not pd.Index(one_minute["timestamp"]).is_monotonic_increasing:
        one = one_minute.sort_values("timestamp").reset_index(drop=True)
    elif isinstance(one_minute.index, pd.RangeIndex) and one_minute.index.start == 0:
        one = one_minute
    else:
        one = one_minute.reset_index(drop=True)

    times = pd.to_datetime(one["timestamp"])
    times_ns = times.to_numpy(dtype="datetime64[ns]").astype(np.int64)
    gaps = np.zeros(len(one), dtype=float)
    if len(one) > 1:
        gaps[1:] = np.diff(times_ns) / 60_000_000_000
    prepared = _PreparedSingleStream(
        frame_id=key,
        row_count=len(one),
        first_timestamp=pd.Timestamp(times.iloc[0]),
        last_timestamp=pd.Timestamp(times.iloc[-1]),
        times=times,
        times_ns=times_ns,
        open_=one["open"].to_numpy(float),
        high=one["high"].to_numpy(float),
        low=one["low"].to_numpy(float),
        close=one["close"].to_numpy(float),
        gaps=gaps,
    )
    _PREPARED_CACHE.clear()
    _PREPARED_CACHE[key] = prepared
    return prepared


def _first_true_index(mask: np.ndarray, offset: int) -> int | None:
    found = np.flatnonzero(mask)
    return int(found[0] + offset) if len(found) else None


def _simulate_single_prepared(
    one_minute: pd.DataFrame,
    entry_events: pd.DataFrame,
    management_events: pd.DataFrame,
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> pd.DataFrame:
    prepared = _prepare_single(one_minute)
    times = prepared.times
    times_ns = prepared.times_ns
    open_ = prepared.open_
    high = prepared.high
    low = prepared.low
    close = prepared.close
    costs = _single_stream_cost_points(spec, config)
    management_times = _management_time_index(management_events)
    next_free = pd.Timestamp.min
    trades: list[Trade] = []

    for event in entry_events.sort_values("signal_time").itertuples(index=False):
        signal_time = pd.Timestamp(event.signal_time)
        if signal_time < next_free:
            continue
        if config.fill_mode == "signal_close":
            entry_time = signal_time
            entry_price = float(event.breakout_close)
            entry_index = _first_index_at_or_after(times_ns, signal_time)
        else:
            entry_index = _first_index_at_or_after(times_ns, signal_time)
            if entry_index >= len(times):
                continue
            entry_time = pd.Timestamp(times.iloc[entry_index])
            entry_price = float(open_[entry_index])

        direction = int(event.direction)
        stop_price = float(event.protective_boundary) - direction * (
            config.stop_buffer_ticks * spec.tick_size
        )
        risk_points = direction * (entry_price - stop_price)
        minimum_risk = config.minimum_risk_ticks * spec.tick_size
        if not np.isfinite(risk_points) or risk_points < minimum_risk:
            continue

        technical_time = _opposite_exit_time(
            management_times,
            direction,
            entry_time,
        )
        max_hold_time = entry_time + pd.Timedelta(minutes=config.max_hold_minutes)
        planned_exit_time = min(
            value for value in (technical_time, max_hold_time) if value is not None
        )
        exit_limit = min(
            _first_index_at_or_after(times_ns, planned_exit_time),
            len(times) - 1,
        )

        gap_index = None
        if exit_limit > entry_index:
            gap_index = _first_true_index(
                prepared.gaps[entry_index + 1 : exit_limit + 1]
                > config.gap_reset_minutes,
                entry_index + 1,
            )
        stop_mask = (
            low[entry_index : exit_limit + 1] <= stop_price
            if direction == 1
            else high[entry_index : exit_limit + 1] >= stop_price
        )
        stop_index = _first_true_index(stop_mask, entry_index)
        technical_index = (
            _first_index_at_or_after(times_ns, technical_time)
            if technical_time is not None
            else None
        )
        if technical_index is not None and technical_index > exit_limit:
            technical_index = None
        max_index = _first_index_at_or_after(times_ns, max_hold_time)
        if max_index > exit_limit:
            max_index = None

        candidates = [
            (index, precedence, reason)
            for index, precedence, reason in (
                (gap_index, 0, "gap_liquidation"),
                (stop_index, 1, "protective_stop"),
                (technical_index, 2, "opposite_step3"),
                (max_index, 3, "max_hold"),
            )
            if index is not None
        ]
        management_signal_time: pd.Timestamp | None = None
        if candidates:
            exit_index, _, exit_reason = min(candidates)
            exit_time = pd.Timestamp(times.iloc[exit_index])
            if exit_reason == "gap_liquidation":
                exit_price = float(open_[exit_index])
            elif exit_reason == "protective_stop":
                exit_price = stop_price
            else:
                exit_price = float(open_[exit_index])
                if exit_reason == "opposite_step3":
                    management_signal_time = technical_time
        else:
            exit_time = pd.Timestamp(times.iloc[-1])
            exit_price = float(close[-1])
            exit_reason = "end_of_data"

        _append_trade(
            trades,
            config=config,
            spec=spec,
            event=event,
            direction=direction,
            signal_time=signal_time,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_price=stop_price,
            risk_points=risk_points,
            cost_points=costs,
            exit_reason=exit_reason,
            management_signal_time=management_signal_time,
        )
        next_free = exit_time

    return pd.DataFrame([trade.as_dict() for trade in trades])


def simulate_validation(
    one_minute: pd.DataFrame,
    entry_events: pd.DataFrame,
    management_events: pd.DataFrame,
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> pd.DataFrame:
    """Equivalent cached/vectorized simulator for NQ validation repetitions."""

    if spec.execution_model != "single_ohlcv":
        return simulate(one_minute, entry_events, management_events, spec, config)
    return _simulate_single_prepared(
        one_minute,
        entry_events,
        management_events,
        spec,
        config,
    )
