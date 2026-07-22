from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.research.cross_market import (
    USA500_PROXY_SPEC,
    classify_proxy_gaps,
    classify_proxy_replication,
    cost_stress_expectancy,
    e6_mask,
)


def test_proxy_gap_contract_separates_short_absence_and_unsafe_gap() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2025-01-02 10:00",
                    "2025-01-02 10:02",
                    "2025-01-02 10:10",
                    "2025-01-02 16:14",
                    "2025-01-02 18:00",
                ]
            ),
            "open": [1.0] * 5,
            "high": [1.0] * 5,
            "low": [1.0] * 5,
            "close": [1.0] * 5,
            "volume": [1.0] * 5,
        }
    )
    gaps = classify_proxy_gaps(frame)
    assert gaps["classification"].tolist() == [
        "short_quote_absence",
        "medium_quote_absence",
        "unclassified_long_gap",
        "daily_maintenance_or_holiday",
    ]
    assert gaps["reject_trade_bridge"].tolist() == [False, True, True, False]


def test_e6_mask_uses_frozen_quarter_atr_threshold() -> None:
    frame = pd.DataFrame(
        {
            "direction": [1, 1, -1, -1],
            "range_high": [110, 110, 110, 110],
            "range_low": [100, 100, 100, 100],
            "prev_d1_high": [120, 120, 112, 114],
            "prev_d1_low": [98, 96, 90, 90],
            "d1_atr20": [8, 8, 8, 8],
        }
    )
    assert e6_mask(frame).tolist() == [False, True, False, True]


def test_cost_stress_uses_instrument_tick_geometry() -> None:
    trades = pd.DataFrame(
        {
            "pnl_r": [0.5, -0.5],
            "entry_price": [100.25, 100.25],
            "stop_price": [99.25, 98.25],
        }
    )
    observed = cost_stress_expectancy(
        trades,
        total_ticks_each_side=2,
        tick_size=USA500_PROXY_SPEC.tick_size,
    )
    expected = np.mean([0.5 - 0.5 / 1.0, -0.5 - 0.5 / 2.0])
    assert np.isclose(observed, expected)


def test_replication_classification_requires_cost_robustness() -> None:
    supported = {
        "net_r": 10,
        "expectancy_r": 0.05,
        "profit_factor": 1.1,
        "two_tick_expectancy_r": 0.01,
        "net_2023": 1,
        "net_2024": 2,
        "net_2025": -1,
    }
    assert classify_proxy_replication(supported) == "DIRECTIONAL_REPLICATION_SUPPORTED"
    supported["two_tick_expectancy_r"] = -0.01
    assert classify_proxy_replication(supported) == "PARTIAL_COST_FRAGILE_REPLICATION"
    supported["expectancy_r"] = -0.01
    assert classify_proxy_replication(supported) == "NO_REPLICATION"
