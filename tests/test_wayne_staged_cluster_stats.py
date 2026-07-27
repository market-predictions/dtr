from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.wayne_direction.cluster_stats import (
    cluster_permutation_p_value,
)


def test_cluster_permutation_preserves_treatment_bundles() -> None:
    rows = []
    for month in range(20):
        rows.extend(
            [
                {
                    "instrument": "EURUSD",
                    "month_id": 201501 + month,
                    "year": 2015,
                    "side": "BULL",
                    "treated": True,
                    "outcome": True,
                },
                {
                    "instrument": "EURUSD",
                    "month_id": 201501 + month,
                    "year": 2015,
                    "side": "BEAR",
                    "treated": False,
                    "outcome": False,
                },
            ]
        )
    p_value = cluster_permutation_p_value(
        pd.DataFrame(rows),
        treatment_column="treated",
        outcome_column="outcome",
        observed_effect=1.0,
        seed=123,
        samples=200,
    )
    assert p_value == 1.0


def test_cluster_permutation_rejects_invalid_sample_count() -> None:
    data = pd.DataFrame(
        [
            {
                "instrument": "EURUSD",
                "month_id": 201501,
                "year": 2015,
                "treated": True,
                "outcome": True,
            },
            {
                "instrument": "EURUSD",
                "month_id": 201502,
                "year": 2015,
                "treated": False,
                "outcome": False,
            },
        ]
    )
    try:
        cluster_permutation_p_value(
            data,
            treatment_column="treated",
            outcome_column="outcome",
            observed_effect=1.0,
            seed=123,
            samples=0,
        )
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
