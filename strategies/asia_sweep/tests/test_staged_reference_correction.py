from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.staged_execution_v3 import (
    simulate_staged_event,
)


def _event_rows() -> pd.DataFrame:
    base = {
        "event_id": "EURUSD_2015-01-06_DOWN_0800",
        "instrument": "EURUSD",
        "trade_date": "2015-01-06",
        "week_key": "2015-W02",
        "year": 2015,
        "weekday": 1,
        "side": "DOWN",
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
                "entry_price": 1.0991,
                "p_reversal": 0.05,
                "p_continuation": 0.80,
                "p_unresolved": 0.15,
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
    return frame


def test_static_reference_ignores_continuation_cancel() -> None:
    result = simulate_staged_event(
        _event_rows(),
        _bars(),
        policy="T0_STATIC_025",
    )
    assert result["exit_reason"] != "CONTINUATION_CANCEL"
    assert "CANCEL" not in result["actions"]


def test_staged_policy_retains_continuation_cancel() -> None:
    result = simulate_staged_event(
        _event_rows(),
        _bars(),
        policy="T0_QUARTERS",
    )
    assert result["exit_reason"] == "CONTINUATION_CANCEL"
    assert result["actions"].endswith("T1:CANCEL")
