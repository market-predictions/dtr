from __future__ import annotations

import json
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import (
    RANDOM_SEED,
    T0_CATEGORICAL_FEATURES,
    T0_NUMERIC_FEATURES,
    T5_INCREMENTAL_FEATURES,
    YEARS,
    PreprocessorState,
    _model,
    feature_spec,
    fit_preprocessor,
    transform_preprocessor,
)
from dtr_lab.strategies.asia_sweep.fingerprint_model_tuning import _safe_average_precision


def _encoded_parent(name: str) -> str:
    known = set(T0_NUMERIC_FEATURES) | set(T5_INCREMENTAL_FEATURES)
    if "__x__" in name:
        return name
    if name.endswith("__missing"):
        return name.removesuffix("__missing")
    if name in known:
        return name
    for categorical in T0_CATEGORICAL_FEATURES:
        prefix = f"{categorical}_"
        if name.startswith(prefix):
            return categorical
    return name


def stable_logistic_fingerprints(
    fitted: list[dict[str, Any]],
) -> pd.DataFrame:
    coefficient_rows: list[pd.DataFrame] = []
    for item in fitted:
        model = item["model"]
        state: PreprocessorState = item["preprocessor"]
        coefficients = model.coef_[0]
        coefficient_rows.append(
            pd.DataFrame(
                {
                    "outer_year": item["outer_year"],
                    "encoded_feature": state.feature_names,
                    "coefficient": coefficients,
                }
            )
        )
    coefficients = pd.concat(coefficient_rows, ignore_index=True)
    coefficients["parent_feature"] = coefficients["encoded_feature"].map(_encoded_parent)
    rows = []
    for feature, group in coefficients.groupby("parent_feature"):
        by_year = group.groupby("outer_year")["coefficient"].apply(
            lambda values: float(values.iloc[np.argmax(np.abs(values.to_numpy()))])
        )
        nonzero = by_year.loc[by_year.abs() > 1e-8]
        positive = int((nonzero > 0).sum())
        negative = int((nonzero < 0).sum())
        direction = "POSITIVE" if positive >= negative else "NEGATIVE"
        consistent = max(positive, negative)
        rows.append(
            {
                "feature": feature,
                "median_importance": float(by_year.abs().median()),
                "median_effect": float(by_year.median()),
                "positive_importance_fold_count": int((by_year.abs() > 1e-8).sum()),
                "positive_direction_fold_count": positive,
                "negative_direction_fold_count": negative,
                "consistent_direction_fold_count": consistent,
                "direction": direction,
                "stable": bool(consistent >= 5),
                "method": "standardised_elastic_net_coefficient",
            }
        )
    result = pd.DataFrame(rows).sort_values(
        ["stable", "median_importance"], ascending=[False, False]
    )
    return result.reset_index(drop=True)


def stable_hgb_fingerprints(
    fitted: list[dict[str, Any]],
    *,
    repeats: int = 3,
) -> pd.DataFrame:
    fold_rows: list[dict[str, Any]] = []
    categorical = set(T0_CATEGORICAL_FEATURES)
    for item in fitted:
        model = item["model"]
        state: PreprocessorState = item["preprocessor"]
        x_train = item["x_train"]
        x_test = item["x_test"]
        y_test = item["test"]["target"].to_numpy(dtype=int)
        names = list(state.feature_names)
        baseline = _safe_average_precision(y_test, model.predict_proba(x_test)[:, 1])
        groups: dict[str, list[int]] = {}
        for index, name in enumerate(names):
            groups.setdefault(_encoded_parent(name), []).append(index)
        for group_number, (feature, indices) in enumerate(sorted(groups.items())):
            seed = RANDOM_SEED + int(item["outer_year"]) * 1000 + group_number
            rng = np.random.default_rng(seed)
            importances = []
            for _ in range(repeats):
                order = rng.permutation(len(x_test))
                shuffled = x_test.copy()
                shuffled[:, indices] = x_test[order][:, indices]
                score = _safe_average_precision(y_test, model.predict_proba(shuffled)[:, 1])
                importances.append(baseline - score)
            importance = float(np.mean(importances))

            direction_value = float("nan")
            if feature not in categorical:
                exact_indices = [i for i in indices if names[i] == feature]
                if exact_indices:
                    low = x_test.copy()
                    high = x_test.copy()
                    source_index = exact_indices[0]
                    q25 = float(np.quantile(x_train[:, source_index], 0.25))
                    q75 = float(np.quantile(x_train[:, source_index], 0.75))
                    low[:, source_index] = q25
                    high[:, source_index] = q75
                    for i in indices:
                        if names[i].endswith("__missing"):
                            low[:, i] = 0.0
                            high[:, i] = 0.0
                    direction_value = float(
                        model.predict_proba(high)[:, 1].mean()
                        - model.predict_proba(low)[:, 1].mean()
                    )
            fold_rows.append(
                {
                    "outer_year": item["outer_year"],
                    "feature": feature,
                    "importance": importance,
                    "direction_effect": direction_value,
                }
            )
    fold_table = pd.DataFrame(fold_rows)
    rows = []
    for feature, group in fold_table.groupby("feature"):
        positive_importance = int((group["importance"] > 0).sum())
        finite_direction = group["direction_effect"].dropna()
        positive_direction = int((finite_direction > 0).sum())
        negative_direction = int((finite_direction < 0).sum())
        consistent_direction = max(positive_direction, negative_direction)
        direction = "POSITIVE" if positive_direction >= negative_direction else "NEGATIVE"
        stable = positive_importance >= 5 and consistent_direction >= 5
        rows.append(
            {
                "feature": feature,
                "median_importance": float(group["importance"].median()),
                "median_effect": (
                    float(finite_direction.median())
                    if not finite_direction.empty
                    else float("nan")
                ),
                "positive_importance_fold_count": positive_importance,
                "positive_direction_fold_count": positive_direction,
                "negative_direction_fold_count": negative_direction,
                "consistent_direction_fold_count": consistent_direction,
                "direction": direction if not finite_direction.empty else "UNDEFINED",
                "stable": bool(stable),
                "method": "grouped_permutation_importance_and_quartile_contrast",
            }
        )
    result = pd.DataFrame(rows).sort_values(
        ["stable", "median_importance"], ascending=[False, False]
    )
    return result.reset_index(drop=True)


def _parameter_key(parameters: dict[str, Any]) -> str:
    return json.dumps(parameters, sort_keys=True, separators=(",", ":"))


def select_final_parameters(
    fold_params: list[dict[str, Any]],
    tuning: pd.DataFrame,
    family: str,
) -> dict[str, Any]:
    keys = [_parameter_key(row["parameters"]) for row in fold_params]
    counts = Counter(keys)
    max_count = max(counts.values())
    candidates = [key for key, count in counts.items() if count == max_count]
    if len(candidates) > 1:
        median_ranks: dict[str, float] = {}
        for key in candidates:
            parameters = json.loads(key)
            ranks = []
            for _, fold in tuning.groupby("outer_year"):
                ranked = fold.sort_values(
                    ["pr_auc", "brier"], ascending=[False, True], kind="mergesort"
                ).reset_index(drop=True)
                mask = np.ones(len(ranked), dtype=bool)
                for name, value in parameters.items():
                    mask &= np.isclose(ranked[name].astype(float), float(value))
                matches = np.flatnonzero(mask)
                if len(matches):
                    ranks.append(int(matches[0]) + 1)
            median_ranks[key] = float(np.median(ranks)) if ranks else float("inf")
        best_rank = min(median_ranks.values())
        candidates = [key for key in candidates if median_ranks[key] == best_rank]
    parsed = [json.loads(key) for key in candidates]
    if family == "elastic_net":
        parsed.sort(
            key=lambda value: (
                -float(value["alpha"]),
                -float(value["l1_ratio"]),
                _parameter_key(value),
            )
        )
    else:
        parsed.sort(
            key=lambda value: (
                int(value["max_leaf_nodes"]),
                -int(value["min_samples_leaf"]),
                -float(value["l2_regularization"]),
                float(value["learning_rate"]),
                _parameter_key(value),
            )
        )
    return parsed[0]


def fit_final_bundle(
    population: pd.DataFrame,
    landmark: str,
    family: str,
    parameters: dict[str, Any],
    stable_fingerprints: pd.DataFrame,
    abstention_rule: dict[str, Any],
) -> dict[str, Any]:
    numeric, categorical, interactions = feature_spec(landmark)
    state = fit_preprocessor(population, numeric, categorical, interactions)
    x = transform_preprocessor(population, state)
    model = _model(family, parameters)
    model.fit(x, population["target"].to_numpy(dtype=int))
    stable = stable_fingerprints.loc[stable_fingerprints["stable"]].head(5)
    return {
        "programme": "ASIAN_SWEEP_FINGERPRINT_V1",
        "stage": "FROZEN_DEVELOPMENT_MODEL",
        "source_run_id": 30174245825,
        "source_commit": "8b1946a40fd9b01069f8c6084fe425bda6d830d2",
        "development_years": YEARS,
        "landmark": landmark,
        "family": family,
        "parameters": parameters,
        "numeric_features": numeric,
        "categorical_features": categorical,
        "interactions": interactions,
        "preprocessor": state,
        "classifier": model,
        "abstention_rule": abstention_rule,
        "stable_fingerprints": stable[["feature", "direction"]].to_dict("records"),
        "development_event_count": int(len(population)),
        "development_success_count": int(population["target"].sum()),
        "development_base_rate": float(population["target"].mean()),
    }
