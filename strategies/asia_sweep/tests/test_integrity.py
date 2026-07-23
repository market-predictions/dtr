from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.integrity import audit_minute_interval


def test_complete_half_open_minute_interval() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2024-01-01 18:00",
                "2024-01-02 01:59",
                freq="1min",
            )
        }
    )
    result = audit_minute_interval(
        frame,
        pd.Timestamp("2024-01-01 18:00"),
        pd.Timestamp("2024-01-02 02:00"),
    )
    assert result.complete
    assert result.expected_minutes == 480
    assert result.observed_minutes == 480
    assert result.missing_minutes == 0


def test_missing_and_off_grid_timestamps_are_reported() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": [
                pd.Timestamp("2024-01-01 18:00"),
                pd.Timestamp("2024-01-01 18:02"),
                pd.Timestamp("2024-01-01 18:02:30"),
            ]
        }
    )
    result = audit_minute_interval(
        frame,
        pd.Timestamp("2024-01-01 18:00"),
        pd.Timestamp("2024-01-01 18:03"),
    )
    assert not result.complete
    assert result.expected_minutes == 3
    assert result.observed_minutes == 2
    assert result.missing_minutes == 1
    assert result.off_grid_timestamps == 1
    assert result.first_missing_timestamp == pd.Timestamp("2024-01-01 18:01")
