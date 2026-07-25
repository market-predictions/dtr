from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import PAIRS, TARGET
from dtr_lab.strategies.asia_sweep.fingerprint_validation_contract import (
    EXPECTED_ABSTENTION_THRESHOLD,
    EXPECTED_ANATOMY_RUN,
    EXPECTED_FAMILY,
    EXPECTED_LANDMARK,
    EXPECTED_PARAMETERS,
    EXPECTED_STABLE_FINGERPRINTS,
    _add_year_quintiles,
    _fingerprint_direction_table,
    _relative_lift,
    _subgroup_lift,
    load_frozen_bundle,
)

HOLDOUT_YEARS = (2024, 2025)
EXPECTED_DEVELOPMENT_RUN = 30177831134
EXPECTED_VALIDATION_RUN = 30178537776
PASS_DECISION = "PASS_FINAL_HOLDOUT_AUTHORIZE_EXECUTABLE_STRATEGY_RESEARCH"
FAIL_DECISION = "FAIL_FINAL_HOLDOUT_STOP_ASIAN_SWEEP_FINGERPRINT_PROGRAMME"


def validate_holdout_events(events: pd.DataFrame) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "sweep_timestamp_utc",
        "t5_timestamp_utc",
        "t5_available",
        TARGET,
    }
    missing = sorted(required - set(events))
    if missing:
        raise ValueError(f"holdout events missing columns: {missing}")
    pairs = tuple(sorted(events["instrument"].dropna().unique()))
    if pairs != PAIRS:
        raise ValueError(f"expected exactly {PAIRS}, found {pairs}")
    years = tuple(sorted(pd.to_datetime(events["trade_date"]).dt.year.unique()))
    if years != HOLDOUT_YEARS:
        raise ValueError(f"expected holdout years {HOLDOUT_YEARS}, found {years}")
    if events["event_id"].duplicated().any():
        raise ValueError("holdout event IDs must be unique")
    if events[TARGET].isna().any():
        raise ValueError("holdout target contains missing values")


__all__ = [
    "EXPECTED_ABSTENTION_THRESHOLD",
    "EXPECTED_ANATOMY_RUN",
    "EXPECTED_DEVELOPMENT_RUN",
    "EXPECTED_FAMILY",
    "EXPECTED_LANDMARK",
    "EXPECTED_PARAMETERS",
    "EXPECTED_STABLE_FINGERPRINTS",
    "EXPECTED_VALIDATION_RUN",
    "FAIL_DECISION",
    "HOLDOUT_YEARS",
    "PASS_DECISION",
    "_add_year_quintiles",
    "_fingerprint_direction_table",
    "_relative_lift",
    "_subgroup_lift",
    "load_frozen_bundle",
    "validate_holdout_events",
]
