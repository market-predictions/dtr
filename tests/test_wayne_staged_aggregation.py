from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


def _module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "aggregate_wayne_staged_sequence.py"
    )
    spec = importlib.util.spec_from_file_location(
        "aggregate_wayne_staged_sequence",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.BOOTSTRAP_SAMPLES = 100
    module.PERMUTATION_SAMPLES = 200
    return module


def _comparison_frame() -> pd.DataFrame:
    rows = []
    instruments = ("AUDUSD", "EURUSD", "GBPUSD", "USDCAD", "USDCHF", "USDJPY")
    for instrument_index, instrument in enumerate(instruments):
        for offset in range(20):
            treatment = offset < 10
            outcome = offset < 9 if treatment else offset in {10, 11}
            rows.append(
                {
                    "instrument": instrument,
                    "month_id": 201500 + instrument_index * 20 + offset + 1,
                    "year": 2015 + offset % 7,
                    "location_rule": "CLOSE_IN_ZONE",
                    "target_tier": "CONSERVATIVE",
                    "sequence_active_primary": treatment,
                    "primary_target_available": True,
                    "primary_reached_by_month_end": outcome,
                }
            )
    return pd.DataFrame(rows)


def test_planned_comparison_detects_large_stable_lift() -> None:
    module = _module()
    result = module._comparison(
        _comparison_frame(),
        name="DAY5_CONSERVATIVE",
        treatment_column="sequence_active_primary",
        available_column="primary_target_available",
        outcome_column="primary_reached_by_month_end",
        target_tier="CONSERVATIVE",
        seed=123,
    )
    assert result["treatment_n"] == 60
    assert result["control_n"] == 60
    assert result["effect"] > 0.60
    assert result["permutation_p"] < 0.05
    assert result["positive_pairs"] == 6


def test_benjamini_hochberg_is_monotone_in_rank() -> None:
    module = _module()
    q_values = module._bh_q_values([0.01, 0.04, 0.03, 0.20])
    assert q_values == [0.04, 0.05333333333333334, 0.05333333333333334, 0.20]
