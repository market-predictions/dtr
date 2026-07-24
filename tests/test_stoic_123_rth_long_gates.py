from __future__ import annotations

from stoic_123_lab.rth_long_proxy_gates import promotion_gates


def _summary(
    *,
    trades: int = 500,
    expectancy: float = 0.20,
    rdd: float = 2.0,
) -> dict[str, object]:
    return {
        "trades": trades,
        "expectancy_r": expectancy,
        "return_to_drawdown": rdd,
        "max_drawdown_r": 25.0,
        "largest_positive_year_share": 0.30,
        "net_2010": 10.0,
        "net_2011": 10.0,
        "net_2012": 10.0,
        "net_2013": 10.0,
    }


def _result(*, holdout: bool = False) -> dict[str, object]:
    baseline = _summary(trades=100 if holdout else 500)
    full = _summary(trades=80 if holdout else 300, expectancy=0.26, rdd=2.5)
    return {
        "summaries": {
            "RTH_LONG_EMA_BREAK": baseline,
            "RTH_LONG_EMA_BREAK_COST_2T": _summary(
                trades=int(baseline["trades"]), expectancy=0.15
            ),
            "RTH_LONG_EMA_BREAK_DELAY_1M": _summary(
                trades=int(baseline["trades"]), expectancy=0.16
            ),
            "RTH_LONG_FULL": full,
        },
        "inferences": {
            "RTH_LONG_EMA_BREAK": {"lo95_expectancy_r": 0.02},
        },
        "matched_rows": [
            {"candidate": "RTH_LONG_EMA_BREAK", "matched_control_passed": True},
            {"candidate": "RTH_LONG_FULL", "matched_control_passed": True},
        ],
    }


def test_rth_long_promotion_gates_can_all_pass() -> None:
    rows = promotion_gates(_result(), _result(holdout=True))
    assert rows
    assert all(bool(row["passed"]) for row in rows)


def test_rth_full_sequence_requires_incremental_mechanism_value() -> None:
    history = _result()
    holdout = _result(holdout=True)
    history["summaries"]["RTH_LONG_FULL"]["expectancy_r"] = 0.21
    history["summaries"]["RTH_LONG_FULL"]["return_to_drawdown"] = 2.1
    holdout["summaries"]["RTH_LONG_FULL"]["expectancy_r"] = 0.21
    rows = promotion_gates(history, holdout)
    mechanism = next(
        row
        for row in rows
        if row["gate"] == "full_sequence_mechanism_value_over_ema_break"
    )
    assert not bool(mechanism["passed"])


def test_rth_primary_requires_positive_holdout() -> None:
    history = _result()
    holdout = _result(holdout=True)
    holdout["summaries"]["RTH_LONG_EMA_BREAK"]["expectancy_r"] = -0.01
    rows = promotion_gates(history, holdout)
    gate = next(
        row for row in rows if row["gate"] == "fresh_holdout_expectancy_positive"
    )
    assert not bool(gate["passed"])
