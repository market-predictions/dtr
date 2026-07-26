from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.model_selection import GroupKFold
from sklearn.utils.class_weight import compute_sample_weight

from dtr_lab.strategies.asia_sweep.early_entry_modeling import (
    CATEGORICAL_FEATURES,
    HGB_GRID,
    LOGISTIC_GRID,
    NUMERIC_FEATURES,
    _apply_platt,
    _fit_platt,
    _make_model,
)

DEVELOPMENT_YEARS = tuple(range(2015, 2020))
LANDMARKS = ("T0", "T1", "T2", "T3")
FAMILIES = ("elastic_net", "hgb")
CLASSES = ("CONTINUATION", "REVERSAL", "UNRESOLVED")
REV_THRESHOLDS = (0.55, 0.60, 0.65, 0.70)
CONT_THRESHOLDS = (0.70, 0.75, 0.80, 0.85)
MAX_UNRESOLVED = (0.20, 0.30, 0.40)
MARGINS = (0.15, 0.25, 0.35)


def prepare_triage_ledger(ledger: pd.DataFrame) -> pd.DataFrame:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "side",
        "weekday",
        "landmark",
        "primary_outcome",
        "two_sided_ambiguous",
        "reward_risk",
        "entry_price",
        "entry_timestamp_utc",
        "stop_price",
        "asian_midpoint",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing triage columns: {missing}")
    frame = ledger.loc[ledger["landmark"].isin(LANDMARKS)].copy()
    frame = frame.loc[~frame["two_sided_ambiguous"].astype(bool)].copy()
    frame["triage_outcome"] = np.select(
        [
            frame["primary_outcome"].eq("MIDPOINT_SUCCESS_09_10"),
            frame["primary_outcome"].isin(
                ("IMMEDIATE_CONTINUATION", "FALSE_REVERSAL")
            ),
        ],
        ["REVERSAL", "CONTINUATION"],
        default="UNRESOLVED",
    )
    frame["resolved_target"] = frame["triage_outcome"].ne("UNRESOLVED").astype(int)
    frame["reversal_target"] = frame["triage_outcome"].eq("REVERSAL").astype(int)
    frame = frame.sort_values(
        ["landmark", "event_id"], kind="mergesort"
    ).reset_index(drop=True)
    if frame.duplicated(["event_id", "landmark"]).any():
        raise ValueError("duplicate event-landmark keys")
    return frame


def _component_population(train: pd.DataFrame, target: str) -> pd.DataFrame:
    if target == "resolved_target":
        return train
    return train.loc[train["resolved_target"].eq(1)].reset_index(drop=True)


def _component_oof(
    train: pd.DataFrame,
    family: str,
    target: str,
) -> tuple[tuple[float, float | int], np.ndarray, pd.DataFrame]:
    population = _component_population(train, target)
    grid = LOGISTIC_GRID if family == "elastic_net" else HGB_GRID
    folds = GroupKFold(n_splits=3)
    groups = population["week_key"].astype(str)
    rows: list[dict[str, Any]] = []
    best: tuple[float, float, tuple[float, float | int], np.ndarray] | None = None
    for config in grid:
        probability = np.full(len(population), math.nan, dtype=float)
        for fit_index, validation_index in folds.split(
            population, population[target], groups
        ):
            fit = population.iloc[fit_index]
            validation = population.iloc[validation_index]
            model = _make_model(family, config)
            weights = compute_sample_weight("balanced", fit[target])
            model.fit(fit, fit[target], model__sample_weight=weights)
            probability[validation_index] = model.predict_proba(validation)[:, 1]
        clipped = np.clip(probability, 1e-6, 1.0 - 1e-6)
        loss = float(log_loss(population[target], clipped))
        brier = float(brier_score_loss(population[target], probability))
        rows.append(
            {
                "component": target,
                "family": family,
                "config": repr(config),
                "inner_log_loss": loss,
                "inner_brier": brier,
            }
        )
        candidate = (loss, brier, config, probability)
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    if best is None:
        raise RuntimeError(f"{family}/{target}: no fitted configuration")
    return best[2], best[3], pd.DataFrame(rows)


def _fit_component(
    train: pd.DataFrame,
    test: pd.DataFrame,
    family: str,
    target: str,
) -> tuple[np.ndarray, np.ndarray, tuple[float, float | int], pd.DataFrame]:
    population = _component_population(train, target)
    config, oof_raw, tuning = _component_oof(train, family, target)
    calibrator = _fit_platt(population[target].to_numpy(), oof_raw)
    oof_probability = _apply_platt(calibrator, oof_raw)
    model = _make_model(family, config)
    weights = compute_sample_weight("balanced", population[target])
    model.fit(population, population[target], model__sample_weight=weights)
    test_probability = _apply_platt(calibrator, model.predict_proba(test)[:, 1])
    return oof_probability, test_probability, config, tuning


def probabilities_from_components(
    p_resolved: np.ndarray,
    p_reversal_given_resolved: np.ndarray,
) -> pd.DataFrame:
    p_resolved = np.clip(p_resolved, 0.0, 1.0)
    p_reversal_given_resolved = np.clip(p_reversal_given_resolved, 0.0, 1.0)
    p_reversal = p_resolved * p_reversal_given_resolved
    p_continuation = p_resolved * (1.0 - p_reversal_given_resolved)
    p_unresolved = 1.0 - p_resolved
    total = p_reversal + p_continuation + p_unresolved
    return pd.DataFrame(
        {
            "p_continuation": p_continuation / total,
            "p_reversal": p_reversal / total,
            "p_unresolved": p_unresolved / total,
        }
    )


def apply_actions(
    probabilities: pd.DataFrame,
    threshold: tuple[float, float, float, float],
) -> np.ndarray:
    reversal_threshold, continuation_threshold, max_unresolved, margin = threshold
    reversal = probabilities["p_reversal"].to_numpy()
    continuation = probabilities["p_continuation"].to_numpy()
    unresolved = probabilities["p_unresolved"].to_numpy()
    action = np.full(len(probabilities), "ABSTAIN", dtype=object)
    reversal_call = (
        (unresolved <= max_unresolved)
        & (reversal >= reversal_threshold)
        & ((reversal - continuation) >= margin)
    )
    continuation_call = (
        (unresolved <= max_unresolved)
        & (continuation >= continuation_threshold)
        & ((continuation - reversal) >= margin)
    )
    action[reversal_call] = "REVERSAL"
    action[continuation_call] = "CONTINUATION"
    return action


def action_metrics(outcome: np.ndarray, action: np.ndarray) -> dict[str, float]:
    take = action != "ABSTAIN"
    correct = action == outcome
    reversal = action == "REVERSAL"
    continuation = action == "CONTINUATION"
    true_reversal = outcome == "REVERSAL"
    return {
        "coverage": float(take.mean()),
        "continuation_coverage": float(continuation.mean()),
        "reversal_calls": float(reversal.sum()),
        "continuation_precision": (
            float(correct[continuation].mean()) if continuation.any() else 0.0
        ),
        "reversal_precision": (
            float(correct[reversal].mean()) if reversal.any() else 0.0
        ),
        "selective_accuracy": float(correct[take].mean()) if take.any() else 0.0,
        "utility_per_event": float(
            (correct[take].sum() - 1.5 * (~correct[take]).sum()) / len(outcome)
        ),
        "continuation_false_veto_rate": (
            float((continuation & true_reversal).sum() / true_reversal.sum())
            if true_reversal.any()
            else 0.0
        ),
    }


def select_threshold(
    outcome: np.ndarray,
    probabilities: pd.DataFrame,
) -> tuple[tuple[float, float, float, float], pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    for threshold in itertools.product(
        REV_THRESHOLDS, CONT_THRESHOLDS, MAX_UNRESOLVED, MARGINS
    ):
        rows.append(
            {
                "rev_threshold": threshold[0],
                "cont_threshold": threshold[1],
                "max_unresolved": threshold[2],
                "margin": threshold[3],
                **action_metrics(outcome, apply_actions(probabilities, threshold)),
            }
        )
    table = pd.DataFrame(rows)
    full = table.loc[
        table["continuation_precision"].ge(0.80)
        & table["reversal_precision"].ge(0.50)
        & table["coverage"].ge(0.20)
    ]
    continuation_only = table.loc[table["continuation_precision"].ge(0.80)]
    pool = full if not full.empty else continuation_only
    if pool.empty:
        pool = table
    pool = pool.sort_values(
        [
            "utility_per_event",
            "coverage",
            "rev_threshold",
            "cont_threshold",
            "margin",
            "max_unresolved",
        ],
        ascending=[False, False, False, False, False, True],
        kind="mergesort",
    )
    selected = pool.iloc[0]
    threshold = (
        float(selected["rev_threshold"]),
        float(selected["cont_threshold"]),
        float(selected["max_unresolved"]),
        float(selected["margin"]),
    )
    table["selected"] = (
        table["rev_threshold"].eq(threshold[0])
        & table["cont_threshold"].eq(threshold[1])
        & table["max_unresolved"].eq(threshold[2])
        & table["margin"].eq(threshold[3])
    )
    return threshold, table


def fit_outer_fold(
    train: pd.DataFrame,
    test: pd.DataFrame,
    family: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    resolved_oof, resolved_test, _, resolved_tuning = _fit_component(
        train, test, family, "resolved_target"
    )
    direction_oof, direction_test, direction_config, direction_tuning = _fit_component(
        train, test, family, "reversal_target"
    )
    resolved_train = train.loc[train["resolved_target"].eq(1)].reset_index(drop=True)
    direction_calibrator = _fit_platt(
        resolved_train["reversal_target"].to_numpy(), direction_oof
    )
    direction_model = _make_model(family, direction_config)
    direction_weights = compute_sample_weight(
        "balanced", resolved_train["reversal_target"]
    )
    direction_model.fit(
        resolved_train,
        resolved_train["reversal_target"],
        model__sample_weight=direction_weights,
    )
    direction_train_all = _apply_platt(
        direction_calibrator, direction_model.predict_proba(train)[:, 1]
    )
    train_probabilities = probabilities_from_components(
        resolved_oof, direction_train_all
    )
    threshold, threshold_table = select_threshold(
        train["triage_outcome"].to_numpy(), train_probabilities
    )
    test_probabilities = probabilities_from_components(resolved_test, direction_test)
    columns = [
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "side",
        "weekday",
        "landmark",
        "triage_outcome",
        "reward_risk",
        "entry_price",
        "entry_timestamp_utc",
        "stop_price",
        "asian_midpoint",
    ]
    output = test.loc[:, columns].reset_index(drop=True)
    output = pd.concat([output, test_probabilities], axis=1)
    output["action"] = apply_actions(test_probabilities, threshold)
    output["family"] = family
    output["rev_threshold"] = threshold[0]
    output["cont_threshold"] = threshold[1]
    output["max_unresolved"] = threshold[2]
    output["margin"] = threshold[3]
    tuning = pd.concat([resolved_tuning, direction_tuning], ignore_index=True)
    tuning = pd.concat(
        [threshold_table.assign(component="action_threshold"), tuning],
        ignore_index=True,
        sort=False,
    )
    return output, tuning


def _multiclass_scores(predictions: pd.DataFrame) -> dict[str, float]:
    labels = list(CLASSES)
    target = pd.Categorical(
        predictions["triage_outcome"], categories=labels
    ).codes
    probability = predictions[
        ["p_continuation", "p_reversal", "p_unresolved"]
    ].to_numpy()
    baseline_probability = np.tile(
        np.bincount(target, minlength=3) / len(target), (len(target), 1)
    )
    one_hot = np.eye(3)[target]
    return {
        "log_loss": float(log_loss(target, probability, labels=[0, 1, 2])),
        "baseline_log_loss": float(
            log_loss(target, baseline_probability, labels=[0, 1, 2])
        ),
        "multiclass_brier": float(
            np.mean(np.sum((one_hot - probability) ** 2, axis=1))
        ),
        "baseline_multiclass_brier": float(
            np.mean(np.sum((one_hot - baseline_probability) ** 2, axis=1))
        ),
    }


def summarize_predictions(predictions: pd.DataFrame) -> dict[str, Any]:
    result = {
        "events": int(len(predictions)),
        **action_metrics(
            predictions["triage_outcome"].to_numpy(),
            predictions["action"].to_numpy(),
        ),
        **_multiclass_scores(predictions),
    }
    evaluated = predictions.copy()
    take = evaluated["action"].ne("ABSTAIN")
    correct = evaluated["action"].eq(evaluated["triage_outcome"])
    evaluated["utility"] = np.where(
        ~take, 0.0, np.where(correct, 1.0, -1.5)
    )
    pair_utility = evaluated.groupby("instrument")["utility"].mean()
    year_utility = evaluated.groupby("year")["utility"].mean()
    correct_reversals = evaluated.loc[
        evaluated["action"].eq("REVERSAL")
        & evaluated["triage_outcome"].eq("REVERSAL")
    ]
    concentration = 0.0
    if not correct_reversals.empty:
        concentration = max(
            float(
                correct_reversals["instrument"]
                .value_counts(normalize=True)
                .max()
            ),
            float(correct_reversals["side"].value_counts(normalize=True).max()),
            float(
                correct_reversals["weekday"].value_counts(normalize=True).max()
            ),
        )
    result.update(
        {
            "pair_positive_utility_count": int(pair_utility.gt(0).sum()),
            "year_positive_utility_count": int(year_utility.gt(0).sum()),
            "correct_reversal_concentration": concentration,
            "median_reversal_call_reward_risk": float(
                evaluated.loc[
                    evaluated["action"].eq("REVERSAL"), "reward_risk"
                ].median()
            ),
        }
    )
    full_gates = {
        "events": result["events"] >= 1500,
        "events_per_pair": bool(
            (evaluated.groupby("instrument").size() >= 600).all()
        ),
        "continuation_precision": result["continuation_precision"] >= 0.80,
        "continuation_coverage": result["continuation_coverage"] >= 0.25,
        "reversal_precision": result["reversal_precision"] >= 0.50,
        "reversal_calls": result["reversal_calls"] >= 100,
        "selective_accuracy": result["selective_accuracy"] >= 0.75,
        "utility": result["utility_per_event"] > 0.05,
        "pair_breadth": result["pair_positive_utility_count"] == 2,
        "year_breadth": result["year_positive_utility_count"] >= 4,
        "log_loss": result["log_loss"] < result["baseline_log_loss"],
        "brier": (
            result["multiclass_brier"]
            < result["baseline_multiclass_brier"]
        ),
        "concentration": result["correct_reversal_concentration"] <= 0.70,
    }
    veto_gates = {
        "continuation_precision": result["continuation_precision"] >= 0.85,
        "continuation_coverage": result["continuation_coverage"] >= 0.25,
        "utility": result["utility_per_event"] > 0.05,
        "pair_breadth": result["pair_positive_utility_count"] == 2,
        "year_breadth": result["year_positive_utility_count"] >= 4,
        "false_veto": result["continuation_false_veto_rate"] <= 0.12,
        "log_loss": result["log_loss"] < result["baseline_log_loss"],
        "brier": (
            result["multiclass_brier"]
            < result["baseline_multiclass_brier"]
        ),
    }
    result["full_gates"] = full_gates
    result["veto_gates"] = veto_gates
    result["full_pass"] = bool(all(full_gates.values()))
    result["veto_pass"] = bool(all(veto_gates.values()))
    return result


def run_development(
    ledger: pd.DataFrame,
    output_directory: Path,
) -> dict[str, Any]:
    frame = prepare_triage_ledger(ledger)
    output_directory.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    tuning_frames: list[pd.DataFrame] = []
    for landmark in LANDMARKS:
        population = frame.loc[frame["landmark"].eq(landmark)].reset_index(drop=True)
        for family in FAMILIES:
            fold_predictions: list[pd.DataFrame] = []
            for outer_year in DEVELOPMENT_YEARS:
                train = population.loc[
                    population["year"].ne(outer_year)
                ].reset_index(drop=True)
                test = population.loc[
                    population["year"].eq(outer_year)
                ].reset_index(drop=True)
                predictions, tuning = fit_outer_fold(train, test, family)
                predictions["outer_year"] = outer_year
                tuning["landmark"] = landmark
                tuning["outer_year"] = outer_year
                fold_predictions.append(predictions)
                tuning_frames.append(tuning)
            predictions = pd.concat(fold_predictions, ignore_index=True)
            summary = summarize_predictions(predictions)
            summary.update({"landmark": landmark, "family": family})
            summaries.append(summary)
            predictions.to_csv(
                output_directory / f"triage_predictions_{landmark}_{family}.csv",
                index=False,
            )
    rows: list[dict[str, Any]] = []
    for summary in summaries:
        row = {
            key: value
            for key, value in summary.items()
            if key not in ("full_gates", "veto_gates")
        }
        row["full_failed"] = ";".join(
            key for key, passed in summary["full_gates"].items() if not passed
        )
        row["veto_failed"] = ";".join(
            key for key, passed in summary["veto_gates"].items() if not passed
        )
        rows.append(row)
    candidates = pd.DataFrame(rows)
    candidates.to_csv(
        output_directory / "triage_candidate_summary.csv", index=False
    )
    pd.concat(tuning_frames, ignore_index=True).to_csv(
        output_directory / "triage_tuning.csv", index=False
    )
    order = {landmark: index for index, landmark in enumerate(LANDMARKS)}
    full = candidates.loc[candidates["full_pass"].astype(bool)].copy()
    veto = candidates.loc[candidates["veto_pass"].astype(bool)].copy()
    if not full.empty:
        full["order"] = full["landmark"].map(order)
        selected = full.sort_values(
            ["order", "utility_per_event"],
            ascending=[True, False],
            kind="mergesort",
        ).iloc[0]
        decision = {
            "decision": "PASS_FULL_TRIAGE",
            "selected_landmark": str(selected["landmark"]),
            "selected_family": str(selected["family"]),
        }
    elif not veto.empty:
        veto["order"] = veto["landmark"].map(order)
        selected = veto.sort_values(
            ["order", "utility_per_event"],
            ascending=[True, False],
            kind="mergesort",
        ).iloc[0]
        decision = {
            "decision": "PASS_CONTINUATION_VETO_ONLY",
            "selected_landmark": str(selected["landmark"]),
            "selected_family": str(selected["family"]),
        }
    else:
        decision = {
            "decision": "FAIL_TRIAGE_STOP",
            "selected_landmark": None,
            "selected_family": None,
        }
    decision.update(
        {
            "programme": "ASIAN_SWEEP_TRIAGE_V6_0",
            "development_years": list(DEVELOPMENT_YEARS),
            "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
            "candidate_count": int(len(candidates)),
            "stage_b_opened": False,
            "stage_c_opened": False,
        }
    )
    (output_directory / "triage_development_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return decision
