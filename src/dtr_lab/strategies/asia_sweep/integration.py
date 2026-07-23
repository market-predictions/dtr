from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd

from .execution import (
    ExecutionConfig,
    ExecutionOutcome,
    ExecutionSignal,
    mark_synthetic_fixture,
    simulate_execution,
    validate_execution_prefix,
)
from .model import DEFAULT_WINDOWS, AsiaSweepVariant

_EVENT_SOURCE_KIND = "SYNTHETIC_EVENT_PACKET"
_MINUTE_EVENT_KEY_ATTR = "asia_sweep_event_key"
_MINUTE_EVENT_DIGEST_ATTR = "asia_sweep_event_contract_digest"
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
_FROZEN_TARGET_RR = 2.0
_SHA256_HEX = frozenset("0123456789abcdef")


def _strict_text(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be non-empty and contain no edge whitespace")
    return value


@dataclass(frozen=True)
class IntegrationConfig:
    """Strict one-instrument synthetic event-to-execution contract."""

    instrument: str
    execution: ExecutionConfig
    session_timezone: str = "America/New_York"
    price_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        _strict_text(self.instrument, name="instrument")
        if not self.session_timezone:
            raise ValueError("session_timezone must be non-empty")
        try:
            ZoneInfo(self.session_timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown session_timezone: {self.session_timezone}") from exc
        if not math.isfinite(self.price_tolerance) or self.price_tolerance <= 0:
            raise ValueError("price_tolerance must be positive and finite")


def mark_synthetic_event_packet(frame: pd.DataFrame) -> pd.DataFrame:
    """Opt in a synthetic packet; this is a workflow guard, not a security boundary."""

    frame.attrs["asia_sweep_event_source_kind"] = _EVENT_SOURCE_KIND
    return frame


def _canonical_trade_date(value: object) -> str:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("trade_date is invalid") from exc
    if pd.isna(timestamp):
        raise ValueError("trade_date is missing")
    return timestamp.strftime("%Y-%m-%d")


def _canonical_event_identity(event: Mapping[str, object]) -> str:
    values = [
        _strict_text(event["instrument"], name="instrument"),
        _canonical_trade_date(event["trade_date"]),
        _strict_text(event["execution_window"], name="execution_window"),
        _strict_text(event["variant"], name="variant"),
    ]
    return "|".join(values)


def stable_event_key(event: Mapping[str, object]) -> str:
    """Build a deterministic key from immutable event identity fields."""

    identity = _canonical_event_identity(event)
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _is_sha256_key(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and set(value).issubset(_SHA256_HEX)
    )


def _is_on_grid(value: float, tick_size: float, tolerance: float) -> bool:
    ticks = value / tick_size
    return math.isclose(ticks, round(ticks), rel_tol=0.0, abs_tol=tolerance)


def _require_grid_price(
    value: object,
    *,
    name: str,
    cfg: IntegrationConfig,
) -> float:
    try:
        price = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(price):
        raise ValueError(f"{name} must be finite")
    if not _is_on_grid(
        price,
        cfg.execution.tick_size,
        cfg.price_tolerance,
    ):
        raise ValueError(f"{name} is off the configured tick grid")
    return price


def _window_bounds(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    window_name = _strict_text(event["execution_window"], name="execution_window")
    windows = {window.name: window for window in DEFAULT_WINDOWS}
    if window_name not in windows:
        raise ValueError(f"unknown execution window: {window_name}")
    window = windows[window_name]
    day = pd.Timestamp(_canonical_trade_date(event["trade_date"]))
    start_naive = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=window.start_hour,
        minute=window.start_minute,
    )
    end_naive = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=window.end_hour,
        minute=window.end_minute,
    )
    start = start_naive.tz_localize(
        cfg.session_timezone,
        ambiguous="raise",
        nonexistent="raise",
    )
    end = end_naive.tz_localize(
        cfg.session_timezone,
        ambiguous="raise",
        nonexistent="raise",
    )
    return start, end


def _window_end(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> pd.Timestamp:
    return _window_bounds(event, cfg)[1]


def _validate_event_packet(
    frame: pd.DataFrame,
    cfg: IntegrationConfig,
) -> pd.DataFrame:
    if frame.attrs.get("asia_sweep_event_source_kind") != _EVENT_SOURCE_KIND:
        raise ValueError("event integration is synthetic-packet-only")
    missing = _REQUIRED_EVENT_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"event packet missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("event packet is empty")
    packet = frame.copy(deep=True)
    instruments = {
        _strict_text(value, name="instrument") for value in packet["instrument"]
    }
    if instruments != {cfg.instrument}:
        raise ValueError(
            "event packet instruments must equal the one configured instrument"
        )
    return packet


def _strict_direction(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("event direction must be -1 or 1")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("event direction must be -1 or 1") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError("event direction must be -1 or 1")
    direction = int(numeric)
    if direction not in (-1, 1):
        raise ValueError("event direction must be -1 or 1")
    return direction


def _validate_event_geometry(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> tuple[int, pd.Timestamp, float, float, float]:
    if _strict_text(event["status"], name="status") != "SIGNAL":
        raise ValueError("only SIGNAL events may be mapped to execution")

    variant_text = _strict_text(event["variant"], name="variant")
    try:
        AsiaSweepVariant(variant_text)
    except ValueError as exc:
        raise ValueError(f"unknown Asia Sweep variant: {variant_text}") from exc

    instrument = _strict_text(event["instrument"], name="instrument")
    if instrument != cfg.instrument:
        raise ValueError("event instrument does not match integration economics")
    direction = _strict_direction(event["direction"])
    try:
        entry_time = pd.Timestamp(event["entry_timestamp"])
    except (TypeError, ValueError) as exc:
        raise ValueError("event entry_timestamp is invalid") from exc
    if pd.isna(entry_time) or entry_time.tzinfo is None:
        raise ValueError("event entry_timestamp must be timezone-aware")
    entry_time = entry_time.tz_convert(cfg.session_timezone)
    if (
        entry_time.second != 0
        or entry_time.microsecond != 0
        or entry_time.nanosecond != 0
    ):
        raise ValueError("event entry_timestamp must be one-minute aligned")

    trade_date = _canonical_trade_date(event["trade_date"])
    if entry_time.strftime("%Y-%m-%d") != trade_date:
        raise ValueError("event entry_timestamp local date must equal trade_date")
    window_start, window_end = _window_bounds(event, cfg)
    if not window_start <= entry_time < window_end:
        raise ValueError("event entry_timestamp must fall inside its execution window")

    entry = _require_grid_price(event["entry_price_raw"], name="event entry", cfg=cfg)
    stop = _require_grid_price(event["stop_price_raw"], name="event stop", cfg=cfg)
    target = _require_grid_price(event["target_price_raw"], name="event target", cfg=cfg)

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


def event_contract_digest(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> str:
    """Hash all execution-relevant event facts after strict canonical validation."""

    direction, entry_time, entry, stop, target = _validate_event_geometry(event, cfg)
    tick_size = cfg.execution.tick_size
    payload = "|".join(
        (
            _canonical_event_identity(event),
            "SIGNAL",
            str(direction),
            entry_time.isoformat(),
            str(int(round(entry / tick_size))),
            str(int(round(stop / tick_size))),
            str(int(round(target / tick_size))),
            str(_FROZEN_TARGET_RR),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def mark_synthetic_event_minute_frame(
    frame: pd.DataFrame,
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> pd.DataFrame:
    """Bind one synthetic minute fixture to a validated event identity and payload."""

    mark_synthetic_fixture(frame)
    frame.attrs[_MINUTE_EVENT_KEY_ATTR] = stable_event_key(event)
    frame.attrs[_MINUTE_EVENT_DIGEST_ATTR] = event_contract_digest(event, cfg)
    return frame


def map_event_to_execution_signal(
    event: Mapping[str, object],
    cfg: IntegrationConfig,
) -> ExecutionSignal:
    """Map one immutable, validated synthetic event into the frozen signal model."""

    direction, entry_time, _, stop, _ = _validate_event_geometry(event, cfg)
    return ExecutionSignal(
        instrument=cfg.instrument,
        direction=direction,
        signal_timestamp=entry_time,
        window_end=_window_end(event, cfg),
        stop_price=stop,
        target_rr=_FROZEN_TARGET_RR,
    )


def _validate_minute_grid(frame: pd.DataFrame, cfg: IntegrationConfig) -> None:
    required = {"timestamp", "open", "high", "low", "close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"minute frame missing grid columns: {sorted(missing)}")
    for column in ("open", "high", "low", "close"):
        values = pd.to_numeric(frame[column], errors="raise")
        for value in values:
            _require_grid_price(value, name=f"minute {column}", cfg=cfg)


def _validate_minute_binding(
    event: Mapping[str, object],
    one_minute: pd.DataFrame,
    cfg: IntegrationConfig,
) -> tuple[str, str]:
    key = stable_event_key(event)
    digest = event_contract_digest(event, cfg)
    if one_minute.attrs.get(_MINUTE_EVENT_KEY_ATTR) != key:
        raise ValueError("minute frame event key does not match mapped event")
    if one_minute.attrs.get(_MINUTE_EVENT_DIGEST_ATTR) != digest:
        raise ValueError("minute frame event contract digest does not match mapped event")
    return key, digest


def execute_mapped_event(
    event: Mapping[str, object],
    one_minute: pd.DataFrame,
    cfg: IntegrationConfig,
) -> tuple[str, ExecutionSignal, ExecutionOutcome]:
    """Map and execute one bound synthetic event without mutating either input."""

    signal = map_event_to_execution_signal(event, cfg)
    key, _ = _validate_minute_binding(event, one_minute, cfg)
    _validate_minute_grid(one_minute, cfg)
    outcome = simulate_execution(signal, one_minute, cfg.execution)
    return key, signal, outcome


def validate_integrated_prefix(
    event: Mapping[str, object],
    one_minute: pd.DataFrame,
    cfg: IntegrationConfig,
) -> bool:
    """Validate mapping determinism and execution prefix causality."""

    signal = map_event_to_execution_signal(event, cfg)
    key, digest = _validate_minute_binding(event, one_minute, cfg)
    _validate_minute_grid(one_minute, cfg)
    replay_event = dict(event)
    replay_signal = map_event_to_execution_signal(replay_event, cfg)
    return (
        key == stable_event_key(replay_event)
        and digest == event_contract_digest(replay_event, cfg)
        and signal == replay_signal
        and validate_execution_prefix(signal, one_minute, cfg.execution)
    )


def replay_synthetic_event_packet(
    events: pd.DataFrame,
    minute_frames: Mapping[str, pd.DataFrame],
    cfg: IntegrationConfig,
) -> pd.DataFrame:
    """Replay a one-instrument marked packet, sorted by stable key."""

    packet = _validate_event_packet(events, cfg)
    keys = packet.apply(lambda row: stable_event_key(row), axis=1)
    if bool(keys.duplicated(keep=False).any()):
        duplicates = sorted(keys[keys.duplicated(keep=False)].unique())
        raise ValueError(f"event packet contains duplicate stable keys: {duplicates[:3]}")

    supplied_keys = set(minute_frames)
    if any(not _is_sha256_key(key) for key in supplied_keys):
        raise ValueError("minute frame keys must be lowercase SHA-256 strings")
    expected_keys = set(keys)
    missing_frames = sorted(expected_keys.difference(supplied_keys))
    orphan_frames = sorted(supplied_keys.difference(expected_keys))
    if missing_frames:
        raise ValueError(f"missing minute frame for event key: {missing_frames[0]}")
    if orphan_frames:
        raise ValueError(f"orphan minute frame key: {orphan_frames[0]}")

    rows: list[dict[str, object]] = []
    for position, (_, event) in enumerate(packet.iterrows()):
        key = keys.iloc[position]
        one_minute = minute_frames[key]
        signal_key, signal, outcome = execute_mapped_event(event, one_minute, cfg)
        digest = event_contract_digest(event, cfg)
        if not validate_integrated_prefix(event, one_minute, cfg):
            raise ValueError(f"integrated prefix replay failed for event key: {key}")
        if signal_key != key:
            raise ValueError("stable event key changed during execution mapping")
        rows.append(
            {
                "stable_event_key": key,
                "event_contract_digest": digest,
                "trade_date": _canonical_trade_date(event["trade_date"]),
                "execution_window": _strict_text(
                    event["execution_window"],
                    name="execution_window",
                ),
                "variant": _strict_text(event["variant"], name="variant"),
                "event_entry_price_raw": float(event["entry_price_raw"]),
                "event_stop_price_raw": float(event["stop_price_raw"]),
                "event_target_price_raw": float(event["target_price_raw"]),
                "mapped_signal_timestamp": signal.signal_timestamp,
                "mapped_window_end": signal.window_end,
                "configured_tick_size": cfg.execution.tick_size,
                "configured_point_value": cfg.execution.point_value,
                "configured_commission_per_side": cfg.execution.commission_per_side,
                "configured_entry_slippage_ticks": cfg.execution.entry_slippage_ticks,
                "configured_stop_slippage_ticks": cfg.execution.stop_slippage_ticks,
                "configured_market_exit_slippage_ticks": (
                    cfg.execution.market_exit_slippage_ticks
                ),
                **outcome.as_dict(),
            }
        )
    return pd.DataFrame(rows).sort_values("stable_event_key").reset_index(drop=True)
