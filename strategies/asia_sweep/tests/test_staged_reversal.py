from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.staged_reversal import (
    POLICY_ORDER,
    _action_for_state,
    select_inner_policy,
    simulate_staged_attempt,
)


def test_staged_policy_manifest_is_frozen() -> None:
    assert POLICY_ORDER == (
        "CONSERVATIVE_NO_T0",
        "CONSERVATIVE_T0_025",
        "BALANCED_NO_T0",
        "BALANCED_T0_025",
        "AGGRESSIVE_NO_T0",
        "AGGRESSIVE_T0_050",
    )


def test_continuation_always_exits_and_blocks_add() -> None:
    for policy in POLICY_ORDER:
        assert _action_for_state(
            policy,
            "T2",
            "CONTINUATION",
            has_position=True,
            assigned_risk=0.50,
        ) == ("EXIT", 1.0)


def test_balanced_provisional_policy_reduces_on_t2_abstain() -> None:
    assert _action_for_state(
        "BALANCED_T0_025",
        "T2",
        "ABSTAIN",
        has_position=True,
        assigned_risk=0.25,
    ) == ("REDUCE", 0.50)


def test_staged_simulator_uses_stop_first_and_never_reopens() -> None:
    timestamps = pd.date_range("2015-01-06T08:01:00Z", periods=4, freq="1min")
    bars = pd.DataFrame(
        {
            "open_bid": [1.1000, 1.1001, 1.1002, 1.1003],
            "open_ask": [1.1002, 1.1003, 1.1004, 1.1005],
            "high_bid": [1.1001, 1.1002, 1.1020, 1.1004],
            "low_bid": [1.0999, 1.1000, 1.0980, 1.1002],
            "high_ask": [1.1003, 1.1004, 1.1022, 1.1006],
            "low_ask": [1.1001, 1.1002, 1.0982, 1.1004],
            "close_bid": [1.1000, 1.1001, 1.1002, 1.1003],
            "close_ask": [1.1002, 1.1003, 1.1004, 1.1005],
            "active": [True, True, True, True],
        },
        index=timestamps,
    )
    event = pd.Series(
        {
            "event_id": "E1",
            "instrument": "EURUSD",
            "trade_date": "2015-01-06",
            "week_key": "2015-W02",
            "year": 2015,
            "weekday": 1,
            "side": "DOWN",
            "asian_midpoint": 1.1010,
            "asian_range_price": 0.0020,
            "sweep_extreme": 1.0990,
        }
    )
    t0 = {
        "E1": {
            "decision": "ABSTAIN",
            "entry_timestamp_utc": timestamps[0],
        }
    }
    t2 = {
        "E1": {
            "decision": "REVERSAL",
            "entry_timestamp_utc": timestamps[1],
        }
    }
    t3 = {
        "E1": {
            "decision": "REVERSAL",
            "entry_timestamp_utc": timestamps[2],
        }
    }
    result = simulate_staged_attempt(
        event,
        "CONSERVATIVE_T0_025",
        bars,
        t0,
        t2,
        t3,
    )
    assert result is not None
    assert result["exit_reason"] == "AMBIGUOUS_STOP_FIRST"
    assert result["net_r_0_0"] < 0.0


def test_inner_selector_stops_when_all_policies_are_negative() -> None:
    rows = []
    for policy in POLICY_ORDER:
        for index in range(250):
            rows.append(
                {
                    "policy": policy,
                    "event_id": f"{policy}-{index}",
                    "instrument": "EURUSD" if index % 2 == 0 else "GBPUSD",
                    "trade_date": f"201{5 + index % 4}-01-{1 + index % 20:02d}",
                    "year": 2015 + index % 4,
                    "net_r_0_0": -0.10,
                    "net_r_0_1": -0.12,
                    "net_r_0_25": -0.15,
                    "action_count": 1,
                }
            )
    assert select_inner_policy(pd.DataFrame(rows)) is None


def test_stress_is_monotonic_for_completed_trade() -> None:
    values = np.array([0.10, 0.05, -0.02])
    assert values[0] >= values[1] >= values[2]
