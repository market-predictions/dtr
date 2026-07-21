from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Literal

import numpy as np
import pandas as pd

from . import engine as base
from .integrity import (
    _BASE_GENERATE_SIGNALS,
    _first_unsafe_gap_between,
    _gap_intervals,
    _gap_table,
    _sanitize_sessions,
    prepare_market_arrays,
)

EntryRoutePolicy = Literal["break_close", "first_pullback", "hybrid"]

_SIGNAL_CONFIG_FIELDS = (
    "sessions",
    "weekdays",
    "min_sweep_range_pct",
    "min_sweep_ticks",
    "valid_sweep_threshold",
    "ideal_sweep_max_pct",
    "too_deep_sweep_pct",
    "volume_expand_mult",
    "atr_expand_mult",
    "reaction_bars",
    "pivot_len",
    "pivot_min_pct",
    "break_mode",
    "break_buffer_pct",
    "break_atr_frac",
    "impulse_mult",
    "require_impulse",
    "acceptance_bars",
    "entry_mode",
    "retest_band_pct",
    "signal_window_bars",
    "max_bars_from_sweep",
    "trend_filter",
    "er_length",
    "er_max",
    "adx_max",
    "tick_size",
)


@dataclass(frozen=True)
class EntryRouteConfig:
    name: str
    policy: EntryRoutePolicy
    band_ticks: int = 4
    band_atr_frac: float = 0.10
    expiry_bars: int = 12
    max_extension_risk: float = 1.50
    hybrid_extension_atr: float = 0.35


@dataclass(frozen=True)
class EntryRouteDecision:
    route_selected: EntryRoutePolicy
    filled: bool
    reason: str
    original_entry_index: int
    routed_entry_index: int = -1
    touch_index: int = -1
    touch_time: pd.Timestamp | None = None
    entry_time: pd.Timestamp | None = None
    entry_price_raw: float = np.nan
    fixed_stop_price: float = np.nan
    baseline_risk_points: float = np.nan
    routed_risk_points: float = np.nan
    extension_atr: float = np.nan
    latency_minutes: int = -1
    price_improvement_ticks: float = np.nan
    reset_epoch: int = -1


@dataclass(frozen=True)
class PreparedEntryRouting:
    signals: tuple[base.CandidateSignal, ...]
    sessions: int
    signal_config_signature: tuple[object, ...]


@dataclass
class EntryRouteFunnel:
    sessions: int = 0
    entry_signals: int = 0
    immediate_selected: int = 0
    pullback_selected: int = 0
    pullback_touched: int = 0
    pullback_responded: int = 0
    no_touch_expired: int = 0
    touch_no_response: int = 0
    invalidated: int = 0
    excessive_extension: int = 0
    reset: int = 0
    scheduled_close: int = 0
    ambiguous_touch_extension: int = 0
    no_fill: int = 0
    skipped_position_open: int = 0
    skipped_unsafe_gap_bridge: int = 0
    trades: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def baseline_routes() -> tuple[EntryRouteConfig, ...]:
    return (
        EntryRouteConfig("ENTRY_BREAK_CLOSE", "break_close"),
        EntryRouteConfig("ENTRY_FIRST_PULLBACK", "first_pullback"),
        EntryRouteConfig("ENTRY_HYBRID_PREDECLARED", "hybrid"),
    )


def _signal_config_signature(cfg: base.StrategyConfig) -> tuple[object, ...]:
    return tuple(getattr(cfg, field) for field in _SIGNAL_CONFIG_FIELDS)


def _fixed_stop(
    signal: base.CandidateSignal, bars: pd.DataFrame, cfg: base.StrategyConfig
) -> float:
    atr = float(bars.iloc[signal.entry_index]["atr14"])
    if not np.isfinite(atr):
        return np.nan
    buffer = max(cfg.tick_size * cfg.stop_buffer_ticks, atr * cfg.stop_atr_frac)
    return (
        signal.sweep_extreme - buffer
        if signal.direction > 0
        else signal.sweep_extreme + buffer
    )


def _risk_points(
    entry_raw: float, stop: float, direction: int, cfg: base.StrategyConfig
) -> float:
    slip = cfg.tick_size * cfg.slippage_ticks_each_side
    entry = entry_raw + slip if direction > 0 else entry_raw - slip
    return entry - stop if direction > 0 else stop - entry


def _route_selected(
    signal: base.CandidateSignal,
    bars: pd.DataFrame,
    route: EntryRouteConfig,
) -> tuple[EntryRoutePolicy, float]:
    atr = float(bars.iloc[signal.entry_index]["atr14"])
    extension_atr = (
        abs(signal.entry_price_raw - signal.pivot) / atr
        if np.isfinite(atr) and atr > 0
        else np.nan
    )
    if route.policy != "hybrid":
        return route.policy, extension_atr
    selected: EntryRoutePolicy = (
        "break_close"
        if np.isfinite(extension_atr) and extension_atr <= route.hybrid_extension_atr
        else "first_pullback"
    )
    return selected, extension_atr


def _epoch_arrays(bars: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    epoch = (
        bars["state_epoch_end"].to_numpy(dtype=np.int64)
        if "state_epoch_end" in bars.columns
        else np.zeros(len(bars), dtype=np.int64)
    )
    reset = (
        bars["contains_reset_gap"].to_numpy(dtype=bool)
        if "contains_reset_gap" in bars.columns
        else np.zeros(len(bars), dtype=bool)
    )
    return epoch, reset


def _minute_slice(
    one_times_ns: np.ndarray,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[int, int]:
    start_ns = np.datetime64(start, "ns").astype(np.int64)
    end_ns = np.datetime64(end, "ns").astype(np.int64)
    return (
        int(np.searchsorted(one_times_ns, start_ns, side="left")),
        int(np.searchsorted(one_times_ns, end_ns, side="left")),
    )


def route_signal(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    signal: base.CandidateSignal,
    cfg: base.StrategyConfig,
    route: EntryRouteConfig,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[base.CandidateSignal | None, EntryRouteDecision]:
    selected, extension_atr = _route_selected(signal, bars, route)
    fixed_stop = _fixed_stop(signal, bars, cfg)
    baseline_risk = _risk_points(signal.entry_price_raw, fixed_stop, signal.direction, cfg)
    epoch, reset = _epoch_arrays(bars)
    signal_epoch = int(epoch[signal.entry_index]) if signal.entry_index < len(epoch) else -1

    if not np.isfinite(fixed_stop) or baseline_risk <= cfg.tick_size:
        return None, EntryRouteDecision(
            route_selected=selected,
            filled=False,
            reason="INVALID_BASELINE_RISK",
            original_entry_index=signal.entry_index,
            fixed_stop_price=fixed_stop,
            baseline_risk_points=baseline_risk,
            extension_atr=extension_atr,
            reset_epoch=signal_epoch,
        )

    if selected == "break_close":
        return signal, EntryRouteDecision(
            route_selected=selected,
            filled=True,
            reason="BREAK_CLOSE",
            original_entry_index=signal.entry_index,
            routed_entry_index=signal.entry_index,
            entry_time=signal.entry_time,
            entry_price_raw=signal.entry_price_raw,
            fixed_stop_price=fixed_stop,
            baseline_risk_points=baseline_risk,
            routed_risk_points=baseline_risk,
            extension_atr=extension_atr,
            latency_minutes=0,
            price_improvement_ticks=0.0,
            reset_epoch=signal_epoch,
        )

    atr = float(bars.iloc[signal.entry_index]["atr14"])
    band = max(cfg.tick_size * route.band_ticks, atr * route.band_atr_frac)
    lower_band = signal.pivot - band
    upper_band = signal.pivot + band
    max_extension = route.max_extension_risk * baseline_risk
    extension_price = signal.entry_price_raw + signal.direction * max_extension
    bar_end = pd.to_datetime(bars["bar_end"])
    bar_start = pd.to_datetime(bars["timestamp"])
    open_price = bars["open"].to_numpy(float)
    close_price = bars["close"].to_numpy(float)
    one_times_ns, _, one_high, one_low, _ = market_arrays or prepare_market_arrays(
        one_minute
    )
    scheduled_close = base._scheduled_close_after(signal.entry_time, cfg)
    last_index = min(len(bars) - 1, signal.entry_index + route.expiry_bars)
    touched = False
    touch_index = -1
    touch_time: pd.Timestamp | None = None

    for index in range(signal.entry_index + 1, last_index + 1):
        if reset[index] or int(epoch[index]) != signal_epoch:
            return None, EntryRouteDecision(
                route_selected=selected,
                filled=False,
                reason="RESET",
                original_entry_index=signal.entry_index,
                touch_index=touch_index,
                touch_time=touch_time,
                fixed_stop_price=fixed_stop,
                baseline_risk_points=baseline_risk,
                extension_atr=extension_atr,
                reset_epoch=signal_epoch,
            )
        if scheduled_close is not None and pd.Timestamp(bar_end.iloc[index]) >= scheduled_close:
            return None, EntryRouteDecision(
                route_selected=selected,
                filled=False,
                reason="SCHEDULED_CLOSE",
                original_entry_index=signal.entry_index,
                touch_index=touch_index,
                touch_time=touch_time,
                fixed_stop_price=fixed_stop,
                baseline_risk_points=baseline_risk,
                extension_atr=extension_atr,
                reset_epoch=signal_epoch,
            )

        j0, j1 = _minute_slice(
            one_times_ns,
            pd.Timestamp(bar_start.iloc[index]),
            pd.Timestamp(bar_end.iloc[index]),
        )
        for j in range(j0, j1):
            minute_touch = one_low[j] <= upper_band and one_high[j] >= lower_band
            minute_invalid = (
                one_low[j] <= fixed_stop
                if signal.direction > 0
                else one_high[j] >= fixed_stop
            )
            minute_extended = (
                one_high[j] >= extension_price
                if signal.direction > 0
                else one_low[j] <= extension_price
            )
            if minute_invalid:
                return None, EntryRouteDecision(
                    route_selected=selected,
                    filled=False,
                    reason="INVALIDATED",
                    original_entry_index=signal.entry_index,
                    touch_index=touch_index,
                    touch_time=touch_time,
                    fixed_stop_price=fixed_stop,
                    baseline_risk_points=baseline_risk,
                    extension_atr=extension_atr,
                    reset_epoch=signal_epoch,
                )
            if not touched and minute_touch and minute_extended:
                return None, EntryRouteDecision(
                    route_selected=selected,
                    filled=False,
                    reason="AMBIGUOUS_TOUCH_EXTENSION",
                    original_entry_index=signal.entry_index,
                    fixed_stop_price=fixed_stop,
                    baseline_risk_points=baseline_risk,
                    extension_atr=extension_atr,
                    reset_epoch=signal_epoch,
                )
            if not touched and minute_extended:
                return None, EntryRouteDecision(
                    route_selected=selected,
                    filled=False,
                    reason="EXCESSIVE_EXTENSION",
                    original_entry_index=signal.entry_index,
                    fixed_stop_price=fixed_stop,
                    baseline_risk_points=baseline_risk,
                    extension_atr=extension_atr,
                    reset_epoch=signal_epoch,
                )
            if not touched and minute_touch:
                touched = True
                touch_index = index
                touch_time = pd.Timestamp(one_times_ns[j]) + pd.Timedelta(minutes=1)

        response = touched and (
            (
                signal.direction > 0
                and close_price[index] > signal.pivot
                and close_price[index] > open_price[index]
            )
            or (
                signal.direction < 0
                and close_price[index] < signal.pivot
                and close_price[index] < open_price[index]
            )
        )
        if response:
            routed_raw = float(close_price[index])
            routed_risk = _risk_points(routed_raw, fixed_stop, signal.direction, cfg)
            if routed_risk <= cfg.tick_size:
                return None, EntryRouteDecision(
                    route_selected=selected,
                    filled=False,
                    reason="INVALID_ROUTED_RISK",
                    original_entry_index=signal.entry_index,
                    touch_index=touch_index,
                    touch_time=touch_time,
                    fixed_stop_price=fixed_stop,
                    baseline_risk_points=baseline_risk,
                    routed_risk_points=routed_risk,
                    extension_atr=extension_atr,
                    reset_epoch=signal_epoch,
                )
            routed = replace(
                signal,
                entry_index=index,
                entry_time=pd.Timestamp(bar_end.iloc[index]),
                entry_price_raw=routed_raw,
            )
            improvement = (
                signal.entry_price_raw - routed_raw
                if signal.direction > 0
                else routed_raw - signal.entry_price_raw
            ) / cfg.tick_size
            return routed, EntryRouteDecision(
                route_selected=selected,
                filled=True,
                reason="PULLBACK_RESPONSE",
                original_entry_index=signal.entry_index,
                routed_entry_index=index,
                touch_index=touch_index,
                touch_time=touch_time,
                entry_time=routed.entry_time,
                entry_price_raw=routed_raw,
                fixed_stop_price=fixed_stop,
                baseline_risk_points=baseline_risk,
                routed_risk_points=routed_risk,
                extension_atr=extension_atr,
                latency_minutes=int(
                    (routed.entry_time - signal.entry_time).total_seconds() // 60
                ),
                price_improvement_ticks=float(improvement),
                reset_epoch=signal_epoch,
            )

    reason = "TOUCH_NO_RESPONSE" if touched else "NO_TOUCH_EXPIRED"
    return None, EntryRouteDecision(
        route_selected=selected,
        filled=False,
        reason=reason,
        original_entry_index=signal.entry_index,
        touch_index=touch_index,
        touch_time=touch_time,
        fixed_stop_price=fixed_stop,
        baseline_risk_points=baseline_risk,
        extension_atr=extension_atr,
        reset_epoch=signal_epoch,
    )


def _simulate_fixed_stop_trade_np(
    one_times_ns: np.ndarray,
    one_open: np.ndarray,
    one_high: np.ndarray,
    one_low: np.ndarray,
    one_close: np.ndarray,
    signal: base.CandidateSignal,
    cfg: base.StrategyConfig,
    fixed_stop: float,
) -> base.Trade | None:
    slip = cfg.tick_size * cfg.slippage_ticks_each_side
    entry = (
        signal.entry_price_raw + slip
        if signal.direction > 0
        else signal.entry_price_raw - slip
    )
    risk_points = entry - fixed_stop if signal.direction > 0 else fixed_stop - entry
    if risk_points <= cfg.tick_size:
        return None
    tp1 = entry + signal.direction * risk_points * cfg.tp1_rr
    tp2 = entry + signal.direction * risk_points * cfg.runner_rr
    start = signal.entry_time
    time_close = base._scheduled_close_after(start, cfg)
    max_end = start + pd.Timedelta(minutes=5 * cfg.max_hold_bars)
    hard_end = max_end if time_close is None else min(max_end, time_close)
    start_ns = np.datetime64(start, "ns").astype(np.int64)
    end_ns = np.datetime64(hard_end, "ns").astype(np.int64)
    j0 = int(np.searchsorted(one_times_ns, start_ns, side="left"))
    j1 = int(np.searchsorted(one_times_ns, end_ns, side="right"))
    if j0 >= j1:
        return None

    remaining = 1.0
    realized_points = 0.0
    tp1_hit = False
    runner_stop = fixed_stop
    mfe = 0.0
    mae = 0.0
    last_idx = j1 - 1
    exit_time = pd.Timestamp(one_times_ns[last_idx]) + pd.Timedelta(minutes=1)
    exit_reason = "MAX_HOLD"
    time_close_ns = (
        None if time_close is None else np.datetime64(time_close, "ns").astype(np.int64)
    )
    max_end_ns = np.datetime64(max_end, "ns").astype(np.int64)

    for j in range(j0, j1):
        minute_end_ns = one_times_ns[j] + 60_000_000_000
        if signal.direction > 0:
            mfe = max(mfe, one_high[j] - entry)
            mae = max(mae, entry - one_low[j])
            stop_hit = one_low[j] <= runner_stop
            t1_hit = (not tp1_hit) and one_high[j] >= tp1
            t2_hit = one_high[j] >= tp2
        else:
            mfe = max(mfe, entry - one_low[j])
            mae = max(mae, one_high[j] - entry)
            stop_hit = one_high[j] >= runner_stop
            t1_hit = (not tp1_hit) and one_low[j] <= tp1
            t2_hit = one_low[j] <= tp2
        if stop_hit and (t1_hit or t2_hit) and cfg.conservative_intrabar:
            px = runner_stop - slip if signal.direction > 0 else runner_stop + slip
            realized_points += remaining * signal.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "STOP_AMBIG"
            break
        if stop_hit:
            px = runner_stop - slip if signal.direction > 0 else runner_stop + slip
            realized_points += remaining * signal.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = (
                pd.Timestamp(minute_end_ns),
                "BE" if tp1_hit and runner_stop == entry else "STOP",
            )
            break
        if t1_hit:
            frac = min(cfg.tp1_fraction, remaining)
            px = tp1 - slip if signal.direction > 0 else tp1 + slip
            realized_points += frac * signal.direction * (px - entry)
            remaining -= frac
            tp1_hit = True
            if cfg.move_runner_to_be:
                runner_stop = entry
        if remaining > 0 and t2_hit:
            px = tp2 - slip if signal.direction > 0 else tp2 + slip
            realized_points += remaining * signal.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "TP2"
            break
        if time_close_ns is not None and minute_end_ns >= time_close_ns:
            px = one_close[j] - slip if signal.direction > 0 else one_close[j] + slip
            realized_points += remaining * signal.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "TIME_CLOSE"
            break
        if minute_end_ns >= max_end_ns:
            px = one_close[j] - slip if signal.direction > 0 else one_close[j] + slip
            realized_points += remaining * signal.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "MAX_HOLD"
            break
    if remaining > 0:
        px = (
            one_close[last_idx] - slip
            if signal.direction > 0
            else one_close[last_idx] + slip
        )
        realized_points += remaining * signal.direction * (px - entry)

    gross_dollars = realized_points * cfg.point_value
    net_dollars = gross_dollars - 2.0 * cfg.commission_per_side
    risk_dollars = risk_points * cfg.point_value
    return base.Trade(
        config_name=cfg.name,
        session=signal.session,
        session_date=signal.session_date,
        direction=signal.direction,
        entry_time=signal.entry_time,
        exit_time=exit_time,
        entry_price=entry,
        stop_price=fixed_stop,
        exit_reason=exit_reason,
        pnl_r=float(net_dollars / risk_dollars),
        pnl_dollars=float(net_dollars),
        mfe_r=float(mfe / risk_points),
        mae_r=float(mae / risk_points),
        holding_minutes=int((exit_time - signal.entry_time).total_seconds() // 60),
        sweep_score=signal.sweep_score,
        day_of_week=signal.day_of_week,
    )


def prepare_entry_routing_context(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: base.StrategyConfig,
) -> PreparedEntryRouting:
    if cfg.entry_mode != "break_close":
        raise ValueError("Entry-routing context requires the frozen break_close signal mode")
    safe_sessions = _sanitize_sessions(one_minute, bars, sessions)
    signal_sessions = safe_sessions.loc[
        ~safe_sessions["integrity_range_gap_rejected"]
    ].copy()
    signals, funnel = _BASE_GENERATE_SIGNALS(bars, signal_sessions, cfg)
    return PreparedEntryRouting(
        signals=tuple(signals),
        sessions=int(funnel.sessions),
        signal_config_signature=_signal_config_signature(cfg),
    )


def _route_row(
    original: base.CandidateSignal,
    routed: base.CandidateSignal | None,
    decision: EntryRouteDecision,
) -> dict[str, object]:
    return {
        **{f"signal_{key}": value for key, value in asdict(original).items()},
        **{f"route_{key}": value for key, value in asdict(decision).items()},
        "routed_entry_time": None if routed is None else routed.entry_time,
        "routed_entry_price_raw": np.nan if routed is None else routed.entry_price_raw,
    }


def _trade_row(trade: base.Trade, decision: EntryRouteDecision) -> dict[str, object]:
    return {
        **asdict(trade),
        **{f"route_{key}": value for key, value in asdict(decision).items()},
    }


def simulate_entry_route(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    cfg: base.StrategyConfig,
    route: EntryRouteConfig,
    prepared: PreparedEntryRouting,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[pd.DataFrame, EntryRouteFunnel, pd.DataFrame]:
    if prepared.signal_config_signature != _signal_config_signature(cfg):
        raise ValueError("Prepared entry-routing context does not match signal config")
    arrays = market_arrays or prepare_market_arrays(one_minute)
    gaps = _gap_table(one_minute)
    unsafe_previous_ns, unsafe_current_ns = _gap_intervals(
        gaps, "reject_trade_bridge"
    )

    decisions: list[
        tuple[base.CandidateSignal, base.CandidateSignal | None, EntryRouteDecision]
    ] = []
    funnel = EntryRouteFunnel(
        sessions=prepared.sessions, entry_signals=len(prepared.signals)
    )
    for original in prepared.signals:
        routed, decision = route_signal(
            one_minute,
            bars,
            original,
            cfg,
            route,
            market_arrays=arrays,
        )
        decisions.append((original, routed, decision))
        if decision.route_selected == "break_close":
            funnel.immediate_selected += 1
        else:
            funnel.pullback_selected += 1
        if decision.touch_index >= 0:
            funnel.pullback_touched += 1
        if decision.reason == "PULLBACK_RESPONSE":
            funnel.pullback_responded += 1
        elif decision.reason == "NO_TOUCH_EXPIRED":
            funnel.no_touch_expired += 1
        elif decision.reason == "TOUCH_NO_RESPONSE":
            funnel.touch_no_response += 1
        elif decision.reason == "INVALIDATED":
            funnel.invalidated += 1
        elif decision.reason == "EXCESSIVE_EXTENSION":
            funnel.excessive_extension += 1
        elif decision.reason == "RESET":
            funnel.reset += 1
        elif decision.reason == "SCHEDULED_CLOSE":
            funnel.scheduled_close += 1
        elif decision.reason == "AMBIGUOUS_TOUCH_EXTENSION":
            funnel.ambiguous_touch_extension += 1
        if not decision.filled:
            funnel.no_fill += 1

    rows: list[dict[str, object]] = []
    next_free = pd.Timestamp.min
    one_times_ns, one_open, one_high, one_low, one_close = arrays
    for _, routed, decision in decisions:
        if routed is None:
            continue
        if routed.entry_time < next_free:
            funnel.skipped_position_open += 1
            continue
        trade = _simulate_fixed_stop_trade_np(
            one_times_ns,
            one_open,
            one_high,
            one_low,
            one_close,
            routed,
            cfg,
            decision.fixed_stop_price,
        )
        if trade is None:
            continue
        gap_ns = _first_unsafe_gap_between(
            unsafe_previous_ns,
            unsafe_current_ns,
            routed.entry_time,
            trade.exit_time,
        )
        if gap_ns is not None:
            funnel.skipped_unsafe_gap_bridge += 1
            next_free = max(next_free, pd.Timestamp(gap_ns))
            continue
        rows.append(_trade_row(trade, decision))
        next_free = trade.exit_time

    funnel.trades = len(rows)
    trades = pd.DataFrame(rows)
    route_table = pd.DataFrame(
        [
            _route_row(original, routed, decision)
            for original, routed, decision in decisions
        ]
    )
    return trades, funnel, route_table


def run_entry_route_backtest(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: base.StrategyConfig,
    route: EntryRouteConfig,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[pd.DataFrame, EntryRouteFunnel, pd.DataFrame]:
    prepared = prepare_entry_routing_context(one_minute, bars, sessions, cfg)
    return simulate_entry_route(
        one_minute,
        bars,
        cfg,
        route,
        prepared,
        market_arrays=market_arrays,
    )


def trade_identity(frame: pd.DataFrame) -> set[tuple[object, ...]]:
    if frame.empty:
        return set()
    work = frame.copy()
    for column in ("session_date", "entry_time"):
        work[column] = pd.to_datetime(work[column])
    columns = ["session", "session_date", "direction", "entry_time"]
    return set(map(tuple, work[columns].itertuples(index=False, name=None)))


def compare_entry_route_portfolios(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
) -> tuple[dict[str, int], pd.DataFrame]:
    reference_keys = trade_identity(reference)
    candidate_keys = trade_identity(candidate)
    removed = reference_keys - candidate_keys
    added = candidate_keys - reference_keys
    rows: list[dict[str, object]] = []
    for status, keys, source in (
        ("removed", removed, reference),
        ("added", added, candidate),
    ):
        if source.empty:
            continue
        work = source.copy()
        work["session_date"] = pd.to_datetime(work["session_date"])
        work["entry_time"] = pd.to_datetime(work["entry_time"])
        for key in sorted(keys, key=str):
            mask = (
                (work["session"] == key[0])
                & (work["session_date"] == key[1])
                & (work["direction"] == key[2])
                & (work["entry_time"] == key[3])
            )
            row = work.loc[mask].iloc[0]
            rows.append({"status": status, **row.to_dict()})
    return {
        "retained": len(reference_keys & candidate_keys),
        "removed": len(removed),
        "added": len(added),
    }, pd.DataFrame(rows)
