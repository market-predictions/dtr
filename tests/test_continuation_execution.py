from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from dtr_lab.research import continuation
from dtr_lab.research.continuation import (
    ContinuationConfig,
    ContinuationFunnel,
    ContinuationSignal,
    ContinuationTrade,
)


def _signal() -> ContinuationSignal:
    return ContinuationSignal(
        config_name="TEST",
        session="NEW_YORK_9AM",
        session_date=pd.Timestamp("2025-01-07"),
        day_of_week=1,
        direction=1,
        range_high=100.0,
        range_low=90.0,
        range_size=10.0,
        boundary=100.0,
        break_index=0,
        acceptance_index=0,
        entry_index=0,
        break_time=pd.Timestamp("2025-01-07 09:35"),
        acceptance_time=pd.Timestamp("2025-01-07 09:35"),
        entry_time=pd.Timestamp("2025-01-07 09:35"),
        event_end_time=pd.Timestamp("2025-01-07 10:30"),
        entry_price_raw=101.0,
        acceptance_bars=1,
        entry_mode="immediate",
        break_displacement_atr=0.5,
        break_bar_range_mult=1.0,
        volume_mult=1.0,
        entry_distance_range_pct=0.1,
        vwap_aligned=True,
        vwap_slope_aligned=True,
        er20=0.4,
        adx14=25.0,
        minutes_from_range_end=5,
    )


def test_post_entry_close_inside_exits_failed_breakout() -> None:
    signal = _signal()
    cfg = ContinuationConfig(
        stop_buffer_ticks=4,
        stop_atr_frac=0.0,
        slippage_ticks_each_side=0.0,
    )
    times = pd.date_range("2025-01-07 09:35", "2025-01-07 09:44", freq="1min")
    times_ns = times.to_numpy(dtype="datetime64[ns]").astype(np.int64)
    high = np.full(len(times), 101.25)
    low = np.full(len(times), 100.25)
    close = np.full(len(times), 101.0)
    close[4] = 99.75
    low[4] = 99.50
    bars = pd.DataFrame(
        {
            "bar_end": [pd.Timestamp("2025-01-07 09:40"), pd.Timestamp("2025-01-07 09:45")],
            "atr14": [2.0, 2.0],
        }
    )

    trade = continuation._simulate_continuation_trade(
        times_ns,
        np.full(len(times), 101.0),
        high,
        low,
        close,
        bars,
        signal,
        cfg,
        {pd.Timestamp("2025-01-07 09:40").value, pd.Timestamp("2025-01-07 09:45").value},
    )

    assert trade is not None
    assert trade.exit_reason == "FAILED_BREAKOUT"
    assert trade.exit_time == pd.Timestamp("2025-01-07 09:40")


def test_open_trade_crossing_unsafe_gap_is_rejected(monkeypatch) -> None:
    times = pd.date_range("2025-01-07 09:00", "2025-01-07 10:00", freq="1min")
    times = times[times != pd.Timestamp("2025-01-07 09:40")]
    one = pd.DataFrame(
        {
            "timestamp": times,
            "open": np.full(len(times), 100.0),
            "high": np.full(len(times), 100.5),
            "low": np.full(len(times), 99.5),
            "close": np.full(len(times), 100.0),
            "volume": np.full(len(times), 10.0),
        }
    )
    bars = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2025-01-07 09:35")],
            "bar_end": [pd.Timestamp("2025-01-07 09:40")],
            "atr14": [2.0],
        }
    )
    signal = _signal()
    fake_trade = ContinuationTrade(
        config_name="TEST",
        session=signal.session,
        session_date=signal.session_date,
        day_of_week=signal.day_of_week,
        direction=1,
        acceptance_bars=1,
        entry_mode="immediate",
        break_time=signal.break_time,
        acceptance_time=signal.acceptance_time,
        entry_time=pd.Timestamp("2025-01-07 09:35"),
        exit_time=pd.Timestamp("2025-01-07 09:45"),
        entry_price=101.0,
        stop_price=99.0,
        boundary=100.0,
        exit_reason="EVENT_END",
        pnl_r=0.5,
        pnl_dollars=20.0,
        mfe_r=1.0,
        mae_r=0.5,
        holding_minutes=10,
        break_displacement_atr=0.5,
        break_bar_range_mult=1.0,
        volume_mult=1.0,
        entry_distance_range_pct=0.1,
        vwap_aligned=True,
        vwap_slope_aligned=True,
        er20=0.4,
        adx14=25.0,
        minutes_from_range_end=5,
    )
    monkeypatch.setattr(
        continuation,
        "generate_continuation_signals",
        lambda *_args, **_kwargs: ([signal], ContinuationFunnel()),
    )
    monkeypatch.setattr(
        continuation,
        "_simulate_continuation_trade",
        lambda *_args, **_kwargs: replace(fake_trade),
    )

    trades, funnel = continuation.run_continuation_backtest(
        one,
        bars,
        pd.DataFrame(),
        ContinuationConfig(),
        gap_policy="reject_unsafe",
    )

    assert trades.empty
    assert funnel.skipped_unsafe_gap_bridge == 1


def test_continuation_gap_liquidates_at_worse_of_stop_and_resume_open() -> None:
    signal = _signal()
    cfg = ContinuationConfig(
        stop_buffer_ticks=4,
        stop_atr_frac=0.0,
        slippage_ticks_each_side=0.0,
        failed_breakout_exit=False,
    )
    times = pd.to_datetime(
        [
            "2025-01-07 09:35",
            "2025-01-07 09:36",
            "2025-01-07 09:42",
            "2025-01-07 09:43",
        ]
    )
    times_ns = times.to_numpy(dtype="datetime64[ns]").astype(np.int64)
    open_ = np.array([101.0, 101.0, 98.0, 98.0])
    high = np.array([101.2, 101.2, 98.5, 98.5])
    low = np.array([100.8, 100.8, 97.5, 97.5])
    close = np.array([101.0, 101.0, 98.0, 98.0])
    bars = pd.DataFrame({"bar_end": [pd.Timestamp("2025-01-07 09:40")], "atr14": [2.0]})
    trade = continuation._simulate_continuation_trade(
        times_ns,
        open_,
        high,
        low,
        close,
        bars,
        signal,
        cfg,
        {pd.Timestamp("2025-01-07 09:40").value},
        unsafe_previous_ns=np.array([pd.Timestamp("2025-01-07 09:36").value]),
        unsafe_current_ns=np.array([pd.Timestamp("2025-01-07 09:42").value]),
        gap_policy="liquidate",
    )
    assert trade is not None
    assert trade.exit_reason == "GAP_LIQUIDATION"
    assert trade.exit_time == pd.Timestamp("2025-01-07 09:42")
    assert trade.gap_liquidation_price == 98.0
    assert trade.pnl_r < -1.0
