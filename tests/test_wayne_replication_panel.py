from __future__ import annotations

from copy import deepcopy

import pandas as pd

from dtr_lab.strategies.wayne_direction import (
    REPLICATION_PAIRS,
    annual_spread_quantiles,
    evaluate_quality_metrics,
    expected_calendar_minutes,
)


def _passing_metrics() -> dict[str, object]:
    return {
        "instrument": "NZDUSD",
        "years": list(range(2015, 2022)),
        "source_minutes": expected_calendar_minutes(2015, 2021),
        "active_mismatch_rows": 0,
        "invalid_active_ohlc_rows": 0,
        "invalid_active_spread_rows": 0,
        "active_fraction": 0.71,
        "full_daily_fraction": 0.97,
        "full_h4_fraction": 0.96,
        "spread_median_pips": 0.8,
        "spread_p95_pips": 2.4,
        "spread_p99_pips": 5.0,
    }


def test_replication_candidate_universe_is_frozen() -> None:
    assert REPLICATION_PAIRS == ("EURGBP", "EURJPY", "GBPJPY", "NZDUSD")


def test_expected_calendar_minutes_includes_leap_years() -> None:
    assert expected_calendar_minutes(2015, 2021) == 3_682_080


def test_annual_spread_quantiles_use_active_series_index() -> None:
    series = pd.Series(
        [1.0, 3.0, 9.0],
        index=pd.to_datetime(
            [
                "2019-12-31 23:59:00+00:00",
                "2020-01-02 12:00:00+00:00",
                "2020-01-02 12:01:00+00:00",
            ]
        ),
    )
    result = annual_spread_quantiles(series, 2020)
    assert result["spread_median_pips"] == 6.0
    assert result["spread_p95_pips"] == 8.7
    assert result["spread_p99_pips"] == 8.94


def test_complete_quality_metrics_pass() -> None:
    gates = evaluate_quality_metrics(_passing_metrics())
    assert gates
    assert all(gates.values())


def test_spread_and_timestamp_defects_fail_separately() -> None:
    spread = deepcopy(_passing_metrics())
    spread["spread_p95_pips"] = 8.01
    spread_gates = evaluate_quality_metrics(spread)
    assert not spread_gates["p95_spread_gate"]
    assert sum(not value for value in spread_gates.values()) == 1

    rows = deepcopy(_passing_metrics())
    rows["source_minutes"] = int(rows["source_minutes"]) - 1
    row_gates = evaluate_quality_metrics(rows)
    assert not row_gates["complete_calendar_rows"]
    assert sum(not value for value in row_gates.values()) == 1


def test_non_candidate_and_activity_mismatch_are_rejected() -> None:
    metrics = deepcopy(_passing_metrics())
    metrics["instrument"] = "AUDJPY"
    metrics["active_mismatch_rows"] = 1
    gates = evaluate_quality_metrics(metrics)
    assert not gates["candidate_is_frozen"]
    assert not gates["bid_ask_active_match"]
