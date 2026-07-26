from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.extended_reversal_targets import (
    TARGET_ORDER,
    _label_target,
    _opposing_liquidity_target,
)


def test_extended_target_hierarchy_is_frozen() -> None:
    assert TARGET_ORDER == (
        "EXT_FIXED_3R_1200",
        "EXT_FIXED_4R_1400",
        "EXT_FIXED_2R_1100",
        "EXT_OPPOSING_LIQUIDITY_1400",
        "EXT_OPPOSITE_BOUNDARY_1100",
    )


def test_extended_same_bar_ambiguity_is_stop_first() -> None:
    timestamp = pd.Timestamp("2015-01-06T08:03:00Z")
    bars = pd.DataFrame(
        {
            "low_bid": [1.0980],
            "high_bid": [1.1020],
            "high_ask": [1.1022],
            "low_ask": [1.0982],
            "active": [True],
        },
        index=pd.DatetimeIndex([timestamp]),
    )
    row = pd.Series(
        {
            "instrument": "EURUSD",
            "trade_date": "2015-01-06",
            "entry_timestamp_utc": timestamp,
        }
    )
    outcome = _label_target(
        row,
        bars,
        target_name="EXT_FIXED_2R_1100",
        target_price=1.1015,
        entry_price=1.1000,
        stop_price=1.0995,
        is_long=True,
    )
    assert outcome is not None
    assert outcome["extended_stop_first"] == 1
    assert outcome["extended_ambiguous_stop_first"] == 1
    assert outcome["extended_target_hit"] == 0


def test_opposing_liquidity_is_in_reversal_direction() -> None:
    row = pd.Series({"event_id": "E1"})
    levels = pd.DataFrame(
        [
            {
                "event_id": "E1",
                "available_at_0800": True,
                "level_side": "HIGH",
                "level_price": 1.1010,
            },
            {
                "event_id": "E1",
                "available_at_0800": True,
                "level_side": "HIGH",
                "level_price": 1.1020,
            },
            {
                "event_id": "E1",
                "available_at_0800": True,
                "level_side": "LOW",
                "level_price": 1.0980,
            },
        ]
    )
    assert np.isclose(
        _opposing_liquidity_target(
            row,
            levels,
            is_long=True,
            entry_price=1.1000,
        ),
        1.1010,
    )
    assert np.isclose(
        _opposing_liquidity_target(
            row,
            levels,
            is_long=False,
            entry_price=1.1000,
        ),
        1.0980,
    )


def test_target_behind_entry_is_ineligible() -> None:
    timestamp = pd.Timestamp("2015-01-06T08:03:00Z")
    bars = pd.DataFrame(
        {
            "low_bid": [1.0990],
            "high_bid": [1.1010],
            "high_ask": [1.1012],
            "low_ask": [1.0992],
            "active": [True],
        },
        index=pd.DatetimeIndex([timestamp]),
    )
    row = pd.Series(
        {
            "instrument": "EURUSD",
            "trade_date": "2015-01-06",
            "entry_timestamp_utc": timestamp,
        }
    )
    assert (
        _label_target(
            row,
            bars,
            target_name="EXT_OPPOSITE_BOUNDARY_1100",
            target_price=1.0990,
            entry_price=1.1000,
            stop_price=1.0980,
            is_long=True,
        )
        is None
    )
