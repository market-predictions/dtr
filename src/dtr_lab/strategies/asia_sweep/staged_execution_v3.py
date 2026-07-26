from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.asia_sweep import staged_execution_v2 as base
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

POLICIES = base.POLICIES
STAGED_POLICIES = base.STAGED_POLICIES
REFERENCE_POLICIES = base.REFERENCE_POLICIES
DIAGNOSTIC_POLICIES = base.DIAGNOSTIC_POLICIES

load_hgb_triage_predictions = base.load_hgb_triage_predictions
prepare_staged_population = base.prepare_staged_population
summarize_staged = base.summarize_staged
decide_staged = base.decide_staged
write_staged_outputs = base.write_staged_outputs


def simulate_staged_event(
    event_rows: pd.DataFrame,
    bars: pd.DataFrame,
    *,
    policy: str,
) -> dict[str, Any]:
    """Run the frozen simulator with cancellation disabled for static references."""
    if policy in STAGED_POLICIES:
        return base.simulate_staged_event(event_rows, bars, policy=policy)
    if policy not in REFERENCE_POLICIES + DIAGNOSTIC_POLICIES:
        raise ValueError(policy)

    original_cancel = base._cancel_active
    base._cancel_active = lambda _row: False
    try:
        return base.simulate_staged_event(event_rows, bars, policy=policy)
    finally:
        base._cancel_active = original_cancel


def simulate_staged_development(
    population: pd.DataFrame,
    source_root: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (symbol, year), group in population.groupby(
        ["instrument", "year"], sort=True
    ):
        bars = load_bid_ask_minutes(
            source_root / str(symbol), str(symbol), int(year)
        )
        for _, event_rows in group.groupby("event_id", sort=True):
            for policy in POLICIES:
                rows.append(
                    simulate_staged_event(event_rows, bars, policy=policy)
                )
    return pd.DataFrame(rows)
