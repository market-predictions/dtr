from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import (
    YEARS,
    _model,
    _parameter_grid,
    feature_spec,
    fit_preprocessor,
    transform_preprocessor,
)


def _safe_average_precision(y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(average_precision_score(y, p))


def _safe_roc_auc(y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, p))


def _fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    landmark: Literal["T0", "T5"],
    family: Literal["elastic_net", "hgb"],
    params: dict[str, Any],
):
    numeric, categorical, interactions = feature_spec(landmark)
    state = fit_preprocessor(train, numeric, categorical, interactions)
    x_train = transform_preprocessor(train, state)
    x_test = transform_preprocessor(test, state)
    model = _model(family, params)
    model.fit(x_train, train["target"].to_numpy(dtype=int))
    predictions = model.predict_proba(x_test)[:, 1]
    return model, state, predictions


def select_hyperparameters(
    outer_train: pd.DataFrame,
    landmark: Literal["T0", "T5"],
    family: Literal["elastic_net", "hgb"],
) -> tuple[dict[str, Any], pd.DataFrame]:
    numeric, categorical, interactions = feature_spec(landmark)
    prepared_folds: list[dict[str, Any]] = []
    training_years = sorted(outer_train["year"].unique())
    for inner_year in training_years:
        inner_train = outer_train.loc[outer_train["year"] != inner_year]
        inner_test = outer_train.loc[outer_train["year"] == inner_year]
        if inner_train["target"].nunique() < 2 or inner_test.empty:
            raise RuntimeError(f"invalid inner fold for year {inner_year}")
        state = fit_preprocessor(inner_train, numeric, categorical, interactions)
        prepared_folds.append(
            {
                "inner_year": int(inner_year),
                "x_train": transform_preprocessor(inner_train, state),
                "y_train": inner_train["target"].to_numpy(dtype=int),
                "x_test": transform_preprocessor(inner_test, state),
                "y_test": inner_test["target"].to_numpy(dtype=int),
            }
        )

    rows: list[dict[str, Any]] = []
    for params in _parameter_grid(family):
        prediction_parts: list[pd.DataFrame] = []
        converged_folds = 0
        failed = False
        for fold in prepared_folds:
            try:
                model = _model(family, params)
                model.fit(fold["x_train"], fold["y_train"])
                prediction = model.predict_proba(fold["x_test"])[:, 1]
                if family == "elastic_net":
                    converged = bool(int(model.n_iter_) < model.max_iter)
                else:
                    converged = True
                converged_folds += int(converged)
            except Exception:
                failed = True
                break
            prediction_parts.append(
                pd.DataFrame(
                    {
                        "target": fold["y_test"],
                        "prediction": prediction,
                    }
                )
            )
        if failed or not prediction_parts:
            pr_auc = float("nan")
            brier = float("nan")
        else:
            ledger = pd.concat(prediction_parts, ignore_index=True)
            pr_auc = _safe_average_precision(
                ledger["target"].to_numpy(), ledger["prediction"].to_numpy()
            )
            brier = float(
                brier_score_loss(
                    ledger["target"].to_numpy(), ledger["prediction"].to_numpy()
                )
            )
        rows.append(
            {
                **params,
                "pr_auc": pr_auc,
                "brier": brier,
                "converged_fold_count": converged_folds,
                "total_inner_folds": len(prepared_folds),
                "fully_converged": converged_folds == len(prepared_folds),
            }
        )
    results = pd.DataFrame(rows)
    valid = results.dropna(subset=["pr_auc", "brier"]).copy()
    if valid.empty:
        raise RuntimeError(f"no valid hyperparameters for {landmark} {family}")
    best_pr = float(valid["pr_auc"].max())
    candidates = valid.loc[valid["pr_auc"] >= best_pr - 0.002].copy()
    best_brier = float(candidates["brier"].min())
    candidates = candidates.loc[candidates["brier"] <= best_brier + 0.001].copy()
    if candidates["fully_converged"].any():
        candidates = candidates.loc[candidates["fully_converged"]].copy()
    if family == "elastic_net":
        candidates = candidates.sort_values(
            ["alpha", "l1_ratio"], ascending=[False, False], kind="mergesort"
        )
        best = {
            "alpha": float(candidates.iloc[0]["alpha"]),
            "l1_ratio": float(candidates.iloc[0]["l1_ratio"]),
        }
    else:
        candidates = candidates.sort_values(
            ["max_leaf_nodes", "min_samples_leaf", "l2_regularization", "learning_rate"],
            ascending=[True, False, False, True],
            kind="mergesort",
        )
        first = candidates.iloc[0]
        best = {
            "learning_rate": float(first["learning_rate"]),
            "max_leaf_nodes": int(first["max_leaf_nodes"]),
            "min_samples_leaf": int(first["min_samples_leaf"]),
            "l2_regularization": float(first["l2_regularization"]),
        }
    return best, results


def outer_cross_validate(
    population: pd.DataFrame,
    landmark: Literal["T0", "T5"],
    family: Literal["elastic_net", "hgb"],
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    prediction_rows: list[pd.DataFrame] = []
    tuning_rows: list[pd.DataFrame] = []
    fitted: list[dict[str, Any]] = []
    fold_params: list[dict[str, Any]] = []
    for outer_year in YEARS:
        train = population.loc[population["year"] != outer_year].copy()
        test = population.loc[population["year"] == outer_year].copy()
        best_params, tuning = select_hyperparameters(train, landmark, family)
        tuning.insert(0, "outer_year", outer_year)
        tuning.insert(1, "landmark", landmark)
        tuning.insert(2, "family", family)
        tuning_rows.append(tuning)
        model, state, p = _fit_predict(train, test, landmark, family, best_params)
        fold = test[
            [
                "event_id",
                "instrument",
                "trade_date",
                "week_key",
                "year",
                "side",
                "weekday",
                "sweep_timestamp_utc",
                "target",
            ]
        ].copy()
        fold["prediction"] = p
        fold["baseline_prediction"] = float(train["target"].mean())
        fold["outer_year"] = outer_year
        fold["landmark"] = landmark
        fold["family"] = family
        prediction_rows.append(fold)
        fold_params.append(
            {
                "outer_year": outer_year,
                "landmark": landmark,
                "family": family,
                "parameters": best_params,
            }
        )
        fitted.append(
            {
                "outer_year": outer_year,
                "model": model,
                "preprocessor": state,
                "train": train,
                "test": test,
                "x_train": transform_preprocessor(train, state),
                "x_test": transform_preprocessor(test, state),
                "predictions": p,
            }
        )
    predictions = pd.concat(prediction_rows, ignore_index=True)
    if len(predictions) != len(population) or predictions["event_id"].nunique() != len(population):
        raise AssertionError("each eligible event must receive exactly one OOF prediction")
    return predictions, pd.concat(tuning_rows, ignore_index=True), fitted, fold_params
