from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import build_population

AMSTERDAM_TZ = "Europe/Amsterdam"
PIP_SIZE = {"EURUSD": 0.0001, "GBPUSD": 0.0001}
STRESS_PIPS = 0.10
MIN_DAILY_ACTIVE_MINUTES = 1200
MIN_WEEK_DAYS = 4

FACTOR_FAMILIES: dict[str, str] = {
    "d1_direction": "HTF_DIRECTION",
    "w1_direction": "HTF_DIRECTION",
    "d1_w1_agreement": "HTF_DIRECTION",
    "reversal_vs_d1": "HTF_DIRECTION",
    "reversal_vs_w1": "HTF_DIRECTION",
    "d1_slope_strength": "TREND_STRENGTH",
    "w1_slope_strength": "TREND_STRENGTH",
    "d1_efficiency_state": "TREND_STRENGTH",
    "d1_trend_change": "TREND_CHANGE",
    "daily_atr_regime": "VOLATILITY",
    "weekly_range_regime": "VOLATILITY",
    "realized_vol_regime": "VOLATILITY",
    "atr_transition": "VOLATILITY",
    "asian_compression_bucket": "VOLATILITY",
    "prior_day_position": "LOCATION",
    "prior_week_position": "LOCATION",
    "prior_day_boundary_distance": "LOCATION",
    "prior_week_boundary_distance": "LOCATION",
    "daily_open_displacement_state": "LOCATION",
    "weekly_open_displacement_state": "LOCATION",
    "overnight_gap_state": "LOCATION",
    "monday_range_position": "LOCATION",
    "weekday": "SESSION_CALENDAR",
    "sweep_half_hour": "SESSION_CALENDAR",
}


def _percentile(value: float, history: Iterable[float], minimum: int) -> float:
    sample = np.asarray(list(history), dtype=float)
    sample = sample[np.isfinite(sample)]
    if not np.isfinite(value) or len(sample) < minimum:
        return math.nan
    below = float((sample < value).sum())
    equal = float((sample == value).sum())
    return (below + 0.5 * equal) / len(sample)


def _ols_slope(values: pd.Series) -> float:
    sample = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if len(sample) < 2:
        return math.nan
    x = np.arange(len(sample), dtype=float)
    return float(np.polyfit(x, sample, 1)[0])


def _sign(value: float, tolerance: float = 0.0) -> int:
    if not np.isfinite(value) or abs(value) <= tolerance:
        return 0
    return 1 if value > 0.0 else -1


def _direction_state(short_return: float, long_return: float) -> str:
    if not np.isfinite(short_return) or not np.isfinite(long_return):
        return "WARMUP"
    short_sign = _sign(short_return)
    long_sign = _sign(long_return)
    if short_sign == 1 and long_sign == 1:
        return "UP"
    if short_sign == -1 and long_sign == -1:
        return "DOWN"
    return "MIXED"


def _strength_state(value: float) -> str:
    if not np.isfinite(value):
        return "WARMUP"
    magnitude = abs(value)
    if magnitude < 0.75:
        return "WEAK"
    if magnitude < 2.0:
        return "MODERATE"
    return "STRONG"


def _efficiency_state(value: float) -> str:
    if not np.isfinite(value):
        return "WARMUP"
    if value < 0.25:
        return "ROTATIONAL"
    if value < 0.50:
        return "ORDERED"
    return "PERSISTENT"


def _trend_change_state(rate5: float, rate20: float, atr20: float) -> str:
    if not all(np.isfinite(item) for item in (rate5, rate20, atr20)) or atr20 <= 0.0:
        return "WARMUP"
    if abs(rate20) <= 0.01 * atr20:
        return "FLAT"
    if _sign(rate5) != _sign(rate20):
        return "CONFLICT"
    ratio = abs(rate5) / abs(rate20)
    if ratio > 1.25:
        return "ACCELERATING"
    if ratio < 0.75:
        return "DECELERATING"
    return "STABLE"


def _percentile_state(value: float) -> str:
    if not np.isfinite(value):
        return "WARMUP"
    if value <= 0.30:
        return "COMPRESSED"
    if value < 0.70:
        return "NORMAL"
    return "EXPANDED"


def _transition_state(ratio: float) -> str:
    if not np.isfinite(ratio):
        return "WARMUP"
    if ratio > 1.10:
        return "RISING"
    if ratio < 0.90:
        return "FALLING"
    return "STABLE"


def _range_position(value: float, low: float, high: float) -> tuple[float, str]:
    if not all(np.isfinite(item) for item in (value, low, high)) or high <= low:
        return math.nan, "WARMUP"
    position = (value - low) / (high - low)
    if position < 0.0:
        state = "BELOW"
    elif position < 1.0 / 3.0:
        state = "LOWER"
    elif position < 2.0 / 3.0:
        state = "MIDDLE"
    elif position <= 1.0:
        state = "UPPER"
    else:
        state = "ABOVE"
    return float(position), state


def _boundary_distance_state(value: float) -> str:
    if not np.isfinite(value):
        return "WARMUP"
    if value <= 0.25:
        return "NEAR"
    if value <= 0.75:
        return "INTERMEDIATE"
    return "FAR"


def _displacement_state(value: float) -> str:
    if not np.isfinite(value):
        return "WARMUP"
    if value < -0.25:
        return "DOWN"
    if value > 0.25:
        return "UP"
    return "FLAT"


def _reversal_direction(sweep_side: str) -> str:
    if sweep_side == "UP":
        return "DOWN"
    if sweep_side == "DOWN":
        return "UP"
    raise ValueError(f"unsupported sweep side: {sweep_side}")


def _relation(direction: str, structural: str) -> str:
    if structural == "WARMUP":
        return "WARMUP"
    if structural == "MIXED":
        return "MIXED"
    return "ALIGNED" if direction == structural else "OPPOSED"


def _agreement(d1: str, w1: str) -> str:
    if "WARMUP" in {d1, w1}:
        return "WARMUP"
    if d1 == "MIXED" or w1 == "MIXED":
        return "MIXED"
    if d1 == w1 == "UP":
        return "ALIGNED_UP"
    if d1 == w1 == "DOWN":
        return "ALIGNED_DOWN"
    return "CONFLICT"


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
            quotes[f"{column}_bid"] + quotes[f"{column}_ask"]
        )
    out["is_active_quote"] = quotes["active"].astype("int8")
    out.index = out.index.tz_convert(AMSTERDAM_TZ)
    return out.sort_index()


def build_daily_context(minutes: pd.DataFrame) -> pd.DataFrame:
    active = minutes.loc[minutes["is_active_quote"].gt(0)].copy()
    active["trade_date"] = active.index.date
    daily = active.groupby("trade_date", sort=True).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        active_minutes=("close", "size"),
    )
    daily = daily.loc[daily["active_minutes"].ge(MIN_DAILY_ACTIVE_MINUTES)].copy()
    prior_close = daily["close"].shift(1)
    daily["true_range"] = np.maximum.reduce(
        [
            (daily["high"] - daily["low"]).to_numpy(float),
            (daily["high"] - prior_close).abs().to_numpy(float),
            (daily["low"] - prior_close).abs().to_numpy(float),
        ]
    )
    daily["atr20"] = daily["true_range"].rolling(20, min_periods=20).mean()
    daily["ret5"] = daily["close"] / daily["close"].shift(5) - 1.0
    daily["ret20"] = daily["close"] / daily["close"].shift(20) - 1.0
    daily["rate5"] = (daily["close"] - daily["close"].shift(5)) / 5.0
    daily["rate20"] = (daily["close"] - daily["close"].shift(20)) / 20.0
    daily["slope20"] = [
        _ols_slope(daily["close"].iloc[max(0, index - 19) : index + 1])
        if index >= 19
        else math.nan
        for index in range(len(daily))
    ]
    daily["slope20_atr"] = 20.0 * daily["slope20"] / daily["atr20"]
    changes = daily["close"].diff().abs()
    denominator = changes.rolling(20, min_periods=20).sum()
    daily["efficiency20"] = (
        (daily["close"] - daily["close"].shift(20)).abs() / denominator
    )
    daily_return = daily["close"].pct_change()
    daily["realized_vol5"] = daily_return.rolling(5, min_periods=5).std(ddof=0)
    atr_values = daily["atr20"].to_numpy(dtype=float)
    rv_values = daily["realized_vol5"].to_numpy(dtype=float)
    daily["atr_percentile252"] = [
        _percentile(value, atr_values[max(0, i - 252) : i], 60)
        for i, value in enumerate(atr_values)
    ]
    daily["realized_vol_percentile126"] = [
        _percentile(value, rv_values[max(0, i - 126) : i], 40)
        for i, value in enumerate(rv_values)
    ]
    daily["atr_ratio_5"] = daily["atr20"] / daily["atr20"].shift(5)
    daily["d1_direction"] = [
        _direction_state(short, long)
        for short, long in zip(daily["ret5"], daily["ret20"], strict=False)
    ]
    daily["d1_slope_strength"] = daily["slope20_atr"].map(_strength_state)
    daily["d1_efficiency_state"] = daily["efficiency20"].map(_efficiency_state)
    daily["d1_trend_change"] = [
        _trend_change_state(rate5, rate20, atr)
        for rate5, rate20, atr in zip(
            daily["rate5"], daily["rate20"], daily["atr20"], strict=False
        )
    ]
    daily["daily_atr_regime"] = daily["atr_percentile252"].map(_percentile_state)
    daily["realized_vol_regime"] = daily["realized_vol_percentile126"].map(
        _percentile_state
    )
    daily["atr_transition"] = daily["atr_ratio_5"].map(_transition_state)
    daily.index = pd.to_datetime(daily.index)
    daily.index.name = "trade_date"
    return daily


def build_weekly_context(daily: pd.DataFrame) -> pd.DataFrame:
    rows = daily.reset_index().copy()
    rows["week_start"] = rows["trade_date"] - pd.to_timedelta(
        rows["trade_date"].dt.weekday, unit="D"
    )
    weekly = rows.groupby("week_start", sort=True).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        valid_days=("trade_date", "size"),
    )
    weekly = weekly.loc[weekly["valid_days"].ge(MIN_WEEK_DAYS)].copy()
    weekly["range"] = weekly["high"] - weekly["low"]
    weekly["ret1"] = weekly["close"] / weekly["close"].shift(1) - 1.0
    weekly["ret4"] = weekly["close"] / weekly["close"].shift(4) - 1.0
    weekly["slope8"] = [
        _ols_slope(weekly["close"].iloc[max(0, index - 7) : index + 1])
        if index >= 7
        else math.nan
        for index in range(len(weekly))
    ]
    weekly["median_range20"] = weekly["range"].rolling(
        20, min_periods=20
    ).median()
    weekly["slope8_range"] = 8.0 * weekly["slope8"] / weekly["median_range20"]
    ranges = weekly["range"].to_numpy(dtype=float)
    weekly["range_percentile52"] = [
        _percentile(value, ranges[max(0, i - 52) : i], 20)
        for i, value in enumerate(ranges)
    ]
    weekly["w1_direction"] = [
        _direction_state(short, long)
        for short, long in zip(weekly["ret1"], weekly["ret4"], strict=False)
    ]
    weekly["w1_slope_strength"] = weekly["slope8_range"].map(_strength_state)
    weekly["weekly_range_regime"] = weekly["range_percentile52"].map(
        _percentile_state
    )
    weekly.index = pd.to_datetime(weekly.index)
    weekly.index.name = "week_start"
    return weekly


def _last_prior_row(frame: pd.DataFrame, timestamp: pd.Timestamp) -> pd.Series | None:
    prior = frame.loc[frame.index < timestamp]
    return None if prior.empty else prior.iloc[-1]


def _context_anchor(
    minutes: pd.DataFrame, trade_date: pd.Timestamp
) -> tuple[float, float]:
    day_start = trade_date.tz_localize(AMSTERDAM_TZ)
    asian_end = day_start + pd.Timedelta(hours=8)
    path = minutes.loc[
        (minutes.index >= day_start)
        & (minutes.index < asian_end)
        & minutes["is_active_quote"].gt(0)
    ]
    if path.empty:
        return math.nan, math.nan
    return float(path.iloc[-1]["close"]), float(path.iloc[0]["open"])


def _current_week_open(minutes: pd.DataFrame, trade_date: pd.Timestamp) -> float:
    week_start = trade_date - pd.Timedelta(days=int(trade_date.weekday()))
    start = week_start.tz_localize(AMSTERDAM_TZ)
    end = trade_date.tz_localize(AMSTERDAM_TZ) + pd.Timedelta(hours=8)
    path = minutes.loc[
        (minutes.index >= start)
        & (minutes.index < end)
        & minutes["is_active_quote"].gt(0)
    ]
    return math.nan if path.empty else float(path.iloc[0]["open"])


def build_event_context(
    events: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    symbol: str,
) -> pd.DataFrame:
    symbol = symbol.upper()
    population = build_population(events, "T5").copy()
    population = population.loc[population["instrument"].eq(symbol)].copy()
    if population.empty:
        raise ValueError(f"{symbol}: empty T5 population")
    population["trade_date_ts"] = pd.to_datetime(
        population["trade_date"], errors="raise"
    )
    population["t5_timestamp_utc"] = pd.to_datetime(
        population["t5_timestamp_utc"], utc=True, errors="raise"
    )
    minutes = midpoint_minutes(quotes)
    daily = build_daily_context(minutes)
    weekly = build_weekly_context(daily)
    rows: list[dict[str, Any]] = []
    for event in population.sort_values(
        ["trade_date_ts", "event_id"]
    ).itertuples(index=False):
        trade_date = pd.Timestamp(event.trade_date_ts)
        week_start = trade_date - pd.Timedelta(days=int(trade_date.weekday()))
        prior_day = _last_prior_row(daily, trade_date)
        prior_week = _last_prior_row(weekly, week_start)
        anchor, daily_open = _context_anchor(minutes, trade_date)
        weekly_open = _current_week_open(minutes, trade_date)
        reversal = _reversal_direction(str(event.side))
        if prior_day is None:
            prior_day = pd.Series(dtype=object)
        if prior_week is None:
            prior_week = pd.Series(dtype=object)
        atr20 = float(prior_day.get("atr20", math.nan))
        d1 = str(prior_day.get("d1_direction", "WARMUP"))
        w1 = str(prior_week.get("w1_direction", "WARMUP"))
        pd_position, pd_state = _range_position(
            anchor,
            float(prior_day.get("low", math.nan)),
            float(prior_day.get("high", math.nan)),
        )
        pw_position, pw_state = _range_position(
            anchor,
            float(prior_week.get("low", math.nan)),
            float(prior_week.get("high", math.nan)),
        )
        if np.isfinite(atr20) and atr20 > 0.0:
            pd_distance = min(
                abs(anchor - float(prior_day.get("high", math.nan))),
                abs(anchor - float(prior_day.get("low", math.nan))),
            ) / atr20
            pw_distance = min(
                abs(anchor - float(prior_week.get("high", math.nan))),
                abs(anchor - float(prior_week.get("low", math.nan))),
            ) / atr20
            daily_disp = (anchor - daily_open) / atr20
            weekly_disp = (anchor - weekly_open) / atr20
            overnight_gap = (
                daily_open - float(prior_day.get("close", math.nan))
            ) / atr20
        else:
            pd_distance = math.nan
            pw_distance = math.nan
            daily_disp = math.nan
            weekly_disp = math.nan
            overnight_gap = math.nan
        monday_state = "WARMUP"
        monday_position = math.nan
        if trade_date.weekday() >= 1:
            monday = daily.loc[daily.index == week_start]
            if not monday.empty:
                monday_position, monday_state = _range_position(
                    anchor,
                    float(monday.iloc[0]["low"]),
                    float(monday.iloc[0]["high"]),
                )
        record = event._asdict()
        record.update(
            {
                "context_anchor_price": anchor,
                "context_daily_open": daily_open,
                "context_weekly_open": weekly_open,
                "context_atr20": atr20,
                "d1_direction": d1,
                "w1_direction": w1,
                "d1_w1_agreement": _agreement(d1, w1),
                "reversal_vs_d1": _relation(reversal, d1),
                "reversal_vs_w1": _relation(reversal, w1),
                "d1_slope_atr": float(prior_day.get("slope20_atr", math.nan)),
                "d1_slope_strength": str(
                    prior_day.get("d1_slope_strength", "WARMUP")
                ),
                "w1_slope_range": float(prior_week.get("slope8_range", math.nan)),
                "w1_slope_strength": str(
                    prior_week.get("w1_slope_strength", "WARMUP")
                ),
                "d1_efficiency20": float(
                    prior_day.get("efficiency20", math.nan)
                ),
                "d1_efficiency_state": str(
                    prior_day.get("d1_efficiency_state", "WARMUP")
                ),
                "d1_trend_change": str(
                    prior_day.get("d1_trend_change", "WARMUP")
                ),
                "daily_atr_percentile": float(
                    prior_day.get("atr_percentile252", math.nan)
                ),
                "daily_atr_regime": str(
                    prior_day.get("daily_atr_regime", "WARMUP")
                ),
                "weekly_range_percentile": float(
                    prior_week.get("range_percentile52", math.nan)
                ),
                "weekly_range_regime": str(
                    prior_week.get("weekly_range_regime", "WARMUP")
                ),
                "realized_vol_percentile": float(
                    prior_day.get("realized_vol_percentile126", math.nan)
                ),
                "realized_vol_regime": str(
                    prior_day.get("realized_vol_regime", "WARMUP")
                ),
                "atr_transition": str(
                    prior_day.get("atr_transition", "WARMUP")
                ),
                "prior_day_position_value": pd_position,
                "prior_day_position": pd_state,
                "prior_week_position_value": pw_position,
                "prior_week_position": pw_state,
                "prior_day_boundary_distance_atr": pd_distance,
                "prior_day_boundary_distance": _boundary_distance_state(pd_distance),
                "prior_week_boundary_distance_atr": pw_distance,
                "prior_week_boundary_distance": _boundary_distance_state(pw_distance),
                "daily_open_displacement_atr": daily_disp,
                "daily_open_displacement_state": _displacement_state(daily_disp),
                "weekly_open_displacement_atr": weekly_disp,
                "weekly_open_displacement_state": _displacement_state(weekly_disp),
                "overnight_gap_atr": overnight_gap,
                "overnight_gap_state": _displacement_state(overnight_gap),
                "monday_range_position_value": monday_position,
                "monday_range_position": monday_state,
            }
        )
        rows.append(record)
    result = pd.DataFrame(rows)
    if result["event_id"].duplicated().any():
        raise ValueError(f"{symbol}: duplicate context event ids")
    return add_stressed_payoff_proxy(result, quotes, symbol=symbol)


def add_stressed_payoff_proxy(
    context: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    symbol: str,
) -> pd.DataFrame:
    symbol = symbol.upper()
    pip = PIP_SIZE[symbol]
    out = context.copy()
    payoffs: list[float] = []
    reward_risks: list[float] = []
    eligible: list[bool] = []
    for row in out.itertuples(index=False):
        decision = pd.Timestamp(row.t5_timestamp_utc)
        next_rows = quotes.loc[(quotes.index > decision) & quotes["active"]].head(1)
        is_long = str(row.side) == "DOWN"
        if next_rows.empty:
            payoffs.append(math.nan)
            reward_risks.append(math.nan)
            eligible.append(False)
            continue
        quote = next_rows.iloc[0]
        entry = float(quote["open_ask"] if is_long else quote["open_bid"])
        stop = (
            float(row.sweep_extreme) - 0.20 * float(row.asian_range_price)
            if is_long
            else float(row.sweep_extreme) + 0.20 * float(row.asian_range_price)
        )
        target = float(row.asian_midpoint)
        slip = STRESS_PIPS * pip
        stressed_entry = entry + slip if is_long else entry - slip
        stressed_stop = stop - slip if is_long else stop + slip
        risk = (
            stressed_entry - stressed_stop
            if is_long
            else stressed_stop - stressed_entry
        )
        reward = (
            target - stressed_entry if is_long else stressed_entry - target
        )
        valid = risk > 0.0 and reward > 0.0
        reward_risk = reward / risk if valid else math.nan
        target_value = int(row.target)
        payoff = (
            reward_risk
            if valid and target_value == 1
            else (-1.0 if valid else math.nan)
        )
        payoffs.append(float(payoff) if np.isfinite(payoff) else math.nan)
        reward_risks.append(
            float(reward_risk) if np.isfinite(reward_risk) else math.nan
        )
        eligible.append(bool(valid))
    out["stressed_reward_risk_proxy"] = reward_risks
    out["stressed_payoff_proxy"] = payoffs
    out["economic_proxy_eligible"] = eligible
    return out
