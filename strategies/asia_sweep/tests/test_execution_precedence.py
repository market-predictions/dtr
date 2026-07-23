from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.execution import (
    ExecutionConfig,
    ExecutionReason,
    ExecutionSignal,
    mark_synthetic_fixture,
    simulate_execution,
)


def _frame() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02 02:05", periods=20, freq="1min")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": 100.0,
            "high": 100.25,
            "low": 99.75,
            "close": 100.0,
            "is_active_quote": 1,
        }
    )
    return mark_synthetic_fixture(frame)


def _signal(*, target_rr: float = 2.0) -> ExecutionSignal:
    return ExecutionSignal(
        instrument="NQ_SYNTHETIC",
        direction=1,
        signal_timestamp=pd.Timestamp("2024-01-02 02:05"),
        window_end=pd.Timestamp("2024-01-02 02:20"),
        stop_price=99.0,
        target_rr=target_rr,
    )


def _config() -> ExecutionConfig:
    return ExecutionConfig(
        tick_size=0.25,
        point_value=20.0,
        commission_per_side=2.25,
    )


def test_first_unsafe_stale_condition_owns_later_missing_minute() -> None:
    frame = _frame()
    frame.loc[1:11, "is_active_quote"] = 0
    missing = pd.Timestamp("2024-01-02 02:17")
    frame = frame[frame["timestamp"] != missing].copy()
    mark_synthetic_fixture(frame)

    outcome = simulate_execution(_signal(), frame, _config())

    assert outcome.reason == ExecutionReason.STALE_ACTIVITY_LIQUIDATION
    assert outcome.exit_timestamp == pd.Timestamp("2024-01-02 02:18")
    assert outcome.gap_minutes == 12


def test_target_ratio_is_frozen_at_two_r() -> None:
    with pytest.raises(ValueError, match="frozen target_rr of 2.0"):
        _signal(target_rr=1.5)
