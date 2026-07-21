from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.research import integrity, resample_5m


def _market_with_long_gap() -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-07 09:00", "2025-01-07 10:00", freq="1min")
    missing = pd.date_range("2025-01-07 09:11", "2025-01-07 09:20", freq="1min")
    timestamps = timestamps[~timestamps.isin(missing)]
    prices = 100.0 + np.arange(len(timestamps), dtype=float) * 0.01
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": prices,
            "high": prices + 0.25,
            "low": prices - 0.25,
            "close": prices + 0.05,
            "volume": np.full(len(timestamps), 10.0),
        }
    )


def test_range_rejected_when_gap_resumes_after_range_end() -> None:
    one = _market_with_long_gap()
    bars = resample_5m(one)
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    sessions = pd.DataFrame(
        [
            {
                "session": "NEW_YORK_9AM",
                "session_date": pd.Timestamp("2025-01-07"),
                "range_start": pd.Timestamp("2025-01-07 09:00"),
                "range_end": pd.Timestamp("2025-01-07 09:15"),
                "break_end": pd.Timestamp("2025-01-07 10:00"),
                "range_high": 101.0,
                "range_low": 100.0,
                "range_size": 1.0,
                "post_start_index": int(
                    np.searchsorted(
                        bar_times,
                        np.datetime64(pd.Timestamp("2025-01-07 09:15")),
                        side="left",
                    )
                ),
                "post_end_index": int(
                    np.searchsorted(
                        bar_times,
                        np.datetime64(pd.Timestamp("2025-01-07 10:00")),
                        side="left",
                    )
                ),
                "weekday": 1,
            }
        ]
    )

    sanitized = integrity._sanitize_sessions(one, bars, sessions)

    assert bool(sanitized.iloc[0]["integrity_range_gap_rejected"])


def test_trade_overlap_detected_before_gap_resume_timestamp() -> None:
    previous_ns = np.array([pd.Timestamp("2025-01-07 10:01").value], dtype=np.int64)
    current_ns = np.array([pd.Timestamp("2025-01-07 10:05").value], dtype=np.int64)

    detected = integrity._first_unsafe_gap_between(
        previous_ns,
        current_ns,
        pd.Timestamp("2025-01-07 10:00"),
        pd.Timestamp("2025-01-07 10:04"),
    )

    assert detected == int(current_ns[0])
