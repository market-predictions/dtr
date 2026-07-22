from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dtr_lab.research import StrategyConfig, engine


def _bars(times: list[str], atr: float = 1.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(times),
            "bar_end": pd.to_datetime(times) + pd.Timedelta(minutes=5),
            "atr14": np.full(len(times), atr),
        }
    )


def _signal(direction: int, entry_time: str, entry_index: int = 0) -> engine.CandidateSignal:
    return engine.CandidateSignal(
        session="NEW_YORK_9AM",
        session_date=pd.Timestamp(entry_time).normalize(),
        direction=direction,
        sweep_index=entry_index,
        entry_index=entry_index,
        entry_time=pd.Timestamp(entry_time),
        entry_price_raw=100.0,
        sweep_extreme=99.0 if direction > 0 else 101.0,
        range_high=101.0,
        range_low=99.0,
        pivot=100.0,
        sweep_score=3,
        day_of_week=1,
    )


def _arrays(opens: list[float]) -> tuple[np.ndarray, ...]:
    times = pd.to_datetime(
        ["2025-01-07 10:00", "2025-01-07 10:01", "2025-01-07 10:05", "2025-01-07 10:06"]
    )
    open_ = np.asarray(opens, dtype=float)
    high = open_ + 0.10
    low = open_ - 0.10
    close = open_.copy()
    return (
        times.to_numpy(dtype="datetime64[ns]").astype(np.int64),
        open_,
        high,
        low,
        close,
    )


def _cfg(**kwargs: object) -> StrategyConfig:
    payload = {
        "name": "gap-test",
        "stop_buffer_ticks": 2,
        "stop_atr_frac": 0.0,
        "slippage_ticks_each_side": 1.0,
        "commission_per_side": 0.0,
        "tp1_rr": 10.0,
        "runner_rr": 20.0,
        "time_close_mode": "none",
        "max_hold_bars": 12,
    }
    payload.update(kwargs)
    return StrategyConfig(**payload)


def test_long_gap_liquidates_at_worse_of_stop_and_post_gap_open() -> None:
    arrays = _arrays([100.0, 100.1, 97.0, 97.1])
    trade = engine._simulate_trade_np(
        *arrays,
        _bars(["2025-01-07 10:00"]),
        _signal(1, "2025-01-07 10:00"),
        _cfg(),
        unsafe_previous_ns=np.array([pd.Timestamp("2025-01-07 10:01").value]),
        unsafe_current_ns=np.array([pd.Timestamp("2025-01-07 10:05").value]),
        gap_policy="liquidate",
    )

    assert trade is not None
    assert trade.exit_reason == "GAP_LIQUIDATION"
    assert trade.exit_time == pd.Timestamp("2025-01-07 10:05")
    assert trade.gap_previous_timestamp == pd.Timestamp("2025-01-07 10:01")
    assert trade.gap_current_timestamp == pd.Timestamp("2025-01-07 10:05")
    assert trade.gap_minutes == 4
    assert trade.gap_liquidation_price == pytest.approx(96.75)
    assert trade.pnl_r < -1.0


def test_short_gap_liquidation_is_symmetric() -> None:
    arrays = _arrays([100.0, 99.9, 103.0, 102.9])
    trade = engine._simulate_trade_np(
        *arrays,
        _bars(["2025-01-07 10:00"]),
        _signal(-1, "2025-01-07 10:00"),
        _cfg(),
        unsafe_previous_ns=np.array([pd.Timestamp("2025-01-07 10:01").value]),
        unsafe_current_ns=np.array([pd.Timestamp("2025-01-07 10:05").value]),
        gap_policy="liquidate",
    )

    assert trade is not None
    assert trade.exit_reason == "GAP_LIQUIDATION"
    assert trade.exit_time == pd.Timestamp("2025-01-07 10:05")
    assert trade.gap_liquidation_price == pytest.approx(103.25)
    assert trade.pnl_r < -1.0


def test_gap_crossing_scheduled_close_exits_at_first_observable_open() -> None:
    arrays = _arrays([100.0, 100.1, 99.0, 99.1])
    trade = engine._simulate_trade_np(
        *arrays,
        _bars(["2025-01-07 10:00"]),
        _signal(1, "2025-01-07 10:00"),
        _cfg(time_close_mode="everyday", time_close_hour=10, time_close_minute=3),
        unsafe_previous_ns=np.array([pd.Timestamp("2025-01-07 10:01").value]),
        unsafe_current_ns=np.array([pd.Timestamp("2025-01-07 10:05").value]),
        gap_policy="liquidate",
    )

    assert trade is not None
    assert trade.exit_reason == "GAP_LIQUIDATION"
    assert trade.exit_time == pd.Timestamp("2025-01-07 10:05")


def test_entry_at_gap_resume_does_not_bridge_prior_gap() -> None:
    arrays = _arrays([100.0, 100.1, 100.0, 100.2])
    trade = engine._simulate_trade_np(
        *arrays,
        _bars(["2025-01-07 10:05"]),
        _signal(1, "2025-01-07 10:05"),
        _cfg(max_hold_bars=1),
        unsafe_previous_ns=np.array([pd.Timestamp("2025-01-07 10:01").value]),
        unsafe_current_ns=np.array([pd.Timestamp("2025-01-07 10:05").value]),
        gap_policy="liquidate",
    )

    assert trade is not None
    assert trade.exit_reason != "GAP_LIQUIDATION"
    assert trade.gap_minutes == 0


def test_unknown_trade_gap_policy_fails_closed() -> None:
    arrays = _arrays([100.0, 100.1, 100.2, 100.3])
    with pytest.raises(ValueError, match="Unknown trade gap policy"):
        engine._simulate_trade_np(
            *arrays,
            _bars(["2025-01-07 10:00"]),
            _signal(1, "2025-01-07 10:00"),
            _cfg(),
            gap_policy="ignore_forever",
        )
