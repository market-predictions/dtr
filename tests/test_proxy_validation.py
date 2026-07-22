from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.research.proxy_validation import (
    classify_proxy_oos,
    clean_dukascopy_candles,
    paired_date_delta,
)


def test_clean_dukascopy_candles_removes_only_flat_zero_volume_rows() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": [
                pd.Timestamp("2026-01-02 14:00", tz="UTC").timestamp() * 1000,
                pd.Timestamp("2026-01-02 14:01", tz="UTC").timestamp() * 1000,
            ],
            "open": [100.0, 100.0],
            "high": [100.0, 101.0],
            "low": [100.0, 99.0],
            "close": [100.0, 100.5],
            "volume": [0.0, 4.0],
        }
    )
    cleaned, audit = clean_dukascopy_candles(frame)
    assert len(cleaned) == 1
    assert audit["removed_flat_zero_volume_rows"] == 1
    assert cleaned.iloc[0]["timestamp"] == pd.Timestamp("2026-01-02 09:01")


def test_paired_date_delta_preserves_observed_portfolio_difference() -> None:
    control = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(["2026-01-02", "2026-01-05"]),
            "pnl_r": [1.0, -0.5],
        }
    )
    candidate = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(["2026-01-02", "2026-01-06"]),
            "pnl_r": [0.5, 1.0],
        }
    )
    result = paired_date_delta(control, candidate, iterations=1000, seed=7)
    assert np.isclose(result["observed_delta_r"], 1.0)
    assert result["blocks"] == 3


def test_proxy_oos_classification_enforces_comparability_first() -> None:
    common = {
        "unfiltered_trades": 50,
        "unfiltered_net_r": 5.0,
        "unfiltered_expectancy_r": 0.1,
        "unfiltered_two_tick_expectancy_r": 0.05,
    }
    assert (
        classify_proxy_oos(
            five_minute_correlation=0.69,
            direction_agreement=0.8,
            **common,
        )
        == "PROXY_NOT_COMPARABLE"
    )
    assert (
        classify_proxy_oos(
            five_minute_correlation=0.9,
            direction_agreement=0.8,
            **common,
        )
        == "SUPPORTS_PROXY_CONTINUATION"
    )
