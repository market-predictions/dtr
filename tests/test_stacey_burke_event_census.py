from __future__ import annotations

from datetime import date

import pandas as pd
from pandas.testing import assert_frame_equal

from stacey_burke_lab.event_census import (
    _assign_market_clocks,
    _first_reclaim,
    build_completed_day_references,
    detect_pair_event_census,
)


def _base_frame(
    *,
    start: str = "2025-01-01",
    end: str = "2025-02-20",
) -> pd.DataFrame:
    timestamps = pd.date_range(start, end, freq="min", tz="UTC", inclusive="left")
    frame = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "mid_open": 1.1000,
            "mid_high": 1.1010,
            "mid_low": 1.0990,
            "mid_close": 1.1000,
            "active_both": True,
            "source_partition": "2025",
        }
    )
    clocks = _assign_market_clocks(frame)
    frame["active_both"] = clocks["trading_date"].dt.weekday < 5
    return frame


def _london_minute_mask(
    frame: pd.DataFrame,
    *,
    session_date: date,
    hour: int,
    minute: int,
) -> pd.Series:
    london = frame["timestamp_utc"].dt.tz_convert("Europe/London")
    return (
        (london.dt.date == session_date)
        & (london.dt.hour == hour)
        & (london.dt.minute == minute)
    )


def test_market_clocks_keep_london_window_dst_safe() -> None:
    frame = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                [
                    "2025-03-28T07:00:00Z",
                    "2025-03-31T06:00:00Z",
                ],
                utc=True,
            )
        }
    )
    clocks = _assign_market_clocks(frame)
    assert clocks["london_minute"].tolist() == [7 * 60, 7 * 60]


def test_first_sweep_clock_does_not_reset_after_expiry() -> None:
    timestamps = pd.date_range(
        "2025-02-10T07:00:00Z",
        periods=90,
        freq="min",
        tz="UTC",
    )
    session = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "mid_high": 1.1000,
            "mid_low": 1.0990,
            "mid_close": 1.1000,
            "active_both": True,
        }
    )
    session.loc[5:20, "mid_close"] = 1.1011
    session.loc[5, "mid_high"] = 1.1012
    session.loc[25, ["mid_high", "mid_close"]] = [1.1013, 1.1009]

    candidate = _first_reclaim(
        session,
        side="high",
        level=1.1010,
        threshold=0.0001,
        reclaim_minutes=15,
    )

    assert candidate is not None
    assert candidate["swept"]
    assert not candidate["reclaimed"]
    assert candidate["sweep_timestamp"] == timestamps[5]


def test_future_append_does_not_change_completed_references() -> None:
    complete = _base_frame(end="2025-02-20")
    truncated = complete.loc[
        complete["timestamp_utc"] < pd.Timestamp("2025-02-10T00:00:00Z")
    ].copy()
    future = complete.copy()
    future_mask = future["timestamp_utc"] >= pd.Timestamp("2025-02-10T00:00:00Z")
    future.loc[future_mask, "mid_high"] = 2.0
    future.loc[future_mask, "mid_low"] = 0.5

    before = build_completed_day_references(truncated, atr_days=5)
    after = build_completed_day_references(future, atr_days=5)
    stable_index = before.index[before.index <= pd.Timestamp("2025-02-07")]
    assert_frame_equal(before.loc[stable_index], after.loc[stable_index])


def test_same_minute_reclaim_is_retained_without_return_fields() -> None:
    frame = _base_frame()
    event_mask = _london_minute_mask(
        frame,
        session_date=date(2025, 2, 10),
        hour=7,
        minute=30,
    )
    frame.loc[event_mask, "mid_high"] = 1.1012
    frame.loc[event_mask, "mid_close"] = 1.1009

    events, sessions, summary = detect_pair_event_census(
        frame=frame,
        symbol="EURUSD",
    )

    assert len(events) == 1
    event = events.iloc[0]
    assert event["swept_side"] == "high"
    assert event["reversal_direction"] == "short_reversal"
    assert event["same_minute_reclaim"]
    assert event["reclaim_delay_minutes"] == 0
    assert summary["retained_events"] == 1
    assert not summary["forward_returns_inspected"]
    assert not summary["performance_execution"]
    prohibited = ("forward", "return", "entry", "stop", "target", "pnl")
    assert not any(
        token in column.lower()
        for column in events.columns
        for token in prohibited
    )
    retained = sessions.loc[sessions["retained_event"]]
    assert retained["london_date"].tolist() == ["2025-02-10"]


def test_same_timestamp_dual_reclaim_is_ambiguous_and_excluded() -> None:
    frame = _base_frame()
    event_mask = _london_minute_mask(
        frame,
        session_date=date(2025, 2, 10),
        hour=7,
        minute=30,
    )
    frame.loc[event_mask, "mid_high"] = 1.1020
    frame.loc[event_mask, "mid_low"] = 1.0980
    frame.loc[event_mask, "mid_close"] = 1.1000

    events, sessions, summary = detect_pair_event_census(
        frame=frame,
        symbol="EURUSD",
    )

    assert events.empty
    assert summary["sessions_ambiguous"] == 1
    ambiguous = sessions.loc[sessions["ambiguous"]]
    assert ambiguous["exclusion_reason"].tolist() == [
        "ambiguous_same_reclaim_timestamp"
    ]


def test_session_below_active_coverage_floor_is_ineligible() -> None:
    frame = _base_frame()
    london = frame["timestamp_utc"].dt.tz_convert("Europe/London")
    session_mask = (
        (london.dt.date == date(2025, 2, 10))
        & (london.dt.hour >= 7)
        & (london.dt.hour < 10)
    )
    inactive_index = frame.index[session_mask][:10]
    frame.loc[inactive_index, "active_both"] = False
    event_mask = _london_minute_mask(
        frame,
        session_date=date(2025, 2, 10),
        hour=7,
        minute=30,
    )
    frame.loc[event_mask, "mid_high"] = 1.1020
    frame.loc[event_mask, "mid_close"] = 1.1000

    events, sessions, _ = detect_pair_event_census(
        frame=frame,
        symbol="EURUSD",
    )

    assert events.empty
    target = sessions.loc[sessions["london_date"] == "2025-02-10"].iloc[0]
    assert not target["eligible"]
    assert "insufficient_active_minutes" in target["exclusion_reason"]
