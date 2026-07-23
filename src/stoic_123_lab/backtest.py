from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .config import InstrumentSpec, SequenceConfig


@dataclass(frozen=True)
class Trade:
    arm_id: str
    instrument: str
    direction: int
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    stop_price: float
    initial_risk_points: float
    gross_r: float
    cost_r: float
    pnl_r: float
    exit_reason: str
    management_signal_time: pd.Timestamp | None
    base_lock_time: pd.Timestamp

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _first_index_at_or_after(times_ns: np.ndarray, timestamp: pd.Timestamp) -> int:
    target = np.datetime64(timestamp).astype("datetime64[ns]").astype(np.int64)
    return int(np.searchsorted(times_ns, target))


def _trade_cost_points(spec: InstrumentSpec, config: SequenceConfig) -> float:
    slippage = 2.0 * config.slippage_ticks_each_side * spec.tick_size
    commission = 2.0 * spec.commission_per_side / spec.point_value
    return slippage + commission


def _opposite_exit_time(
    management_events: pd.DataFrame,
    direction: int,
    entry_time: pd.Timestamp,
) -> pd.Timestamp | None:
    if management_events.empty:
        return None
    selected = management_events.loc[
        (management_events["direction"] == -direction)
        & (pd.to_datetime(management_events["signal_time"]) > entry_time)
    ]
    if selected.empty:
        return None
    return pd.Timestamp(selected.sort_values("signal_time").iloc[0]["signal_time"])


def simulate(
    one_minute: pd.DataFrame,
    entry_events: pd.DataFrame,
    management_events: pd.DataFrame,
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> pd.DataFrame:
    if entry_events.empty:
        return pd.DataFrame()
    one = one_minute.sort_values("timestamp").reset_index(drop=True)
    times = pd.to_datetime(one["timestamp"])
    times_ns = times.to_numpy(dtype="datetime64[ns]").astype(np.int64)
    open_ = one["open"].to_numpy(float)
    high = one["high"].to_numpy(float)
    low = one["low"].to_numpy(float)
    close = one["close"].to_numpy(float)
    costs = _trade_cost_points(spec, config)
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
            if entry_index >= len(one):
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

        technical_time = _opposite_exit_time(management_events, direction, entry_time)
        max_hold_time = entry_time + pd.Timedelta(minutes=config.max_hold_minutes)
        planned_exit_time = min(
            [value for value in (technical_time, max_hold_time) if value is not None]
        )
        exit_index_limit = min(_first_index_at_or_after(times_ns, planned_exit_time), len(one) - 1)
        exit_price = float(close[-1])
        exit_time = pd.Timestamp(times.iloc[-1])
        exit_reason = "end_of_data"
        management_signal_time: pd.Timestamp | None = None
        previous_time = entry_time

        for index in range(entry_index, exit_index_limit + 1):
            current_time = pd.Timestamp(times.iloc[index])
            if index > entry_index:
                gap = (current_time - previous_time).total_seconds() / 60
                if gap > config.gap_reset_minutes:
                    exit_price = float(open_[index])
                    exit_time = current_time
                    exit_reason = "gap_liquidation"
                    break
            previous_time = current_time

            stop_hit = low[index] <= stop_price if direction == 1 else high[index] >= stop_price
            if stop_hit:
                exit_price = stop_price
                exit_time = current_time
                exit_reason = "protective_stop"
                break

            if technical_time is not None and current_time >= technical_time:
                exit_price = float(open_[index])
                exit_time = current_time
                exit_reason = "opposite_step3"
                management_signal_time = technical_time
                break

            if current_time >= max_hold_time:
                exit_price = float(open_[index])
                exit_time = current_time
                exit_reason = "max_hold"
                break

        gross_r = direction * (exit_price - entry_price) / risk_points
        cost_r = costs / risk_points
        pnl_r = gross_r - cost_r
        trades.append(
            Trade(
                arm_id=config.arm_id,
                instrument=spec.name,
                direction=direction,
                signal_time=signal_time,
                entry_time=entry_time,
                exit_time=exit_time,
                entry_price=entry_price,
                exit_price=exit_price,
                stop_price=stop_price,
                initial_risk_points=risk_points,
                gross_r=float(gross_r),
                cost_r=float(cost_r),
                pnl_r=float(pnl_r),
                exit_reason=exit_reason,
                management_signal_time=management_signal_time,
                base_lock_time=pd.Timestamp(event.base_lock_time),
            )
        )
        next_free = exit_time

    return pd.DataFrame([trade.as_dict() for trade in trades])
