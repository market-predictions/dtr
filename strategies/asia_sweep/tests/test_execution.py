from __future__ import annotations

import inspect
from dataclasses import asdict

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep import execution as execution_module
from dtr_lab.strategies.asia_sweep.execution import (
    ExecutionConfig,
    ExecutionReason,
    ExecutionSignal,
    ExecutionStatus,
    mark_synthetic_fixture,
    simulate_execution,
    validate_execution_prefix,
)


_CONFIG = ExecutionConfig(
    tick_size=0.25,
    point_value=20.0,
    commission_per_side=2.25,
)


def _frame(
    start: str = "2024-01-02 02:05",
    periods: int = 16,
    price: float = 100.0,
) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=periods, freq="1min")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": price,
            "high": price + 0.20,
            "low": price - 0.20,
            "close": price,
            "is_active_quote": 1,
        }
    )
    return mark_synthetic_fixture(frame)


def _signal(
    *,
    direction: int = 1,
    stop: float = 99.0,
    start: str = "2024-01-02 02:05",
    end: str = "2024-01-02 02:15",
) -> ExecutionSignal:
    return ExecutionSignal(
        instrument="NQ_SYNTHETIC",
        direction=direction,
        signal_timestamp=pd.Timestamp(start),
        window_end=pd.Timestamp(end),
        stop_price=stop,
        target_rr=2.0,
    )


def _preserve_fixture_marker(frame: pd.DataFrame) -> pd.DataFrame:
    return mark_synthetic_fixture(frame.copy())


def test_real_or_unmarked_source_is_rejected() -> None:
    frame = _frame()
    frame.attrs.clear()
    with pytest.raises(ValueError, match="synthetic-test-only"):
        simulate_execution(_signal(), frame, _CONFIG)


def test_missing_exact_entry_minute_blocks_trade() -> None:
    frame = _frame(start="2024-01-02 02:06")
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.status == ExecutionStatus.BLOCKED
    assert outcome.reason == ExecutionReason.MISSING_ENTRY_MINUTE
    assert outcome.net_r is None


def test_inactive_entry_minute_blocks_trade() -> None:
    frame = _frame()
    frame.loc[0, "is_active_quote"] = 0
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.status == ExecutionStatus.BLOCKED
    assert outcome.reason == ExecutionReason.INACTIVE_ENTRY_MINUTE


@pytest.mark.parametrize(
    ("direction", "stop", "entry_open"),
    [(1, 99.0, 99.0), (-1, 101.0, 101.0)],
)
def test_entry_open_at_stop_blocks_trade(
    direction: int,
    stop: float,
    entry_open: float,
) -> None:
    frame = _frame(price=entry_open)
    outcome = simulate_execution(
        _signal(direction=direction, stop=stop),
        frame,
        _CONFIG,
    )
    assert outcome.reason == ExecutionReason.ENTRY_GAP_THROUGH_STOP
    assert outcome.net_r is None


def test_one_tick_or_smaller_executed_risk_blocks_trade() -> None:
    frame = _frame(price=99.25)
    outcome = simulate_execution(_signal(stop=99.25), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.ENTRY_GAP_THROUGH_STOP

    frame = _frame(price=99.25)
    outcome = simulate_execution(_signal(stop=99.25 - 0.25), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.EXECUTED_RISK_TOO_SMALL


@pytest.mark.parametrize(
    ("direction", "stop", "touch_column", "touch_price"),
    [(1, 99.0, "high", 103.0), (-1, 101.0, "low", 97.0)],
)
def test_entry_minute_target_and_long_short_symmetry(
    direction: int,
    stop: float,
    touch_column: str,
    touch_price: float,
) -> None:
    frame = _frame()
    frame.loc[0, touch_column] = touch_price
    outcome = simulate_execution(
        _signal(direction=direction, stop=stop),
        frame,
        _CONFIG,
    )
    assert outcome.reason == ExecutionReason.TARGET
    assert outcome.exit_timestamp == pd.Timestamp("2024-01-02 02:05")
    assert outcome.gross_r == pytest.approx(2.0)
    assert outcome.net_r < outcome.gross_r


def test_entry_minute_collision_is_stop_first() -> None:
    frame = _frame()
    frame.loc[0, ["high", "low"]] = [103.0, 98.0]
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.STOP
    assert outcome.collision is True
    assert outcome.gross_r < -1.0


def test_later_minute_collision_is_stop_first() -> None:
    frame = _frame()
    frame.loc[2, ["high", "low"]] = [103.0, 98.0]
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.STOP
    assert outcome.exit_timestamp == pd.Timestamp("2024-01-02 02:07")
    assert outcome.collision is True


def test_stop_gap_exits_at_open_with_adverse_slippage() -> None:
    frame = _frame()
    frame.loc[2, ["open", "high", "low", "close"]] = [98.5, 98.8, 98.0, 98.4]
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.STOP_GAP
    assert outcome.exit_price_raw == pytest.approx(98.5)
    assert outcome.exit_price == pytest.approx(98.25)


def test_target_gap_fills_at_target_without_favorable_improvement() -> None:
    frame = _frame()
    frame.loc[2, ["open", "high", "low", "close"]] = [104.0, 104.2, 103.8, 104.0]
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.TARGET_GAP
    assert outcome.exit_price_raw == pytest.approx(outcome.target_price)
    assert outcome.exit_price == pytest.approx(outcome.target_price)
    assert outcome.gross_r == pytest.approx(2.0)


def test_missing_post_entry_minute_liquidates_at_next_open() -> None:
    frame = _frame()
    missing = pd.Timestamp("2024-01-02 02:07")
    frame = _preserve_fixture_marker(frame[frame["timestamp"] != missing])
    frame.loc[frame["timestamp"] == pd.Timestamp("2024-01-02 02:08"), "open"] = 99.5
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.DATA_GAP_LIQUIDATION
    assert outcome.exit_timestamp == pd.Timestamp("2024-01-02 02:08")
    assert outcome.exit_price == pytest.approx(99.25)
    assert outcome.gap_minutes == 1


def test_missing_data_without_observation_by_window_end_is_unresolved() -> None:
    frame = _frame(periods=2)
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.status == ExecutionStatus.UNRESOLVED
    assert outcome.reason == ExecutionReason.UNRESOLVED_DATA_EXIT
    assert outcome.net_r is None


def test_ten_inactive_minutes_are_tolerated_until_active_time_exit() -> None:
    frame = _frame(periods=12)
    frame.loc[1:10, "is_active_quote"] = 0
    signal = _signal(end="2024-01-02 02:16")
    outcome = simulate_execution(signal, frame, _CONFIG)
    assert outcome.reason == ExecutionReason.TIME_EXIT
    assert outcome.exit_timestamp == pd.Timestamp("2024-01-02 02:16")


def test_eleventh_inactive_minute_liquidates_on_next_active_open() -> None:
    frame = _frame(periods=15)
    frame.loc[1:11, "is_active_quote"] = 0
    signal = _signal(end="2024-01-02 02:18")
    outcome = simulate_execution(signal, frame, _CONFIG)
    assert outcome.reason == ExecutionReason.STALE_ACTIVITY_LIQUIDATION
    assert outcome.exit_timestamp == pd.Timestamp("2024-01-02 02:17")
    assert outcome.gap_minutes == 11


def test_stale_run_without_active_time_exit_is_unresolved() -> None:
    frame = _frame(periods=12)
    frame.loc[1:, "is_active_quote"] = 0
    signal = _signal(end="2024-01-02 02:16")
    outcome = simulate_execution(signal, frame, _CONFIG)
    assert outcome.status == ExecutionStatus.UNRESOLVED
    assert outcome.reason == ExecutionReason.UNRESOLVED_STALE_EXIT
    assert outcome.net_r is None


def test_exact_window_end_uses_bar_open_and_market_slippage() -> None:
    frame = _frame()
    frame.loc[
        frame["timestamp"] == pd.Timestamp("2024-01-02 02:15"),
        "open",
    ] = 100.5
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    assert outcome.reason == ExecutionReason.TIME_EXIT
    assert outcome.exit_price_raw == pytest.approx(100.5)
    assert outcome.exit_price == pytest.approx(100.25)
    assert outcome.holding_minutes == 10


def test_missing_or_inactive_time_exit_is_unresolved() -> None:
    frame = _frame()
    frame = _preserve_fixture_marker(
        frame[frame["timestamp"] != pd.Timestamp("2024-01-02 02:15")]
    )
    missing = simulate_execution(_signal(), frame, _CONFIG)
    assert missing.reason == ExecutionReason.UNRESOLVED_TIME_EXIT

    frame = _frame()
    frame.loc[frame["timestamp"] == pd.Timestamp("2024-01-02 02:15"), "is_active_quote"] = 0
    inactive = simulate_execution(_signal(), frame, _CONFIG)
    assert inactive.reason == ExecutionReason.UNRESOLVED_TIME_EXIT


def test_commission_is_separate_from_slippage_and_net_r() -> None:
    frame = _frame()
    frame.loc[0, "high"] = 103.0
    outcome = simulate_execution(_signal(), frame, _CONFIG)
    expected_risk_dollars = 1.25 * 20.0
    expected_commission_r = 4.50 / expected_risk_dollars
    assert outcome.commission_dollars == pytest.approx(4.50)
    assert outcome.commission_r == pytest.approx(expected_commission_r)
    assert outcome.net_r == pytest.approx(2.0 - expected_commission_r)


@pytest.mark.parametrize("exit_case", ["target", "stop", "gap", "time"])
def test_prefix_replay_reproduces_determining_exit(exit_case: str) -> None:
    frame = _frame()
    if exit_case == "target":
        frame.loc[2, "high"] = 103.0
    elif exit_case == "stop":
        frame.loc[2, "low"] = 98.0
    elif exit_case == "gap":
        missing = pd.Timestamp("2024-01-02 02:07")
        frame = _preserve_fixture_marker(frame[frame["timestamp"] != missing])
    assert validate_execution_prefix(_signal(), frame, _CONFIG) is True


def test_signal_and_input_frame_are_not_mutated() -> None:
    frame = _frame()
    before_frame = frame.copy(deep=True)
    before_signal = asdict(_signal())
    simulate_execution(_signal(), frame, _CONFIG)
    pd.testing.assert_frame_equal(frame, before_frame)
    assert asdict(_signal()) == before_signal


def test_duplicate_and_off_grid_timestamps_fail_loudly() -> None:
    duplicate = pd.concat([_frame().iloc[:2], _frame().iloc[:1]], ignore_index=True)
    mark_synthetic_fixture(duplicate)
    with pytest.raises(ValueError, match="duplicate timestamps"):
        simulate_execution(_signal(), duplicate, _CONFIG)

    off_grid = _frame()
    off_grid.loc[0, "timestamp"] += pd.Timedelta(seconds=30)
    with pytest.raises(ValueError, match="off-grid timestamps"):
        simulate_execution(_signal(), off_grid, _CONFIG)


def test_activity_audit_can_be_disabled_for_generic_synthetic_bars() -> None:
    frame = _frame().drop(columns="is_active_quote")
    mark_synthetic_fixture(frame)
    config = ExecutionConfig(
        tick_size=0.25,
        point_value=20.0,
        commission_per_side=2.25,
        activity_column=None,
    )
    outcome = simulate_execution(_signal(), frame, config)
    assert outcome.reason == ExecutionReason.TIME_EXIT


def test_execution_module_never_calls_active_dtr_signal_generator() -> None:
    source = inspect.getsource(execution_module)
    assert "generate_signals" not in source
    assert "dtr_lab.research.engine" not in source
