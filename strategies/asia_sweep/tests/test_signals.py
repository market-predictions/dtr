from __future__ import annotations

import pandas as pd

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


def test_aggressive_reclaim_emits_signal_after_close() -> None:
    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [101.0, 102.0, 99.5, 100.5]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
    )
    row = _london_row(ledger)
    assert row["status"] == "SIGNAL"
    assert row["swept_side"] == "LOW"
    assert row["entry_timestamp"] == pd.Timestamp("2024-01-02 03:05")
    assert row["stop_price_raw"] == 99.0
    assert row["target_price_raw"] == 103.5


def test_one_tick_penetration_is_not_a_sweep() -> None:
    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [101.0, 102.0, 99.75, 100.5]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
    )
    row = _london_row(ledger)
    assert row["status"] == "NO_SWEEP"


def test_sweep_without_same_bar_reclaim_is_rejected() -> None:
    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [100.5, 101.0, 99.5, 99.75]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
    )
    row = _london_row(ledger)
    assert row["status"] == "REJECTED"
    assert row["rejection_reason"] == "no_same_bar_reclaim"


def test_wick_variant_requires_morphology() -> None:
    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [100.0, 104.0, 99.5, 100.25]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.WICK_QUALIFIED),
    )
    row = _london_row(ledger)
    assert row["status"] == "REJECTED"
    assert row["rejection_reason"] == "morphology_failed"


def test_displacement_uses_only_prior_body_reference() -> None:
    bars = _base_bars()
    sweep_idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 04:00")][0]
    bars.loc[sweep_idx, ["open", "high", "low", "close"]] = [101.0, 102.0, 99.5, 100.5]
    disp_idx = sweep_idx + 1
    bars.loc[disp_idx, ["open", "high", "low", "close"]] = [100.5, 103.0, 100.25, 102.5]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.DISPLACEMENT),
    )
    row = _london_row(ledger)
    assert row["status"] == "SIGNAL"
    assert bool(row["displacement_present"])
    assert row["displacement_delay_bars"] == 1
    assert row["entry_timestamp"] == pd.Timestamp("2024-01-02 04:10")


def test_double_sweep_same_bar_is_rejected_as_ambiguous() -> None:
    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [105.0, 110.5, 99.5, 105.0]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
    )
    row = _london_row(ledger)
    assert row["status"] == "REJECTED"
    assert row["rejection_reason"] == "ambiguous_double_sweep"


def test_failed_retest_waits_for_confirmed_reaction_and_break() -> None:
    bars = _base_bars()
    i0 = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[i0, ["open", "high", "low", "close"]] = [101.0, 102.0, 99.5, 100.5]
    bars.loc[i0 + 1, ["open", "high", "low", "close"]] = [100.5, 103.0, 100.25, 102.5]
    bars.loc[i0 + 2, ["open", "high", "low", "close"]] = [102.5, 102.75, 101.5, 102.0]
    bars.loc[i0 + 3, ["open", "high", "low", "close"]] = [102.0, 102.25, 100.5, 101.5]
    bars.loc[i0 + 4, ["open", "high", "low", "close"]] = [101.5, 103.5, 101.25, 103.25]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.FAILED_RETEST),
    )
    row = _london_row(ledger)
    assert row["status"] == "SIGNAL"
    assert bool(row["failed_retest_present"])
    assert row["entry_timestamp"] == pd.Timestamp("2024-01-02 03:25")


def test_prefix_replay_preserves_aggressive_signal() -> None:
    from dtr_lab.strategies.asia_sweep.validation import assert_prefix_causality

    bars = _base_bars()
    idx = bars.index[bars["timestamp"] == pd.Timestamp("2024-01-02 03:00")][0]
    bars.loc[idx, ["open", "high", "low", "close"]] = [101.0, 102.0, 99.5, 100.5]
    assert_prefix_causality(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.AGGRESSIVE_RECLAIM),
    )


def test_displacement_reference_includes_pre_window_bars() -> None:
    bars = _base_bars()
    pre = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2024-01-02 00:00",
                "2024-01-02 01:55",
                freq="5min",
            ),
            "open": 104.75,
            "high": 105.25,
            "low": 104.50,
            "close": 105.0,
            "volume": 10.0,
        }
    )
    pre["bar_end"] = pre["timestamp"] + pd.Timedelta(minutes=5)
    bars = pd.concat([pre, bars], ignore_index=True).sort_values("timestamp")
    sweep_idx = bars.index[
        bars["timestamp"] == pd.Timestamp("2024-01-02 02:00")
    ][0]
    bars.loc[sweep_idx, ["open", "high", "low", "close"]] = [
        101.0,
        102.0,
        99.5,
        100.5,
    ]
    bars.loc[sweep_idx + 1, ["open", "high", "low", "close"]] = [
        100.5,
        103.0,
        100.25,
        102.5,
    ]
    ledger = build_event_ledger(
        "NQ",
        _one_minute(),
        bars,
        _cfg(AsiaSweepVariant.DISPLACEMENT),
    )
    row = _london_row(ledger)
    assert row["status"] == "SIGNAL"
    assert row["entry_timestamp"] == pd.Timestamp("2024-01-02 02:10")
