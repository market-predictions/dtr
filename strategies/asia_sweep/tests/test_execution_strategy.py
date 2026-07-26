from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.execution_contract import (
    FROZEN_THRESHOLD,
    amsterdam_1000,
    prepare_execution_events,
)
from dtr_lab.strategies.asia_sweep.execution_metrics import (
    FAIL_DECISION,
    PASS_DECISION,
    choose_discovery_variant,
    summarize_variant,
)
from dtr_lab.strategies.asia_sweep.execution_simulator import simulate_event


def _event(**overrides: object) -> pd.Series:
    values: dict[str, object] = {
        "event_id": "EURUSD_2024-01-02_DOWN_0800",
        "instrument": "EURUSD",
        "trade_date": "2024-01-02",
        "week_key": "2024-W01",
        "year": 2024,
        "weekday": 1,
        "side": "DOWN",
        "prediction": 0.40,
        "t5_timestamp_utc": pd.Timestamp("2024-01-02T08:05:00Z"),
        "asian_high": 1.1020,
        "asian_low": 1.1000,
        "asian_midpoint": 1.1010,
        "asian_range_price": 0.0020,
        "sweep_extreme": 1.0995,
    }
    values.update(overrides)
    return pd.Series(values)


def _bars(*, ambiguous: bool = False) -> pd.DataFrame:
    index = pd.to_datetime(
        [
            "2024-01-02T08:05:00Z",
            "2024-01-02T08:06:00Z",
            "2024-01-02T08:07:00Z",
        ],
        utc=True,
    )
    target_high = 1.1012
    stop_low = 1.0990 if ambiguous else 1.1000
    return pd.DataFrame(
        {
            "open_bid": [1.1000, 1.1000, 1.1008],
            "high_bid": [1.1001, target_high, 1.1010],
            "low_bid": [1.0999, stop_low, 1.1006],
            "close_bid": [1.1000, 1.1008, 1.1009],
            "is_active_quote_bid": [1, 1, 1],
            "open_ask": [1.1002, 1.1002, 1.1010],
            "high_ask": [1.1003, 1.1014, 1.1012],
            "low_ask": [1.1001, 1.1002, 1.1008],
            "close_ask": [1.1002, 1.1010, 1.1011],
            "is_active_quote_ask": [1, 1, 1],
            "active": [True, True, True],
        },
        index=index,
    )


def test_market_entry_occurs_strictly_after_t5_and_uses_ask_for_long() -> None:
    result = simulate_event(
        _event(),
        _bars(),
        variant="MKT_NEXT_OPEN",
        expiry=amsterdam_1000("2024-01-02"),
    )
    assert result["filled"] is True
    assert result["entry_timestamp_utc"] == "2024-01-02T08:06:00+00:00"
    assert result["entry_price"] == pytest.approx(1.1002)
    assert result["exit_reason"] == "TARGET"
    assert result["net_r_0_1"] < result["net_r_0_0"]


def test_same_bar_stop_and_target_is_scored_stop_first() -> None:
    result = simulate_event(
        _event(),
        _bars(ambiguous=True),
        variant="MKT_NEXT_OPEN",
        expiry=amsterdam_1000("2024-01-02"),
    )
    assert result["exit_reason"] == "AMBIGUOUS_STOP_FIRST"
    assert result["ambiguous_stop_first"] is True
    assert result["net_r_0_0"] == pytest.approx(-1.0)


def test_limit_order_cannot_fill_after_its_replacement_expiry() -> None:
    bars = _bars()
    result = simulate_event(
        _event(),
        bars,
        variant="LIMIT_ASIAN_BOUNDARY",
        expiry=pd.Timestamp("2024-01-02T08:06:00Z"),
    )
    assert result["filled"] is False
    assert result["status"] in {"NO_ACTIVE_ENTRY", "UNFILLED"}


def test_execution_population_enforces_threshold_and_t5_unresolved_state() -> None:
    raw_event = _event().to_dict()
    raw_event.pop("prediction")
    events = pd.DataFrame(
        [
            {
                **raw_event,
                "t5_available": True,
                "midpoint_success_09_10": False,
                "midpoint_first_passage_utc": None,
                "barrier_first_passage_utc": None,
                "opposite_first_passage_utc": None,
            }
        ]
    )
    predictions = pd.DataFrame(
        [
            {
                "event_id": events.iloc[0]["event_id"],
                "instrument": "EURUSD",
                "trade_date": "2024-01-02",
                "year": 2024,
                "side": "DOWN",
                "prediction": FROZEN_THRESHOLD,
                "target": 0,
                "landmark": "T5",
                "family": "hgb",
            }
        ]
    )
    eligible = prepare_execution_events(
        events,
        predictions,
        symbol="EURUSD",
        start_year=2024,
        end_year=2024,
    )
    assert len(eligible) == 1
    resolved = events.copy()
    resolved.loc[0, "midpoint_first_passage_utc"] = "2024-01-02T08:05:00Z"
    with pytest.raises(ValueError, match="resolved by T5"):
        prepare_execution_events(
            resolved,
            predictions,
            symbol="EURUSD",
            start_year=2024,
            end_year=2024,
        )


def _orders(expectancy_positive: bool) -> pd.DataFrame:
    rows = []
    start = pd.Timestamp("2015-01-05T08:00:00Z")
    for index in range(200):
        year = 2015 + index % 5
        instrument = "EURUSD" if index % 2 == 0 else "GBPUSD"
        base_r = 0.40 if index % 3 else -0.10
        if not expectancy_positive:
            base_r = -0.20 if index % 2 else 0.05
        rows.append(
            {
                "event_id": f"event-{index:03d}",
                "instrument": instrument,
                "trade_date": f"{year}-01-{index % 20 + 1:02d}",
                "week_key": f"{year}-W{index % 20 + 1:02d}",
                "year": year,
                "weekday": index % 5,
                "side": "UP" if index % 2 else "DOWN",
                "prediction": 0.20 + 0.001 * index,
                "variant": "MKT_NEXT_OPEN",
                "status": "FILLED",
                "filled": True,
                "entry_timestamp_utc": start + pd.Timedelta(minutes=index),
                "reward_risk": 1.5,
                "exit_reason": "TARGET" if base_r > 0 else "STOP",
                "net_r_0_0": base_r,
                "net_r_0_1": base_r - 0.01,
                "net_r_0_25": base_r - 0.025,
            }
        )
    return pd.DataFrame(rows)


def test_discovery_selection_passes_only_an_eligible_frozen_variant() -> None:
    passing = summarize_variant(_orders(True), "MKT_NEXT_OPEN")
    assert passing["eligible"] is True
    pass_selection = choose_discovery_variant(
        [
            passing,
            {**passing, "variant": "LIMIT_ASIAN_BOUNDARY"},
            {**passing, "variant": "LIMIT_HALF_RETRACE"},
        ]
    )
    assert pass_selection["decision"] == PASS_DECISION
    assert pass_selection["selected_variant"] == "MKT_NEXT_OPEN"

    failing = summarize_variant(_orders(False), "MKT_NEXT_OPEN")
    fail_selection = choose_discovery_variant(
        [
            failing,
            {**failing, "variant": "LIMIT_ASIAN_BOUNDARY"},
            {**failing, "variant": "LIMIT_HALF_RETRACE"},
        ]
    )
    assert fail_selection["decision"] == FAIL_DECISION
    assert fail_selection["selected_variant"] is None


def test_entry_variant_manifest_is_not_silently_expanded() -> None:
    from dtr_lab.strategies.asia_sweep.execution_contract import ENTRY_VARIANTS

    assert ENTRY_VARIANTS == (
        "MKT_NEXT_OPEN",
        "LIMIT_ASIAN_BOUNDARY",
        "LIMIT_HALF_RETRACE",
    )
    assert np.isclose(FROZEN_THRESHOLD, 0.18252984704127595, atol=0, rtol=0)
