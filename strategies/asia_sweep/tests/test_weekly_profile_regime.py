from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.weekly_profile_regime import (
    aggregate_mechanism_decision,
    classify_trade_role,
    classify_weekly_phase,
)


def test_classifies_early_week_retracement_continuation() -> None:
    role = classify_trade_role(
        structural_trend="UP",
        trade_direction="DOWN",
        weekday=1,
        current_week_direction="DOWN",
        countertrend_excursion_atr=0.40,
        withtrend_excursion_atr=0.10,
    )
    assert role == "WEEKLY_RETRACE_CONTINUATION"


def test_classifies_trend_resumption_after_countertrend_excursion() -> None:
    role = classify_trade_role(
        structural_trend="DOWN",
        trade_direction="DOWN",
        weekday=2,
        current_week_direction="UP",
        countertrend_excursion_atr=0.55,
        withtrend_excursion_atr=0.15,
    )
    phase = classify_weekly_phase(
        structural_trend="DOWN",
        weekday=2,
        current_week_direction="FLAT",
        countertrend_excursion_atr=0.55,
        withtrend_excursion_atr=0.15,
        recovery_from_countertrend_extreme_atr=0.25,
    )
    assert role == "HTF_TREND_RESUMPTION"
    assert phase == "MIDWEEK_TREND_RESUMPTION"


def _row(
    *,
    event_id: str,
    instrument: str,
    year: int,
    role: str,
    hit: int,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "instrument": instrument,
        "year": year,
        "extended_target": "EXT_OPPOSITE_BOUNDARY_1100",
        "trade_role": role,
        "structural_trend": "UP",
        "event_weekday": 1,
        "trade_aligns_structural": True,
        "trade_opposes_structural": False,
        "extended_target_hit": hit,
        "extended_reward_risk_stress_010": 2.0,
        "observed_stressed_ev_proxy": 2.0 if hit else -1.0,
    }


def test_hierarchical_gate_opens_modeling_for_broad_positive_h1() -> None:
    rows: list[dict[str, object]] = []
    for pair_index, pair in enumerate(("EURUSD", "GBPUSD")):
        for year in range(2015, 2020):
            for index in range(20):
                rows.append(
                    _row(
                        event_id=f"s-{pair_index}-{year}-{index}",
                        instrument=pair,
                        year=year,
                        role="HTF_TREND_RESUMPTION",
                        hit=int(index % 2 == 0),
                    )
                )
            for index in range(20):
                rows.append(
                    _row(
                        event_id=f"r-{pair_index}-{year}-{index}",
                        instrument=pair,
                        year=year,
                        role="ROTATION_OR_AMBIGUOUS",
                        hit=int(index < 2),
                    )
                )
    decision, summary = aggregate_mechanism_decision(pd.DataFrame(rows))
    assert decision["decision"] == "PASS_WEEKLY_PROFILE_MECHANISM_OPEN_MODELING"
    assert decision["selected_hypothesis"] == "H1_HTF_TREND_RESUMPTION"
    assert decision["selected_target"] == "EXT_OPPOSITE_BOUNDARY_1100"
    selected = summary.loc[summary["passed"]].iloc[0]
    assert selected["pair_ev_positive_count"] == 2
    assert selected["year_ev_positive_count"] == 5


def test_gate_stops_when_payoff_is_negative() -> None:
    rows: list[dict[str, object]] = []
    for pair_index, pair in enumerate(("EURUSD", "GBPUSD")):
        for year in range(2015, 2020):
            for index in range(20):
                rows.append(
                    _row(
                        event_id=f"n-{pair_index}-{year}-{index}",
                        instrument=pair,
                        year=year,
                        role="HTF_TREND_RESUMPTION",
                        hit=int(index == 0),
                    )
                )
    decision, _ = aggregate_mechanism_decision(pd.DataFrame(rows))
    assert decision["decision"] == "FAIL_WEEKLY_PROFILE_MECHANISM_STOP"
    assert decision["modeling_authorized"] is False
