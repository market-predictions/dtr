from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_labels import (
    enforce_window_and_two_sided_labels,
)


def _event(
    *,
    event_id: str,
    side: str,
    sweep: str,
    midpoint: str | None,
    barrier: str | None,
    success: bool,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "instrument": "EURUSD",
        "trade_date": "2020-01-15",
        "side": side,
        "sweep_timestamp_utc": sweep,
        "midpoint_first_passage_utc": midpoint,
        "barrier_first_passage_utc": barrier,
        "midpoint_success_09_10": success,
        "full_range_success": False,
        "two_sided_ambiguous": False,
        "primary_outcome": "MIDPOINT_SUCCESS_09_10" if success else "STALLED_REACTION",
    }


def test_pre_0900_midpoint_is_early_not_primary_success() -> None:
    events = pd.DataFrame(
        [
            _event(
                event_id="up",
                side="UP",
                sweep="2020-01-15T07:30:00Z",  # 08:30 Amsterdam
                midpoint="2020-01-15T07:50:00Z",  # 08:50 Amsterdam
                barrier=None,
                success=True,
            )
        ]
    )
    result = enforce_window_and_two_sided_labels(events)
    assert bool(result.iloc[0]["early_midpoint"])
    assert not bool(result.iloc[0]["midpoint_success_09_10"])
    assert result.iloc[0]["primary_outcome"] == "EARLY_MIDPOINT"


def test_pre_0900_sweep_can_succeed_after_0900() -> None:
    events = pd.DataFrame(
        [
            _event(
                event_id="up",
                side="UP",
                sweep="2020-01-15T07:30:00Z",
                midpoint="2020-01-15T08:10:00Z",  # 09:10 Amsterdam
                barrier=None,
                success=True,
            )
        ]
    )
    result = enforce_window_and_two_sided_labels(events)
    assert not bool(result.iloc[0]["early_midpoint"])
    assert bool(result.iloc[0]["midpoint_success_09_10"])


def test_later_opposite_sweep_before_resolution_makes_first_event_ambiguous() -> None:
    events = pd.DataFrame(
        [
            _event(
                event_id="up",
                side="UP",
                sweep="2020-01-15T08:05:00Z",
                midpoint="2020-01-15T08:40:00Z",
                barrier=None,
                success=True,
            ),
            _event(
                event_id="down",
                side="DOWN",
                sweep="2020-01-15T08:30:00Z",
                midpoint=None,
                barrier="2020-01-15T08:50:00Z",
                success=False,
            ),
        ]
    )
    result = enforce_window_and_two_sided_labels(events).set_index("event_id")
    assert bool(result.at["up", "two_sided_ambiguous"])
    assert not bool(result.at["up", "midpoint_success_09_10"])
    assert result.at["up", "primary_outcome"] == "TWO_SIDED_AMBIGUOUS"
    assert not bool(result.at["down", "two_sided_ambiguous"])


def test_opposite_sweep_after_resolution_does_not_invalidate_success() -> None:
    events = pd.DataFrame(
        [
            _event(
                event_id="up",
                side="UP",
                sweep="2020-01-15T08:05:00Z",
                midpoint="2020-01-15T08:20:00Z",
                barrier=None,
                success=True,
            ),
            _event(
                event_id="down",
                side="DOWN",
                sweep="2020-01-15T08:30:00Z",
                midpoint=None,
                barrier="2020-01-15T08:50:00Z",
                success=False,
            ),
        ]
    )
    result = enforce_window_and_two_sided_labels(events).set_index("event_id")
    assert not bool(result.at["up", "two_sided_ambiguous"])
    assert bool(result.at["up", "midpoint_success_09_10"])
