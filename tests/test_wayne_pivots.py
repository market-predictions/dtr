from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_pivots.pivot_atlas import evaluate_geometry_atlas
from dtr_lab.strategies.wayne_pivots.pivot_geometry import (
    STRUCTURES,
    TARGETS,
    _first_passage,
    build_anatomy_ledger,
    build_structures,
    pivot_day_start,
    traditional_structure,
)


def test_traditional_structure_exact() -> None:
    levels = traditional_structure(110.0, 100.0, 105.0)
    assert levels == {
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


def test_placebo_translation_preserves_wayne_distances() -> None:
    structures = build_structures(110.0, 100.0, 107.0)
    wayne = structures["WAYNE"]
    for name, levels in structures.items():
        assert set(levels) == set(wayne)
        for level in levels:
            assert np.isclose(
                levels[level] - levels["P"],
                wayne[level] - wayne["P"],
            ), name


def test_new_york_boundary_is_dst_safe() -> None:
    timestamps = pd.DatetimeIndex(
        [
            "2021-03-15 20:59:00+00:00",
            "2021-03-15 21:00:00+00:00",
            "2021-01-15 21:59:00+00:00",
            "2021-01-15 22:00:00+00:00",
        ]
    )
    starts = pivot_day_start(timestamps)
    expected = pd.DatetimeIndex(
        [
            "2021-03-14 21:00:00+00:00",
            "2021-03-15 21:00:00+00:00",
            "2021-01-14 22:00:00+00:00",
            "2021-01-15 22:00:00+00:00",
        ]
    )
    assert starts.equals(expected)


def test_same_minute_target_and_stop_is_stop_first() -> None:
    highs = np.array([101.0, 110.0, 103.0])
    lows = np.array([99.0, 90.0, 98.0])
    success, outcome, target_index, stop_index = _first_passage(
        highs,
        lows,
        start_index=0,
        side="BULL",
        target=105.0,
        stop=95.0,
    )
    assert not success
    assert outcome == "AMBIGUOUS_STOP_FIRST"
    assert target_index == stop_index == 1


def _synthetic_quotes() -> pd.DataFrame:
    index = pd.date_range(
        "2021-01-03 22:00:00+00:00",
        periods=4 * 1440,
        freq="min",
    )
    phase = np.linspace(0.0, 16.0 * np.pi, len(index))
    midpoint = 1.1000 + 0.0100 * np.sin(phase)
    spread = 0.0002
    frame = pd.DataFrame(index=index)
    for side, adjustment in (("bid", -spread / 2.0), ("ask", spread / 2.0)):
        frame[f"open_{side}"] = midpoint + adjustment
        frame[f"high_{side}"] = midpoint + adjustment + 0.0004
        frame[f"low_{side}"] = midpoint + adjustment - 0.0004
        frame[f"close_{side}"] = midpoint + adjustment
        frame[f"is_active_quote_{side}"] = 1
    frame["active"] = True
    return frame


def test_anatomy_ledger_is_deterministic_and_unique() -> None:
    ledger, day_ledger = build_anatomy_ledger(
        _synthetic_quotes(),
        symbol="EURUSD",
        start_year=2021,
        end_year=2021,
    )
    assert not ledger.empty
    assert not day_ledger.empty
    assert set(ledger["structure"]).issubset(set(STRUCTURES))
    key = [
        "instrument",
        "pivot_day_start_utc",
        "structure",
        "side",
        "target_name",
    ]
    assert not ledger.duplicated(key).any()
    assert ledger["reward_r"].gt(0.0).all()


def _small_atlas_ledger() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    days = pd.date_range("2020-01-01", periods=25, freq="D", tz="UTC")
    for day in days:
        for structure in STRUCTURES:
            for side, target_names in TARGETS.items():
                for target_name in target_names:
                    rows.append(
                        {
                            "instrument": "EURUSD",
                            "pivot_day_start_utc": day,
                            "pivot_day_local_date": day.date().isoformat(),
                            "year": 2020,
                            "structure": structure,
                            "side": side,
                            "target_name": target_name,
                            "eligible_fresh": True,
                            "success": structure == "WAYNE",
                            "strict_payoff_r": 0.1 if structure == "WAYNE" else 0.0,
                        }
                    )
    return pd.DataFrame(rows)


def test_geometry_gate_cannot_pass_on_small_single_pair_sample() -> None:
    comparison, candidate, _subgroup, decision = evaluate_geometry_atlas(
        _small_atlas_ledger()
    )
    assert len(comparison) == 60
    assert not candidate["passes_geometry"].any()
    assert (
        decision["decision"]["decision"]
        == "FAIL_DAILY_PIVOT_GEOMETRY_STOP_BEFORE_BIAS"
    )
    assert not decision["decision"]["bias_stage_opened"]
