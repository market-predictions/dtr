from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.weekly_transition_validation import (
    CONFIRMATION_GATE,
    DIAGNOSTIC_TARGETS,
    evaluate_stage,
    evaluate_target,
    final_programme_decision,
)


def _build_ledger(*, positive_transition: bool = True) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for target in DIAGNOSTIC_TARGETS:
        for pair_index, pair in enumerate(("EURUSD", "GBPUSD")):
            for year in (2020, 2021, 2022):
                for index in range(10):
                    hit = int(positive_transition and index < 5)
                    rr = 4.0 if target != "EXT_FIXED_3R_1200" else 3.0
                    rows.append(
                        {
                            "event_id": f"t-{target}-{pair_index}-{year}-{index}",
                            "instrument": pair,
                            "trade_date": f"{year}-03-{index + 1:02d}",
                            "year": year,
                            "extended_target": target,
                            "extended_target_hit": hit,
                            "extended_reward_risk_stress_010": rr,
                            "observed_stressed_ev_proxy": rr if hit else -1.0,
                            "transition_population": True,
                            "transition_reference": True,
                        }
                    )
                for index in range(10):
                    rows.append(
                        {
                            "event_id": f"r-{target}-{pair_index}-{year}-{index}",
                            "instrument": pair,
                            "trade_date": f"{year}-06-{index + 1:02d}",
                            "year": year,
                            "extended_target": target,
                            "extended_target_hit": 0,
                            "extended_reward_risk_stress_010": 4.0,
                            "observed_stressed_ev_proxy": -1.0,
                            "transition_population": False,
                            "transition_reference": True,
                        }
                    )
    return pd.DataFrame(rows)


def test_confirmation_gate_passes_broad_positive_transition() -> None:
    decision = evaluate_stage(
        _build_ledger(positive_transition=True),
        gate=CONFIRMATION_GATE,
    )
    assert decision["decision"] == (
        "PASS_WEEKLY_TRANSITION_CONFIRMATION_OPEN_FINAL_HOLDOUT"
    )
    assert decision["passed"] is True
    primary = decision["results"]["EXT_OPPOSING_LIQUIDITY_1400"]
    assert primary["events"] == 60
    assert primary["positive_ev_pairs"] == 2
    assert primary["positive_ev_years"] == 3
    assert primary["absolute_hit_rate_lift"] > 0.20


def test_confirmation_stops_when_transition_payoff_is_negative() -> None:
    decision = evaluate_stage(
        _build_ledger(positive_transition=False),
        gate=CONFIRMATION_GATE,
    )
    assert decision["decision"] == "FAIL_WEEKLY_TRANSITION_CONFIRMATION_STOP"
    assert decision["passed"] is False
    assert "pooled_ev" in decision["failed_gates"]


def test_bootstrap_is_deterministic() -> None:
    ledger = _build_ledger(positive_transition=True)
    first = evaluate_target(
        ledger,
        target="EXT_OPPOSING_LIQUIDITY_1400",
        years=(2020, 2021, 2022),
    )
    second = evaluate_target(
        ledger,
        target="EXT_OPPOSING_LIQUIDITY_1400",
        years=(2020, 2021, 2022),
    )
    assert first["bootstrap_probability_positive"] == second[
        "bootstrap_probability_positive"
    ]
    assert first["bootstrap_p10"] == second["bootstrap_p10"]


def test_final_programme_requires_final_and_combined_pass() -> None:
    assert final_programme_decision(
        {"passed": True},
        {"passed": True},
    ) == "PASS_WEEKLY_TRANSITION_FINAL_HOLDOUT_OPEN_EXECUTION_PNL"
    assert final_programme_decision(
        {"passed": True},
        {"passed": False},
    ) == "FAIL_WEEKLY_TRANSITION_FINAL_HOLDOUT_STOP"
