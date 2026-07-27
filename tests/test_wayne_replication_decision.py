from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.wayne_direction import REPLICATION_PAIRS
from dtr_lab.strategies.wayne_direction import replication_decision as decision


def _ledger(
    *,
    active_counts: dict[str, int] | None = None,
    treatment_success: bool = True,
) -> pd.DataFrame:
    counts = active_counts or {pair: 5 for pair in REPLICATION_PAIRS}
    rows: list[dict[str, object]] = []
    for pair_position, pair in enumerate(REPLICATION_PAIRS):
        active_count = counts[pair]
        total = active_count + 60
        for position in range(total):
            active = position < active_count
            year = 2015 + (position % 5)
            conservative_success = (
                active and treatment_success and position % 5 != 0
            ) or (not active and position % 5 == 0)
            for tier in ("CONSERVATIVE", "STRETCH"):
                rows.append(
                    {
                        "instrument": pair,
                        "opportunity_id": f"{pair}-opp-{position}",
                        "month_id": year * 10000 + pair_position * 1000 + position,
                        "year": year,
                        "side": "BULL" if position % 2 == 0 else "BEAR",
                        "location_rule": "CLOSE_IN_ZONE",
                        "target_tier": tier,
                        "sequence_active_sensitivity": active,
                        "sensitivity_target_available": True,
                        "sensitivity_reached_by_month_end": (
                            conservative_success
                            if tier == "CONSERVATIVE"
                            else active and treatment_success and position % 3 == 0
                        ),
                        "stage_sensitivity": (
                            "COMPLETE_ACTIVE" if active else "LOCATION_ONLY"
                        ),
                    }
                )
    return pd.DataFrame(rows)


@pytest.fixture(autouse=True)
def _fast_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(decision, "BOOTSTRAP_SAMPLES", 40)
    monkeypatch.setattr(
        decision,
        "cluster_permutation_p_value",
        lambda *args, **kwargs: 0.01,
    )


def test_replication_pass_requires_sample_effect_and_breadth() -> None:
    result = decision.build_replication_decision(_ledger())
    assert result["decision"] == "PASS_REPLICATION_AUTHORIZE_MINIMAL_CONTEXT_PHASE"
    assert result["active_day10"] == 20
    assert result["conservative"]["treatment_n"] == 20
    assert result["conservative"]["control_n"] == 240
    assert result["conservative"]["effect"] > 0.10
    assert result["conservative"]["positive_pairs"] == 4
    assert result["conservative"]["positive_years"] == 4


def test_replication_stops_on_insufficient_sample() -> None:
    result = decision.build_replication_decision(
        _ledger(active_counts={pair: 2 for pair in REPLICATION_PAIRS})
    )
    assert result["decision"] == "FAIL_REPLICATION_SAMPLE_INSUFFICIENT"
    assert not result["sample_gates"]["active_day10_at_least_20"]
    assert not result["sample_gates"]["three_pairs_have_at_least_three_active"]


def test_replication_stops_when_effect_reverses() -> None:
    result = decision.build_replication_decision(
        _ledger(treatment_success=False)
    )
    assert result["decision"] == "FAIL_REPLICATION_EFFECT_NOT_REPRODUCED"
    assert result["conservative"]["effect"] < 0.0
    assert not result["effect_gates"]["agrees_with_original_positive_direction"]


def test_replication_stops_on_pair_concentration() -> None:
    result = decision.build_replication_decision(
        _ledger(
            active_counts={
                "EURGBP": 9,
                "EURJPY": 4,
                "GBPJPY": 4,
                "NZDUSD": 3,
            }
        )
    )
    assert result["decision"] == "FAIL_REPLICATION_BREADTH_OR_CONCENTRATION"
    assert result["maximum_pair_concentration"] == 0.45
    assert not result["breadth_gates"]["no_pair_above_40pct"]


def test_duplicate_opportunity_target_rows_are_rejected() -> None:
    ledger = _ledger()
    ledger = pd.concat([ledger, ledger.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate replication rows"):
        decision.normalize_replication_ledger(ledger)
