from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest

from dtr_lab.research import StrategyConfig, resample_5m, run_backtest
from dtr_lab.research import engine, integrity


def _market_with_unsafe_gap() -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-07 09:00", "2025-01-07 10:05", freq="1min")
    timestamps = timestamps[timestamps != pd.Timestamp("2025-01-07 10:02")]
    prices = 100.0 + np.arange(len(timestamps), dtype=float) * 0.01
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": prices,
            "high": prices + 0.25,
            "low": prices - 0.25,
            "close": prices + 0.05,
            "volume": np.full(len(timestamps), 10.0),
        }
    )


def _session(bars: pd.DataFrame) -> pd.DataFrame:
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    return pd.DataFrame(
        [
            {
                "session": "NEW_YORK_9AM",
                "session_date": pd.Timestamp("2025-01-07"),
                "range_start": pd.Timestamp("2025-01-07 09:00"),
                "range_end": pd.Timestamp("2025-01-07 09:30"),
                "break_end": pd.Timestamp("2025-01-07 10:01"),
                "range_high": 101.0,
                "range_low": 100.0,
                "range_size": 1.0,
                "post_start_index": int(
                    np.searchsorted(
                        bar_times,
                        np.datetime64(pd.Timestamp("2025-01-07 09:30")),
                        side="left",
                    )
                ),
                "post_end_index": int(
                    np.searchsorted(
                        bar_times,
                        np.datetime64(pd.Timestamp("2025-01-07 10:01")),
                        side="left",
                    )
                ),
                "weekday": 1,
            }
        ]
    )


def _trade() -> engine.Trade:
    return engine.Trade(
        config_name="test",
        session="NEW_YORK_9AM",
        session_date=pd.Timestamp("2025-01-07"),
        direction=1,
        entry_time=pd.Timestamp("2025-01-07 10:00"),
        exit_time=pd.Timestamp("2025-01-07 10:05"),
        entry_price=100.0,
        stop_price=99.0,
        exit_reason="MAX_HOLD",
        pnl_r=0.5,
        pnl_dollars=10.0,
        mfe_r=1.0,
        mae_r=0.2,
        holding_minutes=5,
        sweep_score=3,
        day_of_week=1,
    )


def test_observe_only_preserves_trade_and_reports_bridge(monkeypatch) -> None:
    one = _market_with_unsafe_gap()
    bars = resample_5m(one)
    sessions = _session(bars)
    original_post_end = int(sessions.iloc[0]["post_end_index"])
    trade = _trade()

    def legacy_run(
        one_arg,
        bars_arg,
        sessions_arg,
        cfg_arg,
        market_arrays=None,
    ):
        assert int(sessions_arg.iloc[0]["post_end_index"]) == original_post_end
        return pd.DataFrame([asdict(trade)]), engine.Funnel(sessions=1, trades=1)

    monkeypatch.setattr(integrity, "_BASE_RUN_BACKTEST", legacy_run)

    trades, funnel = run_backtest(
        one,
        bars,
        sessions,
        StrategyConfig(name="test"),
        gap_policy="observe_only",
    )

    assert len(trades) == 1
    assert funnel.as_dict()["observed_unsafe_gap_bridges"] == 1
    assert funnel.as_dict()["skipped_unsafe_gap_bridge"] == 0
    assert funnel.as_dict()["trades"] == 1


def test_unknown_gap_policy_fails_closed() -> None:
    one = _market_with_unsafe_gap()
    bars = resample_5m(one)
    sessions = _session(bars)

    with pytest.raises(ValueError, match="Unknown gap policy"):
        run_backtest(
            one,
            bars,
            sessions,
            StrategyConfig(name="test"),
            gap_policy="fill_missing",  # type: ignore[arg-type]
        )
