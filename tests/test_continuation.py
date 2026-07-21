from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.research.continuation import (
    ContinuationConfig,
    generate_continuation_signals,
)


def _fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    one_times = pd.date_range("2025-01-07 09:00", "2025-01-07 10:59", freq="1min")
    one = pd.DataFrame(
        {
            "timestamp": one_times,
            "open": np.full(len(one_times), 95.0),
            "high": np.full(len(one_times), 95.25),
            "low": np.full(len(one_times), 94.75),
            "close": np.full(len(one_times), 95.0),
            "volume": np.full(len(one_times), 10.0),
        }
    )
    bar_times = pd.date_range("2025-01-07 09:00", "2025-01-07 10:55", freq="5min")
    bars = pd.DataFrame(
        {
            "timestamp": bar_times,
            "bar_end": bar_times + pd.Timedelta(minutes=5),
            "open": np.full(len(bar_times), 95.0),
            "high": np.full(len(bar_times), 95.5),
            "low": np.full(len(bar_times), 94.5),
            "close": np.full(len(bar_times), 95.0),
            "volume": np.full(len(bar_times), 100.0),
            "atr14": np.full(len(bar_times), 2.0),
            "median_range20": np.full(len(bar_times), 1.0),
            "vol_sma20": np.full(len(bar_times), 100.0),
            "eth_vwap": np.full(len(bar_times), 96.0),
            "eth_vwap_slope3": np.full(len(bar_times), 0.5),
            "er20": np.full(len(bar_times), 0.4),
            "adx14": np.full(len(bar_times), 24.0),
        }
    )
    sessions = pd.DataFrame(
        [
            {
                "session": "NEW_YORK_9AM",
                "session_date": pd.Timestamp("2025-01-07"),
                "range_start": pd.Timestamp("2025-01-07 09:00"),
                "range_end": pd.Timestamp("2025-01-07 09:30"),
                "break_end": pd.Timestamp("2025-01-07 10:30"),
                "range_high": 100.0,
                "range_low": 90.0,
                "range_size": 10.0,
                "post_start_index": 6,
                "post_end_index": 18,
                "weekday": 1,
            }
        ]
    )
    return one, bars, sessions


def test_one_bar_immediate_accepts_first_break() -> None:
    one, bars, sessions = _fixture()
    bars.loc[6, ["open", "high", "low", "close"]] = [99.5, 101.5, 99.0, 101.0]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(acceptance_bars=1, entry_mode="immediate"),
    )

    assert len(signals) == 1
    assert signals[0].direction == 1
    assert signals[0].entry_index == 6
    assert funnel.break_attempts == 1
    assert funnel.acceptance_pass == 1
    assert funnel.entry_signals == 1


def test_two_bar_acceptance_requires_second_close_outside() -> None:
    one, bars, sessions = _fixture()
    bars.loc[6, ["open", "high", "low", "close"]] = [99.5, 101.5, 99.0, 101.0]
    bars.loc[7, ["open", "high", "low", "close"]] = [100.5, 101.0, 98.5, 99.5]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(acceptance_bars=2, entry_mode="immediate"),
    )

    assert signals == []
    assert funnel.acceptance_failed == 1


def test_pullback_requires_touch_and_outward_rejection() -> None:
    one, bars, sessions = _fixture()
    bars.loc[6, ["open", "high", "low", "close"]] = [99.5, 101.5, 99.0, 101.0]
    bars.loc[7, ["open", "high", "low", "close"]] = [101.3, 102.0, 101.2, 101.5]
    bars.loc[8, ["open", "high", "low", "close"]] = [100.4, 101.6, 100.2, 101.2]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(acceptance_bars=1, entry_mode="pullback"),
    )

    assert len(signals) == 1
    assert signals[0].entry_index == 8
    assert funnel.pullback_touch == 1
    assert funnel.pullback_rejection == 1


def test_pullback_invalidates_on_close_back_inside() -> None:
    one, bars, sessions = _fixture()
    bars.loc[6, ["open", "high", "low", "close"]] = [99.5, 101.5, 99.0, 101.0]
    bars.loc[7, ["open", "high", "low", "close"]] = [100.5, 101.0, 98.5, 99.5]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(acceptance_bars=1, entry_mode="pullback"),
    )

    assert signals == []
    assert funnel.failed_return_inside_pre_entry == 1


def test_minimum_minutes_filter_is_applied_before_signal() -> None:
    one, bars, sessions = _fixture()
    bars.loc[6, ["open", "high", "low", "close"]] = [99.5, 101.5, 99.0, 101.0]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(
            acceptance_bars=1,
            entry_mode="immediate",
            min_minutes_from_range_end=10,
        ),
    )

    assert signals == []
    assert funnel.timing_filter_rejected == 1


def test_one_bar_immediate_accepts_downside_break() -> None:
    one, bars, sessions = _fixture()
    bars.loc[6, ["open", "high", "low", "close"]] = [90.5, 91.0, 88.5, 89.0]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(acceptance_bars=1, entry_mode="immediate"),
    )

    assert len(signals) == 1
    assert signals[0].direction == -1
    assert signals[0].boundary == 90.0
    assert funnel.entry_signals == 1


def test_gap_inside_range_rejects_session() -> None:
    one, bars, sessions = _fixture()
    one = one[one["timestamp"] != pd.Timestamp("2025-01-07 09:10")].copy()
    bars.loc[6, ["open", "high", "low", "close"]] = [99.5, 101.5, 99.0, 101.0]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(acceptance_bars=1, entry_mode="immediate"),
    )

    assert signals == []
    assert funnel.sessions_range_gap_rejected == 1


def test_gap_after_range_truncates_signal_path() -> None:
    one, bars, sessions = _fixture()
    one = one[one["timestamp"] != pd.Timestamp("2025-01-07 09:41")].copy()
    bars.loc[10, ["open", "high", "low", "close"]] = [99.5, 101.5, 99.0, 101.0]

    signals, funnel = generate_continuation_signals(
        one,
        bars,
        sessions,
        ContinuationConfig(acceptance_bars=1, entry_mode="immediate"),
    )

    assert signals == []
    assert funnel.sessions_signal_path_truncated == 1
