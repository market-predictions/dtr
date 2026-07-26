from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from dtr_lab.strategies.asia_sweep.early_entry_modeling import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    PAIRS,
    YEARS,
)
from dtr_lab.strategies.asia_sweep.extended_reversal_targets import (
    LANDMARKS,
    TARGET_ORDER,
)

ModelFamily = Literal["elastic_net", "hgb"]
FAMILIES: tuple[ModelFamily, ...] = ("elastic_net", "hgb")
RANDOM_SEED = 20260726
ELASTIC_GRID = tuple(
    (alpha, l1_ratio)
    for alpha in (0.0001, 0.0003, 0.001)
    for l1_ratio in (0.25, 0.50)
)
HGB_GRID = ((0.04, 7), (0.08, 15))


def validate_extended_ledger(frame: pd.DataFrame) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "side",
        "weekday",
        "landmark",
        "extended_target",
        "extended_target_hit",
        "extended_reward_risk",
        "extended_reward_risk_stress_010",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing extended model columns: {missing}")
    if tuple(sorted(frame["instrument"].unique())) != PAIRS:
        raise ValueError("extended model ledger must contain EURUSD and GBPUSD")
    years = tuple(sorted(pd.to_numeric(frame["year"]).astype(int).unique()))
    if years != YEARS:
        raise ValueError("extended model ledger must contain 2015-2019")
    if frame.duplicated(["event_id", "landmark", "extended_target"]).any():
        raise ValueError("extended model keys must be unique")


def _elastic(config: tuple[float, float]) -> Pipeline:
    alpha, l1_ratio = config
    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                list(NUMERIC_FEATURES),
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                list(CATEGORICAL_FEATURES),
            ),
        ]
    )
    model = SGDClassifier(
        loss="log_loss",
        penalty="elasticnet",
        alpha=alpha,
        l1_ratio=l1_ratio,
        max_iter=2000,
        tol=1e-4,
        random_state=RANDOM_SEED,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def _hgb(config: tuple[float, int]) -> Pipeline:
    learning_rate, leaves = config
    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                SimpleImputer(strategy="median", add_indicator=True),
                list(NUMERIC_FEATURES),
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        (
                            "encode",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                            ),
                        ),
                    ]
                ),
                list(CATEGORICAL_FEATURES),
            ),
        ]
    )
    model = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_leaf_nodes=leaves,
        min_samples_leaf=45,
        l2_regularization=5.0,
        max_iter=100,
        random_state=RANDOM_SEED,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def _model(family: ModelFamily, config: tuple[float, float | int]) -> Pipeline:
    if family == "elastic_net":
        return _elastic((float(config[0]), float(config[1])))
    return _hgb((float(config[0]), int(config[1])))


def _fit_platt(target: np.ndarray, probabilities: np.ndarray) -> LogisticRegression:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    return LogisticRegression(C=1e4, solver="lbfgs", max_iter=1000).fit(
        logits, target
    )


def _apply_platt(
    calibrator: LogisticRegression,
    probabilities: np.ndarray,
) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    return calibrator.predict_proba(logits)[:, 1]


def fit_outer_predictions(
    ledger: pd.DataFrame,
    *,
    target_name: str,
    landmark: str,
    family: ModelFamily,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if target_name not in TARGET_ORDER or landmark not in LANDMARKS:
        raise ValueError("extended target or landmark outside frozen contract")
    population = ledger.loc[
        ledger["extended_target"].eq(target_name)
        & ledger["landmark"].eq(landmark)
    ].reset_index(drop=True)
    if population["extended_target_hit"].sum() < 20:
        raise ValueError(f"{target_name}/{landmark}: insufficient positive cases")
    grid = ELASTIC_GRID if family == "elastic_net" else HGB_GRID
    predictions: list[pd.DataFrame] = []
    tuning: list[dict[str, Any]] = []
    for outer_year in YEARS:
        train = population.loc[population["year"].ne(outer_year)].reset_index(drop=True)
        test = population.loc[population["year"].eq(outer_year)].copy()
        groups = train["week_key"].astype(str)
        inner = GroupKFold(n_splits=3)
        best: tuple[float, float, tuple[float, float | int], np.ndarray] | None = None
        for config in grid:
            inner_probability = np.full(len(train), math.nan, dtype=float)
            for fit_index, validation_index in inner.split(
                train,
                train["extended_target_hit"],
                groups,
            ):
                model = _model(family, config)
                model.fit(
                    train.iloc[fit_index],
                    train.iloc[fit_index]["extended_target_hit"],
                )
                inner_probability[validation_index] = model.predict_proba(
                    train.iloc[validation_index]
                )[:, 1]
            clipped = np.clip(inner_probability, 1e-6, 1.0 - 1e-6)
            loss = float(log_loss(train["extended_target_hit"], clipped))
            pr_auc = float(
                average_precision_score(train["extended_target_hit"], clipped)
            )
            candidate = (loss, -pr_auc, config, inner_probability)
            if best is None or candidate[:2] < best[:2]:
                best = candidate
        if best is None:
            raise RuntimeError(f"{target_name}/{landmark}/{family}: no model")
        loss, negative_pr_auc, config, inner_probability = best
        calibrator = _fit_platt(
            train["extended_target_hit"].to_numpy(dtype=int),
            inner_probability,
        )
        model = _model(family, config)
        model.fit(train, train["extended_target_hit"])
        probability = _apply_platt(calibrator, model.predict_proba(test)[:, 1])
        output_columns = [
            "event_id",
            "instrument",
            "trade_date",
            "week_key",
            "year",
            "side",
            "weekday",
            "landmark",
            "extended_target",
            "extended_target_hit",
            "extended_reward_risk",
            "extended_reward_risk_stress_010",
            "entry_timestamp_utc",
            "entry_price",
            "stop_price",
            "extended_target_price",
        ]
        output = test.loc[:, output_columns].copy()
        output["probability"] = probability
        output["family"] = family
        output["outer_year"] = outer_year
        predictions.append(output)
        tuning.append(
            {
                "extended_target": target_name,
                "landmark": landmark,
                "family": family,
                "outer_year": outer_year,
                "config": repr(config),
                "inner_log_loss": loss,
                "inner_pr_auc": -negative_pr_auc,
            }
        )
    return pd.concat(predictions, ignore_index=True), pd.DataFrame(tuning)


def _year_deciles(predictions: pd.DataFrame) -> pd.DataFrame:
    result = predictions.copy()
    result["decile"] = result.groupby("year")["probability"].transform(
        lambda values: pd.qcut(values.rank(method="first"), 10, labels=False) + 1
    )
    return result


def _breadth(group: pd.DataFrame, column: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for value, segment in group.groupby(column, sort=True):
        top = segment.loc[segment["decile"].eq(10)]
        rows.append(
            {
                column: value,
                "events": int(len(segment)),
                "base_rate": float(segment["extended_target_hit"].mean()),
                "top_decile_events": int(len(top)),
                "top_decile_rate": float(top["extended_target_hit"].mean()),
            }
        )
    table = pd.DataFrame(rows)
    table["positive_top_lift"] = table["top_decile_rate"].gt(table["base_rate"])
    return table


def summarize_predictions(
    predictions: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    scored = _year_deciles(predictions)
    target = scored["extended_target_hit"].to_numpy(dtype=int)
    probability = scored["probability"].to_numpy(dtype=float)
    base_rate = float(target.mean())
    pr_auc = float(average_precision_score(target, probability))
    brier = float(brier_score_loss(target, probability))
    top = scored.loc[scored["decile"].eq(10)].copy()
    bottom = scored.loc[scored["decile"].eq(1)].copy()
    expected_value = (
        top["probability"] * top["extended_reward_risk_stress_010"]
        - (1.0 - top["probability"])
    )
    tables = {
        column: _breadth(scored, column)
        for column in ("instrument", "year", "weekday", "side")
    }
    concentration = max(
        float(top[column].value_counts(normalize=True).max())
        for column in ("instrument", "year", "weekday", "side")
    )
    summary: dict[str, Any] = {
        "events": int(len(scored)),
        "positive_cases": int(target.sum()),
        "base_rate": base_rate,
        "pr_auc": pr_auc,
        "pr_auc_relative_lift": pr_auc / base_rate - 1.0,
        "brier": brier,
        "constant_brier": base_rate * (1.0 - base_rate),
        "top_decile_events": int(len(top)),
        "top_decile_rate": float(top["extended_target_hit"].mean()),
        "top_decile_lift": float(top["extended_target_hit"].mean() / base_rate),
        "bottom_decile_rate": float(bottom["extended_target_hit"].mean()),
        "bottom_decile_ratio": float(bottom["extended_target_hit"].mean() / base_rate),
        "median_top_decile_reward_risk_stress_010": float(
            top["extended_reward_risk_stress_010"].median()
        ),
        "top_decile_rr_stress_at_least_1_25": float(
            top["extended_reward_risk_stress_010"].ge(1.25).mean()
        ),
        "median_top_decile_ev_stress_010": float(expected_value.median()),
        "pair_positive_lift_count": int(
            tables["instrument"]["positive_top_lift"].sum()
        ),
        "year_positive_lift_count": int(tables["year"]["positive_top_lift"].sum()),
        "max_top_decile_concentration": concentration,
    }
    gates = {
        "sample_size": summary["events"] >= 400
        and summary["positive_cases"] >= 75
        and summary["top_decile_events"] >= 50,
        "pr_auc_lift": summary["pr_auc_relative_lift"] >= 0.50,
        "top_decile_lift": summary["top_decile_lift"] >= 2.00,
        "bottom_decile": summary["bottom_decile_ratio"] <= 0.60,
        "brier": summary["brier"] < summary["constant_brier"],
        "pair_breadth": summary["pair_positive_lift_count"] == 2,
        "year_breadth": summary["year_positive_lift_count"] >= 4,
        "reward_risk": summary["median_top_decile_reward_risk_stress_010"] >= 1.50,
        "reward_risk_breadth": summary["top_decile_rr_stress_at_least_1_25"]
        >= 0.75,
        "expected_value": summary["median_top_decile_ev_stress_010"] > 0.0,
        "concentration": summary["max_top_decile_concentration"] <= 0.70,
    }
    summary["gates"] = gates
    summary["passes"] = bool(all(gates.values()))
    return summary, {"predictions": scored, **tables}
