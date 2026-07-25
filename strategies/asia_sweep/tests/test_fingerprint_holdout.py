from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep import fingerprint_holdout_contract as contract


def _holdout_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": ["eur-2024", "gbp-2024", "eur-2025", "gbp-2025"],
            "instrument": ["EURUSD", "GBPUSD", "EURUSD", "GBPUSD"],
            "trade_date": ["2024-01-03", "2024-01-03", "2025-01-03", "2025-01-03"],
            "week_key": ["2024-W01", "2024-W01", "2025-W01", "2025-W01"],
            "sweep_timestamp_utc": ["2024-01-03T08:00:00Z"] * 2
            + ["2025-01-03T08:00:00Z"] * 2,
            "t5_timestamp_utc": ["2024-01-03T08:05:00Z"] * 2
            + ["2025-01-03T08:05:00Z"] * 2,
            "t5_available": True,
            "midpoint_success_09_10": [0, 1, 0, 1],
        }
    )


def test_holdout_events_require_exact_pairs_and_years() -> None:
    contract.validate_holdout_events(_holdout_rows())
    contaminated = _holdout_rows()
    contaminated.loc[0, "trade_date"] = "2023-01-03"
    with pytest.raises(ValueError, match="holdout years"):
        contract.validate_holdout_events(contaminated)


def test_holdout_events_reject_duplicate_ids() -> None:
    duplicated = _holdout_rows()
    duplicated.loc[1, "event_id"] = duplicated.loc[0, "event_id"]
    with pytest.raises(ValueError, match="unique"):
        contract.validate_holdout_events(duplicated)


def test_final_holdout_constants_match_frozen_validation() -> None:
    assert contract.HOLDOUT_YEARS == (2024, 2025)
    assert contract.EXPECTED_DEVELOPMENT_RUN == 30177831134
    assert contract.EXPECTED_VALIDATION_RUN == 30178537776
    assert contract.EXPECTED_LANDMARK == "T5"
    assert contract.EXPECTED_FAMILY == "hgb"
    assert contract.EXPECTED_ABSTENTION_THRESHOLD == 0.18252984704127595
    assert contract.PASS_DECISION == (
        "PASS_FINAL_HOLDOUT_AUTHORIZE_EXECUTABLE_STRATEGY_RESEARCH"
    )
    assert contract.FAIL_DECISION == (
        "FAIL_FINAL_HOLDOUT_STOP_ASIAN_SWEEP_FINGERPRINT_PROGRAMME"
    )


def test_low_reversal_probability_is_not_encoded_as_continuation() -> None:
    exported = set(contract.__all__)
    assert "continuation_probability" not in exported
    assert "continuation_signal" not in exported
