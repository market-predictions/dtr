from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Literal

import numpy as np
import pandas as pd

from .engine import metrics, prepare_market_arrays
from .integrity import (
    _first_unsafe_gap_between,
    _gap_intervals,
    _gap_table,
    _sanitize_sessions,
)

EntryMode = Literal["immediate", "pullback"]


@dataclass(frozen=True)
class ContinuationConfig:
    name: str = "continuation_baseline"
    sessions: tuple[str, ...] = ("LONDON_2AM", "NEW_YORK_9AM", "ASIA_7PM")
    weekdays: tuple[int, ...] = (0, 1, 2, 3, 4)
    acceptance_bars: int = 1
    entry_mode: EntryMode = "immediate"
    break_buffer_ticks: int = 1
    break_atr_frac: float = 0.0
    pullback_window_bars: int = 12
    pullback_band_pct: float = 0.10
    pullback_band_ticks: int = 4
    max_entry_extension_pct: float = 1.50
    min_minutes_from_range_end: int = 0
    stop_buffer_ticks: int = 4
    stop_atr_frac: float = 0.10
    tp1_rr: float = 1.0
    runner_rr: float = 3.0
    tp1_fraction: float = 0.50
    move_runner_to_be: bool = True
    max_hold_bars: int = 72
    slippage_ticks_each_side: float = 1.0
    commission_per_side: float = 2.25
    tick_size: float = 0.25
    point_value: float = 20.0
    conservative_intrabar: bool = True
    failed_breakout_exit: bool = True

    def __post_init__(self) -> None:
        if self.acceptance_bars not in (1, 2):
            raise ValueError("acceptance_bars must be 1 or 2")
        if self.entry_mode not in ("immediate", "pullback"):
            raise ValueError("entry_mode must be immediate or pullback")
        if self.runner_rr <= self.tp1_rr:
            raise ValueError("runner_rr must exceed tp1_rr")
        if not 0 < self.tp1_fraction <= 1:
            raise ValueError("tp1_fraction must be in (0, 1]")


@dataclass
class ContinuationSignal:
    config_name: str
    session: str
    session_date: pd.Timestamp
    day_of_week: int
    direction: int
    range_high: float
    range_low: float
    range_size: float
    boundary: float
    break_index: int
    acceptance_index: int
    entry_index: int
    break_time: pd.Timestamp
    acceptance_time: pd.Timestamp
    entry_time: pd.Timestamp
    event_end_time: pd.Timestamp
    entry_price_raw: float
    acceptance_bars: int
    entry_mode: str
    break_displacement_atr: float
    break_bar_range_mult: float
    volume_mult: float
    entry_distance_range_pct: float
    vwap_aligned: bool
    vwap_slope_aligned: bool
    er20: float
    adx14: float
    minutes_from_range_end: int


@dataclass
class ContinuationTrade:
    config_name: str
    session: str
    session_date: pd.Timestamp
    day_of_week: int
    direction: int
    acceptance_bars: int
    entry_mode: str
    break_time: pd.Timestamp
    acceptance_time: pd.Timestamp
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    stop_price: float
    boundary: float
    exit_reason: str
    pnl_r: float
    pnl_dollars: float
    mfe_r: float
    mae_r: float
    holding_minutes: int
    break_displacement_atr: float
    break_bar_range_mult: float
    volume_mult: float
    entry_distance_range_pct: float
    vwap_aligned: bool
    vwap_slope_aligned: bool
    er20: float
    adx14: float
    minutes_from_range_end: int
    gap_previous_timestamp: pd.Timestamp | None = None
    gap_current_timestamp: pd.Timestamp | None = None
    gap_minutes: int = 0
    gap_liquidation_price: float = np.nan


@dataclass
class ContinuationFunnel:
    sessions_raw: int = 0
    sessions_eligible: int = 0
    sessions_range_gap_rejected: int = 0
    sessions_signal_path_truncated: int = 0
    break_attempts: int = 0
    acceptance_pass: int = 0
    acceptance_failed: int = 0
    immediate_extension_rejected: int = 0
    pullback_touch: int = 0
    pullback_rejection: int = 0
    failed_return_inside_pre_entry: int = 0
    failed_opposite_boundary_pre_entry: int = 0
    failed_extension_pre_entry: int = 0
    entry_window_expired: int = 0
    timing_filter_rejected: int = 0
    entry_signals: int = 0
    skipped_position_open: int = 0
    skipped_unsafe_gap_bridge: int = 0
    gap_liquidations: int = 0
    trades: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def baseline_configs() -> list[ContinuationConfig]:
    base = ContinuationConfig()
    return [
        replace(base, name="CONT_A1_IMMEDIATE", acceptance_bars=1, entry_mode="immediate"),
        replace(base, name="CONT_A2_IMMEDIATE", acceptance_bars=2, entry_mode="immediate"),
        replace(base, name="CONT_A1_PULLBACK", acceptance_bars=1, entry_mode="pullback"),
        replace(base, name="CONT_A2_PULLBACK", acceptance_bars=2, entry_mode="pullback"),
    ]


def _finite_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator) or denominator == 0:
        return np.nan
    return float(numerator / denominator)


def _signal_diagnostics(
    bars: pd.DataFrame,
    row: object,
    break_index: int,
    entry_index: int,
    direction: int,
    boundary: float,
) -> dict[str, object]:
    break_row = bars.iloc[break_index]
    entry_row = bars.iloc[entry_index]
    atr = float(break_row["atr14"])
    median_range = float(break_row["median_range20"])
    vol_sma = float(break_row["vol_sma20"])
    break_range = float(break_row["high"] - break_row["low"])
    displacement = direction * (float(break_row["close"]) - boundary)
    entry_distance = direction * (float(entry_row["close"]) - boundary)
    vwap = float(entry_row["eth_vwap"])
    slope = float(entry_row["eth_vwap_slope3"])
    close = float(entry_row["close"])
    return {
        "break_displacement_atr": _finite_ratio(displacement, atr),
        "break_bar_range_mult": _finite_ratio(break_range, median_range),
        "volume_mult": _finite_ratio(float(break_row["volume"]), vol_sma),
        "entry_distance_range_pct": _finite_ratio(entry_distance, float(row.range_size)),
        "vwap_aligned": bool(np.isfinite(vwap) and direction * (close - vwap) > 0),
        "vwap_slope_aligned": bool(np.isfinite(slope) and direction * slope > 0),
        "er20": float(entry_row["er20"]),
        "adx14": float(entry_row["adx14"]),
        "minutes_from_range_end": int(
            (pd.Timestamp(bars.iloc[entry_index]["bar_end"]) - pd.Timestamp(row.range_end))
            .total_seconds()
            // 60
        ),
    }


def generate_continuation_signals(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: ContinuationConfig,
) -> tuple[list[ContinuationSignal], ContinuationFunnel]:
    safe_sessions = _sanitize_sessions(one_minute, bars, sessions)
    funnel = ContinuationFunnel(sessions_raw=len(safe_sessions))
    if safe_sessions.empty:
        return [], funnel

    close = bars["close"].to_numpy(float)
    open_ = bars["open"].to_numpy(float)
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    atr = bars["atr14"].to_numpy(float)
    bar_end = pd.to_datetime(bars["bar_end"]).to_numpy(dtype="datetime64[ns]")
    signals: list[ContinuationSignal] = []

    for row in safe_sessions.itertuples(index=False):
        if row.session not in cfg.sessions or int(row.weekday) not in cfg.weekdays:
            continue
        funnel.sessions_eligible += 1
        if bool(row.integrity_range_gap_rejected):
            funnel.sessions_range_gap_rejected += 1
            continue
        if bool(row.integrity_signal_path_truncated):
            funnel.sessions_signal_path_truncated += 1

        start = int(row.post_start_index)
        end = int(row.post_end_index)
        if end <= start:
            continue
        range_high = float(row.range_high)
        range_low = float(row.range_low)
        range_size = float(row.range_size)
        if not np.isfinite(range_size) or range_size <= 0:
            continue

        break_index = -1
        direction = 0
        boundary = np.nan
        for i in range(start, end):
            atr_buffer = atr[i] * cfg.break_atr_frac if np.isfinite(atr[i]) else 0.0
            buffer = max(cfg.tick_size * cfg.break_buffer_ticks, atr_buffer)
            if close[i] >= range_high + buffer:
                break_index, direction, boundary = i, 1, range_high
                break
            if close[i] <= range_low - buffer:
                break_index, direction, boundary = i, -1, range_low
                break
        if break_index < 0:
            continue
        funnel.break_attempts += 1

        acceptance_index = break_index
        if cfg.acceptance_bars == 2:
            second = break_index + 1
            if second >= end or direction * (close[second] - boundary) <= 0:
                funnel.acceptance_failed += 1
                continue
            acceptance_index = second
        funnel.acceptance_pass += 1

        max_extension = range_size * cfg.max_entry_extension_pct
        entry_index = acceptance_index
        if cfg.entry_mode == "immediate":
            extension = direction * (close[entry_index] - boundary)
            if extension > max_extension:
                funnel.immediate_extension_rejected += 1
                continue
        else:
            entry_index = -1
            failed_before_entry = False
            band = max(
                cfg.tick_size * cfg.pullback_band_ticks,
                range_size * cfg.pullback_band_pct,
            )
            search_end = min(end, acceptance_index + cfg.pullback_window_bars + 1)
            for i in range(acceptance_index + 1, search_end):
                if direction > 0:
                    if low[i] <= range_low:
                        funnel.failed_opposite_boundary_pre_entry += 1
                        failed_before_entry = True
                        break
                    if close[i] <= boundary:
                        funnel.failed_return_inside_pre_entry += 1
                        failed_before_entry = True
                        break
                    if high[i] - boundary > max_extension:
                        funnel.failed_extension_pre_entry += 1
                        failed_before_entry = True
                        break
                    touched = low[i] <= boundary + band
                    if touched:
                        funnel.pullback_touch += 1
                    if touched and close[i] > boundary and close[i] > open_[i]:
                        entry_index = i
                        funnel.pullback_rejection += 1
                        break
                else:
                    if high[i] >= range_high:
                        funnel.failed_opposite_boundary_pre_entry += 1
                        failed_before_entry = True
                        break
                    if close[i] >= boundary:
                        funnel.failed_return_inside_pre_entry += 1
                        failed_before_entry = True
                        break
                    if boundary - low[i] > max_extension:
                        funnel.failed_extension_pre_entry += 1
                        failed_before_entry = True
                        break
                    touched = high[i] >= boundary - band
                    if touched:
                        funnel.pullback_touch += 1
                    if touched and close[i] < boundary and close[i] < open_[i]:
                        entry_index = i
                        funnel.pullback_rejection += 1
                        break
            if entry_index < 0:
                if not failed_before_entry:
                    funnel.entry_window_expired += 1
                continue

        diagnostics = _signal_diagnostics(
            bars, row, break_index, entry_index, direction, boundary
        )
        if int(diagnostics["minutes_from_range_end"]) < cfg.min_minutes_from_range_end:
            funnel.timing_filter_rejected += 1
            continue
        funnel.entry_signals += 1
        signals.append(
            ContinuationSignal(
                config_name=cfg.name,
                session=str(row.session),
                session_date=pd.Timestamp(row.session_date),
                day_of_week=int(row.weekday),
                direction=direction,
                range_high=range_high,
                range_low=range_low,
                range_size=range_size,
                boundary=float(boundary),
                break_index=break_index,
                acceptance_index=acceptance_index,
                entry_index=entry_index,
                break_time=pd.Timestamp(bar_end[break_index]),
                acceptance_time=pd.Timestamp(bar_end[acceptance_index]),
                entry_time=pd.Timestamp(bar_end[entry_index]),
                event_end_time=pd.Timestamp(row.break_end),
                entry_price_raw=float(close[entry_index]),
                acceptance_bars=cfg.acceptance_bars,
                entry_mode=cfg.entry_mode,
                **diagnostics,
            )
        )

    signals.sort(key=lambda signal: signal.entry_time)
    return signals, funnel


def _simulate_continuation_trade(
    one_times_ns: np.ndarray,
    one_open: np.ndarray,
    one_high: np.ndarray,
    one_low: np.ndarray,
    one_close: np.ndarray,
    bars: pd.DataFrame,
    signal: ContinuationSignal,
    cfg: ContinuationConfig,
    five_minute_ends: set[int],
    *,
    unsafe_previous_ns: np.ndarray | None = None,
    unsafe_current_ns: np.ndarray | None = None,
    gap_policy: str = "observe",
) -> ContinuationTrade | None:
    if gap_policy not in ("observe", "liquidate"):
        raise ValueError(f"Unknown continuation trade gap policy: {gap_policy}")
    atr = float(bars.iloc[signal.entry_index]["atr14"])
    if not np.isfinite(atr):
        return None
    slip = cfg.tick_size * cfg.slippage_ticks_each_side
    entry = signal.entry_price_raw + signal.direction * slip
    stop_buffer = max(cfg.tick_size * cfg.stop_buffer_ticks, atr * cfg.stop_atr_frac)
    stop = signal.boundary - signal.direction * stop_buffer
    risk_points = signal.direction * (entry - stop)
    if risk_points <= cfg.tick_size:
        return None

    tp1 = entry + signal.direction * risk_points * cfg.tp1_rr
    tp2 = entry + signal.direction * risk_points * cfg.runner_rr
    max_end = signal.entry_time + pd.Timedelta(minutes=5 * cfg.max_hold_bars)
    hard_end = min(max_end, signal.event_end_time)
    start_ns = np.datetime64(signal.entry_time, "ns").astype(np.int64)
    end_ns = np.datetime64(hard_end, "ns").astype(np.int64)
    unsafe_previous = (
        np.asarray(unsafe_previous_ns, dtype=np.int64)
        if unsafe_previous_ns is not None
        else np.array([], dtype=np.int64)
    )
    unsafe_current = (
        np.asarray(unsafe_current_ns, dtype=np.int64)
        if unsafe_current_ns is not None
        else np.array([], dtype=np.int64)
    )
    if unsafe_previous.size != unsafe_current.size:
        raise ValueError("Unsafe gap interval arrays must have equal length")
    gap_index = -1
    gap_resume_ns: int | None = None
    scan_end_ns = end_ns
    if gap_policy == "liquidate" and unsafe_current.size:
        relevant = (unsafe_current > start_ns) & (unsafe_previous < end_ns)
        indexes = np.flatnonzero(relevant)
        if indexes.size:
            gap_index = int(indexes[0])
            gap_resume_ns = int(unsafe_current[gap_index])
            scan_end_ns = max(scan_end_ns, gap_resume_ns)

    j0 = int(np.searchsorted(one_times_ns, start_ns, side="left"))
    end_side = (
        "right"
        if gap_resume_ns is not None and gap_resume_ns >= end_ns
        else "left"
    )
    j1 = int(np.searchsorted(one_times_ns, scan_end_ns, side=end_side))
    if j0 >= j1:
        return None

    remaining = 1.0
    realized_points = 0.0
    tp1_hit = False
    runner_stop = stop
    mfe = 0.0
    mae = 0.0
    last_index = j1 - 1
    exit_time = pd.Timestamp(one_times_ns[last_index]) + pd.Timedelta(minutes=1)
    exit_reason = "EVENT_END" if hard_end == signal.event_end_time else "MAX_HOLD"
    gap_previous_timestamp: pd.Timestamp | None = None
    gap_current_timestamp: pd.Timestamp | None = None
    gap_minutes = 0
    gap_liquidation_price = np.nan

    for j in range(j0, j1):
        current_ns = int(one_times_ns[j])
        if gap_resume_ns is not None and current_ns >= gap_resume_ns:
            open_px = float(one_open[j])
            if signal.direction > 0:
                mfe = max(mfe, open_px - entry)
                mae = max(mae, entry - open_px)
                price = min(runner_stop - slip, open_px - slip)
            else:
                mfe = max(mfe, entry - open_px)
                mae = max(mae, open_px - entry)
                price = max(runner_stop + slip, open_px + slip)
            realized_points += remaining * signal.direction * (price - entry)
            remaining = 0.0
            exit_time = pd.Timestamp(current_ns)
            exit_reason = "GAP_LIQUIDATION"
            gap_previous_timestamp = pd.Timestamp(int(unsafe_previous[gap_index]))
            gap_current_timestamp = pd.Timestamp(int(unsafe_current[gap_index]))
            gap_minutes = int(
                (int(unsafe_current[gap_index]) - int(unsafe_previous[gap_index]))
                // 60_000_000_000
            )
            gap_liquidation_price = float(price)
            break

        minute_end_ns = current_ns + 60_000_000_000
        if signal.direction > 0:
            mfe = max(mfe, one_high[j] - entry)
            mae = max(mae, entry - one_low[j])
            stop_hit = one_low[j] <= runner_stop
            first_target_hit = (not tp1_hit) and one_high[j] >= tp1
            runner_target_hit = one_high[j] >= tp2
        else:
            mfe = max(mfe, entry - one_low[j])
            mae = max(mae, one_high[j] - entry)
            stop_hit = one_high[j] >= runner_stop
            first_target_hit = (not tp1_hit) and one_low[j] <= tp1
            runner_target_hit = one_low[j] <= tp2

        if stop_hit and (first_target_hit or runner_target_hit) and cfg.conservative_intrabar:
            price = runner_stop - signal.direction * slip
            realized_points += remaining * signal.direction * (price - entry)
            remaining = 0.0
            exit_time = pd.Timestamp(minute_end_ns)
            exit_reason = "STOP_AMBIG"
            break
        if stop_hit:
            price = runner_stop - signal.direction * slip
            realized_points += remaining * signal.direction * (price - entry)
            remaining = 0.0
            exit_time = pd.Timestamp(minute_end_ns)
            exit_reason = "BE" if tp1_hit and runner_stop == entry else "STOP"
            break
        if first_target_hit:
            fraction = min(cfg.tp1_fraction, remaining)
            price = tp1 - signal.direction * slip
            realized_points += fraction * signal.direction * (price - entry)
            remaining -= fraction
            tp1_hit = True
            if cfg.move_runner_to_be:
                runner_stop = entry
        if remaining > 0 and runner_target_hit:
            price = tp2 - signal.direction * slip
            realized_points += remaining * signal.direction * (price - entry)
            remaining = 0.0
            exit_time = pd.Timestamp(minute_end_ns)
            exit_reason = "TP2"
            break

        if (
            remaining > 0
            and cfg.failed_breakout_exit
            and minute_end_ns in five_minute_ends
            and signal.direction * (one_close[j] - signal.boundary) <= 0
        ):
            price = one_close[j] - signal.direction * slip
            realized_points += remaining * signal.direction * (price - entry)
            remaining = 0.0
            exit_time = pd.Timestamp(minute_end_ns)
            exit_reason = "FAILED_BREAKOUT"
            break

    if remaining > 0:
        price = one_close[last_index] - signal.direction * slip
        realized_points += remaining * signal.direction * (price - entry)

    gross_dollars = realized_points * cfg.point_value
    commission = 2.0 * cfg.commission_per_side
    net_dollars = gross_dollars - commission
    pnl_r = net_dollars / (risk_points * cfg.point_value)
    return ContinuationTrade(
        config_name=cfg.name,
        session=signal.session,
        session_date=signal.session_date,
        day_of_week=signal.day_of_week,
        direction=signal.direction,
        acceptance_bars=signal.acceptance_bars,
        entry_mode=signal.entry_mode,
        break_time=signal.break_time,
        acceptance_time=signal.acceptance_time,
        entry_time=signal.entry_time,
        exit_time=exit_time,
        entry_price=float(entry),
        stop_price=float(stop),
        boundary=signal.boundary,
        exit_reason=exit_reason,
        pnl_r=float(pnl_r),
        pnl_dollars=float(net_dollars),
        mfe_r=float(mfe / risk_points),
        mae_r=float(mae / risk_points),
        holding_minutes=int((exit_time - signal.entry_time).total_seconds() // 60),
        break_displacement_atr=signal.break_displacement_atr,
        break_bar_range_mult=signal.break_bar_range_mult,
        volume_mult=signal.volume_mult,
        entry_distance_range_pct=signal.entry_distance_range_pct,
        vwap_aligned=signal.vwap_aligned,
        vwap_slope_aligned=signal.vwap_slope_aligned,
        er20=signal.er20,
        adx14=signal.adx14,
        minutes_from_range_end=signal.minutes_from_range_end,
        gap_previous_timestamp=gap_previous_timestamp,
        gap_current_timestamp=gap_current_timestamp,
        gap_minutes=gap_minutes,
        gap_liquidation_price=float(gap_liquidation_price),
    )


def run_continuation_backtest(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: ContinuationConfig,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
    *,
    gap_policy: Literal["reject_unsafe", "liquidate_unsafe"] = "liquidate_unsafe",
) -> tuple[pd.DataFrame, ContinuationFunnel]:
    signals, funnel = generate_continuation_signals(one_minute, bars, sessions, cfg)
    if gap_policy not in ("reject_unsafe", "liquidate_unsafe"):
        raise ValueError(f"Unknown continuation gap policy: {gap_policy}")
    one_times_ns, one_open, one_high, one_low, one_close = (
        market_arrays or prepare_market_arrays(one_minute)
    )
    gaps = _gap_table(one_minute)
    unsafe_previous_ns, unsafe_current_ns = _gap_intervals(gaps, "reject_trade_bridge")

    five_minute_ends = set(
        pd.to_datetime(bars["bar_end"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
        .tolist()
    )
    trades: list[ContinuationTrade] = []
    next_free = pd.Timestamp.min
    for signal in signals:
        if signal.entry_time < next_free:
            funnel.skipped_position_open += 1
            continue
        trade = _simulate_continuation_trade(
            one_times_ns,
            one_open,
            one_high,
            one_low,
            one_close,
            bars,
            signal,
            cfg,
            five_minute_ends,
            unsafe_previous_ns=unsafe_previous_ns,
            unsafe_current_ns=unsafe_current_ns,
            gap_policy="liquidate" if gap_policy == "liquidate_unsafe" else "observe",
        )
        if trade is None:
            continue
        if gap_policy == "reject_unsafe":
            gap = _first_unsafe_gap_between(
                unsafe_previous_ns,
                unsafe_current_ns,
                signal.entry_time,
                trade.exit_time,
            )
            if gap is not None:
                funnel.skipped_unsafe_gap_bridge += 1
                next_free = max(next_free, pd.Timestamp(gap))
                continue
        if trade.exit_reason == "GAP_LIQUIDATION":
            funnel.gap_liquidations += 1
        trades.append(trade)
        next_free = trade.exit_time

    funnel.trades = len(trades)
    return pd.DataFrame([asdict(trade) for trade in trades]), funnel


def evaluate_continuation_baselines(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    configs: list[ContinuationConfig] | None = None,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, ContinuationFunnel]]:
    configs = configs or baseline_configs()
    market_arrays = prepare_market_arrays(one_minute)
    rows: list[dict[str, object]] = []
    trades_by_name: dict[str, pd.DataFrame] = {}
    funnels: dict[str, ContinuationFunnel] = {}
    periods = {
        "development": (pd.Timestamp("2023-01-01"), pd.Timestamp("2024-07-01")),
        "validation": (pd.Timestamp("2024-07-01"), pd.Timestamp("2025-04-01")),
        "research_later": (pd.Timestamp("2025-04-01"), pd.Timestamp("2025-12-11")),
    }

    for cfg in configs:
        trades, funnel = run_continuation_backtest(
            one_minute,
            bars,
            sessions,
            cfg,
            market_arrays=market_arrays,
        )
        trades_by_name[cfg.name] = trades
        funnels[cfg.name] = funnel
        row: dict[str, object] = {
            "name": cfg.name,
            "acceptance_bars": cfg.acceptance_bars,
            "entry_mode": cfg.entry_mode,
            **{f"funnel_{key}": value for key, value in funnel.as_dict().items()},
            **{f"all_{key}": value for key, value in metrics(trades).items()},
        }
        for period, (start, end) in periods.items():
            subset = (
                trades[(trades["entry_time"] >= start) & (trades["entry_time"] < end)]
                if not trades.empty
                else trades
            )
            row.update({f"{period}_{key}": value for key, value in metrics(subset).items()})
        rows.append(row)

    return pd.DataFrame(rows), trades_by_name, funnels
