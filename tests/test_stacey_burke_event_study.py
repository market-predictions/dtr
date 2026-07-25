from __future__ import annotations

import pandas as pd

from stacey_burke_lab.event_study import (
    DEFAULT_STUDY_DEFINITION,
    _nearest_distinct_date_controls,
    match_pair_events,
)


def _candidate_rows() -> pd.DataFrame:
    rows = []
    for day in range(2, 9):
        for minute_offset in (0, 1):
            rows.append(
                {
                    "timestamp_utc": pd.Timestamp(
                        f"2020-01-{day:02d}T08:{minute_offset:02d}:00Z"
                    ),
                    "london_date_key": f"2020-01-{day:02d}",
                    "year": 2020,
                    "weekday": 2,
                    "london_bucket": 32,
                    "pre_return_15m": 0.001 * day + minute_offset * 0.1,
                    "realized_vol_60m": 0.002 * day + minute_offset * 0.1,
                    "raw_forward_change": 0.001 * day,
                    "atr20": 0.01,
                }
            )
    return pd.DataFrame(rows)


def _event_row() -> pd.Series:
    return pd.Series(
        {
            "event_id": "EURUSD-2020-01-01-high",
            "factor_block": "usd_europe",
            "london_date_key": "2020-01-01",
            "reclaim_timestamp": pd.Timestamp("2020-01-01T08:00:00Z"),
            "reversal_direction": "short_reversal",
            "swept_side": "high",
            "atr20": 0.01,
            "pre_return_15m": 0.003,
            "realized_vol_60m": 0.006,
            "event_outcome_atr": 0.25,
            "direction_sign": -1.0,
            "year": 2020,
            "weekday": 2,
            "london_bucket": 32,
        }
    )


def test_matching_uses_five_distinct_control_dates() -> None:
    controls = _nearest_distinct_date_controls(
        event=_event_row(),
        candidates=_candidate_rows(),
        definition=DEFAULT_STUDY_DEFINITION,
    )

    assert len(controls) == 5
    assert controls["london_date_key"].nunique() == 5
    assert controls["timestamp_utc"].is_monotonic_increasing is False
    assert controls.iloc[0]["london_date_key"] == "2020-01-03"


def test_short_reversal_controls_are_direction_signed() -> None:
    matched, controls, summary = match_pair_events(
        events=pd.DataFrame([_event_row()]),
        candidates=_candidate_rows(),
        symbol="EURUSD",
    )

    assert len(matched) == 1
    assert len(controls) == 5
    assert controls["control_london_date"].nunique() == 5
    assert (controls["control_outcome_atr"] < 0).all()
    assert matched.iloc[0]["event_outcome_atr"] == 0.25
    assert matched.iloc[0]["effect_atr"] > 0.25
    assert summary["performance_execution"] is False
    assert summary["strategy_pnl_calculated"] is False
