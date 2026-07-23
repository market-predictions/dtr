from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.model import AsiaSweepConfig, AsiaSweepVariant
from dtr_lab.strategies.asia_sweep.signals import build_event_ledger


def _one_minute() -> pd.DataFrame:
    ts = pd.date_range("2024-01-01 18:00", "2024-01-02 11:59", freq="1min")
    frame = pd.DataFrame(
        {
            "timestamp": ts,
            "open": 105.0,
            "high": 109.0,
            "low": 101.0,
            "close": 105.0,
            "volume": 1.0,
        }
    )
    frame.loc[frame["timestamp"] == pd.Timestamp("2024-01-01 19:00"), "high"] = 110.0
    frame.loc[frame["timestamp"] == pd.Timestamp("2024-01-01 20:00"), "low"] = 100.0
    return frame


def _base_bars() -> pd.DataFrame:
    ts = pd.date_range("2024-01-02 02:00", "2024-01-02 11:25", freq="5min")
    bars = pd.DataFrame(
        {
            "timestamp": ts,
            "open": 104.75,
            "high": 105.25,
            "low": 104.50,
            "close": 105.0,
            "volume": 10.0,
        }
    )
    bars["bar_end"] = bars["timestamp"] + pd.Timedelta(minutes=5)
    return bars


def _cfg(variant: AsiaSweepVariant) -> AsiaSweepConfig:
    return AsiaSweepConfig(
        name="test",
        variant=variant,
        tick_size=0.25,
        point_value=20.0,
        commission_per_side=2.25,
    )


def _london_row(ledger: pd.DataFrame) -> pd.Series:
    return ledger[
        (ledger["trade_date"] == pd.Timestamp("2024-01-02"))
        & (ledger["execution_window"] == "LONDON")
    ].iloc[0]


def _reclaim_bars() -> pd.DataFrame:
    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [101.0, 102.0, 99.5, 100.5]
    return bars


def test_missing_asia_minute_makes_window_ineligible() -> None:
    one = _one_minute()
    one = one[one["timestamp"] != pd.Timestamp("2024-01-01 19:30")]
    row = _london_row(
        build_event_ledger(
            "NQ",
            one,
            _base_bars(),
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )
    )
    assert row["status"] == "INELIGIBLE"
    assert row["rejection_reason"] == "incomplete_asia_range"
    assert not bool(row["asia_complete"])
    assert row["asia_missing_minutes"] == 1


def test_missing_pre_signal_minute_blocks_signal_causally() -> None:
    one = _one_minute()
    one = one[one["timestamp"] != pd.Timestamp("2024-01-02 02:30")]
    row = _london_row(
        build_event_ledger(
            "NQ",
            one,
            _reclaim_bars(),
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )
    )
    assert row["status"] == "INELIGIBLE"
    assert row["rejection_reason"] == "incomplete_pre_signal_path"
    assert not bool(row["pre_signal_path_complete"])
    assert row["pre_signal_missing_minutes"] == 1


def test_future_gap_does_not_retroactively_remove_signal() -> None:
    one = _one_minute()
    one = one[one["timestamp"] != pd.Timestamp("2024-01-02 05:30")]
    row = _london_row(
        build_event_ledger(
            "NQ",
            one,
            _reclaim_bars(),
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )
    )
    assert row["status"] == "SIGNAL"
    assert bool(row["pre_signal_path_complete"])
    assert not bool(row["execution_window_complete"])
    assert row["execution_missing_minutes"] == 1


def test_incomplete_no_sweep_window_is_not_no_sweep() -> None:
    one = _one_minute()
    one = one[one["timestamp"] != pd.Timestamp("2024-01-02 05:00")]
    row = _london_row(
        build_event_ledger(
            "NQ",
            one,
            _base_bars(),
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )
    )
    assert row["status"] == "INELIGIBLE"
    assert row["rejection_reason"] == "incomplete_execution_window"


def test_duplicate_one_minute_timestamp_is_rejected() -> None:
    one = pd.concat([_one_minute(), _one_minute().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate timestamps"):
        build_event_ledger(
            "NQ",
            one,
            _base_bars(),
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )


def test_wick_thresholds_are_inclusive() -> None:
    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [
        102.0,
        104.5,
        99.5,
        102.5,
    ]
    row = _london_row(
        build_event_ledger(
            "NQ",
            _one_minute(),
            bars,
            _cfg(AsiaSweepVariant.WICK_QUALIFIED),
        )
    )
    assert row["status"] == "SIGNAL"
    assert row["wick_ratio"] == 0.5
    assert row["close_location_value"] == 0.6


def _failed_retest_bars(retest_low: float) -> pd.DataFrame:
    bars = _base_bars()
    i0 = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[i0, ["open", "high", "low", "close"]] = [101.0, 102.0, 99.5, 100.5]
    bars.loc[i0 + 1, ["open", "high", "low", "close"]] = [100.5, 103.0, 100.25, 102.5]
    bars.loc[i0 + 2, ["open", "high", "low", "close"]] = [102.5, 102.75, 101.5, 102.0]
    bars.loc[i0 + 3, ["open", "high", "low", "close"]] = [
        102.0,
        102.25,
        retest_low,
        101.5,
    ]
    bars.loc[i0 + 4, ["open", "high", "low", "close"]] = [101.5, 103.5, 101.25, 103.25]
    return bars


def test_failed_retest_equal_to_original_extreme_is_rejected() -> None:
    row = _london_row(
        build_event_ledger(
            "NQ",
            _one_minute(),
            _failed_retest_bars(99.5),
            _cfg(AsiaSweepVariant.FAILED_RETEST),
        )
    )
    assert row["status"] == "REJECTED"
    assert row["rejection_reason"] == "no_failed_retest"


def test_failed_retest_beyond_original_extreme_is_rejected() -> None:
    row = _london_row(
        build_event_ledger(
            "NQ",
            _one_minute(),
            _failed_retest_bars(99.25),
            _cfg(AsiaSweepVariant.FAILED_RETEST),
        )
    )
    assert row["status"] == "REJECTED"
    assert row["rejection_reason"] == "no_failed_retest"


def test_sweep_before_execution_window_is_ignored() -> None:
    before = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2024-01-02 01:55")],
            "open": [101.0],
            "high": [102.0],
            "low": [99.5],
            "close": [100.5],
            "volume": [10.0],
            "bar_end": [pd.Timestamp("2024-01-02 02:00")],
        }
    )
    bars = pd.concat([before, _base_bars()], ignore_index=True).sort_values("timestamp")
    row = _london_row(
        build_event_ledger(
            "NQ",
            _one_minute(),
            bars,
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )
    )
    assert row["status"] == "NO_SWEEP"


def test_repeated_event_ledger_is_byte_stable() -> None:
    first = build_event_ledger(
        "NQ",
        _one_minute(),
        _reclaim_bars(),
        _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
    )
    second = build_event_ledger(
        "NQ",
        _one_minute(),
        _reclaim_bars(),
        _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
    )
    assert first.to_csv(index=False) == second.to_csv(index=False)


def test_signal_logic_is_instrument_name_independent() -> None:
    nq = _london_row(
        build_event_ledger(
            "NQ",
            _one_minute(),
            _reclaim_bars(),
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )
    )
    es = _london_row(
        build_event_ledger(
            "ES",
            _one_minute(),
            _reclaim_bars(),
            _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
        )
    )
    assert nq["status"] == es["status"] == "SIGNAL"
    assert nq["entry_timestamp"] == es["entry_timestamp"]
    assert nq["direction"] == es["direction"]
