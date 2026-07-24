from __future__ import annotations

import numpy as np

from stoic_123_lab import usa500_rth_gates, usa500_rth_study


def _summary(
    *,
    trades: int,
    expectancy: float,
    net_r: float,
    drawdown: float,
    return_to_drawdown: float,
    net_2012: float = np.nan,
    net_2013: float = np.nan,
) -> dict[str, object]:
    return {
        "trades": trades,
        "expectancy_r": expectancy,
        "net_r": net_r,
        "max_drawdown_r": drawdown,
        "return_to_drawdown": return_to_drawdown,
        "largest_positive_year_share": 0.50,
        "net_2012": net_2012,
        "net_2013": net_2013,
    }


def _result(*, positive: bool) -> dict[str, object]:
    sign = 1.0 if positive else -1.0
    expectancy = 0.20 * sign
    break_summary = _summary(
        trades=400,
        expectancy=expectancy,
        net_r=80.0 * sign,
        drawdown=25.0,
        return_to_drawdown=3.2 * sign,
        net_2012=30.0 * sign,
        net_2013=50.0 * sign,
    )
    full_summary = _summary(
        trades=120,
        expectancy=(expectancy + 0.06 if positive else expectancy - 0.06),
        net_r=40.0 * sign,
        drawdown=20.0,
        return_to_drawdown=2.0 * sign,
        net_2012=15.0 * sign,
        net_2013=25.0 * sign,
    )
    summaries = {
        "RTH_LONG_EMA_BREAK": break_summary,
        "RTH_LONG_FULL": full_summary,
        "RTH_LONG_EMA_BREAK_COST_2T": {"expectancy_r": expectancy - 0.05},
        "RTH_LONG_EMA_BREAK_DELAY_1M": {"expectancy_r": expectancy - 0.03},
    }
    inferences = {
        "RTH_LONG_EMA_BREAK": {
            "lo95_expectancy_r": 0.05 if positive else -0.30,
        }
    }
    matched_rows = [
        {
            "candidate": "RTH_LONG_EMA_BREAK",
            "matched_control_passed": positive,
        },
        {
            "candidate": "RTH_LONG_FULL",
            "matched_control_passed": positive,
        },
    ]
    return {
        "summaries": summaries,
        "inferences": inferences,
        "matched_rows": matched_rows,
    }


def test_usa500_spec_uses_explicit_es_proxy_economics() -> None:
    spec = usa500_rth_study.USA500_RTH_SPEC
    assert spec.name == "ES_PROXY"
    assert spec.tick_size == 0.25
    assert spec.point_value == 50.0
    assert spec.commission_per_side == 2.25
    assert "USA500" in spec.source_classification
    assert "not CME ES futures" in spec.source_classification


def test_positive_synthetic_transfer_passes_all_gates() -> None:
    history = _result(positive=True)
    holdout = _result(positive=True)
    rows = usa500_rth_gates.promotion_gates(history, holdout)
    assert len(rows) == 18
    assert all(bool(row["passed"]) for row in rows)


def test_negative_synthetic_transfer_fails_expectancy_and_controls() -> None:
    history = _result(positive=False)
    holdout = _result(positive=False)
    rows = usa500_rth_gates.promotion_gates(history, holdout)
    by_name = {str(row["gate"]): bool(row["passed"]) for row in rows}
    assert not by_name["fresh_history_expectancy_positive"]
    assert not by_name["fresh_holdout_expectancy_positive"]
    assert not by_name["primary_matched_time_control_passes"]
    assert not by_name["full_sequence_mechanism_value_over_ema_break"]
