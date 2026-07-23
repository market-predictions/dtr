from __future__ import annotations

import numpy as np
import pandas as pd

from stoic_123_lab.config import SequenceConfig
from stoic_123_lab.validation_short_direction import detect_short_stage_events
from stoic_123_lab.validation_short_matching import matched_time_short_events


def _bars(
    closes: list[float],
    minutes: int = 5,
    start: str = "2025-01-02 09:00",
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
        arm_id="TEST",
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


def test_short_ema_break_requires_close_not_wick() -> None:
    execution = _bars([100, 100, 100, 100])
    execution.loc[3, "low"] = 95
    execution.loc[3, "close"] = 100
    result = detect_short_stage_events(
        execution,
        _bars([100, 100], minutes=60),
        _config(),
        model="ema_break",
    )
    assert result.events.empty


def test_short_retest_waits_and_uses_causal_high() -> None:
    execution = _bars([100, 100, 100, 100, 98, 99, 98])
    execution.loc[5, "high"] = 100.5
    result = detect_short_stage_events(
        execution,
        _bars([100, 100], minutes=60),
        _config(),
        model="ema_break_retest",
    )
    assert len(result.events) == 1
    event = result.events.iloc[0]
    assert int(event["direction"]) == -1
    assert event["step1_time"] < event["signal_time"]
    assert event["base_lock_time"] < event["signal_time"]
    assert np.isclose(event["protective_boundary"], 100.5)


def _matching_fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    execution = _bars(
        list(np.linspace(110, 90, 5000)),
        start="2025-01-01 00:00",
    )
    map_bars = _bars(
        list(np.linspace(110, 90, 500)),
        minutes=60,
        start="2025-01-01 00:00",
    )
    full = pd.DataFrame(
        {
            "arm_id": ["TEST", "TEST"],
            "direction": [-1, -1],
            "signal_time": [
                pd.Timestamp("2025-01-08 15:05"),
                pd.Timestamp("2025-01-10 15:05"),
            ],
            "breakout_close": [108.0, 107.0],
            "protective_boundary": [110.0, 109.0],
            "base_lock_time": [
                pd.Timestamp("2025-01-08 15:00"),
                pd.Timestamp("2025-01-10 15:00"),
            ],
        }
    )
    return execution, map_bars, full


def test_matched_short_control_is_deterministic_and_preserves_risk_width() -> None:
    execution, map_bars, full = _matching_fixture()
    first = matched_time_short_events(full, execution, map_bars, _config(), seed=7)
    second = matched_time_short_events(full, execution, map_bars, _config(), seed=7)
    assert not first.empty
    pd.testing.assert_frame_equal(first, second)
    assert first.attrs["match_fraction"] == second.attrs["match_fraction"]
    assert not set(pd.to_datetime(first["signal_time"])) & set(
        pd.to_datetime(full["signal_time"])
    )
    assert first["signal_time"].is_unique
    assert (first["direction"] == -1).all()
    observed_width = first["protective_boundary"] - first["breakout_close"]
    assert np.allclose(observed_width, 2.0)


def test_matched_short_control_uses_only_complete_nonreset_bars() -> None:
    execution, map_bars, full = _matching_fixture()
    execution.loc[20:40, "full_bar"] = False
    execution.loc[60:80, "gap_minutes"] = 30.0
    matched = matched_time_short_events(full, execution, map_bars, _config(), seed=11)
    assert not matched.empty
    eligible = execution.set_index("bar_end")
    for signal_time in pd.to_datetime(matched["signal_time"]):
        source = eligible.loc[signal_time]
        assert bool(source["full_bar"])
        assert float(source["gap_minutes"]) <= _config().gap_reset_minutes


def test_matching_uses_new_york_session_from_utc_timestamps() -> None:
    execution, map_bars, full = _matching_fixture()
    matched = matched_time_short_events(
        full,
        execution,
        map_bars,
        _config(),
        seed=13,
        source_timezone="UTC",
        session_timezone="America/New_York",
    )
    assert not matched.empty
    original_local = (
        pd.to_datetime(full["signal_time"])
        .dt.tz_localize("UTC")
        .dt.tz_convert("America/New_York")
    )
    matched_local = (
        pd.to_datetime(matched["signal_time"])
        .dt.tz_localize("UTC")
        .dt.tz_convert("America/New_York")
    )
    assert set(original_local.dt.hour * 2 + original_local.dt.minute // 30) == set(
        matched_local.dt.hour * 2 + matched_local.dt.minute // 30
    )
