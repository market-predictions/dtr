from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.auction_state import (
    SESSION_SPECS,
    _range_percentile,
    _reference_bounds,
    detect_state,
)
from dtr_lab.strategies.asia_sweep.auction_state_analysis import (
    build_diagnostic_summary,
)
from dtr_lab.strategies.asia_sweep.auction_state_retest import (
    attach_retest_forward_metrics,
)

TZ = "America/New_York"


def _bars(rows: list[dict[str, float]]) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02 02:00", periods=len(rows), freq="5min", tz=TZ)
    frame = pd.DataFrame(rows, index=timestamps)
    frame["bar_end"] = frame.index + pd.Timedelta(minutes=5)
    return frame


def _bar(
    open_: float,
    high: float,
    low: float,
    close: float,
) -> dict[str, float]:
    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "active": 1,
        "source_bars": 5,
    }


def test_acceptance_requires_two_consecutive_outside_closes() -> None:
    frame = _bars(
        [
            _bar(100.5, 101.4, 100.3, 101.2),
            _bar(101.2, 101.8, 101.1, 101.4),
            _bar(101.4, 101.6, 100.8, 100.9),
        ]
    )
    state = detect_state(frame, high=101.0, low=99.0)
    assert state is not None
    assert state.state == "ACCEPTANCE"
    assert state.first_side == "UP"
    assert state.detection_index == 1
    assert state.outside_close_count == 2


def test_rejection_requires_reclaim_plus_two_inside_closes() -> None:
    frame = _bars(
        [
            _bar(99.5, 99.8, 98.6, 99.2),
            _bar(99.2, 99.6, 99.0, 99.3),
            _bar(99.3, 99.7, 99.1, 99.4),
        ]
    )
    state = detect_state(frame, high=101.0, low=99.0)
    assert state is not None
    assert state.state == "REJECTION"
    assert state.first_side == "DOWN"
    assert state.detection_index == 2
    assert state.inside_hold_count == 3


def test_same_bar_double_breach_is_two_sided() -> None:
    frame = _bars([_bar(100.0, 101.5, 98.5, 100.0)])
    state = detect_state(frame, high=101.0, low=99.0)
    assert state is not None
    assert state.state == "TWO_SIDED"
    assert state.first_side == "DOUBLE"
    assert state.detection_index == 0


def test_opposite_breach_before_confirmation_overrides_state() -> None:
    frame = _bars(
        [
            _bar(100.5, 101.4, 100.2, 101.2),
            _bar(101.2, 101.5, 98.8, 100.0),
            _bar(100.0, 100.4, 99.5, 100.1),
        ]
    )
    state = detect_state(frame, high=101.0, low=99.0)
    assert state is not None
    assert state.state == "TWO_SIDED"
    assert state.opposite_index == 1


def test_mixed_closes_remain_unresolved() -> None:
    frame = _bars(
        [
            _bar(100.5, 101.4, 100.0, 100.8),
            _bar(100.8, 101.3, 100.5, 101.1),
            _bar(101.1, 101.2, 100.4, 100.9),
        ]
    )
    state = detect_state(frame, high=101.0, low=99.0)
    assert state is not None
    assert state.state == "UNRESOLVED"
    assert state.detection_index == 2


def test_new_york_reference_is_european_range_not_asian_range() -> None:
    day = pd.Timestamp("2024-01-02", tz=TZ)
    specs = {spec.name: spec for spec in SESSION_SPECS}
    london = _reference_bounds(day, specs["LONDON"])
    new_york = _reference_bounds(day, specs["NEW_YORK"])
    assert london[0] == pd.Timestamp("2024-01-01 18:00", tz=TZ)
    assert london[1] == pd.Timestamp("2024-01-02 02:00", tz=TZ)
    assert new_york[0] == pd.Timestamp("2024-01-02 02:00", tz=TZ)
    assert new_york[1] == pd.Timestamp("2024-01-02 08:30", tz=TZ)


def test_range_percentile_uses_only_prior_history() -> None:
    history = [float(value) for value in range(1, 61)]
    assert _range_percentile(30.5, history) == pytest.approx(0.5)
    assert math.isnan(_range_percentile(1.0, history[:19]))


def _minute_frame() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02 02:00", periods=31, freq="1min", tz=TZ)
    prices = np.linspace(101.0, 104.0, len(timestamps))
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": prices,
            "high": prices + 0.1,
            "low": prices - 0.1,
            "close": prices,
            "is_active_quote": 1,
        }
    )


def test_retest_metrics_anchor_at_retest_resumption() -> None:
    ledger = pd.DataFrame(
        [
            {
                "state_detection_timestamp": pd.Timestamp(
                    "2024-01-02 02:05",
                    tz=TZ,
                ),
                "retest_resume": True,
                "retest_detection_timestamp": pd.Timestamp(
                    "2024-01-02 02:10",
                    tz=TZ,
                ),
                "window_end": pd.Timestamp("2024-01-02 02:30", tz=TZ),
                "hypothesis_direction": 1,
                "reference_high": 101.0,
                "reference_low": 99.0,
            }
        ]
    )
    enriched = attach_retest_forward_metrics(ledger, _minute_frame())
    assert pd.Timestamp(enriched.loc[0, "retest_anchor_timestamp"]) == pd.Timestamp(
        "2024-01-02 02:10",
        tz=TZ,
    )
    assert enriched.loc[0, "retest_return_15m_range_fraction"] > 0


def _diagnostic_row(
    instrument: str,
    trade_date: str,
    session: str,
    *,
    return_30: float,
    return_60: float,
) -> dict[str, object]:
    row: dict[str, object] = {
        "instrument": instrument,
        "trade_date": trade_date,
        "session": session,
        "state": "ACCEPTANCE",
        "compression_bucket": "COMPRESSED",
        "external_confluence": False,
        "retest_resume": False,
        "midpoint_hit": None,
        "projection_hit": True,
        "opposite_boundary_hit": None,
        "retest_midpoint_hit": None,
        "retest_projection_hit": None,
        "retest_opposite_boundary_hit": None,
        "return_session_range_fraction": return_60,
        "mfe_session_range_fraction": abs(return_60) + 0.1,
        "mae_session_range_fraction": 0.1,
        "retest_return_session_range_fraction": math.nan,
        "retest_mfe_session_range_fraction": math.nan,
        "retest_mae_session_range_fraction": math.nan,
        "retest_anchor_timestamp": pd.NaT,
        "retest_anchor_price": math.nan,
        "retest_anchor_active": False,
    }
    for horizon in (5, 15, 30, 60):
        value = return_30 if horizon <= 30 else return_60
        row[f"return_{horizon}m_range_fraction"] = value
        row[f"mfe_{horizon}m_range_fraction"] = abs(value) + 0.1
        row[f"mae_{horizon}m_range_fraction"] = 0.1
        row[f"retest_return_{horizon}m_range_fraction"] = math.nan
        row[f"retest_mfe_{horizon}m_range_fraction"] = math.nan
        row[f"retest_mae_{horizon}m_range_fraction"] = math.nan
    return row


def _candidate_frame(*, second_period_return: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for instrument in ("NQ_PROXY", "ES_PROXY"):
        for index in range(20):
            rows.append(
                _diagnostic_row(
                    instrument,
                    f"2023-03-{index + 1:02d}",
                    "NEW_YORK",
                    return_30=0.1,
                    return_60=0.1,
                )
            )
            rows.append(
                _diagnostic_row(
                    instrument,
                    f"2024-03-{index + 1:02d}",
                    "NEW_YORK",
                    return_30=second_period_return,
                    return_60=second_period_return,
                )
            )
    return pd.DataFrame(rows)


def test_positive_aggregate_is_rejected_when_second_period_decays() -> None:
    summary = build_diagnostic_summary(_candidate_frame(second_period_return=-0.02))
    assert summary["decision"] == (
        "NO_MECHANISM_PASSES_DEVELOPMENT_PROMOTION_STANDARD"
    )
    assert summary["passing_mechanism_sessions"] == []


def test_promotion_key_retains_mechanism_and_session_identity() -> None:
    summary = build_diagnostic_summary(_candidate_frame(second_period_return=0.05))
    assert summary["decision"] == "PROMOTE_ONE_CHALLENGER"
    assert summary["selected_challenger"] == (
        "COMPRESSED_RANGE_ACCEPTANCE:NEW_YORK"
    )
