from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dtr_lab.research.cisd import (
    CISDVariant,
    PreparedCISD,
    _signal_config_signature,
    annotate_signal,
    compare_cisd_portfolios,
    simulate_cisd_variant,
    variant_passes,
)
from dtr_lab.research.engine import CandidateSignal, StrategyConfig


def _bars(
    open_price: list[float],
    close: list[float],
    *,
    high: list[float] | None = None,
    low: list[float] | None = None,
) -> pd.DataFrame:
    timestamp = pd.date_range("2025-01-02 09:00", periods=len(open_price), freq="5min")
    high = high or [max(o, c) + 0.25 for o, c in zip(open_price, close, strict=True)]
    low = low or [min(o, c) - 0.25 for o, c in zip(open_price, close, strict=True)]
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "bar_end": timestamp + pd.Timedelta(minutes=5),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "atr14": np.ones(len(open_price)),
            "state_epoch_start": np.zeros(len(open_price), dtype=int),
            "state_epoch_end": np.zeros(len(open_price), dtype=int),
            "contains_reset_gap": np.zeros(len(open_price), dtype=bool),
        }
    )


def _signal(direction: int, sweep: int, entry: int, bars: pd.DataFrame) -> CandidateSignal:
    return CandidateSignal(
        session="NEW_YORK_9AM",
        session_date=pd.Timestamp("2025-01-02"),
        direction=direction,
        sweep_index=sweep,
        entry_index=entry,
        entry_time=pd.Timestamp(bars.iloc[entry]["bar_end"]),
        entry_price_raw=float(bars.iloc[entry]["close"]),
        sweep_extreme=99.0 if direction > 0 else 105.0,
        range_high=104.0,
        range_low=100.0,
        pivot=102.0,
        sweep_score=3,
        day_of_week=3,
    )


def test_bullish_cisd_sequence_and_last_candle_anchors_are_causal() -> None:
    bars = _bars(
        [100.0, 102.0, 101.0, 100.5, 102.0],
        [99.0, 100.0, 100.0, 101.0, 103.0],
        high=[100.25, 102.25, 101.25, 101.25, 103.25],
        low=[98.75, 99.75, 99.75, 99.75, 99.75],
    )
    annotation = annotate_signal(bars, _signal(1, sweep=0, entry=4, bars=bars))

    assert annotation.sequence_confirmed
    assert annotation.last_candle_confirmed
    assert annotation.sequence_anchor == 100.0
    assert annotation.last_anchor == 102.0
    assert annotation.sequence_confirm_index == 3
    assert annotation.last_confirm_index == 4
    assert annotation.sequence_age_bars == 1
    assert annotation.sequence_retest
    assert annotation.sequence_retest_on_entry_bar


def test_bearish_cisd_is_directionally_symmetric() -> None:
    bars = _bars(
        [104.0, 102.0, 103.0, 103.5, 102.0],
        [105.0, 104.0, 104.0, 103.0, 101.0],
    )
    annotation = annotate_signal(bars, _signal(-1, sweep=0, entry=4, bars=bars))

    assert annotation.sequence_confirmed
    assert annotation.last_candle_confirmed
    assert annotation.sequence_anchor == 104.0
    assert annotation.last_anchor == 102.0
    assert annotation.sequence_confirm_index == 3
    assert annotation.last_confirm_index == 4


def test_newer_opposite_delivery_expires_unconfirmed_older_sequence() -> None:
    bars = _bars(
        [100.0, 101.0, 99.5, 102.0, 100.0, 99.0],
        [99.0, 100.0, 101.0, 100.0, 99.0, 101.0],
    )
    annotation = annotate_signal(bars, _signal(1, sweep=0, entry=5, bars=bars))

    # The first bearish sequence cannot be confirmed after the newer bearish
    # sequence begins. Only the latest sequence is eligible at the entry.
    assert annotation.sequence_confirmed
    assert annotation.sequence_start_index == 3
    assert annotation.sequence_end_index == 4
    assert annotation.sequence_confirm_index == 5
    assert annotation.sequence_anchor == 102.0


def test_reset_epoch_invalidates_cisd_window() -> None:
    bars = _bars(
        [100.0, 102.0, 101.0, 100.5, 102.0],
        [99.0, 100.0, 100.0, 101.0, 103.0],
    )
    bars.loc[3:, "state_epoch_start"] = 1
    bars.loc[3:, "state_epoch_end"] = 1
    bars.loc[3, "contains_reset_gap"] = True

    annotation = annotate_signal(bars, _signal(1, sweep=0, entry=4, bars=bars))

    assert not annotation.sequence_confirmed
    assert not annotation.last_candle_confirmed
    assert annotation.epoch == 1


def test_recency_and_retest_policies_use_confirmed_information_only() -> None:
    bars = _bars(
        [100.0, 102.0, 101.0, 100.5, 101.0, 101.5, 102.0],
        [99.0, 100.0, 100.0, 101.0, 101.25, 101.75, 102.5],
        low=[98.75, 99.75, 99.75, 99.75, 100.75, 100.0, 101.75],
    )
    annotation = annotate_signal(bars, _signal(1, sweep=0, entry=6, bars=bars))

    assert annotation.sequence_confirmed
    assert annotation.sequence_age_bars == 3
    assert annotation.sequence_retest
    assert variant_passes(annotation, CISDVariant("recent3", "sequence_recent_3"))
    assert variant_passes(annotation, CISDVariant("recent6", "sequence_recent_6"))
    assert variant_passes(annotation, CISDVariant("retest", "sequence_retest"))


def test_prepared_context_rejects_signal_logic_change() -> None:
    baseline = StrategyConfig()
    prepared = PreparedCISD(
        signals=(),
        annotations=(),
        sessions=0,
        signal_config_signature=_signal_config_signature(baseline),
    )

    with pytest.raises(ValueError, match="signal-generating config"):
        simulate_cisd_variant(
            pd.DataFrame({"timestamp": []}),
            pd.DataFrame(),
            StrategyConfig(pivot_len=2),
            CISDVariant("observe", "observe"),
            prepared,
            market_arrays=(
                np.array([], dtype=np.int64),
                np.array([]),
                np.array([]),
                np.array([]),
                np.array([]),
            ),
        )


def _portfolio_row(
    session: str,
    date: str,
    direction: int,
    entry_time: str,
    pnl_r: float,
) -> dict[str, object]:
    return {
        "session": session,
        "session_date": date,
        "direction": direction,
        "entry_time": entry_time,
        "pnl_r": pnl_r,
    }


def test_compare_portfolios_attributes_removed_and_newly_enabled() -> None:
    reference = pd.DataFrame(
        [
            _portfolio_row("A", "2025-01-01", 1, "2025-01-01 10:00", 1.0),
            _portfolio_row("A", "2025-01-02", -1, "2025-01-02 10:00", -1.0),
        ]
    )
    candidate = pd.DataFrame(
        [
            _portfolio_row("A", "2025-01-02", -1, "2025-01-02 10:00", -1.0),
            _portfolio_row("B", "2025-01-03", 1, "2025-01-03 11:00", 0.5),
        ]
    )

    summary, attribution = compare_cisd_portfolios(reference, candidate)

    assert summary == {"retained": 1, "removed": 1, "added": 1}
    assert set(attribution["status"]) == {"removed", "added"}
