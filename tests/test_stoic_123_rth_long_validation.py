from __future__ import annotations

import numpy as np
import pandas as pd

from stoic_123_lab.config import SequenceConfig
from stoic_123_lab.validation_rth_long import (
    filter_entry_events_by_session,
    matched_time_rth_long_events,
    session_label,
)


def _bars(
    closes: list[float],
    minutes: int = 5,
    start: str = "2025-01-01 00:00",
) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=len(closes), freq=f"{minutes}min")
    close = np.asarray(closes, dtype=float)
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "bar_end": timestamps + pd.Timedelta(minutes=minutes),
            "open": open_,
            "high": np.maximum(open_, close) + 0.10,
            "low": np.minimum(open_, close) - 0.10,
            "close": close,
            "volume": 1.0,
            "active_minutes": minutes,
            "gap_minutes": 0.0,
            "full_bar": True,
        }
    )


def _config() -> SequenceConfig:
    return SequenceConfig(
        arm_id="TEST_RTH_LONG",
        description="test",
        ema_fast=2,
        ema_slow=3,
        atr_length=2,
        map_mode="none",
        step1_close_buffer_atr=0,
        step1_min_body_fraction=0.20,
        retest_max_bars=5,
        retest_tolerance_atr=0.50,
        require_map_at_step3=False,
    )


def test_rth_session_uses_new_york_dst_rules_and_excludes_close() -> None:
    assert session_label(pd.Timestamp("2026-01-15 14:30")) == "RTH"
    assert session_label(pd.Timestamp("2026-01-15 20:59")) == "RTH"
    assert session_label(pd.Timestamp("2026-01-15 21:00")) == "OVERNIGHT"
    assert session_label(pd.Timestamp("2026-07-15 13:30")) == "RTH"
    assert session_label(pd.Timestamp("2026-07-15 19:59")) == "RTH"
    assert session_label(pd.Timestamp("2026-07-15 20:00")) == "OVERNIGHT"
    assert session_label(pd.Timestamp("2026-07-15 13:29")) == "OVERNIGHT"


def test_entry_filter_preserves_rows_and_does_not_modify_source() -> None:
    events = pd.DataFrame(
        {
            "arm_id": ["TEST", "TEST", "TEST"],
            "direction": [1, 1, 1],
            "signal_time": pd.to_datetime(
                [
                    "2026-07-15 13:30",
                    "2026-07-15 15:00",
                    "2026-07-15 20:00",
                ]
            ),
            "breakout_close": [100.0, 101.0, 102.0],
            "protective_boundary": [98.0, 99.0, 100.0],
        }
    )
    original = events.copy(deep=True)
    rth = filter_entry_events_by_session(events, session="RTH")
    overnight = filter_entry_events_by_session(events, session="OVERNIGHT")
    pd.testing.assert_frame_equal(events, original)
    assert len(rth) == 2
    assert len(overnight) == 1
    assert rth["signal_time"].max() < pd.Timestamp("2026-07-15 20:00")


def _matching_fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    execution = _bars(list(np.linspace(90, 110, 5000)))
    map_bars = _bars(list(np.linspace(90, 110, 500)), minutes=60)
    full = pd.DataFrame(
        {
            "arm_id": ["TEST", "TEST"],
            "entry_model": ["full_123", "full_123"],
            "direction": [1, 1],
            "step1_time": pd.to_datetime(
                ["2025-01-08 15:00", "2025-01-10 15:00"]
            ),
            "retest_time": pd.to_datetime(
                ["2025-01-08 15:00", "2025-01-10 15:00"]
            ),
            "base_lock_time": pd.to_datetime(
                ["2025-01-08 15:00", "2025-01-10 15:00"]
            ),
            "signal_time": pd.to_datetime(
                ["2025-01-08 15:05", "2025-01-10 15:05"]
            ),
            "breakout_close": [108.0, 109.0],
            "protective_boundary": [106.0, 107.0],
            "atr_at_signal": [1.0, 1.0],
            "map_direction_step1": [0, 0],
            "map_direction_signal": [0, 0],
        }
    )
    return execution, map_bars, full


def test_matched_rth_long_is_deterministic_and_preserves_risk() -> None:
    execution, map_bars, full = _matching_fixture()
    first = matched_time_rth_long_events(
        full,
        execution,
        map_bars,
        _config(),
        seed=17,
    )
    second = matched_time_rth_long_events(
        full,
        execution,
        map_bars,
        _config(),
        seed=17,
    )
    assert not first.empty
    pd.testing.assert_frame_equal(first, second)
    assert first.attrs["match_fraction"] == second.attrs["match_fraction"]
    assert first["signal_time"].is_unique
    assert (first["direction"] == 1).all()
    observed_width = first["breakout_close"] - first["protective_boundary"]
    assert np.allclose(observed_width, 2.0)
    assert all(session_label(value) == "RTH" for value in first["signal_time"])
    assert not set(pd.to_datetime(first["signal_time"])) & set(
        pd.to_datetime(full["signal_time"])
    )


def test_matched_rth_long_uses_complete_nonreset_bars_only() -> None:
    execution, map_bars, full = _matching_fixture()
    execution.loc[20:40, "full_bar"] = False
    execution.loc[60:80, "gap_minutes"] = 30.0
    matched = matched_time_rth_long_events(
        full,
        execution,
        map_bars,
        _config(),
        seed=19,
    )
    assert not matched.empty
    eligible = execution.set_index("bar_end")
    for signal_time in pd.to_datetime(matched["signal_time"]):
        source = eligible.loc[signal_time]
        assert bool(source["full_bar"])
        assert float(source["gap_minutes"]) <= _config().gap_reset_minutes
