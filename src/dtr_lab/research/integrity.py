from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from dtr_lab.data.gaps import classify_gaps

from . import engine as base

GapPolicy = Literal["observe_only", "reject_unsafe", "liquidate_unsafe"]

# Capture the pre-integrity implementation once. The package initializer later routes the
# public engine entry points through this module without creating recursive calls here.
_BASE_RESAMPLE_5M = base.resample_5m
_BASE_BUILD_SESSION_TABLE = base.build_session_table
_BASE_GENERATE_SIGNALS = base.generate_signals
_BASE_PREPARE_MARKET_ARRAYS = base.prepare_market_arrays
_BASE_SIMULATE_TRADE = base._simulate_trade_np
_BASE_RUN_BACKTEST = base.run_backtest


@dataclass(frozen=True)
class IntegrityCounters:
    sessions_raw: int = 0
    sessions_range_gap_rejected: int = 0
    sessions_signal_path_truncated: int = 0
    skipped_unsafe_gap_bridge: int = 0
    observed_unsafe_gap_bridges: int = 0
    gap_liquidations: int = 0


class IntegrityFunnel:
    """Compatibility wrapper that extends the existing funnel with integrity counters."""

    def __init__(self, funnel: base.Funnel, counters: IntegrityCounters) -> None:
        self._funnel = funnel
        self._counters = counters

    def __getattr__(self, name: str) -> Any:
        return getattr(self._funnel, name)

    def as_dict(self) -> dict[str, int]:
        return {
            **self._funnel.as_dict(),
            "sessions_raw": self._counters.sessions_raw,
            "sessions_range_gap_rejected": (
                self._counters.sessions_range_gap_rejected
            ),
            "sessions_signal_path_truncated": (
                self._counters.sessions_signal_path_truncated
            ),
            "skipped_unsafe_gap_bridge": self._counters.skipped_unsafe_gap_bridge,
            "observed_unsafe_gap_bridges": (
                self._counters.observed_unsafe_gap_bridges
            ),
            "gap_liquidations": self._counters.gap_liquidations,
        }


def _data_fingerprint(frame: pd.DataFrame) -> tuple[int, int, int]:
    timestamps = pd.to_datetime(frame["timestamp"], errors="raise")
    if timestamps.empty:
        return (0, 0, 0)
    return (len(frame), int(timestamps.iloc[0].value), int(timestamps.iloc[-1].value))


def _bar_fingerprint(bars: pd.DataFrame) -> tuple[int, int, int]:
    if bars.empty:
        return (0, 0, 0)
    timestamps = pd.to_datetime(bars["timestamp"], errors="raise")
    return (len(bars), int(timestamps.iloc[0].value), int(timestamps.iloc[-1].value))


def _session_fingerprint(sessions: pd.DataFrame) -> tuple[int, int]:
    if sessions.empty:
        return (0, 0)
    columns = [
        "session",
        "session_date",
        "range_start",
        "range_end",
        "break_end",
        "post_start_index",
    ]
    work = sessions.loc[:, columns].copy()
    original_end = (
        sessions["integrity_original_post_end_index"]
        if "integrity_original_post_end_index" in sessions.columns
        else sessions["post_end_index"]
    )
    work["post_end_index"] = original_end.to_numpy()
    digest = int(pd.util.hash_pandas_object(work, index=True).sum())
    return (len(work), digest)


def _integrity_fingerprint(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int]]:
    return (
        _data_fingerprint(one_minute),
        _bar_fingerprint(bars),
        _session_fingerprint(sessions),
    )


def _gap_table(one_minute: pd.DataFrame) -> pd.DataFrame:
    fingerprint = _data_fingerprint(one_minute)
    cached = one_minute.attrs.get("dtr_gap_table")
    cached_fingerprint = one_minute.attrs.get("dtr_gap_fingerprint")
    if isinstance(cached, pd.DataFrame) and cached_fingerprint == fingerprint:
        return cached

    gaps = classify_gaps(one_minute, timestamp_column="timestamp")
    one_minute.attrs["dtr_gap_table"] = gaps
    one_minute.attrs["dtr_gap_fingerprint"] = fingerprint
    return gaps


def _gap_ns(gaps: pd.DataFrame, flag: str) -> np.ndarray:
    if gaps.empty:
        return np.array([], dtype=np.int64)
    selected = gaps.loc[gaps[flag], "current_timestamp"]
    return pd.to_datetime(selected).to_numpy(dtype="datetime64[ns]").astype(np.int64)


def _gap_intervals(gaps: pd.DataFrame, flag: str) -> tuple[np.ndarray, np.ndarray]:
    if gaps.empty:
        empty = np.array([], dtype=np.int64)
        return empty, empty
    selected = gaps.loc[gaps[flag], ["previous_timestamp", "current_timestamp"]]
    previous_ns = (
        pd.to_datetime(selected["previous_timestamp"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    current_ns = (
        pd.to_datetime(selected["current_timestamp"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    return previous_ns, current_ns


def resample_5m(one_minute: pd.DataFrame) -> pd.DataFrame:
    """Resample without filling gaps and attach deterministic reset metadata."""

    bars = _BASE_RESAMPLE_5M(one_minute)
    gaps = _gap_table(one_minute)
    reset_ns = _gap_ns(gaps, "reset_strategy_state")
    unsafe_ns = _gap_ns(gaps, "reject_trade_bridge")

    if bars.empty:
        for column in (
            "state_epoch_start",
            "state_epoch_end",
            "unsafe_epoch_start",
            "unsafe_epoch_end",
        ):
            bars[column] = pd.Series(dtype="int64")
        bars["contains_reset_gap"] = pd.Series(dtype="bool")
        bars["contains_unsafe_gap"] = pd.Series(dtype="bool")
        return bars

    starts = bars["timestamp"].to_numpy(dtype="datetime64[ns]").astype(np.int64)
    ends = bars["bar_end"].to_numpy(dtype="datetime64[ns]").astype(np.int64)

    state_start = np.searchsorted(reset_ns, starts, side="left")
    state_end = np.searchsorted(reset_ns, ends, side="left")
    unsafe_start = np.searchsorted(unsafe_ns, starts, side="left")
    unsafe_end = np.searchsorted(unsafe_ns, ends, side="left")

    bars = bars.copy()
    bars["state_epoch_start"] = state_start.astype(np.int64)
    bars["state_epoch_end"] = state_end.astype(np.int64)
    bars["unsafe_epoch_start"] = unsafe_start.astype(np.int64)
    bars["unsafe_epoch_end"] = unsafe_end.astype(np.int64)
    bars["contains_reset_gap"] = state_end > state_start
    bars["contains_unsafe_gap"] = unsafe_end > unsafe_start
    return bars


def _sanitize_sessions(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
) -> pd.DataFrame:
    if sessions.empty:
        fingerprint = _integrity_fingerprint(one_minute, bars, sessions)
        work = sessions.copy()
        work["integrity_original_post_end_index"] = pd.Series(dtype="int64")
        work["integrity_range_gap_rejected"] = pd.Series(dtype="bool")
        work["integrity_signal_path_truncated"] = pd.Series(dtype="bool")
        work.attrs["dtr_integrity_fingerprint"] = fingerprint
        return work

    required = {
        "session",
        "session_date",
        "range_start",
        "range_end",
        "break_end",
        "post_start_index",
        "post_end_index",
    }
    missing = required.difference(sessions.columns)
    if missing:
        raise ValueError(f"Session table missing integrity columns: {sorted(missing)}")

    fingerprint = _integrity_fingerprint(one_minute, bars, sessions)
    if (
        sessions.attrs.get("dtr_integrity_fingerprint") == fingerprint
        and "integrity_original_post_end_index" in sessions.columns
        and "integrity_range_gap_rejected" in sessions.columns
        and "integrity_signal_path_truncated" in sessions.columns
    ):
        return sessions

    gaps = _gap_table(one_minute)
    reset_gaps = (
        gaps.loc[
            gaps["reset_strategy_state"],
            ["previous_timestamp", "current_timestamp"],
        ].copy()
        if not gaps.empty
        else pd.DataFrame(columns=["previous_timestamp", "current_timestamp"])
    )
    if not reset_gaps.empty:
        reset_gaps["previous_timestamp"] = pd.to_datetime(
            reset_gaps["previous_timestamp"]
        )
        reset_gaps["current_timestamp"] = pd.to_datetime(
            reset_gaps["current_timestamp"]
        )
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")

    work = sessions.copy()
    original_ends = (
        work["integrity_original_post_end_index"].astype(int).tolist()
        if "integrity_original_post_end_index" in work.columns
        else work["post_end_index"].astype(int).tolist()
    )
    range_rejected: list[bool] = []
    path_truncated: list[bool] = []
    adjusted_end: list[int] = []

    for row, original_end in zip(work.itertuples(index=False), original_ends, strict=True):
        range_start = pd.Timestamp(row.range_start)
        range_end = pd.Timestamp(row.range_end)
        break_end = pd.Timestamp(row.break_end)

        range_overlap = (
            (reset_gaps["previous_timestamp"] < range_end)
            & (reset_gaps["current_timestamp"] > range_start)
        )
        range_rejected.append(bool(range_overlap.any()))

        new_end = original_end
        truncated = False
        path_overlap = (
            (reset_gaps["previous_timestamp"] < break_end)
            & (reset_gaps["current_timestamp"] > range_end)
        )
        if path_overlap.any():
            first_gap = reset_gaps.loc[path_overlap].iloc[0]
            first_missing = max(
                pd.Timestamp(first_gap["previous_timestamp"])
                + pd.Timedelta(minutes=1),
                range_end,
            )
            gap_bar = int(
                np.searchsorted(
                    bar_times,
                    np.datetime64(first_missing),
                    side="right",
                )
                - 1
            )
            gap_bar = max(0, gap_bar)
            if gap_bar < new_end:
                new_end = gap_bar
                truncated = True

        adjusted_end.append(new_end)
        path_truncated.append(truncated)

    work["integrity_original_post_end_index"] = original_ends
    work["post_end_index"] = adjusted_end
    work["integrity_range_gap_rejected"] = range_rejected
    work["integrity_signal_path_truncated"] = path_truncated
    work.attrs["dtr_integrity_fingerprint"] = _integrity_fingerprint(
        one_minute,
        bars,
        work,
    )
    return work


def _restore_reference_sessions(sessions: pd.DataFrame) -> pd.DataFrame:
    work = sessions.copy()
    if "integrity_original_post_end_index" in work.columns:
        work["post_end_index"] = work["integrity_original_post_end_index"].astype(int)
    return work


def build_session_table(one_minute: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    sessions = _BASE_BUILD_SESSION_TABLE(one_minute, bars)
    return _sanitize_sessions(one_minute, bars, sessions)


def prepare_market_arrays(
    one_minute: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return _BASE_PREPARE_MARKET_ARRAYS(one_minute)


def _first_unsafe_gap_between(
    unsafe_previous_ns: np.ndarray,
    unsafe_current_ns: np.ndarray,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> int | None:
    if unsafe_current_ns.size == 0:
        return None
    start_ns = np.datetime64(start, "ns").astype(np.int64)
    end_ns = np.datetime64(end, "ns").astype(np.int64)
    overlap = (unsafe_previous_ns < end_ns) & (unsafe_current_ns > start_ns)
    indexes = np.flatnonzero(overlap)
    if indexes.size == 0:
        return None
    return int(unsafe_current_ns[int(indexes[0])])


def _count_unsafe_trade_bridges(
    trades: pd.DataFrame,
    unsafe_previous_ns: np.ndarray,
    unsafe_current_ns: np.ndarray,
) -> int:
    if trades.empty or unsafe_current_ns.size == 0:
        return 0
    return sum(
        _first_unsafe_gap_between(
            unsafe_previous_ns,
            unsafe_current_ns,
            pd.Timestamp(row.entry_time),
            pd.Timestamp(row.exit_time),
        )
        is not None
        for row in trades.itertuples(index=False)
    )


def run_backtest(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: base.StrategyConfig,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
    *,
    gap_policy: GapPolicy = "liquidate_unsafe",
) -> tuple[pd.DataFrame, IntegrityFunnel]:
    if gap_policy not in ("observe_only", "reject_unsafe", "liquidate_unsafe"):
        raise ValueError(f"Unknown gap policy: {gap_policy}")

    safe_sessions = _sanitize_sessions(one_minute, bars, sessions)
    if safe_sessions.empty:
        eligible = pd.Series(False, index=safe_sessions.index, dtype=bool)
    else:
        eligible = safe_sessions["session"].isin(cfg.sessions) & safe_sessions[
            "weekday"
        ].isin(cfg.weekdays)
    range_rejected = eligible & safe_sessions["integrity_range_gap_rejected"]
    path_truncated = (
        eligible
        & ~safe_sessions["integrity_range_gap_rejected"]
        & safe_sessions["integrity_signal_path_truncated"]
    )

    gaps = _gap_table(one_minute)
    unsafe_previous_ns, unsafe_current_ns = _gap_intervals(
        gaps, "reject_trade_bridge"
    )

    if gap_policy == "observe_only":
        reference_sessions = _restore_reference_sessions(safe_sessions)
        trades, funnel = _BASE_RUN_BACKTEST(
            one_minute,
            bars,
            reference_sessions,
            cfg,
            market_arrays=market_arrays,
        )
        counters = IntegrityCounters(
            sessions_raw=int(eligible.sum()),
            sessions_range_gap_rejected=int(range_rejected.sum()),
            sessions_signal_path_truncated=int(path_truncated.sum()),
            observed_unsafe_gap_bridges=_count_unsafe_trade_bridges(
                trades,
                unsafe_previous_ns,
                unsafe_current_ns,
            ),
        )
        return trades, IntegrityFunnel(funnel, counters)

    signal_sessions = safe_sessions.loc[
        ~safe_sessions["integrity_range_gap_rejected"]
    ].copy()
    signals, funnel = _BASE_GENERATE_SIGNALS(bars, signal_sessions, cfg)

    one_times_ns, one_open, one_high, one_low, one_close = (
        market_arrays or prepare_market_arrays(one_minute)
    )
    trades: list[base.Trade] = []
    next_free = pd.Timestamp.min
    bridge_rejections = 0
    gap_liquidations = 0

    for signal in signals:
        if signal.entry_time < next_free:
            funnel.skipped_position_open += 1
            continue
        if gap_policy == "liquidate_unsafe":
            trade = _BASE_SIMULATE_TRADE(
                one_times_ns,
                one_open,
                one_high,
                one_low,
                one_close,
                bars,
                signal,
                cfg,
                unsafe_previous_ns=unsafe_previous_ns,
                unsafe_current_ns=unsafe_current_ns,
                gap_policy="liquidate",
            )
        else:
            # Historical noncausal policy retained only to reproduce the suspended
            # 491-trade benchmark and attribute the validity correction.
            trade = _BASE_SIMULATE_TRADE(
                one_times_ns,
                one_open,
                one_high,
                one_low,
                one_close,
                bars,
                signal,
                cfg,
            )
        if trade is None:
            continue

        if gap_policy == "reject_unsafe":
            gap_ns = _first_unsafe_gap_between(
                unsafe_previous_ns,
                unsafe_current_ns,
                signal.entry_time,
                trade.exit_time,
            )
            if gap_ns is not None:
                bridge_rejections += 1
                next_free = max(next_free, pd.Timestamp(gap_ns))
                continue

        if trade.exit_reason == "GAP_LIQUIDATION":
            gap_liquidations += 1
        trades.append(trade)
        next_free = trade.exit_time

    funnel.trades = len(trades)
    counters = IntegrityCounters(
        sessions_raw=int(eligible.sum()),
        sessions_range_gap_rejected=int(range_rejected.sum()),
        sessions_signal_path_truncated=int(path_truncated.sum()),
        skipped_unsafe_gap_bridge=bridge_rejections,
        gap_liquidations=gap_liquidations,
    )
    return pd.DataFrame([asdict(trade) for trade in trades]), IntegrityFunnel(
        funnel,
        counters,
    )

