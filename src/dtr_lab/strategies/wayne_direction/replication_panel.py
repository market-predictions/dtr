from __future__ import annotations

import calendar
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from .calendar import build_new_york_daily_bars, build_new_york_h4_bars
from .data import REPLICATION_PAIRS, midpoint_minutes

PIP_SIZES = {
    "EURGBP": 0.0001,
    "EURJPY": 0.01,
    "GBPJPY": 0.01,
    "NZDUSD": 0.0001,
}


@dataclass(frozen=True)
class ReplicationQualityThresholds:
    start_year: int = 2015
    end_year: int = 2021
    min_active_fraction: float = 0.65
    max_active_fraction: float = 0.76
    min_full_daily_fraction: float = 0.90
    min_full_h4_fraction: float = 0.90
    max_median_spread_pips: float = 3.0
    max_p95_spread_pips: float = 8.0
    max_p99_spread_pips: float = 20.0


DEFAULT_THRESHOLDS = ReplicationQualityThresholds()


def expected_calendar_minutes(start_year: int, end_year: int) -> int:
    if end_year < start_year:
        raise ValueError("end_year must not precede start_year")
    return sum(
        (366 if calendar.isleap(year) else 365) * 24 * 60
        for year in range(start_year, end_year + 1)
    )


def _quantile(series: pd.Series, probability: float) -> float:
    if series.empty:
        return float("nan")
    return float(series.quantile(probability))


def annual_spread_quantiles(
    active_spread_pips: pd.Series,
    year: int,
) -> dict[str, float]:
    if not isinstance(active_spread_pips.index, pd.DatetimeIndex):
        raise ValueError("spread series must use a DatetimeIndex")
    annual = active_spread_pips.loc[active_spread_pips.index.year == year]
    return {
        "spread_median_pips": _quantile(annual, 0.50),
        "spread_p95_pips": _quantile(annual, 0.95),
        "spread_p99_pips": _quantile(annual, 0.99),
    }


def _invalid_ohlc_rows(quotes: pd.DataFrame, side: str) -> int:
    active = quotes[f"is_active_quote_{side}"].eq(1)
    high = quotes[f"high_{side}"].astype(float)
    low = quotes[f"low_{side}"].astype(float)
    open_ = quotes[f"open_{side}"].astype(float)
    close = quotes[f"close_{side}"].astype(float)
    invalid = (
        ~np.isfinite(high)
        | ~np.isfinite(low)
        | ~np.isfinite(open_)
        | ~np.isfinite(close)
        | high.lt(low)
        | high.lt(open_)
        | high.lt(close)
        | low.gt(open_)
        | low.gt(close)
        | low.le(0.0)
    )
    return int((active & invalid).sum())


def evaluate_quality_metrics(
    metrics: dict[str, Any],
    thresholds: ReplicationQualityThresholds = DEFAULT_THRESHOLDS,
) -> dict[str, bool]:
    gates = {
        "candidate_is_frozen": metrics["instrument"] in REPLICATION_PAIRS,
        "complete_year_set": metrics["years"]
        == list(range(thresholds.start_year, thresholds.end_year + 1)),
        "complete_calendar_rows": metrics["source_minutes"]
        == expected_calendar_minutes(thresholds.start_year, thresholds.end_year),
        "bid_ask_active_match": metrics["active_mismatch_rows"] == 0,
        "valid_active_ohlc": metrics["invalid_active_ohlc_rows"] == 0,
        "valid_active_spreads": metrics["invalid_active_spread_rows"] == 0,
        "plausible_active_fraction": thresholds.min_active_fraction
        <= metrics["active_fraction"]
        <= thresholds.max_active_fraction,
        "daily_bar_coverage": metrics["full_daily_fraction"]
        >= thresholds.min_full_daily_fraction,
        "h4_bar_coverage": metrics["full_h4_fraction"]
        >= thresholds.min_full_h4_fraction,
        "median_spread_gate": metrics["spread_median_pips"]
        <= thresholds.max_median_spread_pips,
        "p95_spread_gate": metrics["spread_p95_pips"]
        <= thresholds.max_p95_spread_pips,
        "p99_spread_gate": metrics["spread_p99_pips"]
        <= thresholds.max_p99_spread_pips,
    }
    return gates


def build_pair_quality_summary(
    quotes: pd.DataFrame,
    symbol: str,
    thresholds: ReplicationQualityThresholds = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    symbol = symbol.upper()
    if symbol not in REPLICATION_PAIRS:
        raise ValueError(f"unsupported replication candidate: {symbol}")
    if not isinstance(quotes.index, pd.DatetimeIndex) or quotes.index.tz is None:
        raise ValueError("quotes must use a timezone-aware DatetimeIndex")
    if quotes.index.has_duplicates or not quotes.index.is_monotonic_increasing:
        raise ValueError("quotes must have unique sorted timestamps")

    expected_years = list(range(thresholds.start_year, thresholds.end_year + 1))
    years = sorted(int(year) for year in quotes.index.year.unique())
    bid_active = quotes["is_active_quote_bid"].eq(1)
    ask_active = quotes["is_active_quote_ask"].eq(1)
    both_active = bid_active & ask_active
    active_mismatch = bid_active ^ ask_active

    spread = quotes["close_ask"].astype(float) - quotes["close_bid"].astype(float)
    invalid_spread = both_active & (~np.isfinite(spread) | spread.lt(0.0))
    active_spread_pips = spread.loc[both_active & ~invalid_spread] / PIP_SIZES[symbol]

    minutes = midpoint_minutes(quotes)
    daily = build_new_york_daily_bars(minutes, active_column="active")
    h4 = build_new_york_h4_bars(minutes, active_column="active")

    observed_daily = daily.loc[daily["active_minutes"].ge(600)]
    observed_h4 = h4.loc[h4["active_minutes"].ge(60)]
    full_daily = observed_daily["active_minutes"].ge(1200)
    full_h4 = observed_h4["active_minutes"].ge(180)

    annual_rows: list[dict[str, Any]] = []
    for year in expected_years:
        mask = quotes.index.year == year
        annual_rows.append(
            {
                "year": year,
                "source_minutes": int(mask.sum()),
                "active_minutes": int(both_active.loc[mask].sum()),
                "active_fraction": float(both_active.loc[mask].mean()),
                **annual_spread_quantiles(active_spread_pips, year),
            }
        )

    metrics: dict[str, Any] = {
        "instrument": symbol,
        "years": years,
        "source_minutes": int(len(quotes)),
        "expected_source_minutes": expected_calendar_minutes(
            thresholds.start_year,
            thresholds.end_year,
        ),
        "active_minutes": int(both_active.sum()),
        "active_fraction": float(both_active.mean()),
        "active_mismatch_rows": int(active_mismatch.sum()),
        "invalid_active_ohlc_rows": _invalid_ohlc_rows(quotes, "bid")
        + _invalid_ohlc_rows(quotes, "ask"),
        "invalid_active_spread_rows": int(invalid_spread.sum()),
        "spread_median_pips": _quantile(active_spread_pips, 0.50),
        "spread_p95_pips": _quantile(active_spread_pips, 0.95),
        "spread_p99_pips": _quantile(active_spread_pips, 0.99),
        "observed_daily_bars": int(len(observed_daily)),
        "full_daily_bars": int(full_daily.sum()),
        "full_daily_fraction": float(full_daily.mean()),
        "daily_active_minutes_p10": _quantile(observed_daily["active_minutes"], 0.10),
        "daily_active_minutes_median": _quantile(
            observed_daily["active_minutes"],
            0.50,
        ),
        "observed_h4_bars": int(len(observed_h4)),
        "full_h4_bars": int(full_h4.sum()),
        "full_h4_fraction": float(full_h4.mean()),
        "h4_active_minutes_p10": _quantile(observed_h4["active_minutes"], 0.10),
        "h4_active_minutes_median": _quantile(observed_h4["active_minutes"], 0.50),
        "annual": annual_rows,
        "thresholds": asdict(thresholds),
    }
    gates = evaluate_quality_metrics(metrics, thresholds)
    metrics["gates"] = gates
    metrics["qualified"] = all(gates.values())
    return metrics
