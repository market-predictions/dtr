from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.amsterdam_window import (
    filter_amsterdam_confirmation_window,
)


def _rows(timestamps: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": [f"event-{i}" for i in range(len(timestamps))],
            "state_detection_timestamp": timestamps,
            "year": [0] * len(timestamps),
            "weekday": [0] * len(timestamps),
            "time_bucket": [0] * len(timestamps),
        }
    )


def test_filter_uses_exact_amsterdam_clock_and_half_open_end() -> None:
    rows = _rows(
        [
            "2020-01-15 02:59:00-05:00",  # 08:59 Amsterdam
            "2020-01-15 03:00:00-05:00",  # 09:00 Amsterdam
            "2020-01-15 03:59:00-05:00",  # 09:59 Amsterdam
            "2020-01-15 04:00:00-05:00",  # 10:00 Amsterdam
        ]
    )
    filtered = filter_amsterdam_confirmation_window(rows)
    assert filtered["event_id"].tolist() == ["event-1", "event-2"]
    assert filtered["time_bucket"].tolist() == [18, 19]


def test_filter_handles_non_overlapping_us_eu_dst_weeks() -> None:
    rows = _rows(
        [
            "2020-03-16 03:30:00-04:00",  # 08:30 CET: excluded
            "2020-04-15 03:30:00-04:00",  # 09:30 CEST: included
        ]
    )
    filtered = filter_amsterdam_confirmation_window(rows)
    assert filtered["event_id"].tolist() == ["event-1"]
    assert filtered.iloc[0]["detection_amsterdam"].startswith("2020-04-15 09:30:00")
