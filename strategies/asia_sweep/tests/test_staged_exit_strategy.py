from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.staged_exit_metrics import (
    FAIL_DECISION,
    PASS_DECISION,
    choose_staged_variant,
    summarize_staged_variant,
)
from dtr_lab.strategies.asia_sweep.staged_exit_simulator import (
    STAGED_VARIANTS,
    simulate_staged_trade,
)


def _order(**overrides: object) -> pd.Series:
    values: dict[str, object] = {
        "event_id": "EURUSD_2024-01-02_DOWN_0800",
        "instrument": "EURUSD",
        "trade_date": "2024-01-02",
        "week_key": "2024-W01",
        "year": 2024,
        "weekday": 1,
        "side": "DOWN",
        "prediction": 0.40,
        "variant": "MKT_NEXT_OPEN",
        "filled": True,
        "t5_timestamp_utc": "2024-01-02T08:05:00Z",
        "entry_timestamp_utc": "2024-01-02T08:06:00Z",
        "entry_price": 1.1002,
        "stop_price": 1.0990,
        "asian_midpoint": 1.1010,
        "asian_high": 1.1020,
        "asian_low": 1.1000,
        "asian_range_price": 0.0020,
        "sweep_extreme": 1.0994,
    }
    values.update(overrides)
    return pd.Series(values)


def _bars(rows: list[tuple[str, float, float, float, float]]) -> pd.DataFrame:
    index = pd.to_datetime([row[0] for row in rows], utc=True)
    bid_open = [row[1] for row in rows]
    bid_high = [row[2] for row in rows]
    bid_low = [row[3] for row in rows]
    bid_close = [row[4] for row in rows]
    spread = 0.0002
    return pd.DataFrame(
        {
            "open_bid": bid_open,
            "high_bid": bid_high,
            "low_bid": bid_low,
            "close_bid": bid_close,
            "is_active_quote_bid": [1] * len(rows),
            "open_ask": [value + spread for value in bid_open],
            "high_ask": [value + spread for value in bid_high],
            "low_ask": [value + spread for value in bid_low],
            "close_ask": [value + spread for value in bid_close],
            "is_active_quote_ask": [1] * len(rows),
            "active": [True] * len(rows),
        },
        index=index,
    )


def test_stop_and_tp1_same_bar_scores_full_stop_first() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1002, 1.1012, 1.0989, 1.1005),
        ]
    )
    result = simulate_staged_trade(
        _order(),
        _order(),
        bars,
        variant="MIDPOINT_50_RUNNER_ORIGINAL_STOP",
    )
    assert result["tp1_hit"] is False
    assert result["tp1_exit_reason"] == "STOP_FULL"
    assert result["runner_exit_reason"] == "STOP_FULL"
    assert result["net_r_0_0"] == pytest.approx(-1.0)


def test_tp1_and_tp2_same_bar_fill_both_targets_without_stop() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1002, 1.1022, 1.1000, 1.1018),
        ]
    )
    result = simulate_staged_trade(
        _order(),
        _order(),
        bars,
        variant="MIDPOINT_50_RUNNER_ORIGINAL_STOP",
    )
    assert result["tp1_hit"] is True
    assert result["tp2_hit"] is True
    assert result["runner_exit_reason"] == "TP2_SAME_BAR"
    expected = 0.5 * ((1.1010 - 1.1002) / 0.0012) + 0.5 * (
        (1.1020 - 1.1002) / 0.0012
    )
    assert result["net_r_0_0"] == pytest.approx(expected)


def test_break_even_activates_only_after_tp1_bar() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1002, 1.1011, 1.1000, 1.1009),
            ("2024-01-02T08:07:00Z", 1.1009, 1.1012, 1.1001, 1.1003),
        ]
    )
    result = simulate_staged_trade(
        _order(),
        _order(),
        bars,
        variant="MIDPOINT_50_RUNNER_BE",
    )
    assert result["tp1_hit"] is True
    assert result["break_even_activated"] is True
    assert result["runner_exit_reason"] == "BE_STOP"
    assert result["runner_exit_price"] == pytest.approx(1.1002)


def test_original_stop_runner_can_survive_entry_retest_and_hit_tp2() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1002, 1.1011, 1.1000, 1.1009),
            ("2024-01-02T08:07:00Z", 1.1009, 1.1012, 1.1000, 1.1003),
            ("2024-01-02T08:08:00Z", 1.1003, 1.1021, 1.1002, 1.1019),
        ]
    )
    result = simulate_staged_trade(
        _order(),
        _order(),
        bars,
        variant="MIDPOINT_50_RUNNER_ORIGINAL_STOP",
    )
    assert result["tp2_hit"] is True
    assert result["runner_exit_reason"] == "TP2"


def test_no_tp1_before_1000_closes_complete_position_at_1000() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1002, 1.1008, 1.0998, 1.1004),
            ("2024-01-02T08:59:00Z", 1.1004, 1.1007, 1.1000, 1.1005),
            ("2024-01-02T09:01:00Z", 1.1005, 1.1021, 1.1004, 1.1018),
        ]
    )
    result = simulate_staged_trade(
        _order(),
        _order(),
        bars,
        variant="MIDPOINT_50_RUNNER_ORIGINAL_STOP",
    )
    assert result["tp1_hit"] is False
    assert result["tp1_exit_reason"] == "TIME_1000_FULL"
    assert result["runner_exit_reason"] == "TIME_1000_FULL"
    assert result["runner_exit_timestamp_utc"] == "2024-01-02T08:59:00+00:00"


def _synthetic_orders(expectancy_positive: bool) -> pd.DataFrame:
    rows = []
    start = pd.Timestamp("2015-01-05T08:00:00Z")
    for index in range(200):
        year = 2015 + index % 5
        instrument = "EURUSD" if index % 2 == 0 else "GBPUSD"
        value = 0.40 if index % 3 else -0.10
        if not expectancy_positive:
            value = -0.20 if index % 2 else 0.05
        rows.append(
            {
                "event_id": f"event-{index:03d}",
                "instrument": instrument,
                "trade_date": f"{year}-01-{index % 20 + 1:02d}",
                "week_key": f"{year}-W{index % 20 + 1:02d}",
                "year": year,
                "weekday": index % 5,
                "side": "UP" if index % 2 else "DOWN",
                "prediction": 0.20,
                "entry_timestamp_utc": start + pd.Timedelta(minutes=index),
                "staged_variant": "MIDPOINT_50_RUNNER_ORIGINAL_STOP",
                "status": "FILLED",
                "filled": True,
                "tp1_hit": True,
                "tp2_hit": index % 2 == 0,
                "tp1_leg_r_0_0": value,
                "runner_leg_r_0_0": value,
                "net_r_0_0": value,
                "net_r_0_1": value - 0.01,
                "net_r_0_25": value - 0.025,
                "tp1_exit_reason": "TP1",
                "runner_exit_reason": "TP2",
            }
        )
    return pd.DataFrame(rows)


def test_staged_selection_requires_absolute_gates_and_frozen_hierarchy() -> None:
    passing = summarize_staged_variant(
        _synthetic_orders(True), "MIDPOINT_50_RUNNER_ORIGINAL_STOP"
    )
    challenger = {
        **passing,
        "variant": "MIDPOINT_50_RUNNER_BE",
    }
    selection = choose_staged_variant([passing, challenger])
    assert selection["decision"] == PASS_DECISION
    assert selection["selected_variant"] == "MIDPOINT_50_RUNNER_ORIGINAL_STOP"

    failing = summarize_staged_variant(
        _synthetic_orders(False), "MIDPOINT_50_RUNNER_ORIGINAL_STOP"
    )
    failed_challenger = {**failing, "variant": "MIDPOINT_50_RUNNER_BE"}
    failed = choose_staged_variant([failing, failed_challenger])
    assert failed["decision"] == FAIL_DECISION
    assert failed["selected_variant"] is None


def test_staged_variant_manifest_is_not_silently_expanded() -> None:
    assert STAGED_VARIANTS == (
        "MIDPOINT_50_RUNNER_ORIGINAL_STOP",
        "MIDPOINT_50_RUNNER_BE",
    )
