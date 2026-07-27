from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import (
    TrendConfig,
    build_h4_health,
    build_monthly_context,
    build_new_york_daily_bars,
    build_new_york_h4_bars,
    build_structure_ledger,
    confirmed_swings,
    h4_bar_start,
    pivot_day_start,
    traditional_levels,
)


def _frame_from_close(values: np.ndarray, start: str = "2020-01-01") -> pd.DataFrame:
    index = pd.date_range(start, periods=len(values), freq="D", tz="UTC")
    frame = pd.DataFrame(index=index)
    frame["open"] = values
    frame["high"] = values + 0.30
    frame["low"] = values - 0.30
    frame["close"] = values
    return frame


def _bull_sequence() -> pd.DataFrame:
    values = np.full(70, 100.0)
    values[:20] = 100.0 + np.sin(np.arange(20) / 2.0) * 0.5
    sequence = {
        20: 99.0,
        21: 97.0,
        22: 94.0,
        23: 91.0,
        24: 90.0,
        25: 92.0,
        26: 95.0,
        27: 98.0,
        28: 100.0,
        29: 98.0,
        30: 96.0,
        31: 93.0,
        32: 91.0,
        33: 90.1,
        34: 92.0,
        35: 95.0,
        36: 98.0,
        37: 100.0,
        38: 102.0,
        39: 101.0,
        40: 100.5,
        41: 99.8,
        42: 98.5,
        43: 96.0,
        44: 97.5,
        45: 99.5,
        46: 103.0,
        47: 104.0,
        48: 103.0,
        49: 102.0,
        50: 101.0,
        51: 100.0,
        52: 99.0,
        53: 98.0,
        54: 97.0,
        55: 96.0,
        56: 95.0,
        57: 94.0,
        58: 93.0,
        59: 92.0,
        60: 91.0,
        61: 90.0,
        62: 89.0,
        63: 88.0,
        64: 87.0,
        65: 86.0,
        66: 85.0,
        67: 84.0,
        68: 83.0,
        69: 82.0,
    }
    for position, value in sequence.items():
        values[position] = value
    return _frame_from_close(values)


def _bear_sequence() -> pd.DataFrame:
    bull = _bull_sequence()
    frame = bull.copy()
    frame["open"] = 200.0 - bull["open"]
    frame["close"] = 200.0 - bull["close"]
    frame["high"] = 200.0 - bull["low"]
    frame["low"] = 200.0 - bull["high"]
    return frame


def _sparse_minutes(timestamps: list[str]) -> pd.DataFrame:
    index = pd.DatetimeIndex(timestamps)
    values = np.arange(len(index), dtype=float) + 100.0
    frame = pd.DataFrame(index=index)
    frame["open"] = values
    frame["high"] = values + 0.10
    frame["low"] = values - 0.10
    frame["close"] = values
    return frame


def test_swing_is_observed_only_after_right_side_closes() -> None:
    frame = _frame_from_close(np.array([5.0, 4.0, 3.0, 4.0, 5.0]))
    swings = confirmed_swings(
        frame,
        TrendConfig(swing_left=2, swing_right=2, atr_length=2),
    )
    low = swings.loc[swings["kind"].eq("LOW")].iloc[0]
    assert low["pivot_pos"] == 2
    assert low["observed_pos"] == 4
    assert low["observed_timestamp"] == frame.index[4]


def test_bull_trend_requires_full_sequence_and_is_not_backdated() -> None:
    ledger, _swings = build_structure_ledger(_bull_sequence())
    bos_timestamp = ledger.index[ledger["events"].str.contains("BULL_BOS")][0]
    confirm_timestamp = ledger.index[
        ledger["events"].str.contains("BULL_TREND_CONFIRMED")
    ][0]
    assert ledger.loc[bos_timestamp, "confirmed_direction"] == "NONE"
    assert confirm_timestamp > bos_timestamp
    assert ledger.loc[confirm_timestamp, "confirmed_direction"] == "BULL"
    before = ledger.loc[ledger.index < confirm_timestamp, "confirmed_direction"]
    assert not before.eq("BULL").any()


def test_bear_sequence_is_exact_mirror() -> None:
    ledger, _swings = build_structure_ledger(_bear_sequence())
    confirm = ledger.index[ledger["events"].str.contains("BEAR_TREND_CONFIRMED")][0]
    assert ledger.loc[confirm, "confirmed_direction"] == "BEAR"
    assert ledger["events"].str.contains("BEAR_DOUBLE_TOP").any()
    assert ledger["events"].str.contains("BEAR_BOS").any()
    assert ledger["events"].str.contains("BEAR_RETEST").any()
    assert ledger["events"].str.contains("BEAR_LOWER_HIGH").any()


def test_h4_health_detects_expanding_bullish_alignment() -> None:
    index = pd.date_range("2020-01-01", periods=80, freq="4h", tz="UTC")
    increments = np.linspace(0.05, 0.40, len(index))
    close = 100.0 + np.cumsum(increments)
    frame = pd.DataFrame(index=index)
    frame["open"] = close
    frame["high"] = close + 0.20
    frame["low"] = close - 0.20
    frame["close"] = close
    health = build_h4_health(
        frame,
        fast_length=3,
        medium_length=5,
        slow_length=8,
        atr_length=3,
        slope_bars=2,
        compression_atr=0.01,
    )
    assert health.iloc[-1]["health_state"] == "BULL_EXPANDING"


def test_traditional_monthly_levels_are_exact() -> None:
    assert traditional_levels(110.0, 100.0, 105.0) == {
        "P": 105.0,
        "R1": 110.0,
        "S1": 100.0,
        "R2": 115.0,
        "S2": 95.0,
        "M1": 97.5,
        "M2": 102.5,
        "M3": 107.5,
        "M4": 112.5,
    }


def test_monthly_context_uses_completed_prior_month_only() -> None:
    index = pd.date_range(
        "2020-01-01 22:00:00+00:00",
        periods=60,
        freq="D",
    )
    close = np.r_[np.linspace(101.0, 105.0, 31), np.linspace(106.0, 110.0, 29)]
    frame = pd.DataFrame(index=index)
    frame["open"] = close
    frame["high"] = close + 1.0
    frame["low"] = close - 1.0
    frame["close"] = close
    context = build_monthly_context(frame)
    february = context.loc[context["month_id"].eq(202002)].iloc[0]
    january = frame.iloc[:31]
    expected = traditional_levels(
        float(january["high"].max()),
        float(january["low"].min()),
        float(january["close"].iloc[-1]),
    )
    assert np.isclose(february["P"], expected["P"])
    assert np.isclose(february["M2"], expected["M2"])
    assert np.isclose(february["R2"], expected["R2"])


def test_new_york_boundaries_are_dst_safe() -> None:
    timestamps = pd.DatetimeIndex(
        [
            "2021-03-15 20:59:00+00:00",
            "2021-03-15 21:00:00+00:00",
            "2021-01-15 21:59:00+00:00",
            "2021-01-15 22:00:00+00:00",
        ]
    )
    expected = pd.DatetimeIndex(
        [
            "2021-03-14 21:00:00+00:00",
            "2021-03-15 21:00:00+00:00",
            "2021-01-14 22:00:00+00:00",
            "2021-01-15 22:00:00+00:00",
        ]
    )
    assert pivot_day_start(timestamps).equals(expected)

    repeated_hour = pd.DatetimeIndex(
        [
            "2021-11-07 05:30:00+00:00",
            "2021-11-07 06:30:00+00:00",
        ]
    )
    starts = h4_bar_start(repeated_hour)
    assert starts[0] == starts[1]


def test_aggregated_bars_are_indexed_at_causal_close() -> None:
    spring = build_new_york_daily_bars(
        _sparse_minutes(
            [
                "2021-03-13 22:00:00+00:00",
                "2021-03-14 20:59:00+00:00",
            ]
        )
    )
    assert spring.index[0] == pd.Timestamp("2021-03-14 21:00:00+00:00")
    assert spring.iloc[0]["bar_start_utc"] == pd.Timestamp(
        "2021-03-13 22:00:00+00:00"
    )
    assert spring.iloc[0]["elapsed_minutes"] == 1380

    fall = build_new_york_daily_bars(
        _sparse_minutes(
            [
                "2021-11-06 21:00:00+00:00",
                "2021-11-07 21:59:00+00:00",
            ]
        )
    )
    assert fall.index[0] == pd.Timestamp("2021-11-07 22:00:00+00:00")
    assert fall.iloc[0]["elapsed_minutes"] == 1500

    repeated = build_new_york_h4_bars(
        _sparse_minutes(
            [
                "2021-11-07 05:30:00+00:00",
                "2021-11-07 06:30:00+00:00",
            ]
        )
    )
    assert repeated.index[0] == pd.Timestamp("2021-11-07 10:00:00+00:00")
    assert repeated.iloc[0]["elapsed_minutes"] == 300
