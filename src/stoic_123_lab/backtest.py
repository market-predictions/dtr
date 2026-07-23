from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .config import InstrumentSpec, SequenceConfig


@dataclass(frozen=True)
class Trade:
    arm_id: str
    instrument: str
    execution_model: str
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


def _last_index_before(times_ns: np.ndarray, timestamp: pd.Timestamp) -> int:
    target = np.datetime64(timestamp).astype("datetime64[ns]").astype(np.int64)
    return int(np.searchsorted(times_ns, target, side="left") - 1)


def _single_stream_cost_points(spec: InstrumentSpec, config: SequenceConfig) -> float:
    slippage = 2.0 * config.slippage_ticks_each_side * spec.tick_size
    commission = 2.0 * spec.commission_per_side / spec.point_value
    return slippage + commission


def _commission_cost_points(spec: InstrumentSpec) -> float:
    return 2.0 * spec.commission_per_side / spec.point_value


def _management_time_index(management_events: pd.DataFrame) -> dict[int, np.ndarray]:
    result: dict[int, np.ndarray] = {
        1: np.array([], dtype=np.int64),
        -1: np.array([], dtype=np.int64),
    }
    if management_events.empty:
        return result
    times = pd.to_datetime(management_events["signal_time"])
    for direction in (1, -1):
        selected = times.loc[management_events["direction"].to_numpy() == direction]
        result[direction] = np.sort(selected.to_numpy(dtype="datetime64[ns]").astype(np.int64))
    return result


def _opposite_exit_time(
    management_times: dict[int, np.ndarray],
    direction: int,
    entry_time: pd.Timestamp,
) -> pd.Timestamp | None:
    candidates = management_times[-direction]
    if not len(candidates):
        return None
    target = np.datetime64(entry_time).astype("datetime64[ns]").astype(np.int64)
    index = int(np.searchsorted(candidates, target, side="right"))
    if index >= len(candidates):
        return None
    return pd.Timestamp(candidates[index])


def _append_trade(
    trades: list[Trade],
    *,
    config: SequenceConfig,
    spec: InstrumentSpec,
    event: object,
    direction: int,
    signal_time: pd.Timestamp,
    entry_time: pd.Timestamp,
    exit_time: pd.Timestamp,
    entry_price: float,
    exit_price: float,
    stop_price: float,
    risk_points: float,
    cost_points: float,
    exit_reason: str,
    management_signal_time: pd.Timestamp | None,
) -> None:
    gross_r = direction * (exit_price - entry_price) / risk_points
    cost_r = cost_points / risk_points
    trades.append(
        Trade(
            arm_id=config.arm_id,
            instrument=spec.name,
            execution_model=spec.execution_model,
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
            pnl_r=float(gross_r - cost_r),
            exit_reason=exit_reason,
            management_signal_time=management_signal_time,
            base_lock_time=pd.Timestamp(event.base_lock_time),
        )
    )


def _simulate_single(
    one_minute: pd.DataFrame,
    entry_events: pd.DataFrame,
    management_events: pd.DataFrame,
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> pd.DataFrame:
    one = one_minute.sort_values("timestamp").reset_index(drop=True)
    times = pd.to_datetime(one["timestamp"])
    times_ns = times.to_numpy(dtype="datetime64[ns]").astype(np.int64)
    open_ = one["open"].to_numpy(float)
    high = one["high"].to_numpy(float)
    low = one["low"].to_numpy(float)
    close = one["close"].to_numpy(float)
    costs = _single_stream_cost_points(spec, config)
    next_free = pd.Timestamp.min
    trades: list[Trade] = []
    management_times = _management_time_index(management_events)

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

        technical_time = _opposite_exit_time(management_times, direction, entry_time)
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


def _side_exit_price(
    *,
    direction: int,
    index: int,
    field: str,
    bid: dict[str, np.ndarray],
    ask: dict[str, np.ndarray],
    slippage: float,
) -> float:
    if direction == 1:
        return float(bid[field][index] - slippage)
    return float(ask[field][index] + slippage)


def _simulate_fx(
    one_minute: pd.DataFrame,
    entry_events: pd.DataFrame,
    management_events: pd.DataFrame,
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> pd.DataFrame:
    required = {
        f"{side}_{field}"
        for side in ("bid", "ask")
        for field in ("open", "high", "low", "close")
    }
    missing = required.difference(one_minute.columns)
    if missing:
        raise ValueError(f"FX execution data missing columns: {sorted(missing)}")

    one = one_minute.sort_values("timestamp").reset_index(drop=True)
    times = pd.to_datetime(one["timestamp"])
    times_ns = times.to_numpy(dtype="datetime64[ns]").astype(np.int64)
    bid = {field: one[f"bid_{field}"].to_numpy(float) for field in ("open", "high", "low", "close")}
    ask = {field: one[f"ask_{field}"].to_numpy(float) for field in ("open", "high", "low", "close")}
    slippage = config.slippage_ticks_each_side * spec.tick_size
    commission_costs = _commission_cost_points(spec)
    next_free = pd.Timestamp.min
    trades: list[Trade] = []
    management_times = _management_time_index(management_events)

    for event in entry_events.sort_values("signal_time").itertuples(index=False):
        signal_time = pd.Timestamp(event.signal_time)
        if signal_time < next_free:
            continue
        direction = int(event.direction)
        if config.fill_mode == "signal_close":
            entry_index = _last_index_before(times_ns, signal_time)
            if entry_index < 0:
                continue
            entry_time = signal_time
            entry_price = (
                float(ask["close"][entry_index] + slippage)
                if direction == 1
                else float(bid["close"][entry_index] - slippage)
            )
            path_start_index = entry_index + 1
        else:
            entry_index = _first_index_at_or_after(times_ns, signal_time)
            if entry_index >= len(one):
                continue
            entry_time = pd.Timestamp(times.iloc[entry_index])
            entry_price = (
                float(ask["open"][entry_index] + slippage)
                if direction == 1
                else float(bid["open"][entry_index] - slippage)
            )
            path_start_index = entry_index

        stop_price = float(event.protective_boundary) - direction * (
            config.stop_buffer_ticks * spec.tick_size
        )
        risk_points = direction * (entry_price - stop_price)
        minimum_risk = config.minimum_risk_ticks * spec.tick_size
        if not np.isfinite(risk_points) or risk_points < minimum_risk:
            continue

        technical_time = _opposite_exit_time(management_times, direction, entry_time)
        max_hold_time = entry_time + pd.Timedelta(minutes=config.max_hold_minutes)
        planned_exit_time = min(
            [value for value in (technical_time, max_hold_time) if value is not None]
        )
        exit_index_limit = min(_first_index_at_or_after(times_ns, planned_exit_time), len(one) - 1)
        exit_price = _side_exit_price(
            direction=direction,
            index=len(one) - 1,
            field="close",
            bid=bid,
            ask=ask,
            slippage=slippage,
        )
        exit_time = pd.Timestamp(times.iloc[-1])
        exit_reason = "end_of_data"
        management_signal_time: pd.Timestamp | None = None
        previous_time = entry_time

        for index in range(path_start_index, exit_index_limit + 1):
            current_time = pd.Timestamp(times.iloc[index])
            if current_time < entry_time:
                continue
            if index > path_start_index or current_time > entry_time:
                gap = (current_time - previous_time).total_seconds() / 60
                if gap > config.gap_reset_minutes:
                    exit_price = _side_exit_price(
                        direction=direction,
                        index=index,
                        field="open",
                        bid=bid,
                        ask=ask,
                        slippage=slippage,
                    )
                    exit_time = current_time
                    exit_reason = "gap_liquidation"
                    break
            previous_time = current_time

            stop_hit = (
                bid["low"][index] <= stop_price
                if direction == 1
                else ask["high"][index] >= stop_price
            )
            if stop_hit:
                if direction == 1:
                    raw_exit = min(stop_price, float(bid["open"][index]))
                    exit_price = raw_exit - slippage
                else:
                    raw_exit = max(stop_price, float(ask["open"][index]))
                    exit_price = raw_exit + slippage
                exit_time = current_time
                exit_reason = "protective_stop"
                break

            if technical_time is not None and current_time >= technical_time:
                exit_price = _side_exit_price(
                    direction=direction,
                    index=index,
                    field="open",
                    bid=bid,
                    ask=ask,
                    slippage=slippage,
                )
                exit_time = current_time
                exit_reason = "opposite_step3"
                management_signal_time = technical_time
                break

            if current_time >= max_hold_time:
                exit_price = _side_exit_price(
                    direction=direction,
                    index=index,
                    field="open",
                    bid=bid,
                    ask=ask,
                    slippage=slippage,
                )
                exit_time = current_time
                exit_reason = "max_hold"
                break

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
            cost_points=commission_costs,
            exit_reason=exit_reason,
            management_signal_time=management_signal_time,
        )
        next_free = exit_time

    return pd.DataFrame([trade.as_dict() for trade in trades])


def simulate(
    one_minute: pd.DataFrame,
    entry_events: pd.DataFrame,
    management_events: pd.DataFrame,
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> pd.DataFrame:
    if entry_events.empty:
        return pd.DataFrame()
    if spec.execution_model == "fx_bid_ask":
        return _simulate_fx(one_minute, entry_events, management_events, spec, config)
    return _simulate_single(one_minute, entry_events, management_events, spec, config)
