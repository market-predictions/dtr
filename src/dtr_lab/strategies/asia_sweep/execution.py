from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum

import pandas as pd

_SYNTHETIC_SOURCE_KIND = "SYNTHETIC_TEST_FIXTURE"
_REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close"}


class ExecutionStatus(StrEnum):
    """Terminal state of one isolated execution attempt."""

    EXITED = "EXITED"
    BLOCKED = "BLOCKED"
    UNRESOLVED = "UNRESOLVED"


class ExecutionReason(StrEnum):
    """Explicit execution outcomes; no reason is inferred from P&L."""

    TARGET = "TARGET"
    STOP = "STOP"
    TARGET_GAP = "TARGET_GAP"
    STOP_GAP = "STOP_GAP"
    TIME_EXIT = "TIME_EXIT"
    DATA_GAP_LIQUIDATION = "DATA_GAP_LIQUIDATION"
    STALE_ACTIVITY_LIQUIDATION = "STALE_ACTIVITY_LIQUIDATION"
    MISSING_ENTRY_MINUTE = "MISSING_ENTRY_MINUTE"
    INACTIVE_ENTRY_MINUTE = "INACTIVE_ENTRY_MINUTE"
    ENTRY_GAP_THROUGH_STOP = "ENTRY_GAP_THROUGH_STOP"
    EXECUTED_RISK_TOO_SMALL = "EXECUTED_RISK_TOO_SMALL"
    UNRESOLVED_DATA_EXIT = "UNRESOLVED_DATA_EXIT"
    UNRESOLVED_STALE_EXIT = "UNRESOLVED_STALE_EXIT"
    UNRESOLVED_TIME_EXIT = "UNRESOLVED_TIME_EXIT"


@dataclass(frozen=True)
class ExecutionSignal:
    """Frozen signal-layer facts required by the neutral execution adapter."""

    instrument: str
    direction: int
    signal_timestamp: pd.Timestamp
    window_end: pd.Timestamp
    stop_price: float
    target_rr: float = 2.0

    def __post_init__(self) -> None:
        if self.direction not in (-1, 1):
            raise ValueError("direction must be -1 or 1")
        if self.target_rr <= 0:
            raise ValueError("target_rr must be positive")
        if pd.Timestamp(self.window_end) <= pd.Timestamp(self.signal_timestamp):
            raise ValueError("window_end must be after signal_timestamp")


@dataclass(frozen=True)
class ExecutionConfig:
    """Execution economics and conservative ordering rules."""

    tick_size: float
    point_value: float
    commission_per_side: float
    entry_slippage_ticks: float = 1.0
    stop_slippage_ticks: float = 1.0
    market_exit_slippage_ticks: float = 1.0
    activity_column: str | None = "is_active_quote"
    maximum_consecutive_inactive_minutes: int = 10
    collision_policy: str = "stop_first"

    def __post_init__(self) -> None:
        if self.tick_size <= 0 or self.point_value <= 0:
            raise ValueError("tick_size and point_value must be positive")
        if self.commission_per_side < 0:
            raise ValueError("commission_per_side must be non-negative")
        if self.maximum_consecutive_inactive_minutes < 0:
            raise ValueError("maximum inactive run must be non-negative")
        if self.collision_policy != "stop_first":
            raise ValueError("only stop_first collision policy is supported")


@dataclass(frozen=True)
class ExecutionOutcome:
    """Deterministic execution record; unresolved paths have no manufactured return."""

    status: str
    reason: str
    instrument: str
    direction: int
    signal_timestamp: pd.Timestamp
    window_end: pd.Timestamp
    entry_timestamp: pd.Timestamp | None = None
    entry_price_raw: float | None = None
    entry_price: float | None = None
    stop_price: float | None = None
    target_price: float | None = None
    exit_timestamp: pd.Timestamp | None = None
    exit_price_raw: float | None = None
    exit_price: float | None = None
    gross_points: float | None = None
    gross_r: float | None = None
    commission_dollars: float | None = None
    commission_r: float | None = None
    net_r: float | None = None
    holding_minutes: int | None = None
    collision: bool = False
    gap_minutes: int = 0

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def mark_synthetic_fixture(frame: pd.DataFrame) -> pd.DataFrame:
    """Mark a synthetic test fixture explicitly; real data must never be inferred."""

    frame.attrs["asia_sweep_source_kind"] = _SYNTHETIC_SOURCE_KIND
    return frame


def _adverse_price(
    price: float,
    direction: int,
    ticks: float,
    tick_size: float,
    *,
    entry: bool,
) -> float:
    sign = direction if entry else -direction
    return float(price + sign * ticks * tick_size)


def _validate_frame(frame: pd.DataFrame, cfg: ExecutionConfig) -> pd.DataFrame:
    if frame.attrs.get("asia_sweep_source_kind") != _SYNTHETIC_SOURCE_KIND:
        raise ValueError("execution adapter is synthetic-test-only")
    required = set(_REQUIRED_COLUMNS)
    if cfg.activity_column is not None:
        required.add(cfg.activity_column)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"one_minute missing required columns: {sorted(missing)}")

    out = frame.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    duplicate_mask = out["timestamp"].duplicated(keep=False)
    if bool(duplicate_mask.any()):
        raise ValueError("one_minute has duplicate timestamps")
    off_grid = (
        (out["timestamp"].dt.second != 0)
        | (out["timestamp"].dt.microsecond != 0)
        | (out["timestamp"].dt.nanosecond != 0)
    )
    if bool(off_grid.any()):
        raise ValueError("one_minute has off-grid timestamps")
    out = out.sort_values("timestamp").reset_index(drop=True)
    if out.empty:
        raise ValueError("one_minute is empty")
    return out


def _is_active(row: pd.Series, cfg: ExecutionConfig) -> bool:
    if cfg.activity_column is None:
        return True
    return float(row[cfg.activity_column]) > 0


def _blocked(
    signal: ExecutionSignal,
    reason: ExecutionReason,
) -> ExecutionOutcome:
    return ExecutionOutcome(
        status=ExecutionStatus.BLOCKED,
        reason=reason,
        instrument=signal.instrument,
        direction=signal.direction,
        signal_timestamp=signal.signal_timestamp,
        window_end=signal.window_end,
        stop_price=signal.stop_price,
    )


def _unresolved(
    signal: ExecutionSignal,
    reason: ExecutionReason,
    *,
    entry_time: pd.Timestamp,
    entry_raw: float,
    entry: float,
    target: float,
) -> ExecutionOutcome:
    return ExecutionOutcome(
        status=ExecutionStatus.UNRESOLVED,
        reason=reason,
        instrument=signal.instrument,
        direction=signal.direction,
        signal_timestamp=signal.signal_timestamp,
        window_end=signal.window_end,
        entry_timestamp=entry_time,
        entry_price_raw=entry_raw,
        entry_price=entry,
        stop_price=signal.stop_price,
        target_price=target,
    )


def _finish(
    *,
    signal: ExecutionSignal,
    cfg: ExecutionConfig,
    entry_time: pd.Timestamp,
    entry_raw: float,
    entry: float,
    target: float,
    exit_time: pd.Timestamp,
    exit_raw: float,
    exit_price: float,
    reason: ExecutionReason,
    collision: bool = False,
    gap_minutes: int = 0,
) -> ExecutionOutcome:
    risk_points = abs(entry - signal.stop_price)
    gross_points = signal.direction * (exit_price - entry)
    gross_r = gross_points / risk_points
    commission = 2.0 * cfg.commission_per_side
    commission_r = commission / (risk_points * cfg.point_value)
    holding_minutes = int((exit_time - entry_time).total_seconds() // 60)
    return ExecutionOutcome(
        status=ExecutionStatus.EXITED,
        reason=reason,
        instrument=signal.instrument,
        direction=signal.direction,
        signal_timestamp=signal.signal_timestamp,
        window_end=signal.window_end,
        entry_timestamp=entry_time,
        entry_price_raw=entry_raw,
        entry_price=entry,
        stop_price=signal.stop_price,
        target_price=target,
        exit_timestamp=exit_time,
        exit_price_raw=exit_raw,
        exit_price=exit_price,
        gross_points=gross_points,
        gross_r=gross_r,
        commission_dollars=commission,
        commission_r=commission_r,
        net_r=gross_r - commission_r,
        holding_minutes=holding_minutes,
        collision=collision,
        gap_minutes=gap_minutes,
    )


def _market_exit(
    *,
    signal: ExecutionSignal,
    cfg: ExecutionConfig,
    entry_time: pd.Timestamp,
    entry_raw: float,
    entry: float,
    target: float,
    exit_time: pd.Timestamp,
    exit_raw: float,
    reason: ExecutionReason,
    slippage_ticks: float,
    gap_minutes: int = 0,
) -> ExecutionOutcome:
    exit_price = _adverse_price(
        exit_raw,
        signal.direction,
        slippage_ticks,
        cfg.tick_size,
        entry=False,
    )
    return _finish(
        signal=signal,
        cfg=cfg,
        entry_time=entry_time,
        entry_raw=entry_raw,
        entry=entry,
        target=target,
        exit_time=exit_time,
        exit_raw=exit_raw,
        exit_price=exit_price,
        reason=reason,
        gap_minutes=gap_minutes,
    )


def _risk_and_target(
    signal: ExecutionSignal,
    cfg: ExecutionConfig,
    entry_raw: float,
) -> tuple[float, float, float] | ExecutionOutcome:
    entry = _adverse_price(
        entry_raw,
        signal.direction,
        cfg.entry_slippage_ticks,
        cfg.tick_size,
        entry=True,
    )
    raw_through_stop = (
        entry_raw <= signal.stop_price
        if signal.direction > 0
        else entry_raw >= signal.stop_price
    )
    risk_points = (
        entry - signal.stop_price
        if signal.direction > 0
        else signal.stop_price - entry
    )
    if raw_through_stop or risk_points <= 0:
        return _blocked(signal, ExecutionReason.ENTRY_GAP_THROUGH_STOP)
    if risk_points <= cfg.tick_size:
        return _blocked(signal, ExecutionReason.EXECUTED_RISK_TOO_SMALL)
    target = entry + signal.direction * risk_points * signal.target_rr
    return entry, risk_points, target


def simulate_execution(
    signal: ExecutionSignal,
    one_minute: pd.DataFrame,
    cfg: ExecutionConfig,
) -> ExecutionOutcome:
    """Simulate one frozen signal on synthetic one-minute data only."""

    bars = _validate_frame(one_minute, cfg)
    signal_time = pd.Timestamp(signal.signal_timestamp)
    window_end = pd.Timestamp(signal.window_end)
    by_time = {
        pd.Timestamp(row["timestamp"]): row
        for _, row in bars.iterrows()
    }
    entry_row = by_time.get(signal_time)
    if entry_row is None:
        return _blocked(signal, ExecutionReason.MISSING_ENTRY_MINUTE)
    if not _is_active(entry_row, cfg):
        return _blocked(signal, ExecutionReason.INACTIVE_ENTRY_MINUTE)

    entry_raw = float(entry_row["open"])
    risk_result = _risk_and_target(signal, cfg, entry_raw)
    if isinstance(risk_result, ExecutionOutcome):
        return risk_result
    entry, _, target = risk_result

    expected = pd.date_range(
        signal_time,
        window_end,
        freq="1min",
        inclusive="left",
    )
    inactive_run = 0
    stale_unsafe = False

    for timestamp in expected:
        timestamp = pd.Timestamp(timestamp)
        row = by_time.get(timestamp)
        if row is None:
            future = bars[bars["timestamp"] > timestamp]
            if future.empty:
                return _unresolved(
                    signal,
                    ExecutionReason.UNRESOLVED_DATA_EXIT,
                    entry_time=signal_time,
                    entry_raw=entry_raw,
                    entry=entry,
                    target=target,
                )
            next_row = future.iloc[0]
            next_time = pd.Timestamp(next_row["timestamp"])
            if next_time > window_end:
                return _unresolved(
                    signal,
                    ExecutionReason.UNRESOLVED_DATA_EXIT,
                    entry_time=signal_time,
                    entry_raw=entry_raw,
                    entry=entry,
                    target=target,
                )
            gap_minutes = int((next_time - timestamp).total_seconds() // 60)
            return _market_exit(
                signal=signal,
                cfg=cfg,
                entry_time=signal_time,
                entry_raw=entry_raw,
                entry=entry,
                target=target,
                exit_time=next_time,
                exit_raw=float(next_row["open"]),
                reason=ExecutionReason.DATA_GAP_LIQUIDATION,
                slippage_ticks=cfg.market_exit_slippage_ticks,
                gap_minutes=gap_minutes,
            )

        if not _is_active(row, cfg):
            inactive_run += 1
            if inactive_run > cfg.maximum_consecutive_inactive_minutes:
                stale_unsafe = True
            continue

        if stale_unsafe:
            return _market_exit(
                signal=signal,
                cfg=cfg,
                entry_time=signal_time,
                entry_raw=entry_raw,
                entry=entry,
                target=target,
                exit_time=timestamp,
                exit_raw=float(row["open"]),
                reason=ExecutionReason.STALE_ACTIVITY_LIQUIDATION,
                slippage_ticks=cfg.market_exit_slippage_ticks,
                gap_minutes=inactive_run,
            )
        inactive_run = 0

        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        if signal.direction > 0:
            stop_gap = open_ <= signal.stop_price
            target_gap = open_ >= target
            stop_hit = low <= signal.stop_price
            target_hit = high >= target
        else:
            stop_gap = open_ >= signal.stop_price
            target_gap = open_ <= target
            stop_hit = high >= signal.stop_price
            target_hit = low <= target

        if timestamp != signal_time and stop_gap:
            return _market_exit(
                signal=signal,
                cfg=cfg,
                entry_time=signal_time,
                entry_raw=entry_raw,
                entry=entry,
                target=target,
                exit_time=timestamp,
                exit_raw=open_,
                reason=ExecutionReason.STOP_GAP,
                slippage_ticks=cfg.stop_slippage_ticks,
            )
        if timestamp != signal_time and target_gap:
            return _finish(
                signal=signal,
                cfg=cfg,
                entry_time=signal_time,
                entry_raw=entry_raw,
                entry=entry,
                target=target,
                exit_time=timestamp,
                exit_raw=target,
                exit_price=target,
                reason=ExecutionReason.TARGET_GAP,
            )
        if stop_hit:
            stop_fill = _adverse_price(
                signal.stop_price,
                signal.direction,
                cfg.stop_slippage_ticks,
                cfg.tick_size,
                entry=False,
            )
            return _finish(
                signal=signal,
                cfg=cfg,
                entry_time=signal_time,
                entry_raw=entry_raw,
                entry=entry,
                target=target,
                exit_time=timestamp,
                exit_raw=signal.stop_price,
                exit_price=stop_fill,
                reason=ExecutionReason.STOP,
                collision=bool(target_hit),
            )
        if target_hit:
            return _finish(
                signal=signal,
                cfg=cfg,
                entry_time=signal_time,
                entry_raw=entry_raw,
                entry=entry,
                target=target,
                exit_time=timestamp,
                exit_raw=target,
                exit_price=target,
                reason=ExecutionReason.TARGET,
            )

    time_row = by_time.get(window_end)
    if stale_unsafe:
        if time_row is not None and _is_active(time_row, cfg):
            return _market_exit(
                signal=signal,
                cfg=cfg,
                entry_time=signal_time,
                entry_raw=entry_raw,
                entry=entry,
                target=target,
                exit_time=window_end,
                exit_raw=float(time_row["open"]),
                reason=ExecutionReason.STALE_ACTIVITY_LIQUIDATION,
                slippage_ticks=cfg.market_exit_slippage_ticks,
                gap_minutes=inactive_run,
            )
        return _unresolved(
            signal,
            ExecutionReason.UNRESOLVED_STALE_EXIT,
            entry_time=signal_time,
            entry_raw=entry_raw,
            entry=entry,
            target=target,
        )
    if time_row is None or not _is_active(time_row, cfg):
        return _unresolved(
            signal,
            ExecutionReason.UNRESOLVED_TIME_EXIT,
            entry_time=signal_time,
            entry_raw=entry_raw,
            entry=entry,
            target=target,
        )
    return _market_exit(
        signal=signal,
        cfg=cfg,
        entry_time=signal_time,
        entry_raw=entry_raw,
        entry=entry,
        target=target,
        exit_time=window_end,
        exit_raw=float(time_row["open"]),
        reason=ExecutionReason.TIME_EXIT,
        slippage_ticks=cfg.market_exit_slippage_ticks,
    )


def validate_execution_prefix(
    signal: ExecutionSignal,
    one_minute: pd.DataFrame,
    cfg: ExecutionConfig,
) -> bool:
    """Reproduce an exited decision using no rows after its determining minute."""

    outcome = simulate_execution(signal, one_minute, cfg)
    if outcome.exit_timestamp is None:
        return True
    prefix = one_minute[
        pd.to_datetime(one_minute["timestamp"]) <= outcome.exit_timestamp
    ].copy()
    mark_synthetic_fixture(prefix)
    replay = simulate_execution(signal, prefix, cfg)
    return replay.as_dict() == outcome.as_dict()
