from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from .backtest import simulate
from .config import InstrumentSpec, SequenceConfig
from .reporting import summarize


def _session_label(timestamp: pd.Timestamp) -> str:
    clock = timestamp.time()
    return "RTH" if time(9, 30) <= clock < time(16, 0) else "OVERNIGHT"


def delay_events(events: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if minutes < 0:
        raise ValueError("Delay cannot be negative")
    delayed = events.copy()
    if not delayed.empty and minutes:
        delayed["signal_time"] = pd.to_datetime(delayed["signal_time"]) + pd.Timedelta(
            minutes=minutes
        )
    return delayed


def evaluate_trades(
    trades: pd.DataFrame,
    *,
    instrument: str,
    arm_id: str,
    source_start: pd.Timestamp,
    source_end: pd.Timestamp,
) -> dict[str, object]:
    result = summarize(trades, instrument=instrument, arm_id=arm_id)
    if trades.empty:
        result.update(
            {
                "exposure_hours": 0.0,
                "market_exposure_fraction": 0.0,
                "net_r_per_1000_exposure_hours": np.nan,
                "largest_positive_year_share": np.nan,
                "largest_positive_month_share": np.nan,
            }
        )
        return result

    entry = pd.to_datetime(trades["entry_time"])
    exit_ = pd.to_datetime(trades["exit_time"])
    exposure_hours = float((exit_ - entry).dt.total_seconds().sum() / 3600)
    span_hours = max((source_end - source_start).total_seconds() / 3600, 1.0)
    yearly = trades.assign(year=entry.dt.year).groupby("year")["pnl_r"].sum()
    monthly = trades.assign(month=entry.dt.to_period("M")).groupby("month")["pnl_r"].sum()

    def positive_share(series: pd.Series) -> float:
        positive = series.clip(lower=0)
        total = float(positive.sum())
        return float(positive.max() / total) if total > 0 else np.nan

    result.update(
        {
            "exposure_hours": exposure_hours,
            "market_exposure_fraction": exposure_hours / span_hours,
            "net_r_per_1000_exposure_hours": (
                float(result["net_r"]) / exposure_hours * 1000
                if exposure_hours > 0
                else np.nan
            ),
            "largest_positive_year_share": positive_share(yearly),
            "largest_positive_month_share": positive_share(monthly),
        }
    )
    return result


def session_attribution(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    work = trades.copy()
    work["session_bucket"] = pd.to_datetime(work["entry_time"]).map(_session_label)
    rows = []
    for label, group in work.groupby("session_bucket", sort=True):
        summary = summarize(
            group,
            instrument=str(group["instrument"].iloc[0]),
            arm_id=label,
        )
        rows.append({"session_bucket": label, **summary})
    return pd.DataFrame(rows)


def expanding_year_folds(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    years = sorted(pd.to_datetime(trades["entry_time"]).dt.year.unique())
    rows = []
    for test_year in years[1:]:
        test = trades.loc[pd.to_datetime(trades["entry_time"]).dt.year == test_year]
        summary = summarize(
            test,
            instrument=str(trades["instrument"].iloc[0]),
            arm_id=str(test_year),
        )
        rows.append(
            {
                "train_through_year": int(test_year) - 1,
                "test_year": int(test_year),
                **summary,
            }
        )
    return pd.DataFrame(rows)


def run_scenario(
    *,
    one_minute: pd.DataFrame,
    events: pd.DataFrame,
    management_events: pd.DataFrame,
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> pd.DataFrame:
    return simulate(one_minute, events, management_events, spec, config)
