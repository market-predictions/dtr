from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.sequential_triage import (
    TriageThresholds,
    assign_state,
    decide_action,
    validate_probability_rows,
)
from dtr_lab.strategies.asia_sweep.sequential_triage_modeling import (
    apply_thresholds,
    role_passes,
    select_thresholds,
)


def test_assign_state_is_mutually_exclusive_and_ambiguous_abstains() -> None:
    frame = pd.DataFrame(
        {
            "target": [True, False, False, True],
            "immediate_continuation": [False, True, False, False],
            "two_sided_ambiguous": [False, False, False, True],
        }
    )
    assert assign_state(frame).tolist() == [
        "REVERSAL",
        "CONTINUATION",
        "ABSTAIN",
        "ABSTAIN",
    ]


def test_assign_state_rejects_overlap() -> None:
    frame = pd.DataFrame(
        {
            "target": [True],
            "immediate_continuation": [True],
            "two_sided_ambiguous": [False],
        }
    )
    with pytest.raises(ValueError, match="mutually exclusive"):
        assign_state(frame)


def test_continuation_wins_probability_conflict() -> None:
    thresholds = TriageThresholds(reversal=0.40, continuation=0.45)
    assert decide_action(0.48, 0.55, thresholds) == "EXIT_BLOCK_ADD"
    assert decide_action(0.58, 0.46, thresholds) == "ADD_OR_HOLD"
    assert decide_action(0.35, 0.40, thresholds) == "ABSTAIN"


def test_probability_rows_must_sum_to_one() -> None:
    validate_probability_rows(
        pd.DataFrame(
            {
                "ABSTAIN": [0.40],
                "CONTINUATION": [0.35],
                "REVERSAL": [0.25],
            }
        )
    )
    with pytest.raises(ValueError, match="sum to one"):
        validate_probability_rows(
            pd.DataFrame(
                {
                    "ABSTAIN": [0.40],
                    "CONTINUATION": [0.35],
                    "REVERSAL": [0.35],
                }
            )
        )


def test_formal_threshold_rule_abstains_on_conflict() -> None:
    probabilities = np.array(
        [
            [0.10, 0.60, 0.30],
            [0.10, 0.30, 0.60],
            [0.40, 0.31, 0.29],
            [0.10, 0.48, 0.47],
        ]
    )
    thresholds = {
        "reversal_threshold": 0.45,
        "continuation_threshold": 0.45,
        "conflict_margin": 0.05,
    }
    assert apply_thresholds(probabilities, thresholds).tolist() == [
        "CONTINUATION",
        "REVERSAL",
        "ABSTAIN",
        "ABSTAIN",
    ]


def test_threshold_selection_is_deterministic_and_precision_constrained() -> None:
    target = pd.Series(
        ["REVERSAL"] * 50 + ["CONTINUATION"] * 50 + ["ABSTAIN"] * 100
    )
    probabilities = np.zeros((200, 3), dtype=float)
    probabilities[:50] = [0.10, 0.10, 0.80]
    probabilities[50:100] = [0.10, 0.80, 0.10]
    probabilities[100:] = [0.80, 0.10, 0.10]
    first = select_thresholds(target, probabilities)
    second = select_thresholds(target, probabilities)
    assert first == second
    assert first is not None
    decisions = apply_thresholds(probabilities, first)
    assert float((decisions == "ABSTAIN").mean()) == 0.50
    assert set(decisions[:50]) == {"REVERSAL"}
    assert set(decisions[50:100]) == {"CONTINUATION"}


def test_threshold_selection_stops_when_directional_precision_is_unavailable() -> None:
    target = pd.Series(
        ["REVERSAL"] * 50 + ["CONTINUATION"] * 50 + ["ABSTAIN"] * 100
    )
    probabilities = np.tile([0.34, 0.33, 0.33], (200, 1))
    assert select_thresholds(target, probabilities) is None


def test_role_gate_requires_coverage_and_pair_year_breadth() -> None:
    summary = {
        "continuation_precision": 0.60,
        "continuation_coverage": 0.10,
        "continuation_calibration_better": True,
        "max_action_concentration": 0.60,
    }
    pairs = pd.DataFrame(
        {
            "instrument": ["EURUSD", "GBPUSD"],
            "continuation_decisions": [20, 20],
        }
    )
    years = pd.DataFrame(
        {
            "year": [2015, 2016, 2017, 2018, 2019],
            "continuation_decisions": [5, 5, 5, 5, 0],
        }
    )
    assert role_passes(summary, pairs, years, role="continuation")
    pairs.loc[pairs["instrument"].eq("GBPUSD"), "continuation_decisions"] = 0
    assert not role_passes(summary, pairs, years, role="continuation")
