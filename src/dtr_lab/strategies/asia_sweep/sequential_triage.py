from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

TriageState = Literal["REVERSAL", "CONTINUATION", "ABSTAIN"]
TriageAction = Literal["ADD_OR_HOLD", "EXIT_BLOCK_ADD", "ABSTAIN"]

STATE_ORDER: tuple[TriageState, ...] = ("ABSTAIN", "CONTINUATION", "REVERSAL")


@dataclass(frozen=True)
class TriageThresholds:
    reversal: float
    continuation: float

    def __post_init__(self) -> None:
        for name, value in (
            ("reversal", self.reversal),
            ("continuation", self.continuation),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} threshold must be in [0, 1]")


def assign_state(frame: pd.DataFrame) -> pd.Series:
    """Create the frozen mutually-exclusive development state label."""
    required = {"target", "immediate_continuation", "two_sided_ambiguous"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing state-label columns: {missing}")
    reversal = frame["target"].astype(bool)
    continuation = frame["immediate_continuation"].astype(bool)
    ambiguous = frame["two_sided_ambiguous"].astype(bool)
    overlap = reversal & continuation
    if overlap.any():
        raise ValueError("reversal and continuation labels must be mutually exclusive")
    state = np.full(len(frame), "ABSTAIN", dtype=object)
    state[continuation & ~ambiguous] = "CONTINUATION"
    state[reversal & ~ambiguous] = "REVERSAL"
    return pd.Series(state, index=frame.index, name="triage_state")


def decide_action(
    reversal_probability: float,
    continuation_probability: float,
    thresholds: TriageThresholds,
) -> TriageAction:
    """Map calibrated state probabilities to a conservative staged action."""
    reversal_pass = reversal_probability >= thresholds.reversal
    continuation_pass = continuation_probability >= thresholds.continuation
    continuation_wins = (
        not reversal_pass or continuation_probability >= reversal_probability
    )
    if continuation_pass and continuation_wins:
        return "EXIT_BLOCK_ADD"
    if reversal_pass and reversal_probability > continuation_probability:
        return "ADD_OR_HOLD"
    return "ABSTAIN"


def validate_probability_rows(probabilities: pd.DataFrame) -> None:
    required = set(STATE_ORDER)
    missing = sorted(required - set(probabilities.columns))
    if missing:
        raise ValueError(f"missing probability columns: {missing}")
    values = probabilities.loc[:, list(STATE_ORDER)].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("probabilities must be finite")
    if ((values < 0.0) | (values > 1.0)).any():
        raise ValueError("probabilities must be in [0, 1]")
    if not np.allclose(values.sum(axis=1), 1.0, atol=1e-8):
        raise ValueError("multiclass probabilities must sum to one")
