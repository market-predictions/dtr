from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

SOURCE_INCREMENT = Decimal("0.001")
EXECUTION_TICK = Decimal("0.25")
TARGET_RR = Decimal("2.0")
TARGET_NOISE_FRACTION = Decimal("0.000001")
SESSION_TIMEZONE = "America/New_York"
VARIANTS = (
    "AS_A_AGGRESSIVE_RECLAIM",
    "AS_B_WICK_QUALIFIED",
    "AS_C_DISPLACEMENT",
    "AS_D_FAILED_RETEST",
)
WINDOW_ENDS = {"LONDON": (6, 0), "NEW_YORK": (11, 30)}


@dataclass(frozen=True)
class ShadowExecutionConfig:
    instrument: str
    source_instrument: str
    point_value: float
    commission_per_side: float = 2.25
    entry_slippage_ticks: float = 1.0
    stop_slippage_ticks: float = 1.0
    market_exit_slippage_ticks: float = 1.0
    maximum_consecutive_inactive_minutes: int = 10

    def __post_init__(self) -> None:
        if self.instrument not in {"NQ_PROXY", "ES_PROXY"}:
            raise ValueError("unsupported baseline instrument")
        if not self.source_instrument:
            raise ValueError("source_instrument must be non-empty")
        positive = (self.point_value,)
        non_negative = (
            self.commission_per_side,
            self.entry_slippage_ticks,
            self.stop_slippage_ticks,
            self.market_exit_slippage_ticks,
        )
        if any(not math.isfinite(value) or value <= 0 for value in positive):
            raise ValueError("point_value must be positive and finite")
        if any(not math.isfinite(value) or value < 0 for value in non_negative):
            raise ValueError("cost values must be non-negative and finite")
        if self.maximum_consecutive_inactive_minutes < 0:
            raise ValueError("maximum inactive run must be non-negative")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decimal(value: object, *, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not number.is_finite():
        raise ValueError(f"{name} must be finite")
    return number


def _source_price(value: object, *, name: str) -> Decimal:
    price = _decimal(value, name=name)
    if price <= 0:
        raise ValueError(f"{name} must be positive")
    ticks = price / SOURCE_INCREMENT
    integral = ticks.to_integral_value()
    if ticks != integral:
        raise ValueError(f"{name} is off the source quote grid")
    return integral * SOURCE_INCREMENT


def _floor_tick(value: Decimal) -> Decimal:
    units = (value / EXECUTION_TICK).to_integral_value(rounding=ROUND_FLOOR)
    return units * EXECUTION_TICK


def _ceil_tick(value: Decimal) -> Decimal:
    units = (value / EXECUTION_TICK).to_integral_value(rounding=ROUND_CEILING)
    return units * EXECUTION_TICK


def _strict_direction(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("direction must be -1 or 1")
    numeric = float(value)
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError("direction must be -1 or 1")
    direction = int(numeric)
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    return direction


def _window_end(trade_date: object, execution_window: str) -> pd.Timestamp:
    if execution_window not in WINDOW_ENDS:
        raise ValueError(f"unknown execution window: {execution_window}")
    day = pd.Timestamp(trade_date).strftime("%Y-%m-%d")
    hour, minute = WINDOW_ENDS[execution_window]
    return pd.Timestamp(f"{day} {hour:02d}:{minute:02d}:00").tz_localize(
        SESSION_TIMEZONE,
        ambiguous="raise",
        nonexistent="raise",
    )


def normalize_event(event: pd.Series | dict[str, object]) -> dict[str, object]:
    direction = _strict_direction(event["direction"])
    entry = _source_price(event["entry_price_raw"], name="event entry")
    stop = _source_price(event["stop_price_raw"], name="event stop")
    risk = entry - stop if direction > 0 else stop - entry
    if risk <= 0:
        raise ValueError("raw event risk must be positive")
    canonical_target = entry + Decimal(direction) * risk * TARGET_RR
    reported_target = _decimal(event["target_price_raw"], name="event target")
    tolerance = SOURCE_INCREMENT * TARGET_NOISE_FRACTION
    if abs(reported_target - canonical_target) > tolerance:
        raise ValueError("event target is inconsistent with source-grid 2.0R")
    if direction > 0:
        normalized_entry = _ceil_tick(entry)
        normalized_stop = _ceil_tick(stop)
    else:
        normalized_entry = _floor_tick(entry)
        normalized_stop = _floor_tick(stop)
    normalized_risk = (
        normalized_entry - normalized_stop
        if direction > 0
        else normalized_stop - normalized_entry
    )
    if normalized_risk <= EXECUTION_TICK:
        raise ValueError("normalized event risk must exceed one execution tick")
    normalized_target = (
        normalized_entry + Decimal(direction) * normalized_risk * TARGET_RR
    )
    return {
        "direction": direction,
        "event_entry": float(normalized_entry),
        "event_stop": float(normalized_stop),
        "event_target": float(normalized_target),
        "event_risk": float(normalized_risk),
        "source_entry": float(entry),
        "source_stop": float(stop),
        "source_target": float(canonical_target),
        "source_target_reported": float(reported_target),
    }


def normalize_bar(
    row: pd.Series,
    *,
    direction: int,
    entry_minute: bool,
) -> dict[str, object]:
    raw_open = _source_price(row["open"], name="minute open")
    raw_high = _source_price(row["high"], name="minute high")
    raw_low = _source_price(row["low"], name="minute low")
    raw_close = _source_price(row["close"], name="minute close")
    if raw_high < max(raw_open, raw_close) or raw_low > min(raw_open, raw_close):
        raise ValueError("raw minute violates OHLC geometry")
    if raw_high < raw_low:
        raise ValueError("raw minute high is below low")
    if direction > 0:
        open_ = _ceil_tick(raw_open) if entry_minute else _floor_tick(raw_open)
        high = _floor_tick(raw_high)
        low = _floor_tick(raw_low)
        close = _floor_tick(raw_close)
    else:
        open_ = _floor_tick(raw_open) if entry_minute else _ceil_tick(raw_open)
        high = _ceil_tick(raw_high)
        low = _ceil_tick(raw_low)
        close = _ceil_tick(raw_close)
    repaired_high = max(high, open_, close)
    repaired_low = min(low, open_, close)
    return {
        "open": float(open_),
        "high": float(repaired_high),
        "low": float(repaired_low),
        "close": float(close),
        "is_active_quote": int(row["is_active_quote"]),
        "high_repaired": repaired_high != high,
        "low_repaired": repaired_low != low,
    }


def _adverse_price(
    price: float,
    *,
    direction: int,
    ticks: float,
    entry: bool,
) -> float:
    sign = direction if entry else -direction
    return float(price + sign * ticks * float(EXECUTION_TICK))


def _base_identity(event: pd.Series | dict[str, object]) -> dict[str, object]:
    return {
        "instrument": str(event["instrument"]),
        "trade_date": pd.Timestamp(event["trade_date"]).strftime("%Y-%m-%d"),
        "execution_window": str(event["execution_window"]),
        "variant": str(event["variant"]),
        "direction": _strict_direction(event["direction"]),
    }
