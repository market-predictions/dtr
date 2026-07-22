from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from .engine import StrategyConfig, metrics

InstrumentName = Literal["NQ", "USA500_PROXY"]

# Frozen timing-corrected real-time windows. NQ source labels are shifted to bar-open
# before these windows are applied; Dukascopy labels are already bar-open UTC labels.
SESSION_SPECS = {
    "LONDON_2AM": ((1, 11), (2, 12), (6, 0)),
    "NEW_YORK_9AM": ((8, 11), (9, 12), (14, 0)),
    "ASIA_7PM": ((19, 0), (20, 1), (23, 45)),
}

PRIMARY_START_ET = pd.Timestamp("2022-12-26 18:00:00")
PRIMARY_END_ET = pd.Timestamp("2025-12-10 23:58:00")


@dataclass(frozen=True)
class InstrumentSpec:
    name: InstrumentName
    tick_size: float
    point_value: float
    commission_per_side: float
    source_sha256: str
    source_classification: str
    minimum_range_coverage: float

    def strategy_config(self, *, name: str) -> StrategyConfig:
        return StrategyConfig(
            name=name,
            sessions=("LONDON_2AM", "NEW_YORK_9AM", "ASIA_7PM"),
            weekdays=(1, 2, 3, 4),
            min_sweep_range_pct=0.04,
            min_sweep_ticks=1,
            valid_sweep_threshold=1,
            ideal_sweep_max_pct=0.60,
            too_deep_sweep_pct=1.20,
            volume_expand_mult=1.00,
            atr_expand_mult=1.00,
            reaction_bars=10,
            pivot_len=2,
            pivot_min_pct=0.04,
            break_mode="wick",
            break_buffer_pct=0.0,
            break_atr_frac=0.0,
            impulse_mult=0.90,
            require_impulse=True,
            acceptance_bars=2,
            entry_mode="break_close",
            retest_band_pct=0.05,
            signal_window_bars=25,
            max_bars_from_sweep=40,
            trend_filter="nontrend_er",
            er_length=20,
            er_max=0.35,
            adx_max=22.0,
            stop_buffer_ticks=8,
            stop_atr_frac=0.05,
            tp1_rr=1.25,
            runner_rr=4.0,
            tp1_fraction=0.50,
            move_runner_to_be=True,
            time_close_mode="everyday",
            time_close_hour=16,
            time_close_minute=0,
            max_hold_bars=96,
            slippage_ticks_each_side=1.0,
            commission_per_side=self.commission_per_side,
            tick_size=self.tick_size,
            point_value=self.point_value,
            conservative_intrabar=True,
        )


NQ_SPEC = InstrumentSpec(
    name="NQ",
    tick_size=0.25,
    point_value=20.0,
    commission_per_side=2.25,
    source_sha256="8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc",
    source_classification="NQ futures research archive",
    minimum_range_coverage=20 / 61,
)

USA500_PROXY_SPEC = InstrumentSpec(
    name="USA500_PROXY",
    tick_size=0.25,
    point_value=50.0,
    commission_per_side=2.25,
    source_sha256="199d63e6f284eb1ffb93003e9020bf2852f5d96bf78f0efe50c3bdd09c11a47b",
    source_classification="Dukascopy bid-CFD S&P 500 proxy with ES-equivalent economics",
    minimum_range_coverage=0.95,
)


def load_usa500_proxy(path: str | Path) -> pd.DataFrame:
    """Load qualified active Dukascopy candles and normalize to bar-open ET.

    The input contains no filled flat rows. Timestamps are epoch milliseconds in UTC.
    Timezone conversion occurs before timezone information is removed, preserving DST.
    """

    frame = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"USA500 proxy is missing columns: {sorted(missing)}")
    utc = pd.to_datetime(frame["timestamp"], unit="ms", utc=True, errors="raise")
    frame["timestamp"] = utc.dt.tz_convert("America/New_York").dt.tz_localize(None)
    frame = (
        frame.loc[
            (frame["timestamp"] >= PRIMARY_START_ET)
            & (frame["timestamp"] <= PRIMARY_END_ET)
        ]
        .sort_values("timestamp")
        .drop_duplicates("timestamp")
        .reset_index(drop=True)
    )
    if frame.empty:
        raise ValueError("USA500 proxy has no rows in the frozen comparison period")
    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("USA500 proxy timestamps are not increasing")
    if not (
        (frame["high"] >= frame[["open", "close", "low"]].max(axis=1))
        & (frame["low"] <= frame[["open", "close", "high"]].min(axis=1))
    ).all():
        raise ValueError("USA500 proxy OHLC integrity failed")
    return frame


def classify_proxy_gaps(frame: pd.DataFrame) -> pd.DataFrame:
    """Classify proxy quote absences separately from structural closures.

    Short intervals of at most five minutes are treated as inactive quotation periods,
    not inferred price jumps. Longer unscheduled intervals reset strategy state and are
    unsafe for an open trade. Scheduled 18:00 ET reopens reset state but are not treated
    as missing-price liquidations.
    """

    timestamps = pd.to_datetime(frame["timestamp"], errors="raise").sort_values()
    previous = timestamps.shift(1)
    minutes = ((timestamps - previous).dt.total_seconds() / 60).round().astype("Int64")
    selected = minutes > 1
    gaps = pd.DataFrame(
        {
            "previous_timestamp": previous[selected],
            "current_timestamp": timestamps[selected],
            "gap_minutes": minutes[selected].astype(int),
        }
    ).reset_index(drop=True)

    def label(previous_ts: pd.Timestamp, current_ts: pd.Timestamp, gap: int) -> str:
        if current_ts.hour == 18 and current_ts.minute == 0 and gap >= 60:
            if previous_ts.weekday() == 4 and current_ts.weekday() in (6, 0) and gap > 2_000:
                return "weekend_or_holiday_closure"
            return "daily_maintenance_or_holiday"
        if gap <= 5:
            return "short_quote_absence"
        if gap <= 15:
            return "medium_quote_absence"
        return "unclassified_long_gap"

    if gaps.empty:
        gaps["classification"] = pd.Series(dtype="object")
        gaps["reset_strategy_state"] = pd.Series(dtype="bool")
        gaps["reject_trade_bridge"] = pd.Series(dtype="bool")
        return gaps

    gaps["classification"] = [
        label(previous_ts, current_ts, int(gap))
        for previous_ts, current_ts, gap in gaps.itertuples(index=False, name=None)
    ]
    gaps["reset_strategy_state"] = gaps["classification"] != "short_quote_absence"
    gaps["reject_trade_bridge"] = gaps["classification"].isin(
        {"medium_quote_absence", "unclassified_long_gap"}
    )
    return gaps


def build_covered_session_table(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    *,
    minimum_coverage: float,
) -> pd.DataFrame:
    """Build frozen session ranges with an explicit active-minute coverage gate."""

    one_times = one_minute["timestamp"].to_numpy(dtype="datetime64[ns]")
    one_high = one_minute["high"].to_numpy(float)
    one_low = one_minute["low"].to_numpy(float)
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    days = pd.date_range(
        one_minute["timestamp"].min().normalize(),
        one_minute["timestamp"].max().normalize(),
        freq="D",
    )
    rows: list[dict[str, object]] = []
    for day in days:
        for session, (start_hm, end_hm, break_hm) in SESSION_SPECS.items():
            start = day + pd.Timedelta(hours=start_hm[0], minutes=start_hm[1])
            end = day + pd.Timedelta(hours=end_hm[0], minutes=end_hm[1])
            break_end = day + pd.Timedelta(hours=break_hm[0], minutes=break_hm[1])
            if break_end <= end:
                break_end += pd.Timedelta(days=1)
            j0 = int(np.searchsorted(one_times, np.datetime64(start), side="left"))
            j1 = int(np.searchsorted(one_times, np.datetime64(end), side="left"))
            expected = int((end - start).total_seconds() // 60)
            active = j1 - j0
            if active < int(np.ceil(expected * minimum_coverage)):
                continue
            i0 = int(np.searchsorted(bar_times, np.datetime64(end), side="left"))
            i1 = int(np.searchsorted(bar_times, np.datetime64(break_end), side="left"))
            if i0 >= len(bars) or i1 <= i0:
                continue
            range_high = float(np.max(one_high[j0:j1]))
            range_low = float(np.min(one_low[j0:j1]))
            rows.append(
                {
                    "session": session,
                    "session_date": day,
                    "range_start": start,
                    "range_end": end,
                    "break_end": break_end,
                    "range_high": range_high,
                    "range_low": range_low,
                    "range_size": range_high - range_low,
                    "post_start_index": i0,
                    "post_end_index": min(i1, len(bars)),
                    "weekday": int(day.weekday()),
                    "active_range_minutes": active,
                    "expected_range_minutes": expected,
                    "range_coverage": active / expected,
                }
            )
    return pd.DataFrame(rows)


def e6_mask(signal_features: pd.DataFrame) -> pd.Series:
    """Apply the frozen E6 prior-day directional-extreme rule."""

    required = {
        "direction",
        "range_high",
        "range_low",
        "prev_d1_high",
        "prev_d1_low",
        "d1_atr20",
    }
    missing = required.difference(signal_features.columns)
    if missing:
        raise ValueError(f"E6 signal features missing columns: {sorted(missing)}")
    distance = np.where(
        signal_features["direction"] > 0,
        (signal_features["range_low"] - signal_features["prev_d1_low"]).abs(),
        (signal_features["range_high"] - signal_features["prev_d1_high"]).abs(),
    ) / signal_features["d1_atr20"]
    distance = pd.Series(distance, index=signal_features.index, dtype=float)
    return distance.isna() | (distance > 0.25)


def no_fomc_mask(signal_features: pd.DataFrame, fomc_dates: set[pd.Timestamp]) -> pd.Series:
    entry_dates = pd.to_datetime(signal_features["entry_time"]).dt.normalize()
    return ~entry_dates.isin(pd.DatetimeIndex(fomc_dates).normalize())


def cost_stress_expectancy(
    trades: pd.DataFrame,
    *,
    total_ticks_each_side: float,
    tick_size: float,
) -> float:
    """Convert additional ticks beyond the published one-tick case into R."""

    if trades.empty:
        return np.nan
    risk_points = (trades["entry_price"] - trades["stop_price"]).abs().to_numpy(float)
    additional_ticks = total_ticks_each_side - 1.0
    adjusted = trades["pnl_r"].to_numpy(float) - (
        2.0 * additional_ticks * tick_size / risk_points
    )
    return float(np.mean(adjusted))


def summarize_arm(
    trades: pd.DataFrame,
    *,
    instrument: InstrumentName,
    arm: str,
    eligible_sessions: int,
    candidate_signals: int,
    tick_size: float,
) -> dict[str, object]:
    result: dict[str, object] = {
        "instrument": instrument,
        "arm": arm,
        "eligible_session_opportunities": eligible_sessions,
        "candidate_signals": candidate_signals,
        "trades_per_100_eligible_sessions": (
            100.0 * len(trades) / eligible_sessions if eligible_sessions else np.nan
        ),
        **metrics(trades),
        "one_tick_expectancy_r": metrics(trades)["expectancy_r"],
        "two_tick_expectancy_r": cost_stress_expectancy(
            trades, total_ticks_each_side=2.0, tick_size=tick_size
        ),
        "four_tick_expectancy_r": cost_stress_expectancy(
            trades, total_ticks_each_side=4.0, tick_size=tick_size
        ),
    }
    entry_year = pd.to_datetime(trades["entry_time"]).dt.year if not trades.empty else pd.Series(dtype=int)
    for year in (2023, 2024, 2025):
        result[f"net_{year}"] = float(trades.loc[entry_year == year, "pnl_r"].sum())
    return result


def classify_proxy_replication(summary: pd.Series | dict[str, object]) -> str:
    row = pd.Series(summary)
    if float(row["net_r"]) <= 0 or float(row["expectancy_r"]) <= 0:
        return "NO_REPLICATION"
    positive_years = sum(float(row[f"net_{year}"]) > 0 for year in (2023, 2024, 2025))
    if (
        float(row["profit_factor"]) > 1
        and positive_years >= 2
        and float(row["two_tick_expectancy_r"]) > 0
    ):
        return "DIRECTIONAL_REPLICATION_SUPPORTED"
    return "PARTIAL_COST_FRAGILE_REPLICATION"


def date_block_bootstrap(
    trades: pd.DataFrame,
    *,
    iterations: int = 20_000,
    seed: int = 20260722,
) -> dict[str, float | int]:
    if trades.empty:
        return {
            "blocks": 0,
            "observed_expectancy_r": np.nan,
            "lo95_expectancy_r": np.nan,
            "hi95_expectancy_r": np.nan,
            "prob_expectancy_positive": np.nan,
        }
    work = trades.copy()
    work["block"] = pd.to_datetime(work["session_date"]).dt.normalize()
    blocks = [group["pnl_r"].to_numpy(float) for _, group in work.groupby("block", sort=True)]
    rng = np.random.default_rng(seed)
    means = np.empty(iterations)
    for iteration in range(iterations):
        selected = rng.integers(0, len(blocks), size=len(blocks))
        values = np.concatenate([blocks[index] for index in selected])
        means[iteration] = values.mean()
    return {
        "blocks": len(blocks),
        "observed_expectancy_r": float(work["pnl_r"].mean()),
        "lo95_expectancy_r": float(np.quantile(means, 0.025)),
        "hi95_expectancy_r": float(np.quantile(means, 0.975)),
        "prob_expectancy_positive": float(np.mean(means > 0)),
    }
