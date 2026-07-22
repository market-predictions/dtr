from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def clean_dukascopy_candles(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Remove synthetic flat placeholders and normalize UTC epoch milliseconds to ET."""

    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Dukascopy candles missing columns: {sorted(missing)}")
    raw_rows = len(frame)
    flat = (
        frame["volume"].fillna(0).eq(0)
        & frame["open"].eq(frame["high"])
        & frame["open"].eq(frame["low"])
        & frame["open"].eq(frame["close"])
    )
    work = frame.loc[~flat].copy()
    utc = pd.to_datetime(work["timestamp"], unit="ms", utc=True, errors="raise")
    work["timestamp"] = utc.dt.tz_convert("America/New_York").dt.tz_localize(None)
    duplicates = int(work["timestamp"].duplicated().sum())
    work = (
        work.sort_values("timestamp")
        .drop_duplicates("timestamp", keep="last")
        .reset_index(drop=True)
    )
    ohlc_ok = bool(
        (work["high"] >= work[["open", "close", "low"]].max(axis=1)).all()
        and (work["low"] <= work[["open", "close", "high"]].min(axis=1)).all()
    )
    if work.empty or not work["timestamp"].is_monotonic_increasing or not ohlc_ok:
        raise ValueError("Dukascopy candle structural qualification failed")
    audit: dict[str, Any] = {
        "raw_rows": raw_rows,
        "removed_flat_zero_volume_rows": int(flat.sum()),
        "active_rows": len(work),
        "duplicate_rows_removed": duplicates,
        "strictly_increasing": True,
        "ohlc_integrity_pass": True,
        "first_et": str(work["timestamp"].min()),
        "last_et": str(work["timestamp"].max()),
    }
    return work, audit


def paired_date_delta(
    control: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    iterations: int,
    seed: int,
) -> dict[str, float | int]:
    """Bootstrap candidate-minus-control daily portfolio return deltas."""

    def daily(frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(dtype=float)
        dates = pd.to_datetime(frame["entry_time"]).dt.normalize()
        return frame.groupby(dates)["pnl_r"].sum()

    left = daily(control)
    right = daily(candidate)
    index = left.index.union(right.index).sort_values()
    values = right.reindex(index, fill_value=0).to_numpy(float) - left.reindex(
        index, fill_value=0
    ).to_numpy(float)
    if not len(values):
        return {
            "blocks": 0,
            "observed_delta_r": 0.0,
            "lo95_delta_r": np.nan,
            "hi95_delta_r": np.nan,
            "prob_delta_positive": np.nan,
        }
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(iterations, len(values)), replace=True).sum(axis=1)
    return {
        "blocks": len(values),
        "observed_delta_r": float(values.sum()),
        "lo95_delta_r": float(np.quantile(samples, 0.025)),
        "hi95_delta_r": float(np.quantile(samples, 0.975)),
        "prob_delta_positive": float(np.mean(samples > 0)),
    }


def classify_proxy_oos(
    *,
    five_minute_correlation: float,
    direction_agreement: float,
    unfiltered_trades: int,
    unfiltered_net_r: float,
    unfiltered_expectancy_r: float,
    unfiltered_two_tick_expectancy_r: float,
) -> str:
    """Apply the frozen proxy comparability and 2026 OOS decision contract."""

    if five_minute_correlation < 0.70 or direction_agreement < 0.50:
        return "PROXY_NOT_COMPARABLE"
    if (
        unfiltered_trades >= 30
        and unfiltered_expectancy_r > 0
        and unfiltered_two_tick_expectancy_r > 0
    ):
        return "SUPPORTS_PROXY_CONTINUATION"
    if (
        unfiltered_trades >= 30
        and unfiltered_expectancy_r < 0
        and unfiltered_net_r < 0
    ):
        return "CHALLENGES_MODEL"
    return "AMBIGUOUS_EXTEND_FORWARD"
