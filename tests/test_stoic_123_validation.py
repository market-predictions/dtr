from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from stoic_123_lab.config import SequenceConfig
from stoic_123_lab.validation import (
    detect_long_stage_events,
    entry_config,
    management_config,
    matched_time_events,
)


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


def test_direction_restriction_does_not_disable_management_direction() -> None:
    entry = entry_config(_config(), "long_only")
    management = management_config(entry)
    assert entry.allow_long is True
    assert entry.allow_short is False
    assert management.allow_long is True
    assert management.allow_short is True


def test_ema_break_control_requires_close_not_wick() -> None:
    execution = _bars([100, 100, 100, 100])
    execution.loc[3, "high"] = 105
    execution.loc[3, "close"] = 100
    result = detect_long_stage_events(
        execution,
        _bars([100, 100], minutes=60),
        _config(),
        model="ema_break",
    )
    assert result.events.empty


def test_retest_control_waits_for_retest_and_uses_causal_low() -> None:
    execution = _bars([100, 100, 100, 100, 102, 101, 102])
    execution.loc[5, "low"] = 99.5
    result = detect_long_stage_events(
        execution,
        _bars([100, 100], minutes=60),
        _config(),
        model="ema_break_retest",
    )
    assert len(result.events) == 1
    event = result.events.iloc[0]
    assert event["step1_time"] < event["signal_time"]
    assert event["base_lock_time"] < event["signal_time"]
    assert np.isclose(event["protective_boundary"], 99.5)


def test_matched_time_control_is_deterministic_and_excludes_originals() -> None:
    execution = _bars(list(np.linspace(100, 110, 400)), start="2025-01-01 00:00")
    map_bars = _bars(
        list(np.linspace(100, 110, 40)),
        minutes=60,
        start="2025-01-01 00:00",
    )
    full = pd.DataFrame(
        {
            "arm_id": ["TEST", "TEST"],
            "direction": [1, 1],
            "signal_time": [
                pd.Timestamp("2025-01-02 10:05"),
                pd.Timestamp("2025-01-03 10:05"),
            ],
            "breakout_close": [102.0, 103.0],
            "protective_boundary": [100.0, 101.0],
            "base_lock_time": [
                pd.Timestamp("2025-01-02 10:00"),
                pd.Timestamp("2025-01-03 10:00"),
            ],
        }
    )
    first = matched_time_events(full, execution, map_bars, _config(), seed=7)
    second = matched_time_events(full, execution, map_bars, _config(), seed=7)
    pd.testing.assert_frame_equal(first, second)
    original_times = set(pd.to_datetime(full["signal_time"]))
    assert not set(pd.to_datetime(first["signal_time"])) & original_times
    assert first["signal_time"].is_unique


def test_management_config_preserves_original_timeframe() -> None:
    base = replace(_config(), management_minutes=15)
    management = management_config(base)
    assert management.execution_minutes == 15
