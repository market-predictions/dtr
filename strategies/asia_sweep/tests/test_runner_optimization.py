from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.runner_optimization_selection import (
    build_nested_runner_decision,
)
from dtr_lab.strategies.asia_sweep.runner_optimization_simulator import (
    EXIT_HOURS,
    STOP_POLICIES,
    TARGET_KINDS,
    policy_id,
    runner_policy_manifest,
    simulate_runner_trade,
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
        "entry_timestamp_utc": "2024-01-02T08:06:00Z",
        "entry_price": 1.1000,
        "stop_price": 1.0990,
        "asian_midpoint": 1.1010,
        "asian_high": 1.1040,
        "asian_low": 1.0995,
        "asian_range_price": 0.0045,
        "sweep_extreme": 1.0996,
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


def test_runner_manifest_is_exactly_frozen_40_policy_family() -> None:
    manifest = runner_policy_manifest()
    assert len(manifest) == 40
    assert len({row["policy_id"] for row in manifest}) == 40
    assert TARGET_KINDS == ("2R", "3R", "4R", "5R", "OPPOSITE_BOUNDARY")
    assert EXIT_HOURS == (12, 14, 16, 18)
    assert STOP_POLICIES == ("ORIGINAL_STOP", "BREAK_EVEN_AFTER_TP1")


def test_tp1_after_1000_can_start_runner_and_reach_3r() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1000, 1.1005, 1.0997, 1.1003),
            ("2024-01-02T09:30:00Z", 1.1003, 1.1012, 1.1002, 1.1011),
            ("2024-01-02T10:00:00Z", 1.1011, 1.1032, 1.1010, 1.1030),
        ]
    )
    result = simulate_runner_trade(
        _order(),
        _order(),
        bars,
        target_kind="3R",
        exit_hour=12,
        stop_policy="ORIGINAL_STOP",
    )
    assert result["tp1_hit"] is True
    assert result["runner_target_hit"] is True
    assert result["tp1_timestamp_utc"] == "2024-01-02T09:30:00+00:00"
    assert result["runner_exit_reason"] == "RUNNER_TARGET"
    assert result["runner_target_price"] == pytest.approx(1.1030)


def test_stop_and_tp1_same_bar_is_conservatively_full_stop() -> None:
    bars = _bars(
        [("2024-01-02T08:06:00Z", 1.1000, 1.1012, 1.0989, 1.1005)]
    )
    result = simulate_runner_trade(
        _order(),
        _order(),
        bars,
        target_kind="2R",
        exit_hour=12,
        stop_policy="ORIGINAL_STOP",
    )
    assert result["tp1_hit"] is False
    assert result["tp1_exit_reason"] == "STOP_FULL"
    assert result["runner_exit_reason"] == "STOP_FULL"
    assert result["net_r_0_0"] == pytest.approx(-1.0)


def test_break_even_activates_only_after_tp1_bar() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1000, 1.1012, 1.0998, 1.1010),
            ("2024-01-02T08:07:00Z", 1.1010, 1.1013, 1.0999, 1.1001),
        ]
    )
    result = simulate_runner_trade(
        _order(),
        _order(),
        bars,
        target_kind="3R",
        exit_hour=12,
        stop_policy="BREAK_EVEN_AFTER_TP1",
    )
    assert result["tp1_hit"] is True
    assert result["break_even_activated"] is True
    assert result["runner_exit_reason"] == "BE_STOP"
    assert result["runner_exit_price"] == pytest.approx(1.1000)


def test_no_tp1_exits_full_position_at_policy_horizon() -> None:
    bars = _bars(
        [
            ("2024-01-02T08:06:00Z", 1.1000, 1.1006, 1.0996, 1.1003),
            ("2024-01-02T10:59:00Z", 1.1003, 1.1008, 1.1000, 1.1005),
            ("2024-01-02T11:01:00Z", 1.1005, 1.1012, 1.1004, 1.1011),
        ]
    )
    result = simulate_runner_trade(
        _order(),
        _order(),
        bars,
        target_kind="4R",
        exit_hour=12,
        stop_policy="ORIGINAL_STOP",
    )
    assert result["tp1_hit"] is False
    assert result["tp1_exit_reason"] == "TIME_FULL"
    assert result["runner_exit_timestamp_utc"] == "2024-01-02T10:59:00+00:00"


def _synthetic_grid() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    manifest = runner_policy_manifest()
    robust = policy_id("3R", 14, "ORIGINAL_STOP")
    hindsight = policy_id("5R", 18, "BREAK_EVEN_AFTER_TP1")
    for policy in manifest:
        current = str(policy["policy_id"])
        for year in range(2015, 2020):
            for pair_index, instrument in enumerate(("EURUSD", "GBPUSD")):
                for trade_index in range(20):
                    if current == robust:
                        value = 0.35 if trade_index % 4 else -0.25
                    elif current == hindsight and year == 2019:
                        value = 1.00
                    elif current == hindsight:
                        value = -0.20
                    else:
                        value = -0.05 if trade_index % 3 else 0.02
                    rows.append(
                        {
                            "event_id": (
                                f"{current}-{year}-{instrument}-{trade_index:02d}"
                            ),
                            "instrument": instrument,
                            "trade_date": f"{year}-01-{trade_index + 1:02d}",
                            "week_key": f"{year}-W{trade_index + 1:02d}",
                            "year": year,
                            "weekday": trade_index % 5,
                            "side": "DOWN" if pair_index == 0 else "UP",
                            "prediction": 0.30,
                            "policy_id": current,
                            "target_kind": policy["target_kind"],
                            "exit_hour": policy["exit_hour"],
                            "stop_policy": policy["stop_policy"],
                            "filled": True,
                            "tp1_hit": value > 0,
                            "runner_target_hit": value > 0.30,
                            "tp1_leg_r_0_0": value,
                            "runner_leg_r_0_0": value,
                            "net_r_0_0": value,
                            "net_r_0_1": value - 0.01,
                            "net_r_0_25": value - 0.025,
                            "tp1_exit_reason": "TP1" if value > 0 else "TIME_FULL",
                            "runner_exit_reason": (
                                "RUNNER_TARGET" if value > 0.30 else "TIME_RUNNER"
                            ),
                        }
                    )
    return pd.DataFrame(rows)


def test_nested_selection_ignores_heldout_hindsight_winner() -> None:
    decision = build_nested_runner_decision(_synthetic_grid())
    robust = policy_id("3R", 14, "ORIGINAL_STOP")
    assert decision["modal_policy_id"] == robust
    assert decision["modal_policy_fold_count"] == 5
    fold_table = decision["fold_table"].set_index("outer_year")
    assert fold_table.loc[2019, "selected_policy_id"] == robust
    assert decision["decision"].startswith("PASS_RUNNER_DISCOVERY")
