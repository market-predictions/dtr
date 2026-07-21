from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dtr_lab.research.engine import CandidateSignal, StrategyConfig
from dtr_lab.research.ifvg import (
    IFVGVariant,
    PreparedIFVG,
    _signal_config_signature,
    annotate_signals,
    compare_ifvg_portfolios,
    detect_ifvg_events,
    simulate_ifvg_variant,
    variant_passes,
)


def _bars(high: list[float], low: list[float], close: list[float]) -> pd.DataFrame:
    timestamp = pd.date_range("2025-01-02 09:00", periods=len(high), freq="5min")
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "bar_end": timestamp + pd.Timedelta(minutes=5),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "atr14": np.ones(len(high)),
            "state_epoch_start": np.zeros(len(high), dtype=int),
            "state_epoch_end": np.zeros(len(high), dtype=int),
            "contains_reset_gap": np.zeros(len(high), dtype=bool),
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


def test_bearish_fvg_inverts_bullish_only_on_later_close() -> None:
    bars = _bars(
        high=[105.0, 103.0, 101.0, 102.0, 105.0],
        low=[104.0, 102.0, 100.0, 100.5, 103.0],
        close=[104.5, 102.5, 100.5, 101.5, 104.5],
    )
    events = detect_ifvg_events(bars)

    bullish = [event for event in events if event.direction == 1]
    assert len(bullish) == 1
    assert bullish[0].created_index == 2
    assert bullish[0].inversion_index == 4
    assert bullish[0].lower == 101.0
    assert bullish[0].upper == 104.0


def test_bullish_fvg_inverts_bearish_symmetrically() -> None:
    bars = _bars(
        high=[101.0, 102.0, 105.0, 104.5, 102.0],
        low=[100.0, 101.0, 104.0, 101.8, 100.0],
        close=[100.5, 101.5, 104.5, 103.5, 100.5],
    )
    events = detect_ifvg_events(bars)

    bearish = [event for event in events if event.direction == -1]
    assert len(bearish) == 1
    assert bearish[0].created_index == 2
    assert bearish[0].inversion_index == 4
    assert bearish[0].lower == 101.0
    assert bearish[0].upper == 104.0


def test_reset_epoch_prevents_pre_reset_zone_inversion() -> None:
    bars = _bars(
        high=[105.0, 103.0, 101.0, 102.0, 105.0],
        low=[104.0, 102.0, 100.0, 100.5, 103.0],
        close=[104.5, 102.5, 100.5, 101.5, 104.5],
    )
    bars.loc[3:, "state_epoch_start"] = 1
    bars.loc[3:, "state_epoch_end"] = 1
    bars.loc[3, "contains_reset_gap"] = True

    assert detect_ifvg_events(bars) == []


def test_signal_annotation_requires_inversion_after_sweep() -> None:
    bars = _bars(
        high=[105.0, 103.0, 101.0, 102.0, 105.0, 106.0],
        low=[104.0, 102.0, 100.0, 100.5, 103.0, 104.0],
        close=[104.5, 102.5, 100.5, 101.5, 104.5, 105.0],
    )
    events = detect_ifvg_events(bars)
    before = _signal(1, sweep=5, entry=5, bars=bars)
    after = _signal(1, sweep=2, entry=5, bars=bars)

    annotations = annotate_signals(bars, [before, after], events)

    assert not annotations[0].confirmed
    assert annotations[1].confirmed
    assert annotations[1].age_bars == 1


def test_zone_touch_excludes_inversion_bar_and_honours_age_policy() -> None:
    bars = _bars(
        high=[105.0, 103.0, 101.0, 102.0, 105.0, 105.5, 106.0],
        low=[104.0, 102.0, 100.0, 100.5, 103.0, 103.5, 104.5],
        close=[104.5, 102.5, 100.5, 101.5, 104.5, 105.0, 105.5],
    )
    annotation = annotate_signals(
        bars,
        [_signal(1, sweep=2, entry=6, bars=bars)],
        detect_ifvg_events(bars),
    )[0]

    assert annotation.confirmed
    assert annotation.age_bars == 2
    assert annotation.post_inversion_zone_touch
    assert variant_passes(annotation, IFVGVariant("recent3", "recent_3"))
    assert variant_passes(annotation, IFVGVariant("touch", "zone_touch"))


def test_prepared_context_rejects_signal_logic_change() -> None:
    bars = _bars(
        high=[105.0, 103.0, 101.0, 102.0, 105.0],
        low=[104.0, 102.0, 100.0, 100.5, 103.0],
        close=[104.5, 102.5, 100.5, 101.5, 104.5],
    )
    baseline = StrategyConfig()
    prepared = PreparedIFVG(
        signals=(),
        annotations=(),
        events=(),
        sessions=0,
        signal_config_signature=_signal_config_signature(baseline),
    )
    changed = StrategyConfig(pivot_len=2)

    with pytest.raises(ValueError, match="signal-generating config"):
        simulate_ifvg_variant(
            pd.DataFrame({"timestamp": []}),
            bars,
            changed,
            IFVGVariant("observe", "observe"),
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

    summary, attribution = compare_ifvg_portfolios(reference, candidate)

    assert summary == {"retained": 1, "removed": 1, "added": 1}
    assert set(attribution["status"]) == {"removed", "added"}
