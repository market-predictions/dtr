from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR

import pandas as pd

from .integration import (
    IntegrationConfig,
    event_contract_digest,
    mark_synthetic_event_minute_frame,
    stable_event_key,
)
from .model import DEFAULT_WINDOWS, AsiaSweepVariant

_PROXY_SOURCE_KIND = "SYNTHETIC_DUKASCOPY_INDEX_CFD_PROXY_FIXTURE"
_PROXY_EVENT_KIND_FIELD = "proxy_source_kind"
_PROXY_FRAME_KIND_ATTR = "asia_sweep_proxy_source_kind"
_PROXY_EVENT_KEY_ATTR = "asia_sweep_proxy_event_key"
_PROXY_EVENT_DIGEST_ATTR = "asia_sweep_proxy_event_digest"
_POLICY_VERSION = "DIRECTIONAL_PESSIMISTIC_V1"
_FROZEN_TARGET_RR = Decimal("2.0")
_REQUIRED_EVENT_FIELDS = {
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
    _PROXY_EVENT_KIND_FIELD,
}
_REQUIRED_FRAME_COLUMNS = {
    "timestamp",
    "open",
    "high",
    "low",
    "close",
}


@dataclass(frozen=True)
class ProxyNormalizationConfig:
    """Synthetic proxy-to-execution-grid normalization contract."""

    integration: IntegrationConfig
    source_quote_increment: Decimal | str | float = Decimal("0.001")
    policy_version: str = _POLICY_VERSION

    def __post_init__(self) -> None:
        source_increment = _as_decimal(
            self.source_quote_increment,
            name="source_quote_increment",
        )
        if source_increment <= 0:
            raise ValueError("source_quote_increment must be positive")
        execution_tick = _as_decimal(
            self.integration.execution.tick_size,
            name="execution_tick_size",
        )
        ratio = execution_tick / source_increment
        if ratio != ratio.to_integral_value():
            raise ValueError(
                "execution tick must be an integer multiple of source quote increment"
            )
        if not self.policy_version or self.policy_version != self.policy_version.strip():
            raise ValueError("policy_version must be non-empty and contain no edge whitespace")
        if self.integration.execution.activity_column is None:
            raise ValueError("proxy normalization requires an activity column")
        object.__setattr__(self, "source_quote_increment", source_increment)

    @property
    def execution_tick(self) -> Decimal:
        return _as_decimal(
            self.integration.execution.tick_size,
            name="execution_tick_size",
        )

    @property
    def activity_column(self) -> str:
        value = self.integration.execution.activity_column
        if value is None:  # guarded in __post_init__
            raise RuntimeError("proxy normalization activity column is unavailable")
        return value


@dataclass(frozen=True)
class ProxyEventFacts:
    """Canonical raw proxy event facts at source quote precision."""

    instrument: str
    trade_date: str
    execution_window: str
    variant: str
    direction: int
    entry_timestamp: pd.Timestamp
    window_end: pd.Timestamp
    entry: Decimal
    stop: Decimal
    target: Decimal


@dataclass(frozen=True)
class ProxyNormalizationResult:
    """Auditable normalized event and bound minute frame."""

    event: dict[str, object]
    one_minute: pd.DataFrame
    source_event_digest: str
    normalization_digest: str
    source_frame_digest: str


def _as_decimal(value: object, *, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not number.is_finite():
        raise ValueError(f"{name} must be finite")
    return number


def _strict_text(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be non-empty and contain no edge whitespace")
    return value


def _source_ticks(value: object, *, name: str, cfg: ProxyNormalizationConfig) -> int:
    price = _as_decimal(value, name=name)
    if price <= 0:
        raise ValueError(f"{name} must be positive")
    ticks = price / cfg.source_quote_increment
    integral = ticks.to_integral_value()
    if ticks != integral:
        raise ValueError(f"{name} is off the source quote grid")
    return int(integral)


def _source_price(value: object, *, name: str, cfg: ProxyNormalizationConfig) -> Decimal:
    ticks = _source_ticks(value, name=name, cfg=cfg)
    return Decimal(ticks) * cfg.source_quote_increment


def _floor_to_tick(value: Decimal, tick: Decimal) -> Decimal:
    units = (value / tick).to_integral_value(rounding=ROUND_FLOOR)
    return units * tick


def _ceil_to_tick(value: Decimal, tick: Decimal) -> Decimal:
    units = (value / tick).to_integral_value(rounding=ROUND_CEILING)
    return units * tick


def _strict_direction(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("proxy event direction must be -1 or 1")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("proxy event direction must be -1 or 1") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError("proxy event direction must be -1 or 1")
    direction = int(numeric)
    if direction not in (-1, 1):
        raise ValueError("proxy event direction must be -1 or 1")
    return direction


def _canonical_trade_date(value: object) -> str:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("proxy event trade_date is invalid") from exc
    if pd.isna(timestamp):
        raise ValueError("proxy event trade_date is missing")
    return timestamp.strftime("%Y-%m-%d")


def _window_bounds(
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    window_name = _strict_text(event["execution_window"], name="execution_window")
    windows = {window.name: window for window in DEFAULT_WINDOWS}
    if window_name not in windows:
        raise ValueError(f"unknown proxy execution window: {window_name}")
    window = windows[window_name]
    day = pd.Timestamp(_canonical_trade_date(event["trade_date"]))
    start = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=window.start_hour,
        minute=window.start_minute,
    ).tz_localize(
        cfg.integration.session_timezone,
        ambiguous="raise",
        nonexistent="raise",
    )
    end = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=window.end_hour,
        minute=window.end_minute,
    ).tz_localize(
        cfg.integration.session_timezone,
        ambiguous="raise",
        nonexistent="raise",
    )
    return start, end


def mark_synthetic_proxy_event(event: Mapping[str, object]) -> dict[str, object]:
    """Return a marked copy of a synthetic proxy event."""

    marked = dict(event)
    marked[_PROXY_EVENT_KIND_FIELD] = _PROXY_SOURCE_KIND
    return marked


def _validate_raw_event(
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> ProxyEventFacts:
    missing = _REQUIRED_EVENT_FIELDS.difference(event)
    if missing:
        raise ValueError(f"proxy event missing required fields: {sorted(missing)}")
    if event[_PROXY_EVENT_KIND_FIELD] != _PROXY_SOURCE_KIND:
        raise ValueError("proxy event is not a marked synthetic proxy fixture")

    instrument = _strict_text(event["instrument"], name="instrument")
    if instrument != cfg.integration.instrument:
        raise ValueError("proxy event instrument does not match integration economics")
    if _strict_text(event["status"], name="status") != "SIGNAL":
        raise ValueError("only SIGNAL proxy events may be normalized")
    variant = _strict_text(event["variant"], name="variant")
    try:
        AsiaSweepVariant(variant)
    except ValueError as exc:
        raise ValueError(f"unknown proxy Asia Sweep variant: {variant}") from exc
    direction = _strict_direction(event["direction"])

    try:
        entry_timestamp = pd.Timestamp(event["entry_timestamp"])
    except (TypeError, ValueError) as exc:
        raise ValueError("proxy event entry_timestamp is invalid") from exc
    if pd.isna(entry_timestamp) or entry_timestamp.tzinfo is None:
        raise ValueError("proxy event entry_timestamp must be timezone-aware")
    entry_timestamp = entry_timestamp.tz_convert(cfg.integration.session_timezone)
    if (
        entry_timestamp.second != 0
        or entry_timestamp.microsecond != 0
        or entry_timestamp.nanosecond != 0
    ):
        raise ValueError("proxy event entry_timestamp must be one-minute aligned")

    trade_date = _canonical_trade_date(event["trade_date"])
    if entry_timestamp.strftime("%Y-%m-%d") != trade_date:
        raise ValueError("proxy event local entry date must equal trade_date")
    window_start, window_end = _window_bounds(event, cfg)
    if not window_start <= entry_timestamp < window_end:
        raise ValueError("proxy event entry_timestamp must fall inside its execution window")

    entry = _source_price(event["entry_price_raw"], name="proxy event entry", cfg=cfg)
    stop = _source_price(event["stop_price_raw"], name="proxy event stop", cfg=cfg)
    target = _source_price(event["target_price_raw"], name="proxy event target", cfg=cfg)
    risk = entry - stop if direction > 0 else stop - entry
    if risk <= 0:
        raise ValueError("proxy event risk must be positive")
    expected_target = entry + Decimal(direction) * risk * _FROZEN_TARGET_RR
    if target != expected_target:
        raise ValueError("proxy event target is inconsistent with source-grid 2.0R")
    if direction > 0 and not stop < entry < target:
        raise ValueError("invalid raw long proxy event geometry")
    if direction < 0 and not target < entry < stop:
        raise ValueError("invalid raw short proxy event geometry")

    return ProxyEventFacts(
        instrument=instrument,
        trade_date=trade_date,
        execution_window=_strict_text(
            event["execution_window"],
            name="execution_window",
        ),
        variant=variant,
        direction=direction,
        entry_timestamp=entry_timestamp,
        window_end=window_end,
        entry=entry,
        stop=stop,
        target=target,
    )


def source_event_digest(
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> str:
    """Hash canonical raw event facts at source quote precision."""

    facts = _validate_raw_event(event, cfg)
    payload = "|".join(
        (
            stable_event_key(event),
            facts.entry_timestamp.isoformat(),
            str(facts.direction),
            str(_source_ticks(facts.entry, name="proxy event entry", cfg=cfg)),
            str(_source_ticks(facts.stop, name="proxy event stop", cfg=cfg)),
            str(_source_ticks(facts.target, name="proxy event target", cfg=cfg)),
            str(cfg.source_quote_increment),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalization_digest(
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> str:
    """Hash raw event identity plus the frozen normalization policy."""

    payload = "|".join(
        (
            source_event_digest(event, cfg),
            cfg.policy_version,
            str(cfg.source_quote_increment),
            str(cfg.execution_tick),
            cfg.integration.instrument,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_proxy_event(
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> dict[str, object]:
    """Normalize one raw synthetic proxy event to the frozen execution grid."""

    facts = _validate_raw_event(event, cfg)
    tick = cfg.execution_tick
    if facts.direction > 0:
        entry = _ceil_to_tick(facts.entry, tick)
        stop = _ceil_to_tick(facts.stop, tick)
    else:
        entry = _floor_to_tick(facts.entry, tick)
        stop = _floor_to_tick(facts.stop, tick)
    risk = entry - stop if facts.direction > 0 else stop - entry
    if risk <= tick:
        raise ValueError("normalized proxy event risk must exceed one execution tick")
    target = entry + Decimal(facts.direction) * risk * _FROZEN_TARGET_RR

    normalized = dict(event)
    normalized.pop(_PROXY_EVENT_KIND_FIELD, None)
    normalized["entry_timestamp"] = facts.entry_timestamp
    normalized["entry_price_raw"] = float(entry)
    normalized["stop_price_raw"] = float(stop)
    normalized["target_price_raw"] = float(target)
    normalized["proxy_entry_price_source"] = float(facts.entry)
    normalized["proxy_stop_price_source"] = float(facts.stop)
    normalized["proxy_target_price_source"] = float(facts.target)
    normalized["proxy_source_quote_increment"] = float(cfg.source_quote_increment)
    normalized["proxy_normalization_policy"] = cfg.policy_version
    normalized["proxy_source_event_digest"] = source_event_digest(event, cfg)
    normalized["proxy_normalization_digest"] = normalization_digest(event, cfg)
    return normalized


def mark_synthetic_proxy_minute_frame(
    frame: pd.DataFrame,
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> pd.DataFrame:
    """Return a marked copy of a synthetic raw proxy minute path bound to one event."""

    marked = frame.copy(deep=True)
    marked.attrs[_PROXY_FRAME_KIND_ATTR] = _PROXY_SOURCE_KIND
    marked.attrs[_PROXY_EVENT_KEY_ATTR] = stable_event_key(event)
    marked.attrs[_PROXY_EVENT_DIGEST_ATTR] = source_event_digest(event, cfg)
    return marked


def _canonical_timestamps(
    values: pd.Series,
    cfg: ProxyNormalizationConfig,
) -> pd.Series:
    parsed: list[pd.Timestamp] = []
    for value in values:
        try:
            timestamp = pd.Timestamp(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("proxy minute timestamp is invalid") from exc
        if pd.isna(timestamp) or timestamp.tzinfo is None:
            raise ValueError("proxy minute timestamps must be timezone-aware")
        timestamp = timestamp.tz_convert(cfg.integration.session_timezone)
        if (
            timestamp.second != 0
            or timestamp.microsecond != 0
            or timestamp.nanosecond != 0
        ):
            raise ValueError("proxy minute timestamps must be one-minute aligned")
        parsed.append(timestamp)
    return pd.Series(parsed, index=values.index)


def _validate_raw_frame(
    frame: pd.DataFrame,
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> pd.DataFrame:
    if frame.attrs.get(_PROXY_FRAME_KIND_ATTR) != _PROXY_SOURCE_KIND:
        raise ValueError("proxy minute frame is not a marked synthetic proxy fixture")
    expected_key = stable_event_key(event)
    expected_digest = source_event_digest(event, cfg)
    if frame.attrs.get(_PROXY_EVENT_KEY_ATTR) != expected_key:
        raise ValueError("proxy minute frame event key does not match raw event")
    if frame.attrs.get(_PROXY_EVENT_DIGEST_ATTR) != expected_digest:
        raise ValueError("proxy minute frame event digest does not match raw event")

    required = {*_REQUIRED_FRAME_COLUMNS, cfg.activity_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"proxy minute frame missing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("proxy minute frame is empty")

    out = frame.copy(deep=True)
    out["timestamp"] = _canonical_timestamps(out["timestamp"], cfg)
    if bool(out["timestamp"].duplicated(keep=False).any()):
        raise ValueError("proxy minute frame has duplicate timestamps")
    out = out.sort_values("timestamp").reset_index(drop=True)

    facts = _validate_raw_event(event, cfg)
    if out["timestamp"].iloc[0] < facts.entry_timestamp:
        raise ValueError("proxy minute frame contains rows before event entry")
    if out["timestamp"].iloc[-1] > facts.window_end:
        raise ValueError("proxy minute frame contains rows after execution-window end")

    source_prices: dict[str, list[Decimal]] = {}
    for column in ("open", "high", "low", "close"):
        source_prices[column] = [
            _source_price(value, name=f"proxy minute {column}", cfg=cfg)
            for value in out[column]
        ]
    for position in range(len(out)):
        open_ = source_prices["open"][position]
        high = source_prices["high"][position]
        low = source_prices["low"][position]
        close = source_prices["close"][position]
        if high < max(open_, close) or low > min(open_, close) or high < low:
            raise ValueError("proxy minute frame has invalid raw OHLC geometry")

    activity = pd.to_numeric(out[cfg.activity_column], errors="raise")
    if bool(activity.isna().any()) or not set(activity.unique()).issubset({0, 1}):
        raise ValueError("proxy minute activity values must be exactly 0 or 1")
    out[cfg.activity_column] = activity.astype(int)
    return out


def source_frame_digest(
    frame: pd.DataFrame,
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> str:
    """Hash the canonical raw proxy path without repairing gaps or activity."""

    canonical = _validate_raw_frame(frame, event, cfg)
    rows: list[str] = []
    for _, row in canonical.iterrows():
        timestamp = pd.Timestamp(row["timestamp"]).tz_convert("UTC").isoformat()
        values = [timestamp]
        for column in ("open", "high", "low", "close"):
            values.append(
                str(_source_ticks(row[column], name=f"proxy minute {column}", cfg=cfg))
            )
        values.append(str(int(row[cfg.activity_column])))
        rows.append(",".join(values))
    payload = "\n".join(rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_row(
    row: pd.Series,
    *,
    entry_timestamp: pd.Timestamp,
    direction: int,
    cfg: ProxyNormalizationConfig,
) -> tuple[Decimal, Decimal, Decimal, Decimal, bool, bool]:
    tick = cfg.execution_tick
    timestamp = pd.Timestamp(row["timestamp"])
    raw_open = _source_price(row["open"], name="proxy minute open", cfg=cfg)
    raw_high = _source_price(row["high"], name="proxy minute high", cfg=cfg)
    raw_low = _source_price(row["low"], name="proxy minute low", cfg=cfg)
    raw_close = _source_price(row["close"], name="proxy minute close", cfg=cfg)

    if direction > 0:
        open_ = (
            _ceil_to_tick(raw_open, tick)
            if timestamp == entry_timestamp
            else _floor_to_tick(raw_open, tick)
        )
        high = _floor_to_tick(raw_high, tick)
        low = _floor_to_tick(raw_low, tick)
        close = _floor_to_tick(raw_close, tick)
    else:
        open_ = (
            _floor_to_tick(raw_open, tick)
            if timestamp == entry_timestamp
            else _ceil_to_tick(raw_open, tick)
        )
        high = _ceil_to_tick(raw_high, tick)
        low = _ceil_to_tick(raw_low, tick)
        close = _ceil_to_tick(raw_close, tick)

    repaired_high = max(high, open_, close)
    repaired_low = min(low, open_, close)
    return (
        open_,
        repaired_high,
        repaired_low,
        close,
        repaired_high != high,
        repaired_low != low,
    )


def normalize_proxy_minute_frame(
    frame: pd.DataFrame,
    event: Mapping[str, object],
    cfg: ProxyNormalizationConfig,
) -> pd.DataFrame:
    """Normalize a bound raw synthetic proxy path without filling missing rows."""

    raw = _validate_raw_frame(frame, event, cfg)
    facts = _validate_raw_event(event, cfg)
    normalized_event = normalize_proxy_event(event, cfg)
    out = raw.copy(deep=True)
    for column in ("open", "high", "low", "close"):
        out[f"proxy_{column}_source"] = pd.to_numeric(out[column], errors="raise")

    normalized_rows = [
        _normalize_row(
            row,
            entry_timestamp=facts.entry_timestamp,
            direction=facts.direction,
            cfg=cfg,
        )
        for _, row in out.iterrows()
    ]
    out["open"] = [float(values[0]) for values in normalized_rows]
    out["high"] = [float(values[1]) for values in normalized_rows]
    out["low"] = [float(values[2]) for values in normalized_rows]
    out["close"] = [float(values[3]) for values in normalized_rows]
    out["proxy_high_envelope_repaired"] = [values[4] for values in normalized_rows]
    out["proxy_low_envelope_repaired"] = [values[5] for values in normalized_rows]
    out["proxy_normalization_policy"] = cfg.policy_version

    out = mark_synthetic_event_minute_frame(
        out,
        normalized_event,
        cfg.integration,
    )
    out.attrs[_PROXY_FRAME_KIND_ATTR] = _PROXY_SOURCE_KIND
    out.attrs["asia_sweep_proxy_source_event_digest"] = source_event_digest(event, cfg)
    out.attrs["asia_sweep_proxy_normalization_digest"] = normalization_digest(event, cfg)
    out.attrs["asia_sweep_proxy_source_frame_digest"] = source_frame_digest(
        frame,
        event,
        cfg,
    )
    out.attrs["asia_sweep_proxy_source_quote_increment"] = str(
        cfg.source_quote_increment
    )
    out.attrs["asia_sweep_proxy_execution_tick"] = str(cfg.execution_tick)
    out.attrs["asia_sweep_proxy_normalization_policy"] = cfg.policy_version
    return out


def normalize_proxy_fixture(
    event: Mapping[str, object],
    frame: pd.DataFrame,
    cfg: ProxyNormalizationConfig,
) -> ProxyNormalizationResult:
    """Normalize one bound synthetic proxy event/path without executing it."""

    normalized_event = normalize_proxy_event(event, cfg)
    normalized_frame = normalize_proxy_minute_frame(frame, event, cfg)
    return ProxyNormalizationResult(
        event=normalized_event,
        one_minute=normalized_frame,
        source_event_digest=source_event_digest(event, cfg),
        normalization_digest=normalization_digest(event, cfg),
        source_frame_digest=source_frame_digest(frame, event, cfg),
    )


def validate_normalized_integration_contract(
    result: ProxyNormalizationResult,
    cfg: ProxyNormalizationConfig,
) -> bool:
    """Confirm normalized outputs are bound to the frozen WP5 integration contract."""

    expected_event_digest = event_contract_digest(result.event, cfg.integration)
    return (
        stable_event_key(result.event)
        == result.one_minute.attrs.get("asia_sweep_event_key")
        and expected_event_digest
        == result.one_minute.attrs.get("asia_sweep_event_contract_digest")
        and result.source_event_digest
        == result.one_minute.attrs.get("asia_sweep_proxy_source_event_digest")
        and result.normalization_digest
        == result.one_minute.attrs.get("asia_sweep_proxy_normalization_digest")
        and result.source_frame_digest
        == result.one_minute.attrs.get("asia_sweep_proxy_source_frame_digest")
    )
