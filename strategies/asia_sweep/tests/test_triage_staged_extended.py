from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep import triage_modeling_v2 as triage
from dtr_lab.strategies.asia_sweep.extended_targets import _first_passage_label
from dtr_lab.strategies.asia_sweep.staged_execution_v2 import (
    Tranche,
    _trade_pnl,
    prepare_staged_population,
    simulate_staged_event,
)


def test_inner_direction_predictions_are_group_held_out(monkeypatch) -> None:
    rows: list[dict[str, object]] = []
    for week_index in range(6):
        for row_index in range(2):
            rows.append(
                {
                    "week_key": f"2015-W{week_index + 1:02d}",
                    "resolved_target": 1 if row_index == 0 or week_index % 2 else 0,
                    "reversal_target": (week_index + row_index) % 2,
                }
            )
    frame = pd.DataFrame(rows)
    fitted_weeks: list[set[str]] = []

    class FakeModel:
        def __init__(self, weeks: set[str]) -> None:
            self.weeks = weeks

        def predict_proba(self, validation: pd.DataFrame) -> np.ndarray:
            assert self.weeks.isdisjoint(set(validation["week_key"]))
            probability = np.full(len(validation), 0.6)
            return np.column_stack([1.0 - probability, probability])

    def fake_fit(frame: pd.DataFrame, **_: object) -> FakeModel:
        weeks = set(frame["week_key"])
        fitted_weeks.append(weeks)
        return FakeModel(weeks)

    monkeypatch.setattr(triage, "_fit_weighted_model", fake_fit)
    probability, _, _ = triage._inner_component_predictions(
        frame,
        family="hgb",
        target="reversal_target",
        config=(0.04, 7),
    )
    assert len(fitted_weeks) == 3
    assert np.isfinite(probability).all()


def test_action_thresholds_are_rowwise_and_append_invariant() -> None:
    probability = pd.DataFrame(
        {
            "p_continuation": [0.80, 0.10],
            "p_reversal": [0.05, 0.70],
            "p_unresolved": [0.15, 0.20],
        }
    )
    threshold = (0.65, 0.75, 0.30, 0.25)
    first = triage.apply_actions(probability, threshold)
    appended = pd.concat([probability, probability.iloc[[0]]], ignore_index=True)
    second = triage.apply_actions(appended, threshold)[:2]
    assert first.tolist() == ["CONTINUATION", "REVERSAL"]
    assert second.tolist() == first.tolist()


def _staged_rows(*, continuation_cancel: bool) -> pd.DataFrame:
    base = {
        "event_id": "EURUSD_2015-01-06_DOWN_0800",
        "instrument": "EURUSD",
        "trade_date": "2015-01-06",
        "week_key": "2015-W02",
        "year": 2015,
        "weekday": 1,
        "side": "DOWN",
        "sweep_timestamp_utc": pd.Timestamp("2015-01-06T08:00:00Z"),
        "asian_midpoint": 1.1010,
        "stop_price": 1.0980,
    }
    return pd.DataFrame(
        [
            {
                **base,
                "landmark": "T0",
                "entry_timestamp_utc": pd.Timestamp("2015-01-06T08:01:00Z"),
                "entry_price": 1.0990,
                "p_reversal": 0.20,
                "p_continuation": 0.60,
                "p_unresolved": 0.20,
            },
            {
                **base,
                "landmark": "T1",
                "entry_timestamp_utc": pd.Timestamp("2015-01-06T08:02:00Z"),
                "entry_price": 1.0992,
                "p_reversal": 0.05 if continuation_cancel else 0.20,
                "p_continuation": 0.80 if continuation_cancel else 0.60,
                "p_unresolved": 0.15 if continuation_cancel else 0.20,
            },
        ]
    )


def _bars() -> pd.DataFrame:
    index = pd.date_range("2015-01-06T08:01:00Z", periods=120, freq="1min")
    frame = pd.DataFrame(index=index)
    for side, offset in (("bid", -0.00005), ("ask", 0.00005)):
        frame[f"open_{side}"] = 1.0990 + offset
        frame[f"high_{side}"] = 1.0992 + offset
        frame[f"low_{side}"] = 1.0989 + offset
        frame[f"close_{side}"] = 1.0991 + offset
    frame["active"] = True
    frame.loc[index[1], "open_bid"] = 1.0994
    frame.loc[index[1], "high_bid"] = 1.1012
    return frame


def test_continuation_cancel_occurs_before_decision_bar_range() -> None:
    result = simulate_staged_event(
        _staged_rows(continuation_cancel=True),
        _bars(),
        policy="T0_QUARTERS",
    )
    assert result["exit_reason"] == "CONTINUATION_CANCEL"
    assert result["exit_timestamp_utc"] == "2015-01-06T08:02:00+00:00"


def test_tranche_risk_accounting_uses_each_entry_distance() -> None:
    tranches = [
        Tranche(0.25, 1.1000, pd.Timestamp("2015-01-01T00:00:00Z"), 0.0010),
        Tranche(0.50, 1.1010, pd.Timestamp("2015-01-01T00:01:00Z"), 0.0020),
    ]
    result = _trade_pnl(
        tranches,
        exit_price=1.1030,
        exit_reason="TARGET",
        is_long=True,
        pip=0.0001,
    )
    expected = 0.25 * ((1.1030 - 1.10001) / 0.0010)
    expected += 0.50 * ((1.1030 - 1.10101) / 0.0020)
    assert math.isclose(result, expected)


def test_first_passage_uses_executable_side_and_excludes_ambiguity() -> None:
    index = pd.DatetimeIndex([pd.Timestamp("2015-01-06T08:01:00Z")])
    path = pd.DataFrame(
        {
            "low_bid": [1.0995],
            "high_bid": [1.1008],
            "low_ask": [1.0996],
            "high_ask": [1.1012],
        },
        index=index,
    )
    label, ambiguous, reason = _first_passage_label(
        path,
        is_long=True,
        stop=1.0990,
        target=1.1010,
        horizon=pd.Timestamp("2015-01-06T08:02:00Z"),
    )
    assert label == 0.0
    assert not ambiguous
    assert reason == "HORIZON"

    path.loc[index[0], "low_bid"] = 1.0989
    path.loc[index[0], "high_bid"] = 1.1011
    label, ambiguous, reason = _first_passage_label(
        path,
        is_long=True,
        stop=1.0990,
        target=1.1010,
        horizon=pd.Timestamp("2015-01-06T08:02:00Z"),
    )
    assert np.isnan(label)
    assert ambiguous
    assert reason == "AMBIGUOUS_STOP_FIRST"


def test_one_event_per_pair_day_excludes_same_minute_opposites() -> None:
    ledger = pd.DataFrame(
        [
            {
                "event_id": event_id,
                "instrument": "EURUSD",
                "trade_date": "2015-01-06",
                "week_key": "2015-W02",
                "year": 2015,
                "weekday": 1,
                "side": side,
                "sweep_timestamp_utc": "2015-01-06T08:00:00Z",
                "asian_midpoint": 1.10,
                "stop_price": 1.09,
                "landmark": "T0",
                "entry_price": 1.095,
                "entry_timestamp_utc": "2015-01-06T08:01:00Z",
            }
            for event_id, side in (("UP_EVENT", "UP"), ("DOWN_EVENT", "DOWN"))
        ]
    )
    predictions = ledger[["event_id", "landmark"]].copy()
    predictions["p_reversal"] = 0.2
    predictions["p_continuation"] = 0.6
    predictions["p_unresolved"] = 0.2
    predictions["outer_year"] = 2015
    selected, counts = prepare_staged_population(ledger, predictions)
    assert selected.empty
    assert counts["same_minute_side_ambiguous_days"] == 1
