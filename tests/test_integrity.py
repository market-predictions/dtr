from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.research import StrategyConfig, engine, integrity, resample_5m, run_backtest


def _one_minute(values: list[str]) -> pd.DataFrame:
    timestamps = pd.to_datetime(values)
    prices = 100.0 + np.arange(len(timestamps), dtype=float) * 0.25
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": prices,
            "high": prices + 0.5,
            "low": prices - 0.5,
            "close": prices + 0.25,
            "volume": np.full(len(timestamps), 10.0),
        }
    )


def _range(
    start: str,
    end: str,
    *,
    missing: tuple[str, ...] = (),
) -> pd.DataFrame:
    timestamps = pd.date_range(start, end, freq="1min")
    if missing:
        timestamps = timestamps[~timestamps.isin(pd.to_datetime(list(missing)))]
    return _one_minute([str(value) for value in timestamps])


def _session(
    bars: pd.DataFrame,
    *,
    range_start: str,
    range_end: str,
    break_end: str,
    session: str = "NEW_YORK_9AM",
) -> pd.DataFrame:
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    post_start = int(
        np.searchsorted(bar_times, np.datetime64(pd.Timestamp(range_end)), side="left")
    )
    post_end = int(
        np.searchsorted(bar_times, np.datetime64(pd.Timestamp(break_end)), side="left")
    )
    return pd.DataFrame(
        [
            {
                "session": session,
                "session_date": pd.Timestamp(range_start).normalize(),
                "range_start": pd.Timestamp(range_start),
                "range_end": pd.Timestamp(range_end),
                "break_end": pd.Timestamp(break_end),
                "range_high": 110.0,
                "range_low": 100.0,
                "range_size": 10.0,
                "post_start_index": post_start,
                "post_end_index": post_end,
                "weekday": pd.Timestamp(range_start).weekday(),
            }
        ]
    )


def test_public_package_entry_points_are_integrity_safe_without_engine_mutation() -> None:
    assert resample_5m is integrity.resample_5m
    assert run_backtest is integrity.run_backtest
    assert engine.resample_5m is not resample_5m
    assert engine.run_backtest is not run_backtest


def test_resample_marks_gap_inside_five_minute_bucket() -> None:
    one = _one_minute(
        [
            "2025-01-07 10:00",
            "2025-01-07 10:01",
            "2025-01-07 10:03",
            "2025-01-07 10:04",
            "2025-01-07 10:05",
            "2025-01-07 10:06",
            "2025-01-07 10:07",
            "2025-01-07 10:08",
            "2025-01-07 10:09",
        ]
    )

    bars = resample_5m(one)

    assert int(bars.iloc[0]["source_bars"]) == 4
    assert bool(bars.iloc[0]["contains_reset_gap"])
    assert bool(bars.iloc[0]["contains_unsafe_gap"])
    assert int(bars.iloc[0]["state_epoch_start"]) == 0
    assert int(bars.iloc[0]["state_epoch_end"]) == 1
    assert not bool(bars.iloc[1]["contains_reset_gap"])


def test_session_range_with_gap_is_rejected() -> None:
    one = _range(
        "2025-01-07 01:12",
        "2025-01-07 03:00",
        missing=("2025-01-07 01:30",),
    )
    bars = resample_5m(one)
    sessions = _session(
        bars,
        range_start="2025-01-07 01:12",
        range_end="2025-01-07 02:13",
        break_end="2025-01-07 03:00",
        session="LONDON_2AM",
    )

    sanitized = integrity._sanitize_sessions(one, bars, sessions)

    assert bool(sanitized.iloc[0]["integrity_range_gap_rejected"])


def test_signal_path_stops_before_first_reset_boundary() -> None:
    one = _range(
        "2025-01-07 08:12",
        "2025-01-07 10:00",
        missing=("2025-01-07 09:30",),
    )
    bars = resample_5m(one)
    sessions = _session(
        bars,
        range_start="2025-01-07 08:12",
        range_end="2025-01-07 09:13",
        break_end="2025-01-07 10:00",
    )

    sanitized = integrity._sanitize_sessions(one, bars, sessions)
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    expected_end = int(
        np.searchsorted(
            bar_times,
            np.datetime64(pd.Timestamp("2025-01-07 09:31")),
            side="right",
        )
        - 1
    )

    assert not bool(sanitized.iloc[0]["integrity_range_gap_rejected"])
    assert bool(sanitized.iloc[0]["integrity_signal_path_truncated"])
    assert int(sanitized.iloc[0]["post_end_index"]) == expected_end


def test_legacy_open_trade_gap_rejection_is_reproducible(monkeypatch) -> None:
    one = _range(
        "2025-01-07 09:00",
        "2025-01-07 10:05",
        missing=("2025-01-07 10:02",),
    )
    bars = resample_5m(one)
    sessions = _session(
        bars,
        range_start="2025-01-07 09:00",
        range_end="2025-01-07 09:30",
        break_end="2025-01-07 10:01",
    )
    entry_index = int(
        np.flatnonzero(bars["bar_end"] == pd.Timestamp("2025-01-07 10:00"))[0]
    )
    signal = engine.CandidateSignal(
        session="NEW_YORK_9AM",
        session_date=pd.Timestamp("2025-01-07"),
        direction=1,
        sweep_index=entry_index,
        entry_index=entry_index,
        entry_time=pd.Timestamp("2025-01-07 10:00"),
        entry_price_raw=100.0,
        sweep_extreme=99.0,
        range_high=101.0,
        range_low=100.0,
        pivot=100.5,
        sweep_score=3,
        day_of_week=1,
    )
    trade = engine.Trade(
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

    monkeypatch.setattr(
        integrity,
        "_BASE_GENERATE_SIGNALS",
        lambda bars_arg, sessions_arg, cfg_arg: (
            [signal],
            engine.Funnel(sessions=1, entry_signal=1),
        ),
    )
    monkeypatch.setattr(
        integrity,
        "_BASE_SIMULATE_TRADE",
        lambda *args, **kwargs: trade,
    )

    trades, funnel = run_backtest(
        one,
        bars,
        sessions,
        StrategyConfig(name="test"),
        gap_policy="reject_unsafe",
    )

    assert trades.empty
    assert funnel.as_dict()["skipped_unsafe_gap_bridge"] == 1
    assert funnel.as_dict()["trades"] == 0


def test_clean_trade_remains_in_primary_results(monkeypatch) -> None:
    one = _range("2025-01-07 09:00", "2025-01-07 10:05")
    bars = resample_5m(one)
    sessions = _session(
        bars,
        range_start="2025-01-07 09:00",
        range_end="2025-01-07 09:30",
        break_end="2025-01-07 10:01",
    )
    entry_index = int(
        np.flatnonzero(bars["bar_end"] == pd.Timestamp("2025-01-07 10:00"))[0]
    )
    signal = engine.CandidateSignal(
        session="NEW_YORK_9AM",
        session_date=pd.Timestamp("2025-01-07"),
        direction=1,
        sweep_index=entry_index,
        entry_index=entry_index,
        entry_time=pd.Timestamp("2025-01-07 10:00"),
        entry_price_raw=100.0,
        sweep_extreme=99.0,
        range_high=101.0,
        range_low=100.0,
        pivot=100.5,
        sweep_score=3,
        day_of_week=1,
    )
    trade = engine.Trade(
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

    monkeypatch.setattr(
        integrity,
        "_BASE_GENERATE_SIGNALS",
        lambda bars_arg, sessions_arg, cfg_arg: (
            [signal],
            engine.Funnel(sessions=1, entry_signal=1),
        ),
    )
    monkeypatch.setattr(
        integrity,
        "_BASE_SIMULATE_TRADE",
        lambda *args, **kwargs: trade,
    )

    trades, funnel = run_backtest(one, bars, sessions, StrategyConfig(name="test"))

    assert len(trades) == 1
    assert funnel.as_dict()["skipped_unsafe_gap_bridge"] == 0
    assert funnel.as_dict()["trades"] == 1
