from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from stoic_123_lab.backtest import simulate
from stoic_123_lab.config import NQ_SPEC, SequenceConfig, load_config_family
from stoic_123_lab.data import resample_ohlcv, validate_one_minute
from stoic_123_lab.detector import detect_sequences, validate_event_chronology
from stoic_123_lab.reporting import validate_no_pooling


def _minute_frame(start: str, closes: list[float]) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=len(closes), freq="min")
    close = np.asarray(closes, dtype=float)
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + 0.10
    low = np.minimum(open_, close) - 0.10
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1.0,
        }
    )


def _bars(closes: list[float], minutes: int = 5) -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-02 09:00", periods=len(closes), freq=f"{minutes}min")
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


def test_one_minute_validation_rejects_bad_ohlc() -> None:
    frame = _minute_frame("2025-01-02 09:00", [100, 101])
    frame.loc[1, "high"] = 99
    try:
        validate_one_minute(frame)
    except ValueError as exc:
        assert "OHLC integrity" in str(exc)
    else:
        raise AssertionError("Bad OHLC should fail")


def test_resampling_uses_bar_open_labels_and_completion_time() -> None:
    frame = _minute_frame("2025-01-02 09:00", [100, 101, 102, 103, 104, 105])
    bars = resample_ohlcv(frame, 5)
    assert bars.iloc[0]["timestamp"] == pd.Timestamp("2025-01-02 09:00")
    assert bars.iloc[0]["bar_end"] == pd.Timestamp("2025-01-02 09:05")
    assert bars.iloc[0]["close"] == 104


def test_event_audit_requires_base_lock_before_breakout() -> None:
    events = pd.DataFrame(
        {
            "direction": [1],
            "step1_time": [pd.Timestamp("2025-01-02 09:05")],
            "retest_time": [pd.Timestamp("2025-01-02 09:10")],
            "base_lock_time": [pd.Timestamp("2025-01-02 09:20")],
            "signal_time": [pd.Timestamp("2025-01-02 09:20")],
            "base_upper": [101.0],
            "base_lower": [99.0],
            "breakout_boundary": [101.0],
            "protective_boundary": [99.0],
        }
    )
    try:
        validate_event_chronology(events)
    except ValueError as exc:
        assert "Non-causal" in str(exc)
    else:
        raise AssertionError("Same-bar base lock and breakout must fail")


def test_detector_does_not_count_a_wick_only_step1() -> None:
    config = SequenceConfig(
        arm_id="TEST",
        description="test",
        ema_fast=2,
        ema_slow=3,
        atr_length=2,
        map_mode="none",
        step1_close_buffer_atr=0,
        step1_min_body_fraction=0,
        require_map_at_step3=False,
    )
    execution = _bars([100, 100, 100, 100])
    execution.loc[3, "high"] = 105
    execution.loc[3, "close"] = 100
    map_bars = _bars([100, 100], minutes=60)
    result = detect_sequences(execution, map_bars, config)
    assert result.funnel["step1"] == 0


def test_detector_locks_base_before_confirmed_breakout() -> None:
    config = SequenceConfig(
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
        base_min_bars=3,
        base_max_bars=5,
        base_max_range_atr=1.50,
        base_min_overlap_ratio=0.50,
        step3_close_buffer_atr=0,
        breakout_expiry_bars=5,
        require_map_at_step3=False,
    )
    execution = _bars([100, 100, 100, 100, 102, 101, 100.8, 100.9, 100.85, 100.9, 102])
    map_bars = _bars([100, 100], minutes=60)
    result = detect_sequences(execution, map_bars, config)
    assert len(result.events) == 1
    event = result.events.iloc[0]
    assert event["direction"] == 1
    assert event["base_lock_time"] < event["signal_time"]
    assert np.isclose(event["base_upper"], 101.1)
    validate_event_chronology(result.events)


def test_next_open_fill_and_opposite_step3_exit() -> None:
    one = _minute_frame("2025-01-02 09:00", [100, 101, 102, 103, 104, 105, 106, 105])
    entry_events = pd.DataFrame(
        {
            "arm_id": ["TEST"],
            "direction": [1],
            "signal_time": [pd.Timestamp("2025-01-02 09:02")],
            "breakout_close": [102.0],
            "protective_boundary": [99.0],
            "base_lock_time": [pd.Timestamp("2025-01-02 09:01")],
        }
    )
    management = pd.DataFrame(
        {
            "direction": [-1],
            "signal_time": [pd.Timestamp("2025-01-02 09:06")],
        }
    )
    config = SequenceConfig(
        arm_id="TEST",
        description="test",
        fill_mode="next_open",
        stop_buffer_ticks=0,
        minimum_risk_ticks=1,
        slippage_ticks_each_side=0,
    )
    spec = replace(NQ_SPEC, commission_per_side=0)
    trades = simulate(one, entry_events, management, spec, config)
    assert len(trades) == 1
    assert trades.iloc[0]["entry_time"] == pd.Timestamp("2025-01-02 09:02")
    assert trades.iloc[0]["entry_price"] == 101.0
    assert trades.iloc[0]["exit_time"] == pd.Timestamp("2025-01-02 09:06")
    assert trades.iloc[0]["exit_reason"] == "opposite_step3"


def test_gap_liquidates_open_trade_without_bridging() -> None:
    one = _minute_frame("2025-01-02 09:00", [100, 101, 102])
    later = _minute_frame("2025-01-02 10:00", [110, 111])
    one = pd.concat([one, later], ignore_index=True)
    entry_events = pd.DataFrame(
        {
            "arm_id": ["TEST"],
            "direction": [1],
            "signal_time": [pd.Timestamp("2025-01-02 09:01")],
            "breakout_close": [101.0],
            "protective_boundary": [95.0],
            "base_lock_time": [pd.Timestamp("2025-01-02 09:00")],
        }
    )
    config = SequenceConfig(
        arm_id="TEST",
        description="test",
        stop_buffer_ticks=0,
        minimum_risk_ticks=1,
        max_hold_minutes=180,
        gap_reset_minutes=15,
        slippage_ticks_each_side=0,
    )
    spec = replace(NQ_SPEC, commission_per_side=0)
    trades = simulate(one, entry_events, pd.DataFrame(), spec, config)
    assert trades.iloc[0]["exit_reason"] == "gap_liquidation"
    assert trades.iloc[0]["exit_time"] == pd.Timestamp("2025-01-02 10:00")


def test_phase1_family_is_fixed_and_unique(tmp_path) -> None:
    config_file = tmp_path / "family.yaml"
    config_file.write_text(
        """
defaults:
  map_mode: ema_alignment
arms:
  - arm_id: A
    description: first
  - arm_id: B
    description: second
    map_mode: none
""",
        encoding="utf-8",
    )
    configs = load_config_family(config_file)
    assert [config.arm_id for config in configs] == ["A", "B"]


def test_summary_pooling_is_rejected() -> None:
    summary = pd.DataFrame({"instrument": ["NQ", "NQ_ES_POOL"]})
    try:
        validate_no_pooling(summary)
    except ValueError as exc:
        assert "Unexpected instrument" in str(exc) or "Pooled" in str(exc)
    else:
        raise AssertionError("Pooled rows must fail")


def test_independent_reviewer_reconstructs_trade_ledger() -> None:
    from stoic_123_lab.review import independent_trade_review

    trades = pd.DataFrame(
        {
            "pnl_r": [1.0, -0.25],
            "entry_time": pd.to_datetime(["2025-01-02 09:00", "2025-01-02 10:00"]),
            "exit_time": pd.to_datetime(["2025-01-02 09:30", "2025-01-02 10:30"]),
            "signal_time": pd.to_datetime(["2025-01-02 09:00", "2025-01-02 10:00"]),
            "base_lock_time": pd.to_datetime(["2025-01-02 08:55", "2025-01-02 09:55"]),
            "initial_risk_points": [2.0, 3.0],
        }
    )
    summary = {"trades": 2, "net_r": 0.75, "expectancy_r": 0.375}
    review = independent_trade_review(trades, summary, instrument="NQ", arm_id="TEST")
    assert review["status"] == "PASS"
