from __future__ import annotations

import pandas as pd

from dtr_lab.data import audit_market_data, resample_ohlcv


def _sample_frame() -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-02 09:30", periods=10, freq="1min")
    return pd.DataFrame(
        {
            "timestamp ET": timestamps.strftime("%m/%d/%Y %H:%M"),
            "timestamp_et": timestamps,
            "open": [100.0 + i for i in range(10)],
            "high": [100.5 + i for i in range(10)],
            "low": [99.5 + i for i in range(10)],
            "close": [100.25 + i for i in range(10)],
            "volume": [10 + i for i in range(10)],
        }
    )


def test_audit_detects_clean_minute_data() -> None:
    audit = audit_market_data(_sample_frame())

    assert audit.rows == 10
    assert audit.duplicate_timestamps == 0
    assert audit.missing_values == 0
    assert audit.invalid_ohlc_rows == 0
    assert audit.gaps_over_one_minute == 0
    assert audit.one_minute_interval_pct == 90.0


def test_resample_ohlcv_preserves_price_semantics() -> None:
    result = resample_ohlcv(_sample_frame(), rule="5min")

    assert len(result) == 2
    assert result.loc[0, "open"] == 100.0
    assert result.loc[0, "high"] == 104.5
    assert result.loc[0, "low"] == 99.5
    assert result.loc[0, "close"] == 104.25
    assert result.loc[0, "volume"] == sum(range(10, 15))
    assert result.loc[0, "source_bars"] == 5
