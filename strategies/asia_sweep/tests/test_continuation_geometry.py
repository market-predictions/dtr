from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.continuation_geometry import (
    _nearest_liquidity_target,
    _simulate_objective,
    build_pair_continuation_geometry,
    select_continuation_objective,
    summarize_objective,
)


def _write_quotes(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    timestamps = pd.date_range(
        "2015-01-06T08:02:00Z",
        periods=4,
        freq="1min",
    )
    bid_open = np.array([1.1000, 1.1002, 1.1004, 1.1006])
    ask_open = bid_open + 0.0002
    for side, opens in (("bid", bid_open), ("ask", ask_open)):
        frame = pd.DataFrame(
            {
                "timestamp_utc": timestamps.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": opens,
                "high": opens + 0.0001,
                "low": opens - 0.0001,
                "close": opens,
                "is_active_quote": 1,
            }
        )
        frame.to_csv(
            directory / f"eurusd_m1_{side}_2015.csv.gz",
            index=False,
            compression="gzip",
        )


def _event() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "E1",
                "instrument": "EURUSD",
                "trade_date": "2015-01-06",
                "year": 2015,
                "weekday": 1,
                "side": "UP",
                "decision": "CONTINUATION",
                "p_continuation": 0.70,
                "entry_timestamp_utc": "2015-01-06T08:03:00Z",
                "asian_high": 1.0995,
                "asian_low": 1.0975,
                "asian_range_price": 0.0020,
                "sweep_extreme": 1.1000,
            }
        ]
    )


def test_upper_sweep_continuation_enters_on_ask(tmp_path: Path) -> None:
    _write_quotes(tmp_path)
    geometry = build_pair_continuation_geometry(
        _event(),
        pd.DataFrame(
            columns=[
                "event_id",
                "available_at_0800",
                "level_side",
                "level_price",
            ]
        ),
        tmp_path,
        symbol="EURUSD",
    )
    row = geometry.loc[geometry["objective"].eq("CONT_RANGE_025_1000")].iloc[0]
    assert np.isclose(row["entry_price"], 1.1004)
    assert np.isclose(row["stop_price"], 1.0993)


def test_same_bar_continuation_ambiguity_is_stop_first() -> None:
    timestamp = pd.Timestamp("2015-01-06T08:03:00Z")
    bars = pd.DataFrame(
        {
            "low_bid": [1.0990],
            "high_bid": [1.1020],
            "high_ask": [1.1022],
            "low_ask": [1.0992],
            "active": [True],
        },
        index=pd.DatetimeIndex([timestamp]),
    )
    event = pd.Series(
        {
            "event_id": "E1",
            "instrument": "EURUSD",
            "trade_date": "2015-01-06",
            "year": 2015,
            "weekday": 1,
            "side": "UP",
            "decision": "CONTINUATION",
            "p_continuation": 0.70,
            "entry_timestamp_utc": timestamp,
        }
    )
    result = _simulate_objective(
        event,
        bars,
        objective="CONT_RANGE_025_1000",
        target_price=1.1015,
        horizon_hour=10,
        entry_price=1.1000,
        stop_price=1.0995,
        is_long=True,
    )
    assert result is not None
    assert result["stop_first"]
    assert result["ambiguous_stop_first"]
    assert not result["target_hit"]


def test_next_liquidity_must_be_beyond_sweep_extreme() -> None:
    event = pd.Series({"event_id": "E1", "sweep_extreme": 1.1010})
    levels = pd.DataFrame(
        [
            {
                "event_id": "E1",
                "available_at_0800": True,
                "level_side": "HIGH",
                "level_price": 1.1005,
            },
            {
                "event_id": "E1",
                "available_at_0800": True,
                "level_side": "HIGH",
                "level_price": 1.1015,
            },
            {
                "event_id": "E1",
                "available_at_0800": True,
                "level_side": "HIGH",
                "level_price": 1.1020,
            },
        ]
    )
    assert np.isclose(_nearest_liquidity_target(event, levels, is_long=True), 1.1015)


def test_geometry_gate_does_not_allow_lift_to_rescue_low_reward_risk() -> None:
    rows = []
    for index in range(500):
        selected = index < 100
        rows.append(
            {
                "event_id": f"E{index}",
                "objective": "CONT_RANGE_025_1000",
                "instrument": "EURUSD" if index % 2 == 0 else "GBPUSD",
                "year": 2015 + index % 5,
                "weekday": index % 5,
                "side": "UP" if index % 2 == 0 else "DOWN",
                "decision": "CONTINUATION" if selected else "ABSTAIN",
                "target_hit": selected or index % 5 == 0,
                "reward_risk": 1.0,
                "reward_risk_stress_010": 0.9,
                "p_continuation": 0.70,
            }
        )
    summary, _ = summarize_objective(pd.DataFrame(rows), "CONT_RANGE_025_1000")
    assert summary["selected_lift"] > 1.60
    assert not summary["gates"]["median_reward_risk"]
    assert not summary["passes"]


def test_objective_selection_uses_frozen_order() -> None:
    summaries = pd.DataFrame(
        [
            {"objective": "CONT_FIXED_2R_1200", "passes": True},
            {"objective": "CONT_RANGE_050_1100", "passes": True},
        ]
    )
    assert select_continuation_objective(summaries) == "CONT_RANGE_050_1100"
