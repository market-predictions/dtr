from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import (
    PAIRS,
    TARGET,
    feature_spec,
)

VALIDATION_YEARS = (2022, 2023)
PASS_DECISION = "PASS_VALIDATION_FREEZE_AUTHORIZE_2024_2025_FINAL_HOLDOUT"
FAIL_DECISION = "FAIL_VALIDATION_STOP_BEFORE_2024_2025"
EXPECTED_DEVELOPMENT_RUN = 30177831134
EXPECTED_ANATOMY_RUN = 30174245825
EXPECTED_LANDMARK = "T5"
EXPECTED_FAMILY = "hgb"
EXPECTED_PARAMETERS = {
    "learning_rate": 0.04,
    "max_leaf_nodes": 7,
    "min_samples_leaf": 50,
    "l2_regularization": 5.0,
}
EXPECTED_STABLE_FINGERPRINTS = (
    ("sweep_minute", "POSITIVE"),
    ("t5_reclaim_depth_range_fraction", "POSITIVE"),
    ("t5_mfe_range_fraction", "POSITIVE"),
    ("asian_range_atr20__x__sweep_minute", "NEGATIVE"),
    ("sweep_wick_range_fraction", "POSITIVE"),
)
EXPECTED_ABSTENTION_THRESHOLD = 0.18252984704127595


def _relative_lift(value: float, baseline: float) -> float:
    return float(value / baseline - 1.0) if baseline > 0 else float("nan")


def load_frozen_bundle(path: Path) -> dict[str, Any]:
    bundle = joblib.load(path)
    required = {
        "programme",
        "source_run_id",
        "source_commit",
        "landmark",
        "family",
        "parameters",
        "numeric_features",
        "categorical_features",
        "interactions",
        "preprocessor",
        "classifier",
        "abstention_rule",
        "stable_fingerprints",
        "development_base_rate",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise ValueError(f"frozen bundle missing fields: {missing}")
    if int(bundle["source_run_id"]) != EXPECTED_ANATOMY_RUN:
        raise ValueError("unexpected development anatomy provenance")
    if bundle["landmark"] != EXPECTED_LANDMARK or bundle["family"] != EXPECTED_FAMILY:
        raise ValueError("unexpected selected landmark or model family")
    if bundle["parameters"] != EXPECTED_PARAMETERS:
        raise ValueError(f"unexpected frozen parameters: {bundle['parameters']}")
    threshold = bundle["abstention_rule"].get("threshold")
    if not np.isclose(float(threshold), EXPECTED_ABSTENTION_THRESHOLD, atol=0, rtol=0):
        raise ValueError("frozen abstention threshold changed")
    fingerprints = tuple(
        (row["feature"], row["direction"]) for row in bundle["stable_fingerprints"]
    )
    if fingerprints != EXPECTED_STABLE_FINGERPRINTS:
        raise ValueError(f"stable fingerprint manifest changed: {fingerprints}")
    numeric, categorical, interactions = feature_spec(EXPECTED_LANDMARK)
    if tuple(bundle["numeric_features"]) != tuple(numeric):
        raise ValueError("numeric feature order changed")
    if tuple(bundle["categorical_features"]) != tuple(categorical):
        raise ValueError("categorical feature order changed")
    if tuple(tuple(pair) for pair in bundle["interactions"]) != tuple(interactions):
        raise ValueError("interaction feature order changed")
    return bundle


def validate_validation_events(events: pd.DataFrame) -> None:
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
        raise ValueError(f"validation events missing columns: {missing}")
    pairs = tuple(sorted(events["instrument"].dropna().unique()))
    if pairs != PAIRS:
        raise ValueError(f"expected exactly {PAIRS}, found {pairs}")
    years = tuple(sorted(pd.to_datetime(events["trade_date"]).dt.year.unique()))
    if years != VALIDATION_YEARS:
        raise ValueError(f"expected validation years {VALIDATION_YEARS}, found {years}")
    if events["event_id"].duplicated().any():
        raise ValueError("validation event IDs must be unique")
    if events[TARGET].isna().any():
        raise ValueError("validation target contains missing values")


def _add_year_quintiles(predictions: pd.DataFrame) -> pd.DataFrame:
    result = predictions.copy()
    result["quintile"] = 0
    for _, indices in result.groupby("year").groups.items():
        frame = result.loc[list(indices)].sort_values(["prediction", "event_id"])
        ranks = frame["prediction"].rank(method="first", pct=True)
        result.loc[frame.index, "quintile"] = (
            np.ceil(ranks * 5).clip(1, 5).astype(int).to_numpy()
        )
    return result


def _subgroup_lift(predictions: pd.DataFrame, column: str) -> pd.DataFrame:
    rows = []
    for value, group in predictions.groupby(column, sort=True):
        base = float(group["target"].mean())
        top = float(group.loc[group["quintile"] == 5, "target"].mean())
        rows.append(
            {
                column: value,
                "event_count": int(len(group)),
                "success_count": int(group["target"].sum()),
                "base_rate": base,
                "top_quintile_rate": top,
                "top_quintile_lift": _relative_lift(top, base),
                "positive_top_lift": bool(np.isfinite(top) and top > base),
            }
        )
    return pd.DataFrame(rows)


def _fingerprint_direction_table(
    population: pd.DataFrame,
    transformed: np.ndarray,
    bundle: dict[str, Any],
) -> pd.DataFrame:
    names = list(bundle["preprocessor"].feature_names)
    classifier = bundle["classifier"]
    rows = []
    ordered_ids = population["event_id"].astype(str).to_numpy()
    targets = population["target"].to_numpy(dtype=int)
    for feature, expected in EXPECTED_STABLE_FINGERPRINTS:
        if feature not in names:
            raise ValueError(f"stable feature absent from transformed matrix: {feature}")
        index = names.index(feature)
        values = transformed[:, index]
        order = np.lexsort((ordered_ids, values))
        quartile_count = max(1, len(values) // 4)
        low_indices = order[:quartile_count]
        high_indices = order[-quartile_count:]
        low_rate = float(targets[low_indices].mean())
        high_rate = float(targets[high_indices].mean())
        observed_effect = high_rate - low_rate
        if observed_effect > 0:
            observed_direction = "POSITIVE"
        elif observed_effect < 0:
            observed_direction = "NEGATIVE"
        else:
            observed_direction = "NEUTRAL"

        q25 = float(np.quantile(values, 0.25))
        q75 = float(np.quantile(values, 0.75))
        low = transformed.copy()
        high = transformed.copy()
        low[:, index] = q25
        high[:, index] = q75
        model_effect = float(
            classifier.predict_proba(high)[:, 1].mean()
            - classifier.predict_proba(low)[:, 1].mean()
        )
        if model_effect > 0:
            model_direction = "POSITIVE"
        elif model_effect < 0:
            model_direction = "NEGATIVE"
        else:
            model_direction = "NEUTRAL"
        rows.append(
            {
                "feature": feature,
                "expected_direction": expected,
                "low_quartile_count": quartile_count,
                "high_quartile_count": quartile_count,
                "low_quartile_success_rate": low_rate,
                "high_quartile_success_rate": high_rate,
                "observed_effect": observed_effect,
                "observed_direction": observed_direction,
                "observed_direction_preserved": observed_direction == expected,
                "model_partial_dependence_effect": model_effect,
                "model_partial_dependence_direction": model_direction,
            }
        )
    return pd.DataFrame(rows)
