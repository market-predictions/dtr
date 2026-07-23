from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Mapping

import pandas as pd

from .execution import (
    ExecutionConfig,
    ExecutionOutcome,
    ExecutionSignal,
    mark_synthetic_fixture,
    simulate_execution,
    validate_execution_prefix,
)
from .model import AsiaSweepVariant, DEFAULT_WINDOWS

_EVENT_SOURCE_KIND = "SYNTHETIC_EVENT_PACKET"
_REQUIRED_EVENT_COLUMNS = {
    "instrument",
    "trade_date",
    "execution_window",
    "variant",
    "status",
    "direction",
    "entry_timestamp",
    "entry_price_raw",
    "stop_price_raw",
    "target_price_raw",
}
_IDENTITY_COLUMNS = (
    "instrument",
    "trade_date",
    "execution_window",
    "variant",
)
_FROZEN_TARGET_RR = 2.0


@dataclass(frozen=True)
class IntegrationConfig:
    """Strict synthetic event-to-execution integration contract."""

    execution: ExecutionConfig
    session_timezone: str = "America/New_York"
    price_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        if not self.session_timezone:
            raise ValueError("session_timezone must be non-empty")
        if not math.isfinite(self.price_tolerance) or self.price_tolerance <= 0:
            raise ValueError("price_tolerance must be positive and finite")


def mark_synthetic_event_packet(frame: pd.DataFrame) -> pd.DataFrame:
    """Mark a synthetic event packet; this prevents accidental real-data use."""

    frame.attrs["asia_sweep_event_source_kind"] = _EVENT_SOURCE_KIND
    return frame


def _canonical_trade_date(value: object) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp is pd.NaT:
        raise ValueError("trade_date is missing")
    return timestamp.strftime("%Y-%m-%d")


def _canonical_event_identity(event: Mapping[str, object]) -> str:
    values = [
        str(event["instrument"]),
        _canonical_trade_date(event["trade_date"]),
        str(event["execution_window"]),
        str(event["variant"]),
    ]
    return "|".join(values)


def stable_event_key(event: Mapping[str, object]) -> str:
    """Build a deterministic key from immutable event identity fields."""

    identity = _canonical_event_identity(event)
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _is_on_grid(value: float, tick_size: float, tolerance: float) -> bool:
    ticks = value / tick_size
    return math.isclose(ticks, round(ticks), rel_tol=0.0, abs_tol=tolerance)


def _require_grid_price(
    value: object,
    *,
    name: str,
    cfg: IntegrationConfig,
) -> float:
    price = float(value)
    if not math.isfinite(price):
        raise ValueError(f"{name} must be finite")
    if not _is_on_grid(
        price,
        cfg.execution.tick_size,
        cfg.price_tolerance,
    ):
        raise ValueError(f"{name} is off the configured tick grid")
    return price


def _window_end(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> pd.Timestamp:
    window_name = str(event["execution_window"])
    windows = {window.name: window for window in DEFAULT_WINDOWS}
    if window_name not in windows:
        raise ValueError(f"unknown execution window: {window_name}")
    window = windows[window_name]
    day = pd.Timestamp(_canonical_trade_date(event["trade_date"]))
    naive = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=window.end_hour,
        minute=window.end_minute,
    )
    return naive.tz_localize(
        cfg.session_timezone,
        ambiguous="raise",
        nonexistent="raise",
    )


def _validate_event_packet(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.attrs.get("asia_sweep_event_source_kind") != _EVENT_SOURCE_KIND:
        raise ValueError("event integration is synthetic-packet-only")
    missing = _REQUIRED_EVENT_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"event packet missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("event packet is empty")
    return frame.copy(deep=True)


def _validate_event_geometry(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> tuple[int, pd.Timestamp, float, float, float]:
    if str(event["status"]) != "SIGNAL":
        raise ValueError("only SIGNAL events may be mapped to execution")
    try:
        AsiaSweepVariant(str(event["variant"]))
    except ValueError as exc:
        raise ValueError(f"unknown Asia Sweep variant: {event['variant']}") from exc

    direction = int(event["direction"])
    if direction not in (-1, 1):
        raise ValueError("event direction must be -1 or 1")
    entry_time = pd.Timestamp(event["entry_timestamp"])
    if entry_time.tzinfo is None:
        raise ValueError("event entry_timestamp must be timezone-aware")
    entry_time = entry_time.tz_convert(cfg.session_timezone)
    if (
        entry_time.second != 0
        or entry_time.microsecond != 0
        or entry_time.nanosecond != 0
    ):
        raise ValueError("event entry_timestamp must be one-minute aligned")

    entry = _require_grid_price(event["entry_price_raw"], name="event entry", cfg=cfg)
    stop = _require_grid_price(event["stop_price_raw"], name="event stop", cfg=cfg)
    target = _require_grid_price(event["target_price_raw"], name="event target", cfg=cfg)
    window_end = _window_end(event, cfg)
    if entry_time >= window_end:
        raise ValueError("event entry_timestamp must precede execution-window end")

    risk = entry - stop if direction > 0 else stop - entry
    if risk <= cfg.execution.tick_size:
        raise ValueError("event risk must exceed one tick")
    expected_target = entry + direction * risk * _FROZEN_TARGET_RR
    if not math.isclose(
        target,
        expected_target,
        rel_tol=0.0,
        abs_tol=cfg.price_tolerance * cfg.execution.tick_size,
    ):
        raise ValueError("event target is inconsistent with frozen 2.0R geometry")
    if direction > 0 and not stop < entry < target:
        raise ValueError("invalid long event price geometry")
    if direction < 0 and not target < entry < stop:
        raise ValueError("invalid short event price geometry")
    return direction, entry_time, entry, stop, target


def map_event_to_execution_signal(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> ExecutionSignal:
    """Map one immutable, validated synthetic event into the frozen signal model."""

    direction, entry_time, _, stop, _ = _validate_event_geometry(event, cfg)
    return ExecutionSignal(
        instrument=str(event["instrument"]),
        direction=direction,
        signal_timestamp=entry_time,
        window_end=_window_end(event, cfg),
        stop_price=stop,
        target_rr=_FROZEN_TARGET_RR,
    )


def _validate_minute_grid(frame: pd.DataFrame, cfg: IntegrationConfig) -> None:
    required = {"open", "high", "low", "close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"minute frame missing grid columns: {sorted(missing)}")
    for column in sorted(required):
        values = pd.to_numeric(frame[column], errors="raise")
        for value in values:
            _require_grid_price(value, name=f"minute {column}", cfg=cfg)


def execute_mapped_event(
    event: Mapping[str, object],
    one_minute: pd.DataFrame,
    cfg: IntegrationConfig,
) -> tuple[str, ExecutionSignal, ExecutionOutcome]:
    """Map and execute one synthetic event without mutating either input."""

    signal = map_event_to_execution_signal(event, cfg)
    _validate_minute_grid(one_minute, cfg)
    outcome = simulate_execution(signal, one_minute, cfg.execution)
    return stable_event_key(event), signal, outcome


def validate_integrated_prefix(
    event: Mapping[str, object],
    one_minute: pd.DataFrame,
    cfg: IntegrationConfig,
) -> bool:
    """Validate both mapping determinism and execution prefix causality."""

    signal = map_event_to_execution_signal(event, cfg)
    _validate_minute_grid(one_minute, cfg)
    replay_signal = map_event_to_execution_signal(dict(event), cfg)
    return signal == replay_signal and validate_execution_prefix(
        signal,
        one_minute,
        cfg.execution,
    )


def replay_synthetic_event_packet(
    events: pd.DataFrame,
    minute_frames: Mapping[str, pd.DataFrame],
    cfg: IntegrationConfig,
) -> pd.DataFrame:
    """Replay a marked synthetic packet deterministically, sorted by stable key."""

    packet = _validate_event_packet(events)
    keys = packet.apply(lambda row: stable_event_key(row), axis=1)
    if bool(keys.duplicated(keep=False).any()):
        duplicates = sorted(keys[keys.duplicated(keep=False)].unique())
        raise ValueError(f"event packet contains duplicate stable keys: {duplicates[:3]}")

    rows: list[dict[str, object]] = []
    for position, (_, event) in enumerate(packet.iterrows()):
        key = keys.iloc[position]
        if key not in minute_frames:
            raise ValueError(f"missing minute frame for event key: {key}")
        signal_key, signal, outcome = execute_mapped_event(
            event,
            minute_frames[key],
            cfg,
        )
        record = {
            "stable_event_key": signal_key,
            **{column: event[column] for column in _IDENTITY_COLUMNS},
            "signal_timestamp": signal.signal_timestamp,
            "window_end": signal.window_end,
            **outcome.as_dict(),
        }
        rows.append(record)
    return pd.DataFrame(rows).sort_values("stable_event_key").reset_index(drop=True)
