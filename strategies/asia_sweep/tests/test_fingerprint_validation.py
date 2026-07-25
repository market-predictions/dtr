from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep import fingerprint_validation_contract as contract


class _DirectionalClassifier:
    def predict_proba(self, values: np.ndarray) -> np.ndarray:
        signed = values[:, 0] + values[:, 1] + values[:, 2] - values[:, 3] + values[:, 4]
        probability = 1.0 / (1.0 + np.exp(-signed))
        return np.column_stack([1.0 - probability, probability])


def _validation_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": ["eur-2022", "gbp-2022", "eur-2023", "gbp-2023"],
            "instrument": ["EURUSD", "GBPUSD", "EURUSD", "GBPUSD"],
            "trade_date": ["2022-01-03", "2022-01-03", "2023-01-03", "2023-01-03"],
            "week_key": ["2022-W01", "2022-W01", "2023-W01", "2023-W01"],
            "sweep_timestamp_utc": ["2022-01-03T08:00:00Z"] * 2
            + ["2023-01-03T08:00:00Z"] * 2,
            "t5_timestamp_utc": ["2022-01-03T08:05:00Z"] * 2
            + ["2023-01-03T08:05:00Z"] * 2,
            "t5_available": True,
            "midpoint_success_09_10": [0, 1, 0, 1],
        }
    )


def test_validation_events_require_exact_pairs_and_years() -> None:
    contract.validate_validation_events(_validation_rows())
    future = _validation_rows()
    future.loc[0, "trade_date"] = "2024-01-03"
    with pytest.raises(ValueError, match="validation years"):
        contract.validate_validation_events(future)


def test_year_quintiles_are_assigned_inside_each_year() -> None:
    frame = pd.DataFrame(
        {
            "event_id": [f"event-{index}" for index in range(20)],
            "year": [2022] * 10 + [2023] * 10,
            "prediction": list(np.linspace(0.0, 0.9, 10))
            + list(np.linspace(0.0, 0.9, 10)),
        }
    )
    result = contract._add_year_quintiles(frame)
    for _, group in result.groupby("year"):
        assert set(group["quintile"]) == {1, 2, 3, 4, 5}
        assert len(group.loc[group["quintile"] == 5]) == 2


def test_fingerprint_direction_gate_uses_observed_validation_outcomes() -> None:
    count = 40
    target = np.array([0] * 20 + [1] * 20)
    positive = np.linspace(-2.0, 2.0, count)
    negative = positive[::-1]
    transformed = np.column_stack([positive, positive, positive, negative, positive])
    population = pd.DataFrame(
        {
            "event_id": [f"event-{index:02d}" for index in range(count)],
            "target": target,
        }
    )
    names = [feature for feature, _ in contract.EXPECTED_STABLE_FINGERPRINTS]
    bundle = {
        "preprocessor": SimpleNamespace(feature_names=tuple(names)),
        "classifier": _DirectionalClassifier(),
    }
    result = contract._fingerprint_direction_table(population, transformed, bundle)
    assert result["observed_direction_preserved"].all()
    assert result["model_partial_dependence_direction"].tolist() == [
        "POSITIVE",
        "POSITIVE",
        "POSITIVE",
        "NEGATIVE",
        "POSITIVE",
    ]


def test_frozen_validation_constants_match_development_decision() -> None:
    assert contract.EXPECTED_LANDMARK == "T5"
    assert contract.EXPECTED_FAMILY == "hgb"
    assert contract.EXPECTED_PARAMETERS == {
        "learning_rate": 0.04,
        "max_leaf_nodes": 7,
        "min_samples_leaf": 50,
        "l2_regularization": 5.0,
    }
    assert contract.EXPECTED_ABSTENTION_THRESHOLD == 0.18252984704127595
