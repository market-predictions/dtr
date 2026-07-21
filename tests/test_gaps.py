from __future__ import annotations

import pandas as pd

from dtr_lab.data.gaps import classify_gaps, summarize_gaps


def _frame(values: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"timestamp_et": pd.to_datetime(values)})


def test_classifies_daily_maintenance() -> None:
    gaps = classify_gaps(_frame(["2025-01-06 17:00", "2025-01-06 18:01"]))
    assert gaps["classification"].tolist() == ["daily_maintenance"]
    assert not gaps["reject_trade_bridge"].any()


def test_classifies_weekend_or_monday_holiday() -> None:
    gaps = classify_gaps(_frame(["2025-01-03 17:00", "2025-01-05 18:01"]))
    assert gaps["classification"].tolist() == ["weekend_or_monday_holiday"]
    assert not gaps["reject_trade_bridge"].any()


def test_classifies_missing_and_offset_gaps_as_unsafe() -> None:
    frame = _frame(
        [
            "2025-01-07 10:00",
            "2025-01-07 10:03",
            "2025-01-07 10:15",
            "2025-01-07 16:59",
            "2025-01-07 18:01",
        ]
    )
    gaps = classify_gaps(frame)
    assert gaps["classification"].tolist() == [
        "small_missing_data",
        "medium_missing_data",
        "unclassified_long_gap",
        "maintenance_offset",
    ]
    assert gaps["reject_trade_bridge"].all()


def test_gap_summary_counts_categories() -> None:
    frame = _frame(
        [
            "2025-01-06 17:00",
            "2025-01-06 18:01",
            "2025-01-06 18:03",
        ]
    )
    summary = summarize_gaps(classify_gaps(frame))
    assert summary.total_gaps == 2
    assert summary.daily_maintenance == 1
    assert summary.small_missing_data == 1
    assert summary.unsafe_gaps == 1


def test_empty_gap_frame_is_supported() -> None:
    gaps = classify_gaps(_frame(["2025-01-06 10:00", "2025-01-06 10:01"]))
    summary = summarize_gaps(gaps)
    assert gaps.empty
    assert summary.total_gaps == 0
