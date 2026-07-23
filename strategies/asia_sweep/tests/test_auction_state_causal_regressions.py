from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.auction_state import (
    _forward_metrics,
    detect_state,
)

TZ = "America/New_York"


def _bars(rows: list[dict[str, float]]) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02 02:00", periods=len(rows), freq="5min", tz=TZ)
    frame = pd.DataFrame(rows, index=timestamps)
    frame["bar_end"] = frame.index + pd.Timedelta(minutes=5)
    return frame


def _bar(open_: float, high: float, low: float, close: float) -> dict[str, float]:
    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "active": 1,
        "source_bars": 5,
    }


def test_opposite_breach_during_late_rejection_confirmation_is_two_sided() -> None:
    frame = _bars(
        [
            _bar(100.8, 101.4, 100.6, 101.2),
            _bar(101.2, 101.3, 100.4, 100.8),
            _bar(100.8, 100.9, 99.4, 100.2),
            _bar(100.2, 100.5, 98.8, 100.1),
        ]
    )
    state = detect_state(frame, high=101.0, low=99.0)
    assert state is not None
    assert state.state == "TWO_SIDED"
    assert state.opposite_index == 3
    assert state.detection_index == 3


def test_fixed_horizon_excludes_bar_opening_at_horizon_endpoint() -> None:
    timestamps = pd.date_range("2024-01-02 02:00", periods=11, freq="1min", tz=TZ)
    closes = [100.0] * 5 + [110.0] * 6
    minutes = pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "is_active_quote": 1,
        },
        index=timestamps,
    )
    metrics = _forward_metrics(
        minutes,
        pd.Timestamp("2024-01-02 02:00", tz=TZ),
        pd.Timestamp("2024-01-02 02:10", tz=TZ),
        1,
        101.0,
        99.0,
        "ACCEPTANCE",
    )
    assert metrics["return_5m_range_fraction"] == pytest.approx(0.0)
    assert metrics["mfe_5m_range_fraction"] == pytest.approx(0.0)
    assert metrics["return_15m_range_fraction"] > 0.0
