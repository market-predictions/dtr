from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import (
    build_h4_monthly_attribution,
    classify_d1_relation,
    classify_h4_relation,
)


def test_direction_relation_categories_are_frozen() -> None:
    assert classify_h4_relation("BULL", "BULL", "BULL_EXPANDING") == (
        "ALIGNED_HEALTHY"
    )
    assert classify_h4_relation("BULL", "BULL", "BULL_COMPRESSED") == (
        "ALIGNED_UNHEALTHY"
    )
    assert classify_h4_relation("BULL", "NONE", "MIXED") == "NO_H4_DIRECTION"
    assert classify_h4_relation("BULL", "BEAR", "BEAR_EXPANDING") == (
        "OPPOSITE_H4_DIRECTION"
    )
    assert classify_d1_relation("BEAR", "BEAR") == "D1_ALIGNED"
    assert classify_d1_relation("BEAR", "NONE") == "D1_NONE"
    assert classify_d1_relation("BEAR", "BULL") == "D1_OPPOSED"


def test_month_open_uses_last_completed_h4_without_future_leakage() -> None:
    daily_index = pd.DatetimeIndex(
        [
            "2020-01-31 22:00:00+00:00",
            "2020-02-01 22:00:00+00:00",
            "2020-02-02 22:00:00+00:00",
        ]
    )
    daily = pd.DataFrame(index=daily_index)
    daily["bar_start_utc"] = pd.DatetimeIndex(
        [
            "2020-01-30 22:00:00+00:00",
            "2020-01-31 22:00:00+00:00",
            "2020-02-01 22:00:00+00:00",
        ]
    )
    daily["open"] = [100.0, 102.0, 104.0]
    daily["high"] = [101.0, 104.0, 106.0]
    daily["low"] = [99.0, 101.0, 103.0]
    daily["close"] = [100.5, 103.5, 105.5]

    monthly = pd.DataFrame(index=daily_index)
    monthly["month_id"] = [202001, 202002, 202002]
    monthly["month_open"] = [100.0, 102.0, 102.0]
    monthly["month_open_location"] = ["WARMUP", "BUY_ZONE", "BUY_ZONE"]
    for column, values in {
        "M1": [np.nan, 96.0, 96.0],
        "M2": [np.nan, 101.0, 101.0],
        "M3": [np.nan, 103.0, 103.0],
        "M4": [np.nan, 105.0, 105.0],
        "R1": [np.nan, 104.0, 104.0],
        "R2": [np.nan, 108.0, 108.0],
        "S1": [np.nan, 98.0, 98.0],
        "S2": [np.nan, 94.0, 94.0],
    }.items():
        monthly[column] = values

    d1_structure = pd.DataFrame(
        {"confirmed_direction": ["BULL", "BULL", "BULL"]},
        index=daily_index,
    )
    h4_index = pd.DatetimeIndex(
        [
            "2020-01-31 18:00:00+00:00",
            "2020-01-31 22:00:00+00:00",
            "2020-02-01 02:00:00+00:00",
        ]
    )
    h4_structure = pd.DataFrame(
        {"confirmed_direction": ["BULL", "BULL", "BEAR"]},
        index=h4_index,
    )
    h4_health = pd.DataFrame(
        {"health_state": ["BULL_STABLE", "BULL_EXPANDING", "BEAR_EXPANDING"]},
        index=h4_index,
    )

    result = build_h4_monthly_attribution(
        daily,
        monthly,
        d1_structure,
        h4_structure,
        h4_health,
    )
    assert len(result) == 2
    assert result["h4_source_timestamp"].eq(
        pd.Timestamp("2020-01-31 22:00:00+00:00")
    ).all()
    assert result["h4_direction"].eq("BULL").all()
    assert result["h4_health_state"].eq("BULL_EXPANDING").all()
    assert result["h4_relation"].eq("ALIGNED_HEALTHY").all()
    assert result["d1_relation"].eq("D1_ALIGNED").all()
    reached = result.set_index("target_name")["reached_by_month_end"]
    assert bool(reached["M4"])
    assert not bool(reached["R2"])
