from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

import numpy as np
import pandas as pd

SESSION_TIMEZONE = "America/New_York"
DEVELOPMENT_START = pd.Timestamp("2023-01-01", tz=SESSION_TIMEZONE)
DEVELOPMENT_END = pd.Timestamp("2024-07-01", tz=SESSION_TIMEZONE)
EXECUTION_TICK = Decimal("0.25")
SOURCE_INCREMENT = Decimal("0.001")
RANGE_LOOKBACK = 60
MIN_RANGE_HISTORY = 20
RANGE_PERCENTILE_MIN = 0.20
RANGE_PERCENTILE_MAX = 0.80
CLUSTER_DISTANCE_MAX = 0.10
STOP_BUFFER_TICKS = 2
WINDOW_END_HOUR = 6
MIN_TRADES_PER_PROXY = 20

_REQUIRED = {"timestamp", "open", "high", "low", "close", "is_active_quote"}


@dataclass(frozen=True)
class ClusterExecutionConfig:
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
            raise ValueError("unsupported cluster instrument")
        if not self.source_instrument:
            raise ValueError("source_instrument must be non-empty")
        for value in (self.point_value,):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("point_value must be positive and finite")
        for value in (
            self.commission_per_side,
            self.entry_slippage_ticks,
            self.stop_slippage_ticks,
            self.market_exit_slippage_ticks,
        ):
            if not math.isfinite(value) or value < 0:
                raise ValueError("cost values must be non-negative and finite")


@dataclass
class ClusterFunnel:
    business_days: int = 0
    complete_asia_ranges: int = 0
    range_history_ready: int = 0
    moderate_range: int = 0
    pdh_pdl_cluster: int = 0
    full_cluster_sweep: int = 0
    cluster_reclaim: int = 0
    rejection_hold: int = 0
    opposite_side_clear: int = 0
    impulse_break: int = 0
    midpoint_ahead: int = 0
    signals: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def _local(day: pd.Timestamp, hour: int, minute: int = 0) -> pd.Timestamp:
    day = pd.Timestamp(day)
    return pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=hour,
        minute=minute,
    ).tz_localize(SESSION_TIMEZONE, ambiguous="raise", nonexistent="raise")


def _validate_minutes(frame: pd.DataFrame) -> pd.DataFrame:
    missing = _REQUIRED.difference(frame.columns)
    if missing:
        raise ValueError(f"minute frame missing columns: {sorted(missing)}")
    out = frame.copy(deep=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="raise")
    if out.empty or out["timestamp"].dt.tz is None:
        raise ValueError("minute timestamps must be non-empty and timezone-aware")
    out["timestamp"] = out["timestamp"].dt.tz_convert(SESSION_TIMEZONE)
    if bool(out["timestamp"].duplicated(keep=False).any()):
        raise ValueError("duplicate minute timestamps")
    off_grid = (
        (out["timestamp"].dt.second != 0)
        | (out["timestamp"].dt.microsecond != 0)
        | (out["timestamp"].dt.nanosecond != 0)
    )
    if bool(off_grid.any()):
        raise ValueError("off-grid minute timestamps")
    for column in ("open", "high", "low", "close", "is_active_quote"):
        out[column] = pd.to_numeric(out[column], errors="raise")
        if not bool(np.isfinite(out[column].to_numpy(dtype=float)).all()):
            raise ValueError(f"non-finite {column}")
    invalid = (
        (out["high"] < out[["open", "close"]].max(axis=1))
        | (out["low"] > out[["open", "close"]].min(axis=1))
        | (out["high"] < out["low"])
    )
    if bool(invalid.any()):
        raise ValueError("invalid minute OHLC geometry")
    activity = set(out["is_active_quote"].astype(int).unique())
    if not activity.issubset({0, 1}):
        raise ValueError("activity must be binary")
    out["is_active_quote"] = out["is_active_quote"].astype(int)
    return out.sort_values("timestamp").reset_index(drop=True)


def _resample_five(minutes: pd.DataFrame) -> pd.DataFrame:
    x = minutes.set_index("timestamp")
    out = (
        x.resample("5min", label="left", closed="left")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            active=("is_active_quote", "max"),
            source_bars=("close", "count"),
        )
        .dropna(subset=["open", "high", "low", "close"])
    )
    out["bar_end"] = out.index + pd.Timedelta(minutes=5)
    return out


def _slice(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return frame.loc[(frame.index >= start) & (frame.index < end)]


def _prior_day_levels(minutes: pd.DataFrame, day: pd.Timestamp) -> tuple[float, float]:
    for distance in range(1, 9):
        candidate = pd.Timestamp(day) - pd.DateOffset(days=distance)
        start = _local(candidate, 0)
        end = start + pd.DateOffset(days=1)
        prior = _slice(minutes, start, end)
        prior = prior[prior["is_active_quote"] > 0]
        if not prior.empty:
            return float(prior["high"].max()), float(prior["low"].min())
    return math.nan, math.nan


def causal_range_percentile(value: float, history: list[float]) -> float:
    sample = np.asarray(history[-RANGE_LOOKBACK:], dtype=float)
    sample = sample[np.isfinite(sample)]
    if len(sample) < MIN_RANGE_HISTORY:
        return math.nan
    below = float((sample < value).sum())
    equal = float((sample == value).sum())
    return (below + 0.5 * equal) / len(sample)


def cluster_is_near(reference_level: float, prior_level: float, width: float) -> bool:
    return (
        np.isfinite(reference_level)
        and np.isfinite(prior_level)
        and np.isfinite(width)
        and width > 0
        and abs(reference_level - prior_level) / width <= CLUSTER_DISTANCE_MAX
    )


def _event_id(instrument: str, day: pd.Timestamp) -> str:
    raw = f"{instrument}|{pd.Timestamp(day).strftime('%Y-%m-%d')}|LONDON|PDH_PDL_CLUSTER_V1"
    return hashlib.sha256(raw.encode()).hexdigest()


def classify_cluster_window(
    window: pd.DataFrame,
    *,
    reference_high: float,
    reference_low: float,
    prior_day_high: float,
    prior_day_low: float,
) -> dict[str, Any]:
    """Return the one frozen cluster setup for a completed London window."""

    blank: dict[str, Any] = {"status": "NO_SIGNAL", "reason": "NO_FULL_CLUSTER_SWEEP"}
    if window.empty:
        return {**blank, "reason": "EMPTY_WINDOW"}
    bars = window.reset_index(drop=False)
    width = reference_high - reference_low
    high_near = cluster_is_near(reference_high, prior_day_high, width)
    low_near = cluster_is_near(reference_low, prior_day_low, width)
    if not high_near and not low_near:
        return {**blank, "reason": "NO_PDH_PDL_CLUSTER"}

    high_outer = max(reference_high, prior_day_high) if high_near else math.nan
    high_inner = min(reference_high, prior_day_high) if high_near else math.nan
    low_outer = min(reference_low, prior_day_low) if low_near else math.nan
    low_inner = max(reference_low, prior_day_low) if low_near else math.nan

    first_index: int | None = None
    side: str | None = None
    for index, row in bars.iterrows():
        up = high_near and float(row["high"]) > high_outer
        down = low_near and float(row["low"]) < low_outer
        if not up and not down:
            continue
        if up and down:
            return {**blank, "reason": "DOUBLE_CLUSTER_SWEEP"}
        first_index = int(index)
        side = "UP" if up else "DOWN"
        break
    if first_index is None or side is None:
        return blank

    reclaim_end = min(first_index + 2, len(bars) - 1)
    reclaim_index: int | None = None
    for index in range(first_index, reclaim_end + 1):
        close = float(bars.iloc[index]["close"])
        reclaimed = close < high_inner if side == "UP" else close > low_inner
        if reclaimed:
            reclaim_index = index
            break
    if reclaim_index is None:
        return {
            **blank,
            "reason": "NO_CLUSTER_RECLAIM",
            "first_index": first_index,
            "side": side,
        }
    confirmation_index = reclaim_index + 2
    if confirmation_index >= len(bars):
        return {**blank, "reason": "INCOMPLETE_REJECTION_HOLD", "side": side}
    hold = bars.iloc[reclaim_index + 1 : confirmation_index + 1]
    if side == "UP":
        hold_ok = bool((hold["close"] < high_inner).all())
    else:
        hold_ok = bool((hold["close"] > low_inner).all())
    if not hold_ok:
        return {**blank, "reason": "REJECTION_HOLD_FAILED", "side": side}

    confirm_path = bars.iloc[first_index : confirmation_index + 1]
    opposite = (
        bool((confirm_path["low"] < reference_low).any())
        if side == "UP"
        else bool((confirm_path["high"] > reference_high).any())
    )
    if opposite:
        return {**blank, "reason": "OPPOSITE_ASIA_SIDE_BREACHED", "side": side}

    rejection = bars.iloc[reclaim_index : confirmation_index + 1]
    direction = -1 if side == "UP" else 1
    impulse_level = (
        float(rejection["low"].min()) if direction < 0 else float(rejection["high"].max())
    )
    sweep_extreme = (
        float(confirm_path["high"].max()) if side == "UP" else float(confirm_path["low"].min())
    )
    entry_index: int | None = None
    for index in range(confirmation_index + 1, len(bars)):
        row = bars.iloc[index]
        broken = (
            float(row["close"]) < impulse_level
            if direction < 0
            else float(row["close"]) > impulse_level
        )
        if broken and pd.Timestamp(row["bar_end"]) < pd.Timestamp(window.index.max()) + pd.Timedelta(minutes=5):
            entry_index = index
            break
    if entry_index is None:
        return {**blank, "reason": "NO_IMPULSE_BREAK", "side": side}

    entry_time = pd.Timestamp(bars.iloc[entry_index]["bar_end"])
    midpoint = (reference_high + reference_low) / 2.0
    return {
        "status": "SIGNAL",
        "reason": "QUALIFIED_CLUSTER_REJECTION",
        "side": side,
        "direction": direction,
        "first_index": first_index,
        "reclaim_index": reclaim_index,
        "confirmation_index": confirmation_index,
        "entry_break_index": entry_index,
        "sweep_timestamp": pd.Timestamp(bars.iloc[first_index]["bar_end"]),
        "confirmation_timestamp": pd.Timestamp(bars.iloc[confirmation_index]["bar_end"]),
        "entry_timestamp": entry_time,
        "impulse_level": impulse_level,
        "sweep_extreme": sweep_extreme,
        "midpoint": midpoint,
        "cluster_inner": high_inner if side == "UP" else low_inner,
        "cluster_outer": high_outer if side == "UP" else low_outer,
        "cluster_distance_fraction": (
            abs(reference_high - prior_day_high) / width
            if side == "UP"
            else abs(reference_low - prior_day_low) / width
        ),
    }


def build_cluster_signal_ledger(
    instrument: str,
    one_minute: pd.DataFrame,
    *,
    development_start: pd.Timestamp = DEVELOPMENT_START,
    development_end: pd.Timestamp = DEVELOPMENT_END,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    if instrument not in {"NQ_PROXY", "ES_PROXY"}:
        raise ValueError("unsupported instrument")
    minutes = _validate_minutes(one_minute).set_index("timestamp")
    five = _resample_five(minutes.reset_index())
    history: list[float] = []
    funnel = ClusterFunnel()
    signals: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    first_day = max(
        minutes.index.min().normalize() + pd.DateOffset(days=1),
        development_start - pd.DateOffset(days=100),
    )
    last_day = min(minutes.index.max().normalize(), development_end)
    for day in pd.date_range(first_day, last_day, freq="B"):
        funnel.business_days += int(day >= development_start and day < development_end)
        asia_start = _local(day - pd.DateOffset(days=1), 18)
        asia_end = _local(day, 2)
        window_start = asia_end
        window_end = _local(day, WINDOW_END_HOUR)
        asia = _slice(minutes, asia_start, asia_end)
        asia = asia[asia["is_active_quote"] > 0]
        if asia.empty:
            continue
        high = float(asia["high"].max())
        low = float(asia["low"].min())
        width = high - low
        if not np.isfinite(width) or width <= 0:
            continue
        if day >= development_start and day < development_end:
            funnel.complete_asia_ranges += 1
        percentile = causal_range_percentile(width, history)
        history.append(width)
        if day < development_start or day >= development_end:
            continue
        record: dict[str, Any] = {
            "event_id": _event_id(instrument, day),
            "instrument": instrument,
            "trade_date": day.strftime("%Y-%m-%d"),
            "reference_high": high,
            "reference_low": low,
            "reference_range": width,
            "range_percentile_60": percentile,
            "range_gate_min": RANGE_PERCENTILE_MIN,
            "range_gate_max": RANGE_PERCENTILE_MAX,
            "cluster_distance_max": CLUSTER_DISTANCE_MAX,
        }
        if not np.isfinite(percentile):
            audit.append({**record, "status": "INELIGIBLE", "reason": "RANGE_WARMUP"})
            continue
        funnel.range_history_ready += 1
        if not RANGE_PERCENTILE_MIN <= percentile <= RANGE_PERCENTILE_MAX:
            audit.append({**record, "status": "INELIGIBLE", "reason": "ASIA_RANGE_EXTREME"})
            continue
        funnel.moderate_range += 1
        pdh, pdl = _prior_day_levels(minutes, day)
        record.update({"prior_day_high": pdh, "prior_day_low": pdl})
        high_near = cluster_is_near(high, pdh, width)
        low_near = cluster_is_near(low, pdl, width)
        if not high_near and not low_near:
            audit.append({**record, "status": "INELIGIBLE", "reason": "NO_PDH_PDL_CLUSTER"})
            continue
        funnel.pdh_pdl_cluster += 1
        window = _slice(five, window_start, window_end)
        outcome = classify_cluster_window(
            window,
            reference_high=high,
            reference_low=low,
            prior_day_high=pdh,
            prior_day_low=pdl,
        )
        reason = str(outcome["reason"])
        if reason != "NO_FULL_CLUSTER_SWEEP":
            funnel.full_cluster_sweep += 1
        if reason not in {"NO_FULL_CLUSTER_SWEEP", "DOUBLE_CLUSTER_SWEEP", "NO_CLUSTER_RECLAIM"}:
            funnel.cluster_reclaim += 1
        if reason not in {
            "NO_FULL_CLUSTER_SWEEP",
            "DOUBLE_CLUSTER_SWEEP",
            "NO_CLUSTER_RECLAIM",
            "INCOMPLETE_REJECTION_HOLD",
            "REJECTION_HOLD_FAILED",
        }:
            funnel.rejection_hold += 1
        if reason in {"NO_IMPULSE_BREAK", "QUALIFIED_CLUSTER_REJECTION"}:
            funnel.opposite_side_clear += 1
        if reason == "QUALIFIED_CLUSTER_REJECTION":
            funnel.impulse_break += 1
            entry_time = pd.Timestamp(outcome["entry_timestamp"])
            entry_rows = minutes.loc[minutes.index == entry_time]
            if entry_rows.empty or int(entry_rows.iloc[0]["is_active_quote"]) <= 0:
                outcome = {**outcome, "status": "NO_SIGNAL", "reason": "MISSING_OR_INACTIVE_ENTRY"}
            else:
                entry_raw = float(entry_rows.iloc[0]["open"])
                direction = int(outcome["direction"])
                midpoint = float(outcome["midpoint"])
                target_ahead = midpoint > entry_raw if direction > 0 else midpoint < entry_raw
                if not target_ahead:
                    outcome = {**outcome, "status": "NO_SIGNAL", "reason": "MIDPOINT_NOT_AHEAD"}
                else:
                    funnel.midpoint_ahead += 1
                    stop_raw = float(outcome["sweep_extreme"]) - direction * (
                        STOP_BUFFER_TICKS * float(EXECUTION_TICK)
                    )
                    signal = {
                        **record,
                        **outcome,
                        "execution_window": "LONDON",
                        "variant": "AS_E_PDH_PDL_CLUSTER_MODERATE_RANGE",
                        "entry_price_raw": entry_raw,
                        "stop_price_raw": stop_raw,
                        "target_price_raw": midpoint,
                        "window_end": window_end.isoformat(),
                    }
                    signals.append(signal)
                    funnel.signals += 1
        audit.append({**record, **outcome})
    return pd.DataFrame(signals), pd.DataFrame(audit), funnel.as_dict()


def _dec(value: float) -> Decimal:
    return Decimal(str(value))


def _floor(value: float) -> float:
    d = _dec(value)
    return float((d / EXECUTION_TICK).to_integral_value(rounding=ROUND_FLOOR) * EXECUTION_TICK)


def _ceil(value: float) -> float:
    d = _dec(value)
    return float((d / EXECUTION_TICK).to_integral_value(rounding=ROUND_CEILING) * EXECUTION_TICK)


def _adverse(price: float, direction: int, ticks: float, *, entry: bool) -> float:
    sign = direction if entry else -direction
    return float(price + sign * ticks * float(EXECUTION_TICK))


def _normalize_bar(row: pd.Series, direction: int, entry_minute: bool) -> dict[str, float | int]:
    if direction > 0:
        open_ = _ceil(float(row["open"])) if entry_minute else _floor(float(row["open"]))
        high = _floor(float(row["high"]))
        low = _floor(float(row["low"]))
        close = _floor(float(row["close"]))
    else:
        open_ = _floor(float(row["open"])) if entry_minute else _ceil(float(row["open"]))
        high = _ceil(float(row["high"]))
        low = _ceil(float(row["low"]))
        close = _ceil(float(row["close"]))
    return {
        "open": open_,
        "high": max(high, open_, close),
        "low": min(low, open_, close),
        "close": close,
        "is_active_quote": int(row["is_active_quote"]),
    }


def simulate_cluster_signal(
    event: pd.Series | dict[str, Any],
    source: pd.DataFrame,
    cfg: ClusterExecutionConfig,
) -> dict[str, Any]:
    if str(event["instrument"]) != cfg.instrument:
        raise ValueError("event/config instrument mismatch")
    direction = int(event["direction"])
    if direction not in {-1, 1}:
        raise ValueError("direction must be -1 or 1")
    entry_time = pd.Timestamp(event["entry_timestamp"])
    if entry_time.tzinfo is None:
        raise ValueError("entry timestamp must be timezone-aware")
    entry_time = entry_time.tz_convert(SESSION_TIMEZONE)
    window_end = pd.Timestamp(event["window_end"])
    if window_end.tzinfo is None:
        window_end = window_end.tz_localize(SESSION_TIMEZONE)
    else:
        window_end = window_end.tz_convert(SESSION_TIMEZONE)
    base = {
        key: event[key]
        for key in (
            "event_id",
            "instrument",
            "trade_date",
            "execution_window",
            "variant",
            "direction",
            "range_percentile_60",
            "cluster_distance_fraction",
            "reference_high",
            "reference_low",
            "reference_range",
            "prior_day_high",
            "prior_day_low",
            "sweep_timestamp",
            "confirmation_timestamp",
        )
    }
    rows = source.copy()
    rows["timestamp"] = pd.to_datetime(rows["timestamp"], errors="raise")
    rows["timestamp"] = rows["timestamp"].dt.tz_convert(SESSION_TIMEZONE)
    path = rows[(rows["timestamp"] >= entry_time) & (rows["timestamp"] <= window_end)]
    bars = {
        pd.Timestamp(row["timestamp"]): _normalize_bar(
            row, direction, pd.Timestamp(row["timestamp"]) == entry_time
        )
        for _, row in path.iterrows()
    }
    entry_bar = bars.get(entry_time)
    if entry_bar is None or int(entry_bar["is_active_quote"]) <= 0:
        return {**base, "status": "BLOCKED", "reason": "MISSING_OR_INACTIVE_ENTRY"}
    entry_raw = float(entry_bar["open"])
    entry_price = _adverse(entry_raw, direction, cfg.entry_slippage_ticks, entry=True)
    stop_price = _ceil(float(event["stop_price_raw"])) if direction > 0 else _floor(float(event["stop_price_raw"]))
    target_price = _floor(float(event["target_price_raw"])) if direction > 0 else _ceil(float(event["target_price_raw"]))
    raw_through_stop = entry_raw <= stop_price if direction > 0 else entry_raw >= stop_price
    risk = entry_price - stop_price if direction > 0 else stop_price - entry_price
    target_distance = target_price - entry_price if direction > 0 else entry_price - target_price
    if raw_through_stop or risk <= float(EXECUTION_TICK):
        return {**base, "status": "BLOCKED", "reason": "ENTRY_GAP_OR_RISK_TOO_SMALL"}
    if target_distance <= 0:
        return {**base, "status": "BLOCKED", "reason": "MIDPOINT_NOT_AHEAD_AFTER_NORMALIZATION"}

    mfe = 0.0
    mae = 0.0

    def finish(reason: str, exit_time: pd.Timestamp, exit_raw: float, exit_price: float, collision: bool = False, gap_minutes: int = 0) -> dict[str, Any]:
        gross_points = direction * (exit_price - entry_price)
        gross_r = gross_points / risk
        commission_dollars = 2.0 * cfg.commission_per_side
        commission_r = commission_dollars / (risk * cfg.point_value)
        return {
            **base,
            "status": "EXITED",
            "reason": reason,
            "entry_timestamp": entry_time.isoformat(),
            "entry_price_raw": entry_raw,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "initial_risk_points": risk,
            "planned_reward_r": target_distance / risk,
            "exit_timestamp": exit_time.isoformat(),
            "exit_price_raw": exit_raw,
            "exit_price": exit_price,
            "gross_points": gross_points,
            "gross_r": gross_r,
            "commission_dollars": commission_dollars,
            "commission_r": commission_r,
            "net_r": gross_r - commission_r,
            "mfe_r": mfe / risk,
            "mae_r": mae / risk,
            "holding_minutes": int((exit_time - entry_time).total_seconds() // 60),
            "collision": collision,
            "gap_minutes": gap_minutes,
        }

    expected = pd.date_range(entry_time, window_end, freq="1min", inclusive="left")
    inactive = 0
    stale = False
    for timestamp in expected:
        bar = bars.get(pd.Timestamp(timestamp))
        if bar is None:
            future = [
                (time, candidate)
                for time, candidate in bars.items()
                if time > timestamp and time <= window_end and int(candidate["is_active_quote"]) > 0
            ]
            if not future:
                return {**base, "status": "UNRESOLVED", "reason": "UNRESOLVED_DATA_EXIT"}
            next_time, next_bar = min(future, key=lambda item: item[0])
            exit_price = _adverse(float(next_bar["open"]), direction, cfg.market_exit_slippage_ticks, entry=False)
            return finish(
                "STALE_ACTIVITY_LIQUIDATION" if stale else "DATA_GAP_LIQUIDATION",
                next_time,
                float(next_bar["open"]),
                exit_price,
                gap_minutes=int((next_time - timestamp).total_seconds() // 60) + inactive,
            )
        if int(bar["is_active_quote"]) <= 0:
            inactive += 1
            stale = inactive > cfg.maximum_consecutive_inactive_minutes
            continue
        if stale:
            exit_price = _adverse(float(bar["open"]), direction, cfg.market_exit_slippage_ticks, entry=False)
            return finish("STALE_ACTIVITY_LIQUIDATION", pd.Timestamp(timestamp), float(bar["open"]), exit_price, gap_minutes=inactive)
        inactive = 0
        open_, high, low = float(bar["open"]), float(bar["high"]), float(bar["low"])
        if direction > 0:
            mfe = max(mfe, high - entry_price)
            mae = max(mae, entry_price - low)
            stop_gap, target_gap = open_ <= stop_price, open_ >= target_price
            stop_hit, target_hit = low <= stop_price, high >= target_price
        else:
            mfe = max(mfe, entry_price - low)
            mae = max(mae, high - entry_price)
            stop_gap, target_gap = open_ >= stop_price, open_ <= target_price
            stop_hit, target_hit = high >= stop_price, low <= target_price
        if timestamp != entry_time and stop_gap:
            exit_price = _adverse(open_, direction, cfg.stop_slippage_ticks, entry=False)
            return finish("STOP_GAP", pd.Timestamp(timestamp), open_, exit_price)
        if timestamp != entry_time and target_gap:
            return finish("TARGET_GAP", pd.Timestamp(timestamp), target_price, target_price)
        if stop_hit:
            exit_price = _adverse(stop_price, direction, cfg.stop_slippage_ticks, entry=False)
            return finish("STOP", pd.Timestamp(timestamp), stop_price, exit_price, collision=bool(target_hit))
        if target_hit:
            return finish("TARGET", pd.Timestamp(timestamp), target_price, target_price)

    time_bar = bars.get(window_end)
    if time_bar is None or int(time_bar["is_active_quote"]) <= 0:
        return {**base, "status": "UNRESOLVED", "reason": "UNRESOLVED_TIME_EXIT"}
    raw = float(time_bar["open"])
    exit_price = _adverse(raw, direction, cfg.market_exit_slippage_ticks, entry=False)
    return finish("TIME_EXIT", window_end, raw, exit_price)


def summarize_cluster_results(ledger: pd.DataFrame) -> dict[str, Any]:
    if ledger.empty:
        return {
            "decision": "STOP_FINAL_CLUSTER_CHALLENGER",
            "classification": "NO_TRADES",
            "instruments": {},
            "pooled": {},
        }
    exited = ledger[ledger["status"] == "EXITED"].copy()
    exited["trade_date"] = pd.to_datetime(exited["trade_date"])

    def metrics(frame: pd.DataFrame) -> dict[str, Any]:
        if frame.empty:
            return {"trades": 0}
        wins = frame.loc[frame["net_r"] > 0, "net_r"].sum()
        losses = -frame.loc[frame["net_r"] < 0, "net_r"].sum()
        equity = frame.sort_values(["trade_date", "entry_timestamp"])["net_r"].cumsum()
        equity_with_origin = pd.concat([pd.Series([0.0]), equity.reset_index(drop=True)], ignore_index=True)
        drawdown = equity_with_origin.cummax() - equity_with_origin
        return {
            "trades": int(len(frame)),
            "net_r": float(frame["net_r"].sum()),
            "expectancy_r": float(frame["net_r"].mean()),
            "gross_expectancy_r": float(frame["gross_r"].mean()),
            "profit_factor": float(wins / losses) if losses > 0 else math.inf,
            "win_rate": float((frame["net_r"] > 0).mean()),
            "max_drawdown_r": float(drawdown.max()),
            "mean_planned_reward_r": float(frame["planned_reward_r"].mean()),
            "target_rate": float(frame["reason"].isin(["TARGET", "TARGET_GAP"]).mean()),
            "time_exit_rate": float((frame["reason"] == "TIME_EXIT").mean()),
        }

    instruments = {
        name: metrics(exited[exited["instrument"] == name])
        for name in ("NQ_PROXY", "ES_PROXY")
    }
    pooled = metrics(exited)
    periods = {
        "2023": metrics(exited[exited["trade_date"] < pd.Timestamp("2024-01-01")]),
        "2024_H1": metrics(exited[exited["trade_date"] >= pd.Timestamp("2024-01-01")]),
    }
    blockers: list[str] = []
    for name, values in instruments.items():
        if values.get("trades", 0) < MIN_TRADES_PER_PROXY:
            blockers.append(f"{name}_INSUFFICIENT_SAMPLE")
        if values.get("expectancy_r", -math.inf) <= 0:
            blockers.append(f"{name}_NONPOSITIVE_EXPECTANCY")
    if pooled.get("expectancy_r", -math.inf) < 0.05:
        blockers.append("POOLED_EXPECTANCY_BELOW_0_05R")
    if pooled.get("profit_factor", 0.0) < 1.10:
        blockers.append("POOLED_PROFIT_FACTOR_BELOW_1_10")
    for period, values in periods.items():
        if values.get("trades", 0) == 0 or values.get("expectancy_r", -math.inf) <= 0:
            blockers.append(f"{period}_NONPOSITIVE_OR_EMPTY")
    pass_gate = not blockers
    return {
        "decision": "PROMOTE_ONE_FROZEN_CLUSTER_CHALLENGER" if pass_gate else "STOP_FINAL_CLUSTER_CHALLENGER",
        "classification": "PROMISING_DEVELOPMENT_ONLY" if pass_gate else "NOT_PROMOTABLE",
        "promotion_blockers": blockers,
        "instruments": instruments,
        "pooled": pooled,
        "periods": periods,
        "blocked": int((ledger["status"] == "BLOCKED").sum()),
        "unresolved": int((ledger["status"] == "UNRESOLVED").sum()),
        "validation_partition_opened": False,
    }
