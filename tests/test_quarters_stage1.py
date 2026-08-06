import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dtr_lab.strategies.quarters_theory.stage1 import (  # noqa: E402
    YearData,
    _accepted_crossings,
    _first_passage_symmetric,
    candidate_levels,
    detect_events,
)


def test_candidate_level_phases() -> None:
    close = np.array([1.3001, 1.3399])
    levels = candidate_levels(close)
    assert 13000 in levels
    assert 13250 in levels
    assert set(levels % 50) == {0}


def test_crossing_requires_reset_after_previous_event() -> None:
    close = np.array([0, 70, 110, 80, 110, 70, 110], dtype=float)
    active = np.ones(len(close), dtype=bool)
    accepted = _accepted_crossings(close, active, 100, 1, 25)
    assert accepted == [2, 6]


def test_crossing_ignores_inactive_transition() -> None:
    close = np.array([70, 110], dtype=float)
    active = np.array([False, True])
    assert _accepted_crossings(close, active, 100, 1, 25) == []


def test_first_passage_ordering() -> None:
    high = np.array([1.0005, 1.0012, 1.0013])
    low = np.array([0.9998, 0.9997, 0.9988])
    assert _first_passage_symmetric(high, low, 1.0, 1, 10) == "follow_through"
    assert _first_passage_symmetric(high, low, 1.0, -1, 10) == "reversal"


def test_detect_event_schema_and_directional_return() -> None:
    number_of_rows = 2000
    timestamps = pd.date_range("2020-01-01", periods=number_of_rows, freq="min", tz="UTC")
    close = np.full(number_of_rows, 1.2970)
    close[300:400] = np.linspace(1.2970, 1.3010, 100)
    close[400:] = 1.3015
    year_data = YearData(
        year=2020,
        timestamp_ms=(timestamps.view("int64") // 1_000_000),
        timestamp=timestamps,
        mid_open=close.copy(),
        mid_high=close + 0.0001,
        mid_low=close - 0.0001,
        mid_close=close,
        spread_close_pips=np.full(number_of_rows, 1.0),
        active=np.ones(number_of_rows, dtype=bool),
    )
    events = detect_events(year_data, horizons=(5, 60, 120, 240, 1440))
    upward = events[(events.level_pips == 13000) & (events.direction == 1)]
    assert len(upward) == 1
    assert bool(upward.iloc[0].is_lqp)
    assert upward.iloc[0].return_60m_pips > 0
