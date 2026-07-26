from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.sequential_triage import (
    TriageThresholds,
    assign_state,
    decide_action,
    validate_probability_rows,
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
