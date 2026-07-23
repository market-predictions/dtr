from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.research import engine
from dtr_lab.research.cross_market import (
    USA500_PROXY_SPEC,
    build_covered_session_table,
    classify_proxy_gaps,
    cost_stress_expectancy,
)

SEED = 20260723
YEARS = (2022, 2023, 2024, 2025)

FOMC_DATES = pd.DatetimeIndex(pd.to_datetime([
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
])).normalize()

CPI_DATES = pd.DatetimeIndex(pd.to_datetime([
    "2022-01-12", "2022-02-10", "2022-03-10", "2022-04-12", "2022-05-11", "2022-06-10", "2022-07-13", "2022-08-10", "2022-09-13", "2022-10-13", "2022-11-10", "2022-12-13",
    "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12", "2023-05-10", "2023-06-13", "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-14", "2023-12-12",
    "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15", "2024-06-12", "2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11",
    "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11", "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-24",
])).normalize()

NFP_DATES = pd.DatetimeIndex(pd.to_datetime([
    "2022-01-07", "2022-02-04", "2022-03-04", "2022-04-01", "2022-05-06", "2022-06-03", "2022-07-08", "2022-08-05", "2022-09-02", "2022-10-07", "2022-11-04", "2022-12-02",
    "2023-01-06", "2023-02-03", "2023-03-10", "2023-04-07", "2023-05-05", "2023-06-02", "2023-07-07", "2023-08-04", "2023-09-01", "2023-10-06", "2023-11-03", "2023-12-08",
    "2024-01-05", "2024-02-02", "2024-03-08", "2024-04-05", "2024-05-03", "2024-06-07", "2024-07-05", "2024-08-02", "2024-09-06", "2024-10-04", "2024-11-01", "2024-12-06",
    "2025-01-10", "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02", "2025-06-06", "2025-07-03", "2025-08-01", "2025-09-05", "2025-11-20",
])).normalize()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_proxy(path: Path) -> pd.DataFrame:
    digest = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else Path.open
    if path.suffix == ".gz":
        handle_ctx = gzip.open(path, "rb")
    else:
        handle_ctx = path.open("rb")
    with handle_ctx as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    if digest.hexdigest() != USA500_PROXY_SPEC.source_sha256:
        raise ValueError("USA500 source checksum mismatch")
    frame = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    utc = pd.to_datetime(frame["timestamp"], unit="ms", utc=True, errors="raise")
    frame["timestamp"] = utc.dt.tz_convert("America/New_York").dt.tz_localize(None)
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    if frame.empty or not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("invalid proxy chronology")
    valid = (
        (frame["high"] >= frame[["open", "close", "low"]].max(axis=1))
        & (frame["low"] <= frame[["open", "close", "high"]].min(axis=1))
    )
    if not valid.all():
        raise ValueError("proxy OHLC integrity failed")
    return frame


def attach_gap_metadata(bars: pd.DataFrame, gaps: pd.DataFrame) -> pd.DataFrame:
    reset = pd.to_datetime(gaps.loc[gaps["reset_strategy_state"], "current_timestamp"]).to_numpy(dtype="datetime64[ns]").astype(np.int64)
    unsafe = pd.to_datetime(gaps.loc[gaps["reject_trade_bridge"], "current_timestamp"]).to_numpy(dtype="datetime64[ns]").astype(np.int64)
    starts = bars["timestamp"].to_numpy(dtype="datetime64[ns]").astype(np.int64)
    ends = bars["bar_end"].to_numpy(dtype="datetime64[ns]").astype(np.int64)
    work = bars.copy()
    work["state_epoch_start"] = np.searchsorted(reset, starts, side="left")
    work["state_epoch_end"] = np.searchsorted(reset, ends, side="left")
    work["unsafe_epoch_start"] = np.searchsorted(unsafe, starts, side="left")
    work["unsafe_epoch_end"] = np.searchsorted(unsafe, ends, side="left")
    work["contains_reset_gap"] = work["state_epoch_end"] > work["state_epoch_start"]
    work["contains_unsafe_gap"] = work["unsafe_epoch_end"] > work["unsafe_epoch_start"]
    return work


def sanitize_sessions(sessions: pd.DataFrame, bars: pd.DataFrame, gaps: pd.DataFrame) -> pd.DataFrame:
    reset = gaps.loc[gaps["reset_strategy_state"], ["previous_timestamp", "current_timestamp"]].copy()
    reset["previous_timestamp"] = pd.to_datetime(reset["previous_timestamp"])
    reset["current_timestamp"] = pd.to_datetime(reset["current_timestamp"])
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    rows: list[dict[str, object]] = []
    for row in sessions.itertuples(index=False):
        range_overlap = (reset["previous_timestamp"] < row.range_end) & (reset["current_timestamp"] > row.range_start)
        path_overlap = (reset["previous_timestamp"] < row.break_end) & (reset["current_timestamp"] > row.range_end)
        post_end = int(row.post_end_index)
        truncated = False
        if path_overlap.any():
            first = reset.loc[path_overlap].iloc[0]
            first_missing = max(pd.Timestamp(first["previous_timestamp"]) + pd.Timedelta(minutes=1), pd.Timestamp(row.range_end))
            gap_bar = max(0, int(np.searchsorted(bar_times, np.datetime64(first_missing), side="right") - 1))
            if gap_bar < post_end:
                post_end = gap_bar
                truncated = True
        record = row._asdict()
        record["integrity_original_post_end_index"] = int(row.post_end_index)
        record["post_end_index"] = post_end
        record["integrity_range_gap_rejected"] = bool(range_overlap.any())
        record["integrity_signal_path_truncated"] = truncated
        rows.append(record)
    return pd.DataFrame(rows)


def simulate_all(one: pd.DataFrame, bars: pd.DataFrame, signals: list[engine.CandidateSignal], cfg: engine.StrategyConfig, gaps: pd.DataFrame) -> dict[int, engine.Trade]:
    arrays = engine.prepare_market_arrays(one)
    unsafe = gaps.loc[gaps["reject_trade_bridge"], ["previous_timestamp", "current_timestamp"]]
    unsafe_prev = pd.to_datetime(unsafe["previous_timestamp"]).to_numpy(dtype="datetime64[ns]").astype(np.int64)
    unsafe_curr = pd.to_datetime(unsafe["current_timestamp"]).to_numpy(dtype="datetime64[ns]").astype(np.int64)
    result: dict[int, engine.Trade] = {}
    for signal_id, signal in enumerate(signals):
        trade = engine._simulate_trade_np(*arrays, bars, signal, cfg, unsafe_previous_ns=unsafe_prev, unsafe_current_ns=unsafe_curr, gap_policy="liquidate")
        if trade is not None:
            result[signal_id] = trade
    return result


def sequence(signal_features: pd.DataFrame, cached: dict[int, engine.Trade], mask: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    next_free = pd.Timestamp.min
    for row in signal_features.loc[mask.fillna(False)].sort_values("entry_time").itertuples(index=False):
        trade = cached.get(int(row.signal_id))
        if trade is None or pd.Timestamp(row.entry_time) < next_free:
            continue
        record = asdict(trade)
        record["signal_id"] = int(row.signal_id)
        rows.append(record)
        next_free = pd.Timestamp(trade.exit_time)
    return pd.DataFrame(rows)


def rolling_prior_percentile(frame: pd.DataFrame, column: str, *, window: int = 126, minimum: int = 40) -> pd.Series:
    output = pd.Series(np.nan, index=frame.index, dtype=float)
    for _, indexes in frame.groupby("session", sort=False).groups.items():
        indexes = list(indexes)
        values = frame.loc[indexes, column].to_numpy(float)
        result = np.full(len(values), np.nan)
        for position, value in enumerate(values):
            history = values[max(0, position - window):position]
            history = history[np.isfinite(history)]
            if np.isfinite(value) and len(history) >= minimum:
                result[position] = float(np.mean(history <= value))
        output.loc[indexes] = result
    return output


def daily_weekly(one: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = one.copy()
    work["eth_day"] = (work["timestamp"] - pd.Timedelta(hours=18)).dt.normalize()
    daily = work.groupby("eth_day", as_index=False).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum")).sort_values("eth_day")
    previous_close = daily["close"].shift(1)
    tr = pd.concat([daily["high"] - daily["low"], (daily["high"] - previous_close).abs(), (daily["low"] - previous_close).abs()], axis=1).max(axis=1)
    daily["atr20"] = tr.ewm(alpha=1 / 20, adjust=False, min_periods=20).mean()
    daily["mid"] = (daily["high"] + daily["low"]) / 2
    daily["complete_time"] = daily["eth_day"] + pd.Timedelta(days=1, hours=17)
    daily["week_start"] = daily["eth_day"] - pd.to_timedelta((daily["eth_day"].dt.weekday + 1) % 7, unit="D")
    weekly = daily.groupby("week_start", as_index=False).agg(high=("high", "max"), low=("low", "min"), close=("close", "last")).sort_values("week_start")
    weekly["mid"] = (weekly["high"] + weekly["low"]) / 2
    weekly["complete_time"] = weekly["week_start"] + pd.Timedelta(days=5, hours=17)
    return daily, weekly


def replay_path(signal: engine.CandidateSignal, bars: pd.DataFrame, cfg: engine.StrategyConfig) -> dict[str, float | int]:
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    open_ = bars["open"].to_numpy(float)
    atr = bars["atr14"].to_numpy(float)
    median_range = bars["median_range20"].to_numpy(float)
    last = min(len(bars), signal.sweep_index + cfg.max_bars_from_sweep + 1)
    reclaim_limit = min(last, signal.sweep_index + cfg.reaction_bars + 1)
    reclaim_index = -1
    for index in range(signal.sweep_index, reclaim_limit):
        if (signal.direction > 0 and close[index] >= signal.range_low) or (signal.direction < 0 and close[index] <= signal.range_high):
            reclaim_index = index
            break
    if reclaim_index < 0:
        raise RuntimeError("reclaim replay failed")
    pivot = np.nan
    pivot_ready = -1
    bos_index = -1
    for index in range(max(signal.sweep_index + 2 * cfg.pivot_len, reclaim_index), last):
        candidate_index = index - cfg.pivot_len
        if signal.direction > 0 and engine._pivot_high(high, candidate_index, cfg.pivot_len):
            if high[candidate_index] - signal.sweep_extreme >= max(cfg.tick_size, (signal.range_high - signal.range_low) * cfg.pivot_min_pct):
                pivot, pivot_ready = high[candidate_index], index
        elif signal.direction < 0 and engine._pivot_low(low, candidate_index, cfg.pivot_len):
            if signal.sweep_extreme - low[candidate_index] >= max(cfg.tick_size, (signal.range_high - signal.range_low) * cfg.pivot_min_pct):
                pivot, pivot_ready = low[candidate_index], index
        if not np.isfinite(pivot) or index < pivot_ready:
            continue
        buffer = max((signal.range_high - signal.range_low) * cfg.break_buffer_pct, atr[index] * cfg.break_atr_frac if np.isfinite(atr[index]) else 0.0)
        broke = high[index] >= pivot + buffer if signal.direction > 0 else low[index] <= pivot - buffer
        if cfg.break_mode != "wick":
            broke = close[index] >= pivot + buffer if signal.direction > 0 else close[index] <= pivot - buffer
        if not broke:
            continue
        if cfg.require_impulse:
            impulse = np.isfinite(median_range[index]) and (high[index] - low[index]) > median_range[index] * cfg.impulse_mult and ((close[index] > open_[index]) if signal.direction > 0 else (close[index] < open_[index]))
            if not impulse:
                continue
        bos_index = index
        break
    if bos_index < 0 or not np.isfinite(pivot):
        raise RuntimeError("BOS replay failed")
    bos_range = high[bos_index] - low[bos_index]
    body_fraction = abs(close[bos_index] - open_[bos_index]) / bos_range if bos_range > 0 else 0.0
    close_location = ((close[bos_index] - low[bos_index]) / bos_range if signal.direction > 0 else (high[bos_index] - close[bos_index]) / bos_range) if bos_range > 0 else 0.0
    previous = close[bos_index - 1] if bos_index else close[bos_index]
    true_range = max(bos_range, abs(high[bos_index] - previous), abs(low[bos_index] - previous))
    atr_ratio = true_range / atr[bos_index] if np.isfinite(atr[bos_index]) and atr[bos_index] > 0 else np.nan
    quality = int(body_fraction >= 0.60) + int(close_location >= 0.75) + int(np.isfinite(atr_ratio) and atr_ratio >= 1.0)
    return {"sweep_to_entry_bars": int(signal.entry_index - signal.sweep_index), "bos_quality_score": quality, "bos_body_fraction": float(body_fraction), "bos_close_location": float(close_location), "bos_atr_ratio": float(atr_ratio)}


def geometry(signal: engine.CandidateSignal, bars: pd.DataFrame, cfg: engine.StrategyConfig) -> dict[str, float]:
    atr = float(bars.iloc[signal.entry_index]["atr14"])
    slip = cfg.tick_size * cfg.slippage_ticks_each_side
    entry = signal.entry_price_raw + slip if signal.direction > 0 else signal.entry_price_raw - slip
    buffer = max(cfg.tick_size * cfg.stop_buffer_ticks, atr * cfg.stop_atr_frac)
    stop = signal.sweep_extreme - buffer if signal.direction > 0 else signal.sweep_extreme + buffer
    risk = entry - stop if signal.direction > 0 else stop - entry
    return {"entry_calc": float(entry), "stop_calc": float(stop), "risk_points": float(risk), "entry_extension_r": float(abs(signal.entry_price_raw - signal.pivot) / risk) if risk > cfg.tick_size else np.nan}


def nearest_clearance(row: pd.Series) -> float:
    entry = float(row["entry_calc"])
    risk = float(row["risk_points"])
    if not np.isfinite(risk) or risk <= 0:
        return np.nan
    if int(row["direction"]) > 0:
        candidates = [row["range_high"], row["prev_d1_mid"], row["prev_d1_high"], row["prev_week_mid"], row["prev_week_high"]]
        distances = [float(value) - entry for value in candidates if pd.notna(value) and float(value) > entry]
    else:
        candidates = [row["range_low"], row["prev_d1_mid"], row["prev_d1_low"], row["prev_week_mid"], row["prev_week_low"]]
        distances = [entry - float(value) for value in candidates if pd.notna(value) and float(value) < entry]
    return float(min(distances) / risk) if distances else float("inf")


def add_features(one: pd.DataFrame, bars: pd.DataFrame, sessions: pd.DataFrame, signals: list[engine.CandidateSignal], cfg: engine.StrategyConfig) -> pd.DataFrame:
    rows = []
    for signal_id, signal in enumerate(signals):
        rows.append({
            "signal_id": signal_id,
            "session": signal.session,
            "session_date": pd.Timestamp(signal.session_date).normalize(),
            "weekday": signal.day_of_week,
            "direction": signal.direction,
            "entry_time": pd.Timestamp(signal.entry_time),
            "range_high": signal.range_high,
            "range_low": signal.range_low,
            "range_size": signal.range_high - signal.range_low,
            "pivot": signal.pivot,
            **replay_path(signal, bars, cfg),
            **geometry(signal, bars, cfg),
        })
    features = pd.DataFrame(rows)
    session_context = sessions.copy().sort_values("range_start")
    session_context["range_percentile"] = rolling_prior_percentile(session_context, "range_size")
    daily, weekly = daily_weekly(one)
    session_context = pd.merge_asof(session_context, daily[["complete_time", "high", "low", "mid", "atr20"]].sort_values("complete_time"), left_on="range_start", right_on="complete_time", direction="backward", allow_exact_matches=True).rename(columns={"high": "prev_d1_high", "low": "prev_d1_low", "mid": "prev_d1_mid", "atr20": "d1_atr20"})
    session_context = pd.merge_asof(session_context.sort_values("range_start"), weekly[["complete_time", "high", "low", "mid"]].sort_values("complete_time"), left_on="range_start", right_on="complete_time", direction="backward", allow_exact_matches=True, suffixes=("", "_week")).rename(columns={"high": "prev_week_high", "low": "prev_week_low", "mid": "prev_week_mid"})
    keep = ["session_date", "session", "range_percentile", "prev_d1_high", "prev_d1_low", "prev_d1_mid", "d1_atr20", "prev_week_high", "prev_week_low", "prev_week_mid"]
    features = features.merge(session_context[keep], on=["session_date", "session"], how="left", validate="many_to_one")
    features["directional_extreme_distance_atr"] = np.where(features["direction"] > 0, (features["range_low"] - features["prev_d1_low"]).abs(), (features["range_high"] - features["prev_d1_high"]).abs()) / features["d1_atr20"]
    features["clearance_r"] = features.apply(nearest_clearance, axis=1)
    return features


def max_drawdown(values: np.ndarray) -> float:
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(peaks - equity, initial=0.0))


def profit_factor(values: np.ndarray) -> float:
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    if losses == 0:
        return math.inf if gains > 0 else np.nan
    return gains / losses


def summarize(trades: pd.DataFrame, arm: str, eligible_sessions: int, qualifying_signals: int, tick_size: float) -> dict[str, object]:
    values = trades["pnl_r"].to_numpy(float) if not trades.empty else np.array([], dtype=float)
    net = float(values.sum()) if len(values) else 0.0
    dd = max_drawdown(values) if len(values) else 0.0
    result: dict[str, object] = {
        "arm": arm,
        "eligible_sessions": eligible_sessions,
        "qualifying_signals": qualifying_signals,
        "trades": int(len(trades)),
        "net_r": net,
        "expectancy_r": float(values.mean()) if len(values) else np.nan,
        "median_r": float(np.median(values)) if len(values) else np.nan,
        "profit_factor": profit_factor(values),
        "win_rate": float(np.mean(values > 0)) if len(values) else np.nan,
        "max_drawdown_r": dd,
        "return_dd": net / dd if dd > 0 else np.nan,
        "one_tick_expectancy_r": float(values.mean()) if len(values) else np.nan,
        "two_tick_expectancy_r": cost_stress_expectancy(trades, total_ticks_each_side=2.0, tick_size=tick_size),
        "four_tick_expectancy_r": cost_stress_expectancy(trades, total_ticks_each_side=4.0, tick_size=tick_size),
    }
    entry = pd.to_datetime(trades["entry_time"]) if not trades.empty else pd.Series(dtype="datetime64[ns]")
    positive_total = max(net, 0.0)
    year_nets = []
    for year in YEARS:
        value = float(trades.loc[entry.dt.year == year, "pnl_r"].sum()) if not trades.empty else 0.0
        result[f"net_{year}"] = value
        year_nets.append(value)
    result["positive_years"] = int(sum(value > 0 for value in year_nets))
    result["minimum_year_net_r"] = float(min(year_nets))
    result["single_year_positive_net_share"] = float(max(year_nets) / positive_total) if positive_total > 0 else np.inf
    if not trades.empty:
        session_nets = trades.groupby("session")["pnl_r"].sum()
        result["single_session_positive_net_share"] = float(session_nets.max() / positive_total) if positive_total > 0 else np.inf
    else:
        result["single_session_positive_net_share"] = np.inf
    return result


def block_bootstrap(trades: pd.DataFrame, unit: str, iterations: int, seed: int) -> dict[str, float | int]:
    if trades.empty:
        return {"blocks": 0, "lo95_expectancy_r": np.nan, "hi95_expectancy_r": np.nan, "prob_expectancy_positive": np.nan}
    work = trades.copy()
    dates = pd.to_datetime(work["session_date"])
    labels = dates.dt.normalize() if unit == "date" else dates.dt.to_period("M").astype(str)
    groups = [group["pnl_r"].to_numpy(float) for _, group in work.groupby(labels, sort=True)]
    rng = np.random.default_rng(seed)
    means = np.empty(iterations)
    for index in range(iterations):
        selected = rng.integers(0, len(groups), size=len(groups))
        values = np.concatenate([groups[item] for item in selected])
        means[index] = values.mean()
    return {"blocks": len(groups), "lo95_expectancy_r": float(np.quantile(means, 0.025)), "hi95_expectancy_r": float(np.quantile(means, 0.975)), "prob_expectancy_positive": float(np.mean(means > 0))}


def paired_date_bootstrap(candidate: pd.DataFrame, baseline: pd.DataFrame, iterations: int, seed: int) -> dict[str, float]:
    def series(frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(dtype=float)
        dates = pd.to_datetime(frame["session_date"]).dt.normalize()
        return frame.assign(block=dates).groupby("block")["pnl_r"].sum()
    candidate_series = series(candidate)
    baseline_series = series(baseline)
    index = candidate_series.index.union(baseline_series.index).sort_values()
    differences = candidate_series.reindex(index, fill_value=0.0) - baseline_series.reindex(index, fill_value=0.0)
    values = differences.to_numpy(float)
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(iterations, len(values)), replace=True).sum(axis=1)
    return {"observed_net_difference_r": float(values.sum()), "lo95_net_difference_r": float(np.quantile(samples, 0.025)), "hi95_net_difference_r": float(np.quantile(samples, 0.975)), "prob_net_difference_positive": float(np.mean(samples > 0))}


def eligible_count(sessions: pd.DataFrame, weekdays: tuple[int, ...], allowed_sessions: tuple[str, ...]) -> int:
    return int(sessions.loc[sessions["weekday"].isin(weekdays) & sessions["session"].isin(allowed_sessions)].shape[0])


def changed_attribution(parent: pd.DataFrame, child: pd.DataFrame, label: str) -> pd.DataFrame:
    keys = ["session", "session_date", "direction", "entry_time"]
    left = parent.copy()
    right = child.copy()
    for frame in (left, right):
        for column in ("session_date", "entry_time"):
            frame[column] = pd.to_datetime(frame[column])
    merged = left[keys + ["pnl_r"]].merge(right[keys + ["pnl_r"]], on=keys, how="outer", suffixes=("_parent", "_child"), indicator=True)
    merged["change_type"] = merged["_merge"].map({"left_only": "REMOVED", "right_only": "ADDED", "both": "UNCHANGED"})
    merged["comparison"] = label
    return merged.drop(columns=["_merge"])


def third_fridays(start_year: int, end_year: int) -> pd.DatetimeIndex:
    dates = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            month_days = pd.date_range(f"{year}-{month:02d}-01", periods=31, freq="D")
            month_days = month_days[month_days.month == month]
            fridays = month_days[month_days.weekday == 4]
            dates.append(fridays[2])
    return pd.DatetimeIndex(dates).normalize()


def gate_stage1(row: pd.Series, baseline: pd.Series) -> dict[str, bool]:
    return {
        "gate_cost": bool(row["one_tick_expectancy_r"] > 0 and row["two_tick_expectancy_r"] > 0),
        "gate_effect": bool(row["return_dd"] >= baseline["return_dd"] * 1.15 or (row["max_drawdown_r"] <= baseline["max_drawdown_r"] * 0.80 and row["expectancy_r"] >= baseline["expectancy_r"])),
        "gate_years": bool(row["positive_years"] >= 3 and row["minimum_year_net_r"] >= -5.0),
        "gate_concentration": bool(row["single_year_positive_net_share"] <= 0.70),
        "gate_sample": bool(row["trades"] >= 250 or row["trades"] >= baseline["trades"] * 0.65),
        "gate_paired_mean": bool(row["observed_net_difference_r"] > 0),
    }


def gate_stage2(row: pd.Series, baseline: pd.Series) -> dict[str, bool]:
    return {
        "gate_retention": bool(row["trades"] >= baseline["trades"] * 0.60),
        "gate_cost": bool(row["two_tick_expectancy_r"] > 0),
        "gate_return_dd": bool(row["return_dd"] >= baseline["return_dd"] * 1.15),
        "gate_years": bool(row["positive_years"] >= 3 and row["minimum_year_net_r"] >= -5.0),
        "gate_paired_mean": bool(row["observed_net_difference_r"] > 0),
    }


def event_masks(features: pd.DataFrame) -> dict[str, pd.Series]:
    dates = pd.to_datetime(features["entry_time"]).dt.normalize()
    opex = third_fridays(2022, 2025)
    quarterly = opex[opex.month.isin([3, 6, 9, 12])]
    return {
        "NO_FOMC_DAY": ~dates.isin(FOMC_DATES),
        "NO_CPI_DAY": ~dates.isin(CPI_DATES),
        "NO_NFP_DAY": ~dates.isin(NFP_DATES),
        "NO_MONTHLY_OPEX_DAY": ~dates.isin(opex),
        "NO_QUARTERLY_EXPIRATION_DAY": ~dates.isin(quarterly),
    }


def event_gate(parent: pd.DataFrame, child: pd.DataFrame, summary: pd.Series, parent_summary: pd.Series, changed: pd.DataFrame) -> dict[str, bool]:
    removed = changed.loc[changed["change_type"] == "REMOVED"].copy()
    if removed.empty:
        date_diverse = False
    else:
        removed["entry_date"] = pd.to_datetime(removed["entry_time"]).dt.normalize()
        negative = -removed.loc[removed["pnl_r_parent"] < 0].groupby("entry_date")["pnl_r_parent"].sum()
        date_diverse = bool(len(negative) >= 2 and (negative.max() / negative.sum() <= 0.70 if negative.sum() > 0 else False))
    return {
        "gate_removed": bool(len(removed) >= 8),
        "gate_net": bool(summary["net_r"] > parent_summary["net_r"]),
        "gate_return_dd": bool(summary["return_dd"] > parent_summary["return_dd"]),
        "gate_cost": bool(summary["two_tick_expectancy_r"] >= parent_summary["two_tick_expectancy_r"]),
        "gate_date_diversity": date_diverse,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usa500", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    one = load_proxy(args.usa500)
    gaps = classify_proxy_gaps(one)
    bars = attach_gap_metadata(engine.resample_5m(one), gaps)
    sessions_raw = build_covered_session_table(one, bars, minimum_coverage=USA500_PROXY_SPEC.minimum_range_coverage)
    sessions = sanitize_sessions(sessions_raw, bars, gaps)
    eligible = sessions.loc[~sessions["integrity_range_gap_rejected"]].copy().sort_values(["range_start", "session"])

    broad_cfg = replace(USA500_PROXY_SPEC.strategy_config(name="USA500_CORE_BROAD"), weekdays=(0, 1, 2, 3, 4), sessions=("LONDON_2AM", "NEW_YORK_9AM", "ASIA_7PM"))
    signals, funnel = engine.generate_signals(bars, eligible, broad_cfg)
    cached = simulate_all(one, bars, signals, broad_cfg, gaps)
    features = add_features(one, bars, eligible, signals, broad_cfg)

    calendar_arms = {
        "P0_TUE_FRI_ALL": ((1, 2, 3, 4), ("ASIA_7PM", "LONDON_2AM", "NEW_YORK_9AM")),
        "P1_MON_FRI_ALL": ((0, 1, 2, 3, 4), ("ASIA_7PM", "LONDON_2AM", "NEW_YORK_9AM")),
        "P2_TUE_FRI_NO_ASIA": ((1, 2, 3, 4), ("LONDON_2AM", "NEW_YORK_9AM")),
        "P3_MON_FRI_NO_ASIA": ((0, 1, 2, 3, 4), ("LONDON_2AM", "NEW_YORK_9AM")),
    }
    stage1_trades: dict[str, pd.DataFrame] = {}
    stage1_rows = []
    base_mask = None
    for index, (arm, (weekdays, allowed_sessions)) in enumerate(calendar_arms.items()):
        mask = features["weekday"].isin(weekdays) & features["session"].isin(allowed_sessions)
        trades = sequence(features, cached, mask)
        stage1_trades[arm] = trades
        if arm == "P0_TUE_FRI_ALL":
            base_mask = mask
        row = summarize(trades, arm, eligible_count(eligible, weekdays, allowed_sessions), int(mask.sum()), broad_cfg.tick_size)
        row.update(block_bootstrap(trades, "date", args.iterations, args.seed + 10 + index))
        month = block_bootstrap(trades, "month", args.iterations, args.seed + 20 + index)
        row.update({f"month_{key}": value for key, value in month.items()})
        stage1_rows.append(row)
    stage1 = pd.DataFrame(stage1_rows)
    p0 = stage1.loc[stage1["arm"] == "P0_TUE_FRI_ALL"].iloc[0]
    paired_rows = []
    for index, arm in enumerate(calendar_arms):
        if arm == "P0_TUE_FRI_ALL":
            paired = {"observed_net_difference_r": 0.0, "lo95_net_difference_r": 0.0, "hi95_net_difference_r": 0.0, "prob_net_difference_positive": np.nan}
        else:
            paired = paired_date_bootstrap(stage1_trades[arm], stage1_trades["P0_TUE_FRI_ALL"], args.iterations, args.seed + 100 + index)
        paired_rows.append({"arm": arm, **paired})
    paired_frame = pd.DataFrame(paired_rows)
    stage1 = stage1.merge(paired_frame, on="arm", how="left")
    for index, row in stage1.iterrows():
        flags = gate_stage1(row, p0) if row["arm"] != "P0_TUE_FRI_ALL" else {key: True for key in ("gate_cost", "gate_effect", "gate_years", "gate_concentration", "gate_sample", "gate_paired_mean")}
        for key, value in flags.items():
            stage1.loc[index, key] = value
        stage1.loc[index, "gate_all"] = all(flags.values())
        stage1.loc[index, "uncertainty_class"] = "SUPPORTED" if row["lo95_net_difference_r"] > 0 else "EXPLORATORY" if row["observed_net_difference_r"] > 0 else "NOT_BETTER"
    passing_stage1 = stage1.loc[(stage1["arm"] != "P0_TUE_FRI_ALL") & stage1["gate_all"]]
    selected_calendar = "P0_TUE_FRI_ALL" if passing_stage1.empty else passing_stage1.sort_values(["return_dd", "two_tick_expectancy_r", "net_r"], ascending=False).iloc[0]["arm"]

    weekdays, allowed_sessions = calendar_arms[selected_calendar]
    calendar_mask = features["weekday"].isin(weekdays) & features["session"].isin(allowed_sessions)
    selected_calendar_trades = stage1_trades[selected_calendar]
    selected_calendar_summary = stage1.loc[stage1["arm"] == selected_calendar].iloc[0]

    context_masks = {
        "C0_CALENDAR_BASELINE": calendar_mask,
        "C1_EXCLUDE_COMPRESSED_RANGE": calendar_mask & (features["range_percentile"].isna() | (features["range_percentile"] >= 1 / 3)),
        "C2_EXCLUDE_NEAR_PRIOR_DAY_EXTREME": calendar_mask & (features["directional_extreme_distance_atr"].isna() | (features["directional_extreme_distance_atr"] > 0.25)),
        "C3_PATH_LE_12_BARS": calendar_mask & (features["sweep_to_entry_bars"] <= 12),
        "C4_ENTRY_EXTENSION_LE_0_35R": calendar_mask & (features["entry_extension_r"] <= 0.35),
        "C5_BOS_QUALITY_2_OF_3": calendar_mask & (features["bos_quality_score"] >= 2),
        "C6_CLEAR_TO_TP1": calendar_mask & (features["clearance_r"] >= broad_cfg.tp1_rr),
    }
    context_trades: dict[str, pd.DataFrame] = {}
    context_rows = []
    context_changed = []
    for index, (arm, mask) in enumerate(context_masks.items()):
        trades = sequence(features, cached, mask)
        context_trades[arm] = trades
        row = summarize(trades, arm, eligible_count(eligible, weekdays, allowed_sessions), int(mask.sum()), broad_cfg.tick_size)
        paired = {"observed_net_difference_r": 0.0, "lo95_net_difference_r": 0.0, "hi95_net_difference_r": 0.0, "prob_net_difference_positive": np.nan} if arm == "C0_CALENDAR_BASELINE" else paired_date_bootstrap(trades, selected_calendar_trades, args.iterations, args.seed + 200 + index)
        row.update(paired)
        row.update(block_bootstrap(trades, "date", args.iterations, args.seed + 300 + index))
        context_rows.append(row)
        if arm != "C0_CALENDAR_BASELINE":
            context_changed.append(changed_attribution(selected_calendar_trades, trades, f"{selected_calendar}->{arm}"))
    context = pd.DataFrame(context_rows)
    baseline_context = context.loc[context["arm"] == "C0_CALENDAR_BASELINE"].iloc[0]
    for index, row in context.iterrows():
        flags = gate_stage2(row, baseline_context) if row["arm"] != "C0_CALENDAR_BASELINE" else {key: True for key in ("gate_retention", "gate_cost", "gate_return_dd", "gate_years", "gate_paired_mean")}
        for key, value in flags.items():
            context.loc[index, key] = value
        context.loc[index, "gate_all"] = all(flags.values())
        context.loc[index, "uncertainty_class"] = "SUPPORTED" if row["lo95_net_difference_r"] > 0 else "EXPLORATORY" if row["observed_net_difference_r"] > 0 else "NOT_BETTER"
    passing_context = context.loc[(context["arm"] != "C0_CALENDAR_BASELINE") & context["gate_all"]]
    selected_context = "C0_CALENDAR_BASELINE" if passing_context.empty else passing_context.sort_values(["return_dd", "two_tick_expectancy_r", "net_r"], ascending=False).iloc[0]["arm"]

    selected_context_mask = context_masks[selected_context]
    selected_context_trades = context_trades[selected_context]
    selected_context_summary = context.loc[context["arm"] == selected_context].iloc[0]

    events = event_masks(features)
    event_rows = []
    event_trades: dict[str, pd.DataFrame] = {"E0_CONTEXT_BASELINE": selected_context_trades}
    event_changes = []
    base_event_summary = summarize(selected_context_trades, "E0_CONTEXT_BASELINE", eligible_count(eligible, weekdays, allowed_sessions), int(selected_context_mask.sum()), broad_cfg.tick_size)
    base_event_summary.update({"observed_net_difference_r": 0.0, "lo95_net_difference_r": 0.0, "hi95_net_difference_r": 0.0, "prob_net_difference_positive": np.nan})
    event_rows.append(base_event_summary)
    for index, (event_name, event_mask) in enumerate(events.items()):
        arm = f"E_{event_name}"
        trades = sequence(features, cached, selected_context_mask & event_mask)
        event_trades[arm] = trades
        summary = summarize(trades, arm, eligible_count(eligible, weekdays, allowed_sessions), int((selected_context_mask & event_mask).sum()), broad_cfg.tick_size)
        summary.update(paired_date_bootstrap(trades, selected_context_trades, args.iterations, args.seed + 400 + index))
        changed = changed_attribution(selected_context_trades, trades, f"{selected_context}->{arm}")
        event_changes.append(changed)
        flags = event_gate(selected_context_trades, trades, pd.Series(summary), pd.Series(base_event_summary), changed)
        summary.update(flags)
        summary["gate_all"] = all(flags.values())
        event_rows.append(summary)
    events_frame = pd.DataFrame(event_rows)
    passing_events = events_frame.loc[(events_frame["arm"] != "E0_CONTEXT_BASELINE") & events_frame["gate_all"].fillna(False)]
    selected_event = "E0_CONTEXT_BASELINE" if passing_events.empty else passing_events.sort_values(["return_dd", "two_tick_expectancy_r", "net_r"], ascending=False).iloc[0]["arm"]

    # Outputs.
    stage1.to_csv(args.out / "stage1_calendar_factorial.csv", index=False)
    paired_frame.to_csv(args.out / "stage1_paired_bootstrap.csv", index=False)
    context.to_csv(args.out / "stage2_context_candidates.csv", index=False)
    events_frame.to_csv(args.out / "stage3_event_candidates.csv", index=False)
    features.to_csv(args.out / "signal_features.csv.gz", index=False, compression="gzip")
    pd.concat(context_changed, ignore_index=True).to_csv(args.out / "stage2_changed_trade_attribution.csv", index=False)
    pd.concat(event_changes, ignore_index=True).to_csv(args.out / "stage3_changed_trade_attribution.csv", index=False)
    for arm, trades in {**stage1_trades, **context_trades, **event_trades}.items():
        trades.to_csv(args.out / f"{arm}__trades.csv", index=False)

    controls_path = Path(__file__).resolve().parents[1] / "results" / "2026-07-22" / "nq_usa500_parallel_summary.csv"
    controls = pd.read_csv(controls_path).to_dict(orient="records") if controls_path.exists() else []
    decision = {
        "study_id": "DTR-USA500-WP-20260723-20",
        "preregistration_commit": "f5100c3b43b249c8b24be6355e9b73b9826c84b2",
        "data_sha256": USA500_PROXY_SPEC.source_sha256,
        "data_rows": len(one),
        "active_start_et": str(one["timestamp"].min()),
        "active_end_et": str(one["timestamp"].max()),
        "eligible_sessions": len(eligible),
        "signals": len(features),
        "simulated_signals": len(cached),
        "funnel": funnel.as_dict(),
        "selected_calendar": selected_calendar,
        "selected_calendar_uncertainty": str(stage1.loc[stage1["arm"] == selected_calendar, "uncertainty_class"].iloc[0]),
        "selected_context": selected_context,
        "selected_context_uncertainty": str(context.loc[context["arm"] == selected_context, "uncertainty_class"].iloc[0]),
        "selected_event": selected_event,
        "final_candidate": selected_event if selected_event != "E0_CONTEXT_BASELINE" else selected_context,
        "classification": "EXPLORATORY_RETROSPECTIVE_USA500_CANDIDATE",
        "nq_transfer_controls": controls,
        "no_deployment_authorization": True,
    }
    (args.out / "decision.json").write_text(json.dumps(decision, indent=2, default=str), encoding="utf-8")

    hashes = {}
    for path in sorted(args.out.iterdir()):
        if path.is_file() and path.name != "artifact_hashes.json":
            hashes[path.name] = sha256(path)
    (args.out / "artifact_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(json.dumps(decision, indent=2))
    print("\nSTAGE1\n", stage1[["arm", "trades", "net_r", "expectancy_r", "two_tick_expectancy_r", "max_drawdown_r", "return_dd", "gate_all", "uncertainty_class"]].to_string(index=False))
    print("\nSTAGE2\n", context[["arm", "trades", "net_r", "expectancy_r", "two_tick_expectancy_r", "max_drawdown_r", "return_dd", "gate_all", "uncertainty_class"]].to_string(index=False))
    print("\nSTAGE3\n", events_frame[["arm", "trades", "net_r", "expectancy_r", "two_tick_expectancy_r", "max_drawdown_r", "return_dd", "gate_all"]].to_string(index=False))


if __name__ == "__main__":
    main()
