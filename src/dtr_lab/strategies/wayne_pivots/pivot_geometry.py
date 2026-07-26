from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

NEW_YORK_TZ = "America/New_York"
MIN_ACTIVE_MINUTES = 1200
PRIMARY_PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDCAD", "USDCHF", "USDJPY")
TARGETS = {
    "BULL": ("M4", "R1", "R2"),
    "BEAR": ("M1", "S1", "S2"),
}
PLACEBO_WEIGHTS = {
    "SYNTH_1": (0.02493530, 0.46716300, 0.50790170),
    "SYNTH_2": (0.50115999, 0.08985396, 0.40898605),
    "SYNTH_3": (0.20219939, 0.21936514, 0.57843547),
    "SYNTH_4": (0.58049413, 0.36543086, 0.05407500),
}
STRUCTURES = (
    "WAYNE",
    "PRIOR_CLOSE",
    "RANGE_MID",
    "Q25",
    "Q75",
    "SHIFT_DOWN_025",
    "SHIFT_UP_025",
    "SYNTH_1",
    "SYNTH_2",
    "SYNTH_3",
    "SYNTH_4",
)


def _source_file(directory: Path, symbol: str, side: str, year: int) -> Path:
    return directory / f"{symbol.lower()}_m1_{side}_{year}.csv.gz"


def _load_side(path: Path, side: str) -> pd.DataFrame:
    required = {"timestamp_utc", "open", "high", "low", "close", "is_active_quote"}
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path, compression="gzip")
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    frame = frame.loc[:, sorted(required)].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError(f"{path.name}: duplicate timestamps")
    for column in required - {"timestamp_utc"}:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame.rename(
        columns={
            column: f"{column}_{side}"
            for column in required
            if column != "timestamp_utc"
        }
    )


def load_bid_ask_minutes(
    directory: Path,
    symbol: str,
    *,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    symbol = symbol.upper()
    frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        bid = _load_side(_source_file(directory, symbol, "bid", year), "bid")
        ask = _load_side(_source_file(directory, symbol, "ask", year), "ask")
        merged = bid.merge(ask, on="timestamp_utc", how="inner", validate="one_to_one")
        merged["active"] = (
            merged["is_active_quote_bid"].eq(1)
            & merged["is_active_quote_ask"].eq(1)
        )
        frames.append(merged)
    result = pd.concat(frames, ignore_index=True).sort_values("timestamp_utc")
    if result["timestamp_utc"].duplicated().any():
        raise ValueError(f"{symbol}: duplicate timestamps across annual partitions")
    return result.set_index("timestamp_utc")


def midpoint_minutes(quotes: pd.DataFrame) -> pd.DataFrame:
    required = {
        "open_bid",
        "high_bid",
        "low_bid",
        "close_bid",
        "open_ask",
        "high_ask",
        "low_ask",
        "close_ask",
        "active",
    }
    missing = sorted(required - set(quotes.columns))
    if missing:
        raise ValueError(f"quote frame missing columns: {missing}")
    out = pd.DataFrame(index=pd.DatetimeIndex(quotes.index))
    for column in ("open", "high", "low", "close"):
        out[column] = 0.5 * (
            quotes[f"{column}_bid"].astype(float)
            + quotes[f"{column}_ask"].astype(float)
        )
    out["active"] = quotes["active"].astype(bool)
    return out.sort_index()


def pivot_day_start(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    if index.tz is None:
        raise ValueError("pivot-day assignment requires timezone-aware timestamps")
    local = index.tz_convert(NEW_YORK_TZ)
    boundary = local.normalize() + pd.Timedelta(hours=17)
    boundary = boundary.where(local >= boundary, boundary - pd.Timedelta(days=1))
    return boundary.tz_convert("UTC")


def build_pivot_days(minutes: pd.DataFrame) -> pd.DataFrame:
    active = minutes.loc[minutes["active"]].copy()
    active["pivot_day_start"] = pivot_day_start(pd.DatetimeIndex(active.index))
    daily = active.groupby("pivot_day_start", sort=True).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        active_minutes=("close", "size"),
    )
    daily["valid_day"] = (
        daily["active_minutes"].ge(MIN_ACTIVE_MINUTES)
        & np.isfinite(daily[["high", "low", "close"]]).all(axis=1)
        & daily["high"].gt(daily["low"])
    )
    valid = daily.loc[daily["valid_day"]].copy()
    valid["prior_high"] = valid["high"].shift(1)
    valid["prior_low"] = valid["low"].shift(1)
    valid["prior_close"] = valid["close"].shift(1)
    valid["prior_range"] = valid["prior_high"] - valid["prior_low"]
    valid["source_year"] = valid.index.tz_convert(NEW_YORK_TZ).year
    return valid


def traditional_structure(high: float, low: float, close: float) -> dict[str, float]:
    if not all(np.isfinite(value) for value in (high, low, close)) or high <= low:
        raise ValueError("invalid prior-period OHLC")
    pivot = (high + low + close) / 3.0
    r1 = 2.0 * pivot - low
    s1 = 2.0 * pivot - high
    width = high - low
    r2 = pivot + width
    s2 = pivot - width
    return {
        "P": pivot,
        "R1": r1,
        "S1": s1,
        "R2": r2,
        "S2": s2,
        "M1": 0.5 * (s2 + s1),
        "M2": 0.5 * (s1 + pivot),
        "M3": 0.5 * (pivot + r1),
        "M4": 0.5 * (r1 + r2),
    }


def _translated(structure: dict[str, float], anchor: float) -> dict[str, float]:
    delta = float(anchor) - structure["P"]
    return {name: value + delta for name, value in structure.items()}


def build_structures(high: float, low: float, close: float) -> dict[str, dict[str, float]]:
    wayne = traditional_structure(high, low, close)
    width = high - low
    anchors = {
        "WAYNE": wayne["P"],
        "PRIOR_CLOSE": close,
        "RANGE_MID": 0.5 * (high + low),
        "Q25": low + 0.25 * width,
        "Q75": low + 0.75 * width,
        "SHIFT_DOWN_025": wayne["P"] - 0.25 * width,
        "SHIFT_UP_025": wayne["P"] + 0.25 * width,
    }
    for name, (weight_high, weight_low, weight_close) in PLACEBO_WEIGHTS.items():
        anchors[name] = (
            weight_high * high + weight_low * low + weight_close * close
        )
    return {name: _translated(wayne, anchors[name]) for name in STRUCTURES}


def _first_true(mask: np.ndarray) -> int | None:
    indices = np.flatnonzero(mask)
    return None if len(indices) == 0 else int(indices[0])


def _first_passage(
    highs: np.ndarray,
    lows: np.ndarray,
    *,
    start_index: int,
    side: str,
    target: float,
    stop: float,
) -> tuple[bool, str, int | None, int | None]:
    path_high = highs[start_index:]
    path_low = lows[start_index:]
    if side == "BULL":
        target_offset = _first_true(path_high >= target)
        stop_offset = _first_true(path_low <= stop)
    elif side == "BEAR":
        target_offset = _first_true(path_low <= target)
        stop_offset = _first_true(path_high >= stop)
    else:
        raise ValueError(f"unsupported side: {side}")
    target_index = None if target_offset is None else start_index + target_offset
    stop_index = None if stop_offset is None else start_index + stop_offset
    if target_index is None and stop_index is None:
        return False, "CENSORED", target_index, stop_index
    if stop_index is not None and (target_index is None or stop_index <= target_index):
        state = "AMBIGUOUS_STOP_FIRST" if target_index == stop_index else "STOP_FIRST"
        return False, state, target_index, stop_index
    return True, "TARGET_FIRST", target_index, stop_index


def _fresh_zone_index(
    highs: np.ndarray,
    lows: np.ndarray,
    *,
    zone_low: float,
    zone_high: float,
    side: str,
    conservative_target: float,
    stop: float,
) -> tuple[int | None, str]:
    touch_index = _first_true((highs >= zone_low) & (lows <= zone_high))
    if touch_index is None:
        return None, "NO_TOUCH"
    prior_high = highs[:touch_index]
    prior_low = lows[:touch_index]
    if side == "BULL":
        target_consumed = bool(np.any(prior_high >= conservative_target))
        stop_consumed = bool(np.any(prior_low <= stop))
    else:
        target_consumed = bool(np.any(prior_low <= conservative_target))
        stop_consumed = bool(np.any(prior_high >= stop))
    if target_consumed or stop_consumed:
        if target_consumed and stop_consumed:
            return touch_index, "BOTH_CONSUMED"
        return touch_index, "TARGET_CONSUMED" if target_consumed else "STOP_CONSUMED"
    return touch_index, "FRESH"


def _pivot_slope_state(current: float, previous: float, prior_range: float) -> str:
    if not all(np.isfinite(value) for value in (current, previous, prior_range)):
        return "WARMUP"
    tolerance = 0.01 * prior_range
    difference = current - previous
    if difference > tolerance:
        return "BULL"
    if difference < -tolerance:
        return "BEAR"
    return "FLAT"


def build_anatomy_ledger(
    quotes: pd.DataFrame,
    *,
    symbol: str,
    start_year: int,
    end_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    symbol = symbol.upper()
    minutes = midpoint_minutes(quotes)
    minutes = minutes.copy()
    minutes["pivot_day_start"] = pivot_day_start(pd.DatetimeIndex(minutes.index))
    days = build_pivot_days(minutes)
    rows: list[dict[str, Any]] = []
    day_rows: list[dict[str, Any]] = []
    previous_p = math.nan
    for day in days.itertuples():
        day_start = pd.Timestamp(day.Index)
        local_year = int(day_start.tz_convert(NEW_YORK_TZ).year)
        if local_year < start_year or local_year > end_year:
            continue
        if not all(
            np.isfinite(value)
            for value in (day.prior_high, day.prior_low, day.prior_close, day.prior_range)
        ):
            continue
        structures = build_structures(day.prior_high, day.prior_low, day.prior_close)
        wayne_p = structures["WAYNE"]["P"]
        slope_state = _pivot_slope_state(wayne_p, previous_p, day.prior_range)
        previous_p = wayne_p
        path = minutes.loc[
            minutes["pivot_day_start"].eq(day_start) & minutes["active"]
        ].sort_index()
        if path.empty:
            continue
        timestamps = pd.DatetimeIndex(path.index)
        highs = path["high"].to_numpy(dtype=float)
        lows = path["low"].to_numpy(dtype=float)
        day_rows.append(
            {
                "instrument": symbol,
                "pivot_day_start_utc": day_start,
                "pivot_day_local_date": day_start.tz_convert(NEW_YORK_TZ).date().isoformat(),
                "year": local_year,
                "weekday": day_start.tz_convert(NEW_YORK_TZ).day_name(),
                "active_minutes": int(day.active_minutes),
                "prior_high": float(day.prior_high),
                "prior_low": float(day.prior_low),
                "prior_close": float(day.prior_close),
                "prior_range": float(day.prior_range),
                "wayne_p": float(wayne_p),
                "previous_wayne_p": float(previous_p) if np.isfinite(previous_p) else math.nan,
                "pivot_slope_state": slope_state,
            }
        )
        for structure_name, structure in structures.items():
            for side in ("BULL", "BEAR"):
                if side == "BULL":
                    zone_low, zone_high = structure["M2"], structure["P"]
                    stop = structure["S1"]
                    conservative_target = structure["M4"]
                else:
                    zone_low, zone_high = structure["P"], structure["M3"]
                    stop = structure["R1"]
                    conservative_target = structure["M1"]
                touch_index, freshness = _fresh_zone_index(
                    highs,
                    lows,
                    zone_low=zone_low,
                    zone_high=zone_high,
                    side=side,
                    conservative_target=conservative_target,
                    stop=stop,
                )
                if touch_index is None:
                    continue
                event_time = timestamps[touch_index]
                anchor = 0.5 * (zone_low + zone_high)
                risk = abs(anchor - stop)
                if risk <= 0.0 or not np.isfinite(risk):
                    continue
                if side == "BULL":
                    mfe = float(np.max(highs[touch_index:]) - anchor)
                    mae = float(anchor - np.min(lows[touch_index:]))
                else:
                    mfe = float(anchor - np.min(lows[touch_index:]))
                    mae = float(np.max(highs[touch_index:]) - anchor)
                for target_name in TARGETS[side]:
                    target = structure[target_name]
                    success, outcome, target_index, stop_index = _first_passage(
                        highs,
                        lows,
                        start_index=touch_index,
                        side=side,
                        target=target,
                        stop=stop,
                    )
                    reward_r = abs(target - anchor) / risk
                    strict_payoff_r = reward_r if success else -1.0
                    rows.append(
                        {
                            "event_id": (
                                f"{symbol}:{day_start.isoformat()}:{structure_name}:{side}"
                            ),
                            "instrument": symbol,
                            "pivot_day_start_utc": day_start,
                            "pivot_day_local_date": (
                                day_start.tz_convert(NEW_YORK_TZ).date().isoformat()
                            ),
                            "year": local_year,
                            "weekday": day_start.tz_convert(NEW_YORK_TZ).day_name(),
                            "structure": structure_name,
                            "side": side,
                            "target_name": target_name,
                            "freshness": freshness,
                            "eligible_fresh": freshness == "FRESH",
                            "pivot_slope_state": slope_state,
                            "event_timestamp_utc": event_time,
                            "event_minute": int(touch_index),
                            "zone_low": float(zone_low),
                            "zone_high": float(zone_high),
                            "anchor": float(anchor),
                            "target": float(target),
                            "stop": float(stop),
                            "risk_price": float(risk),
                            "reward_r": float(reward_r),
                            "success": bool(success),
                            "outcome": outcome,
                            "strict_payoff_r": float(strict_payoff_r),
                            "mfe_r": float(mfe / risk),
                            "mae_r": float(mae / risk),
                            "target_timestamp_utc": (
                                pd.NaT if target_index is None else timestamps[target_index]
                            ),
                            "stop_timestamp_utc": (
                                pd.NaT if stop_index is None else timestamps[stop_index]
                            ),
                        }
                    )
    ledger = pd.DataFrame(rows)
    day_ledger = pd.DataFrame(day_rows)
    if ledger.empty:
        raise ValueError(f"{symbol}: empty Wayne pivot anatomy ledger")
    duplicate_key = [
        "instrument",
        "pivot_day_start_utc",
        "structure",
        "side",
        "target_name",
    ]
    if ledger.duplicated(duplicate_key).any():
        raise ValueError(f"{symbol}: duplicate anatomy keys")
    return ledger.sort_values(duplicate_key), day_ledger.sort_values(
        ["instrument", "pivot_day_start_utc"]
    )
