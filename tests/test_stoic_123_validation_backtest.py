from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from stoic_123_lab.backtest import simulate
from stoic_123_lab.config import NQ_SPEC, SequenceConfig
from stoic_123_lab.validation_backtest import simulate_validation


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


def test_validation_simulator_matches_reference_random_paths() -> None:
    rng = np.random.default_rng(13)
    timestamps = pd.date_range("2025-01-02 09:00", periods=1200, freq="1min")
    close = 20000 + np.cumsum(rng.normal(0, 2, len(timestamps)))
    open_ = np.r_[close[0], close[:-1]]
    one = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": np.maximum(open_, close) + rng.uniform(0, 2, len(timestamps)),
            "low": np.minimum(open_, close) - rng.uniform(0, 2, len(timestamps)),
            "close": close,
            "volume": 1.0,
        }
    )
    event_indexes = np.arange(30, 1000, 47)
    events = pd.DataFrame(
        {
            "arm_id": "TEST",
            "direction": np.where(np.arange(len(event_indexes)) % 2 == 0, 1, -1),
            "signal_time": timestamps[event_indexes],
            "base_lock_time": timestamps[event_indexes - 5],
            "breakout_close": close[event_indexes],
            "protective_boundary": np.where(
                np.arange(len(event_indexes)) % 2 == 0,
                close[event_indexes] - 15,
                close[event_indexes] + 15,
            ),
        }
    )
    management = pd.DataFrame(
        {
            "direction": [1, -1, 1, -1],
            "signal_time": timestamps[[250, 500, 750, 1000]],
        }
    )
    config = replace(
        _config(),
        stop_buffer_ticks=0,
        minimum_risk_ticks=1,
        max_hold_minutes=180,
    )
    expected = simulate(one, events, management, NQ_SPEC, config)
    observed = simulate_validation(one, events, management, NQ_SPEC, config)
    pd.testing.assert_frame_equal(observed, expected)


def test_validation_simulator_matches_reference_gap_and_tie_precedence() -> None:
    timestamps = pd.DatetimeIndex(
        [
            pd.Timestamp("2025-01-02 09:00"),
            pd.Timestamp("2025-01-02 09:01"),
            pd.Timestamp("2025-01-02 09:20"),
            pd.Timestamp("2025-01-02 09:21"),
        ]
    )
    one = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [100.0, 100.0, 90.0, 90.0],
            "high": [101.0, 101.0, 91.0, 91.0],
            "low": [99.0, 99.0, 80.0, 80.0],
            "close": [100.0, 100.0, 90.0, 90.0],
            "volume": 1.0,
        }
    )
    events = pd.DataFrame(
        {
            "arm_id": ["TEST"],
            "direction": [1],
            "signal_time": [timestamps[0]],
            "base_lock_time": [timestamps[0] - pd.Timedelta(minutes=5)],
            "breakout_close": [100.0],
            "protective_boundary": [95.0],
        }
    )
    management = pd.DataFrame(
        {"direction": [-1], "signal_time": [timestamps[2]]}
    )
    config = replace(
        _config(),
        stop_buffer_ticks=0,
        minimum_risk_ticks=1,
        max_hold_minutes=60,
        gap_reset_minutes=15,
    )
    expected = simulate(one, events, management, NQ_SPEC, config)
    observed = simulate_validation(one, events, management, NQ_SPEC, config)
    pd.testing.assert_frame_equal(observed, expected)
    assert observed.loc[0, "exit_reason"] == "gap_liquidation"


def test_nq_uses_cached_path_not_reference_fallback(monkeypatch) -> None:
    import stoic_123_lab.validation_backtest as module

    timestamps = pd.date_range("2025-01-02 09:00", periods=5, freq="1min")
    one = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "high": [101.0, 101.0, 101.0, 101.0, 101.0],
            "low": [99.0, 99.0, 99.0, 99.0, 99.0],
            "close": [100.0, 100.0, 100.0, 100.0, 100.0],
            "volume": 1.0,
        }
    )
    events = pd.DataFrame(
        {
            "arm_id": ["TEST"],
            "direction": [1],
            "signal_time": [timestamps[0]],
            "base_lock_time": [timestamps[0] - pd.Timedelta(minutes=5)],
            "breakout_close": [100.0],
            "protective_boundary": [95.0],
        }
    )
    management = pd.DataFrame(columns=["direction", "signal_time"])
    config = replace(
        _config(),
        stop_buffer_ticks=0,
        minimum_risk_ticks=1,
        max_hold_minutes=2,
    )

    def fail_fallback(*args, **kwargs):
        raise AssertionError("reference fallback was called for NQ")

    monkeypatch.setattr(module, "simulate", fail_fallback)
    observed = module.simulate_validation(one, events, management, NQ_SPEC, config)
    assert len(observed) == 1
    assert observed.loc[0, "exit_reason"] == "max_hold"
