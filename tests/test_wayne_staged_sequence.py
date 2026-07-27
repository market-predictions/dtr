from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import build_staged_monthly_sequence


def _inputs(
    *,
    month_open: float = 98.0,
    h4_close: float = 107.0,
    days: int = 12,
) -> tuple[pd.DataFrame, ...]:
    starts = []
    first = pd.Timestamp("2020-02-02 22:00:00+00:00")
    for day in range(days):
        for bucket in range(6):
            starts.append(first + pd.Timedelta(days=day, hours=4 * bucket))
    starts = pd.DatetimeIndex(starts)
    h4_index = starts + pd.Timedelta(hours=4)
    h4 = pd.DataFrame(index=h4_index)
    h4["bar_start_utc"] = starts
    h4["open"] = h4_close
    h4["high"] = h4_close + 0.20
    h4["low"] = h4_close - 0.20
    h4["close"] = h4_close

    structure = pd.DataFrame(index=h4_index)
    structure["confirmed_direction"] = "NONE"
    structure["events"] = ""
    health = pd.DataFrame(index=h4_index)
    health["health_state"] = "MIXED"

    daily_index = pd.date_range(
        "2020-02-03 22:00:00+00:00",
        periods=days,
        freq="D",
    )
    daily = pd.DataFrame(index=daily_index)
    daily["bar_start_utc"] = daily_index - pd.Timedelta(days=1)
    daily["open"] = month_open
    daily["high"] = 108.0
    daily["low"] = 94.0
    daily["close"] = 106.0

    context = pd.DataFrame(index=daily_index)
    levels = {
        "month_id": 202002,
        "month_open": month_open,
        "M1": 90.0,
        "M2": 95.0,
        "M3": 105.0,
        "M4": 110.0,
        "P": 100.0,
        "R2": 120.0,
        "S2": 80.0,
    }
    for column, value in levels.items():
        context[column] = value

    d1 = pd.DataFrame(index=daily_index)
    d1["confirmed_direction"] = "BULL"
    return daily, context, d1, h4, structure, health


def _bull_rows(result: pd.DataFrame) -> pd.DataFrame:
    if result.empty:
        return result
    return result.loc[result["side"].eq("BULL")].copy()


def test_staged_sequence_is_ordered_and_primary_is_causal() -> None:
    daily, context, d1, h4, structure, health = _inputs()
    structure_timestamp = h4.index[8]
    health_timestamp = h4.index[13]
    target_timestamp = h4.index[20]
    structure.loc[structure_timestamp:, "confirmed_direction"] = "BULL"
    structure.loc[structure_timestamp, "events"] = "BULL_TREND_CONFIRMED"
    health.loc[health_timestamp:, "health_state"] = "BULL_EXPANDING"
    h4.loc[target_timestamp, "high"] = 111.0

    rows = _bull_rows(
        build_staged_monthly_sequence(
            daily,
            context,
            d1,
            h4,
            structure,
            health,
        )
    )
    conservative = rows.loc[rows["target_tier"].eq("CONSERVATIVE")].iloc[0]
    assert conservative["location_source"] == "MONTH_OPEN"
    assert conservative["structure_timestamp"] == structure_timestamp
    assert conservative["health_timestamp"] == health_timestamp
    assert conservative["stage_primary"] == "COMPLETE_ACTIVE"
    assert bool(conservative["signal_target_available"])
    assert bool(conservative["signal_reached_before_invalidation"])


def test_target_before_health_is_preconsumed() -> None:
    daily, context, d1, h4, structure, health = _inputs()
    structure_timestamp = h4.index[8]
    health_timestamp = h4.index[13]
    structure.loc[structure_timestamp:, "confirmed_direction"] = "BULL"
    structure.loc[structure_timestamp, "events"] = "BULL_TREND_CONFIRMED"
    health.loc[health_timestamp:, "health_state"] = "BULL_STABLE"
    h4.loc[h4.index[10], "high"] = 111.0

    rows = _bull_rows(
        build_staged_monthly_sequence(
            daily,
            context,
            d1,
            h4,
            structure,
            health,
        )
    )
    conservative = rows.loc[rows["target_tier"].eq("CONSERVATIVE")].iloc[0]
    assert bool(conservative["signal_target_pre_start"])
    assert not bool(conservative["signal_target_available"])
    assert not bool(conservative["signal_reached_before_invalidation"])


def test_day_five_and_day_ten_are_distinct_landmarks() -> None:
    daily, context, d1, h4, structure, health = _inputs()
    structure_timestamp = h4.index[20]
    health_timestamp = h4.index[32]
    structure.loc[structure_timestamp:, "confirmed_direction"] = "BULL"
    structure.loc[structure_timestamp, "events"] = "BULL_TREND_CONFIRMED"
    health.loc[health_timestamp:, "health_state"] = "BULL_EXPANDING"

    rows = _bull_rows(
        build_staged_monthly_sequence(
            daily,
            context,
            d1,
            h4,
            structure,
            health,
        )
    )
    row = rows.iloc[0]
    assert row["stage_primary"] == "STRUCTURE_NO_HEALTH"
    assert row["stage_sensitivity"] == "COMPLETE_ACTIVE"
    assert not bool(row["sequence_active_primary"])
    assert bool(row["sequence_active_sensitivity"])


def test_preexisting_h4_direction_is_not_a_new_turn() -> None:
    daily, context, d1, h4, structure, health = _inputs(
        month_open=106.0,
        h4_close=98.0,
    )
    structure["confirmed_direction"] = "BULL"
    health["health_state"] = "BULL_EXPANDING"

    rows = _bull_rows(
        build_staged_monthly_sequence(
            daily,
            context,
            d1,
            h4,
            structure,
            health,
        )
    )
    row = rows.iloc[0]
    assert bool(row["preexisting_aligned"])
    assert row["stage_primary"] == "PREEXISTING_ALIGNED"
    assert not bool(row["sequence_complete_primary"])


def test_close_location_excludes_wick_only_touch() -> None:
    daily, context, d1, h4, structure, health = _inputs(
        month_open=106.0,
        h4_close=106.0,
    )
    h4.loc[h4.index[2], "low"] = 99.0
    h4.loc[h4.index[2], "high"] = 101.0

    close_rows = _bull_rows(
        build_staged_monthly_sequence(
            daily,
            context,
            d1,
            h4,
            structure,
            health,
            location_rule="CLOSE_IN_ZONE",
        )
    )
    range_rows = _bull_rows(
        build_staged_monthly_sequence(
            daily,
            context,
            d1,
            h4,
            structure,
            health,
            location_rule="RANGE_TOUCH",
        )
    )
    assert close_rows.empty
    assert not range_rows.empty
    assert range_rows.iloc[0]["location_source"] == "H4_RANGE_TOUCH"


def test_target_on_final_confirmation_bar_is_ambiguous() -> None:
    daily, context, d1, h4, structure, health = _inputs()
    timestamp = h4.index[8]
    structure.loc[timestamp:, "confirmed_direction"] = "BULL"
    structure.loc[timestamp, "events"] = "BULL_TREND_CONFIRMED"
    health.loc[timestamp:, "health_state"] = "BULL_EXPANDING"
    h4.loc[timestamp, "high"] = 111.0

    rows = _bull_rows(
        build_staged_monthly_sequence(
            daily,
            context,
            d1,
            h4,
            structure,
            health,
        )
    )
    conservative = rows.loc[rows["target_tier"].eq("CONSERVATIVE")].iloc[0]
    assert bool(conservative["health_same_bar_as_structure"])
    assert bool(conservative["signal_target_same_bar"])
    assert not bool(conservative["signal_target_available"])
