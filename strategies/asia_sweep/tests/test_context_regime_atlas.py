from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep import context_regime_atlas as atlas
from dtr_lab.strategies.asia_sweep.context_regime import (
    FACTOR_FAMILIES,
    _agreement,
    _direction_state,
    _range_position,
    _trend_change_state,
    add_stressed_payoff_proxy,
)


def test_direction_and_change_taxonomy() -> None:
    assert _direction_state(0.1, 0.2) == "UP"
    assert _direction_state(-0.1, -0.2) == "DOWN"
    assert _direction_state(0.1, -0.2) == "MIXED"
    assert _agreement("UP", "UP") == "ALIGNED_UP"
    assert _agreement("DOWN", "UP") == "CONFLICT"
    assert _trend_change_state(2.0, 1.0, 1.0) == "ACCELERATING"
    assert _trend_change_state(0.5, 1.0, 1.0) == "DECELERATING"
    assert _trend_change_state(-1.0, 1.0, 1.0) == "CONFLICT"


def test_range_position_uses_frozen_buckets() -> None:
    assert _range_position(99.0, 100.0, 103.0)[1] == "BELOW"
    assert _range_position(100.5, 100.0, 103.0)[1] == "LOWER"
    assert _range_position(101.5, 100.0, 103.0)[1] == "MIDDLE"
    assert _range_position(102.5, 100.0, 103.0)[1] == "UPPER"
    assert _range_position(104.0, 100.0, 103.0)[1] == "ABOVE"


def test_stressed_payoff_uses_next_active_quote_and_correct_side() -> None:
    index = pd.to_datetime(
        [
            "2020-01-02T08:05:00Z",
            "2020-01-02T08:06:00Z",
            "2020-01-02T08:07:00Z",
        ],
        utc=True,
    )
    quotes = pd.DataFrame(
        {
            "open_bid": [1.1000, 1.1001, 1.1002],
            "open_ask": [1.1002, 1.1003, 1.1004],
            "active": [False, True, True],
        },
        index=index,
    )
    context = pd.DataFrame(
        {
            "t5_timestamp_utc": pd.to_datetime(
                ["2020-01-02T08:05:00Z"], utc=True
            ),
            "side": ["DOWN"],
            "sweep_extreme": [1.0990],
            "asian_range_price": [0.0020],
            "asian_midpoint": [1.1020],
            "target": [1],
        }
    )
    result = add_stressed_payoff_proxy(context, quotes, symbol="EURUSD")
    assert bool(result.loc[0, "economic_proxy_eligible"])
    assert result.loc[0, "stressed_reward_risk_proxy"] > 0.0
    assert result.loc[0, "stressed_payoff_proxy"] == result.loc[
        0, "stressed_reward_risk_proxy"
    ]


def _synthetic_atlas() -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2015-01-05", periods=200, freq="7D")
    for date_index, date in enumerate(dates):
        selected = date_index % 2 == 0
        year = 2015 + date_index // 40
        for pair in ("EURUSD", "GBPUSD"):
            row = {
                "event_id": f"{pair}-{date.date()}",
                "instrument": pair,
                "trade_date": str(date.date()),
                "year": year,
                "target": int(selected),
                "stressed_payoff_proxy": 2.0 if selected else -1.0,
                "economic_proxy_eligible": True,
            }
            for factor in FACTOR_FAMILIES:
                row[factor] = "WARMUP"
            row["d1_direction"] = "UP" if selected else "DOWN"
            row["daily_atr_regime"] = "EXPANDED" if selected else "COMPRESSED"
            rows.append(row)
    return pd.DataFrame(rows)


def test_two_independent_families_authorize_interaction_freeze(
    monkeypatch,
) -> None:
    monkeypatch.setattr(atlas, "BOOTSTRAP_DRAWS", 250)
    monkeypatch.setattr(atlas, "PERMUTATION_DRAWS", 250)
    summary, subgroups, decision = atlas.evaluate_single_factor_atlas(
        _synthetic_atlas()
    )
    assert not summary.empty
    assert not subgroups.empty
    assert decision["decision"]["decision"] == (
        "PASS_SINGLE_FACTOR_ATLAS_AUTHORIZE_INTERACTION_FREEZE"
    )
    assert {"HTF_DIRECTION", "VOLATILITY"}.issubset(
        set(decision["decision"]["passing_families"])
    )
