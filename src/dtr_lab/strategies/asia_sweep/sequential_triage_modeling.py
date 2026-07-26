from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
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
from dtr_lab.strategies.asia_sweep.sequential_triage import assign_state

ModelFamily = Literal["elastic_net", "hgb"]

CLASSES = np.array(["ABSTAIN", "CONTINUATION", "REVERSAL"])
LANDMARKS = ("T0", "T1", "T2", "T3")
RANDOM_SEED = 20260726
ELASTIC_NET_GRID = tuple(
    (c_value, l1_ratio)
    for c_value in (0.05, 0.20, 0.80)
    for l1_ratio in (0.25, 0.50)
)
HGB_GRID = ((0.04, 7), (0.08, 15))
THRESHOLD_GRID = tuple(np.round(np.arange(0.30, 0.71, 0.05), 2))
MARGIN_GRID = tuple(np.round(np.arange(0.00, 0.21, 0.05), 2))


def prepare_triage_ledger(frame: pd.DataFrame) -> pd.DataFrame:
    ledger = frame.loc[frame["landmark"].isin(LANDMARKS)].copy()
    ledger["triage_state"] = assign_state(ledger)
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "side",
        "weekday",
        "landmark",
        "triage_state",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing triage ledger columns: {missing}")
    if tuple(sorted(ledger["instrument"].unique())) != PAIRS:
        raise ValueError("triage ledger must contain EURUSD and GBPUSD")
    years = tuple(sorted(pd.to_numeric(ledger["year"]).astype(int).unique()))
    if years != YEARS:
        raise ValueError("triage ledger must contain exactly 2015-2019")
    if ledger.duplicated(["event_id", "landmark"]).any():
        raise ValueError("event-landmark keys must be unique")
    return ledger.reset_index(drop=True)


def _make_elastic_net(config: tuple[float, float]) -> Pipeline:
    c_value, l1_ratio = config
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
    model = LogisticRegression(
        solver="saga",
        C=c_value,
        l1_ratio=l1_ratio,
        max_iter=1200,
        tol=1e-3,
        random_state=RANDOM_SEED,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def _make_hgb(config: tuple[float, int]) -> Pipeline:
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


def _make_model(family: ModelFamily, config: tuple[float, float | int]) -> Pipeline:
    if family == "elastic_net":
        return _make_elastic_net((float(config[0]), float(config[1])))
    if family == "hgb":
        return _make_hgb((float(config[0]), int(config[1])))
    raise ValueError(f"unsupported triage family: {family}")


def _aligned_probabilities(model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    raw = model.predict_proba(frame)
    classes = model.named_steps["model"].classes_
    class_index = {name: index for index, name in enumerate(classes)}
    aligned = np.zeros((len(frame), len(CLASSES)), dtype=float)
    for output_index, state in enumerate(CLASSES):
        aligned[:, output_index] = raw[:, class_index[state]]
    return aligned


def _fit_calibrators(target: pd.Series, raw: np.ndarray) -> list[LogisticRegression]:
    calibrators: list[LogisticRegression] = []
    for index, state in enumerate(CLASSES):
        binary = target.eq(state).astype(int).to_numpy()
        clipped = np.clip(raw[:, index], 1e-6, 1.0 - 1e-6)
        logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
        calibrators.append(
            LogisticRegression(C=1e4, solver="lbfgs", max_iter=1000).fit(
                logits, binary
            )
        )
    return calibrators


def _apply_calibrators(
    calibrators: list[LogisticRegression], raw: np.ndarray
) -> np.ndarray:
    calibrated: list[np.ndarray] = []
    for index, calibrator in enumerate(calibrators):
        clipped = np.clip(raw[:, index], 1e-6, 1.0 - 1e-6)
        logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
        calibrated.append(calibrator.predict_proba(logits)[:, 1])
    result = np.column_stack(calibrated)
    return result / result.sum(axis=1, keepdims=True)


def _macro_relative_pr_auc(target: pd.Series, probabilities: np.ndarray) -> float:
    lifts: list[float] = []
    for index, state in enumerate(CLASSES):
        binary = target.eq(state).astype(int).to_numpy()
        base_rate = float(binary.mean())
        pr_auc = average_precision_score(binary, probabilities[:, index])
        lifts.append(float(pr_auc / base_rate - 1.0))
    return float(np.mean(lifts))


def apply_thresholds(
    probabilities: np.ndarray,
    thresholds: dict[str, float] | None,
) -> np.ndarray:
    decisions = np.full(len(probabilities), "ABSTAIN", dtype=object)
    if thresholds is None:
        return decisions
    p_abstain = probabilities[:, 0]
    p_continuation = probabilities[:, 1]
    p_reversal = probabilities[:, 2]
    reversal_pass = (
        (p_reversal >= thresholds["reversal_threshold"])
        & ((p_reversal - p_continuation) >= thresholds["conflict_margin"])
        & (p_reversal >= p_abstain)
    )
    continuation_pass = (
        (p_continuation >= thresholds["continuation_threshold"])
        & ((p_continuation - p_reversal) >= thresholds["conflict_margin"])
        & (p_continuation >= p_abstain)
    )
    decisions[reversal_pass & ~continuation_pass] = "REVERSAL"
    decisions[continuation_pass & ~reversal_pass] = "CONTINUATION"
    return decisions


def select_thresholds(
    target: pd.Series,
    probabilities: np.ndarray,
) -> dict[str, float] | None:
    target_values = target.astype(str).to_numpy()
    candidates: list[tuple[float, ...]] = []
    for reversal_threshold in THRESHOLD_GRID:
        for continuation_threshold in THRESHOLD_GRID:
            for conflict_margin in MARGIN_GRID:
                thresholds = {
                    "reversal_threshold": reversal_threshold,
                    "continuation_threshold": continuation_threshold,
                    "conflict_margin": conflict_margin,
                }
                decision = apply_thresholds(probabilities, thresholds)
                reversal_mask = decision == "REVERSAL"
                continuation_mask = decision == "CONTINUATION"
                reversal_count = int(reversal_mask.sum())
                continuation_count = int(continuation_mask.sum())
                abstain_coverage = float((decision == "ABSTAIN").mean())
                if reversal_count < 20 or continuation_count < 20:
                    continue
                if not 0.25 <= abstain_coverage <= 0.75:
                    continue
                reversal_precision = float(
                    (target_values[reversal_mask] == "REVERSAL").mean()
                )
                continuation_precision = float(
                    (target_values[continuation_mask] == "CONTINUATION").mean()
                )
                if reversal_precision < 0.40 or continuation_precision < 0.45:
                    continue
                reversal_coverage = reversal_count / len(target_values)
                continuation_coverage = continuation_count / len(target_values)
                harmonic_precision = (
                    2.0
                    * reversal_precision
                    * continuation_precision
                    / (reversal_precision + continuation_precision)
                )
                balance = math.sqrt(
                    min(reversal_coverage, continuation_coverage)
                    / max(reversal_coverage, continuation_coverage)
                )
                score = (
                    harmonic_precision
                    * math.sqrt(reversal_coverage + continuation_coverage)
                    * balance
                )
                candidates.append(
                    (
                        score,
                        reversal_precision,
                        continuation_precision,
                        abstain_coverage,
                        reversal_coverage,
                        continuation_coverage,
                        reversal_threshold,
                        continuation_threshold,
                        conflict_margin,
                    )
                )
    if not candidates:
        return None
    candidates.sort(
        key=lambda row: (
            -row[0],
            -min(row[1], row[2]),
            -(row[4] + row[5]),
            row[8],
            row[6] + row[7],
        )
    )
    selected = candidates[0]
    return {
        "utility": selected[0],
        "train_reversal_precision": selected[1],
        "train_continuation_precision": selected[2],
        "train_abstain_coverage": selected[3],
        "train_reversal_coverage": selected[4],
        "train_continuation_coverage": selected[5],
        "reversal_threshold": selected[6],
        "continuation_threshold": selected[7],
        "conflict_margin": selected[8],
    }


def fit_outer_predictions(
    ledger: pd.DataFrame,
    *,
    landmark: str,
    family: ModelFamily,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    population = ledger.loc[ledger["landmark"].eq(landmark)].reset_index(drop=True)
    grid = ELASTIC_NET_GRID if family == "elastic_net" else HGB_GRID
    prediction_frames: list[pd.DataFrame] = []
    tuning_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    for outer_year in YEARS:
        train = population.loc[population["year"].ne(outer_year)].reset_index(drop=True)
        test = population.loc[population["year"].eq(outer_year)].copy()
        inner = GroupKFold(n_splits=3)
        best: tuple[float, float, tuple[float, float | int], np.ndarray] | None = None
        for config in grid:
            inner_raw = np.zeros((len(train), len(CLASSES)), dtype=float)
            groups = train["week_key"].astype(str)
            for fit_index, validation_index in inner.split(
                train, train["triage_state"], groups
            ):
                model = _make_model(family, config)
                model.fit(
                    train.iloc[fit_index], train.iloc[fit_index]["triage_state"]
                )
                inner_raw[validation_index] = _aligned_probabilities(
                    model, train.iloc[validation_index]
                )
            loss = float(log_loss(train["triage_state"], inner_raw, labels=CLASSES))
            macro_lift = _macro_relative_pr_auc(train["triage_state"], inner_raw)
            candidate = (loss, -macro_lift, config, inner_raw)
            if best is None or candidate[:2] < best[:2]:
                best = candidate
        if best is None:
            raise RuntimeError(f"{landmark}/{family}/{outer_year}: no configuration")
        loss, negative_macro_lift, config, inner_raw = best
        calibrators = _fit_calibrators(train["triage_state"], inner_raw)
        inner_calibrated = _apply_calibrators(calibrators, inner_raw)
        thresholds = select_thresholds(train["triage_state"], inner_calibrated)
        model = _make_model(family, config)
        model.fit(train, train["triage_state"])
        probabilities = _apply_calibrators(
            calibrators, _aligned_probabilities(model, test)
        )
        output_columns = [
            "event_id",
            "instrument",
            "trade_date",
            "week_key",
            "year",
            "side",
            "weekday",
            "landmark",
            "triage_state",
            "reward_risk",
            "reward_risk_stress_010",
            "entry_timestamp_utc",
            "entry_price",
            "stop_price",
            "asian_midpoint",
        ]
        output = test.loc[:, output_columns].copy()
        output[["p_abstain", "p_continuation", "p_reversal"]] = probabilities
        output["decision"] = apply_thresholds(probabilities, thresholds)
        output["outer_year"] = outer_year
        output["family"] = family
        prediction_frames.append(output)
        tuning_rows.append(
            {
                "landmark": landmark,
                "family": family,
                "outer_year": outer_year,
                "config": repr(config),
                "inner_log_loss": loss,
                "inner_macro_relative_pr_auc_lift": -negative_macro_lift,
            }
        )
        threshold_rows.append(
            {
                "landmark": landmark,
                "family": family,
                "outer_year": outer_year,
                **(thresholds or {}),
                "threshold_found": thresholds is not None,
            }
        )
    return (
        pd.concat(prediction_frames, ignore_index=True),
        pd.DataFrame(tuning_rows),
        pd.DataFrame(threshold_rows),
    )


def _class_metrics(
    target: np.ndarray,
    probabilities: np.ndarray,
    state: str,
) -> dict[str, float | bool]:
    index = int(np.where(CLASSES == state)[0][0])
    binary = (target == state).astype(int)
    base_rate = float(binary.mean())
    pr_auc = float(average_precision_score(binary, probabilities[:, index]))
    brier = float(brier_score_loss(binary, probabilities[:, index]))
    constant_brier = base_rate * (1.0 - base_rate)
    return {
        "base_rate": base_rate,
        "pr_auc": pr_auc,
        "relative_pr_auc_lift": pr_auc / base_rate - 1.0,
        "brier": brier,
        "constant_brier": constant_brier,
        "calibration_better": brier < constant_brier,
    }


def summarize_predictions(
    predictions: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    target = predictions["triage_state"].astype(str).to_numpy()
    probabilities = predictions[
        ["p_abstain", "p_continuation", "p_reversal"]
    ].to_numpy(dtype=float)
    decision = predictions["decision"].astype(str).to_numpy()
    summary: dict[str, Any] = {
        "events": int(len(predictions)),
        "abstain_coverage": float((decision == "ABSTAIN").mean()),
        "actionable_coverage": float((decision != "ABSTAIN").mean()),
    }
    class_lifts: list[float] = []
    for state in CLASSES:
        metrics = _class_metrics(target, probabilities, state)
        class_lifts.append(float(metrics["relative_pr_auc_lift"]))
        for key, value in metrics.items():
            summary[f"{state.lower()}_{key}"] = value
    summary["macro_relative_pr_auc_lift"] = float(np.mean(class_lifts))
    for state in ("REVERSAL", "CONTINUATION"):
        mask = decision == state
        summary[f"{state.lower()}_decisions"] = int(mask.sum())
        summary[f"{state.lower()}_coverage"] = float(mask.mean())
        summary[f"{state.lower()}_precision"] = (
            float((target[mask] == state).mean()) if mask.any() else math.nan
        )
        summary[f"{state.lower()}_recall"] = float(
            ((decision == state) & (target == state)).sum() / (target == state).sum()
        )
    tables: dict[str, pd.DataFrame] = {}
    for column in ("instrument", "year", "weekday", "side"):
        rows: list[dict[str, Any]] = []
        for value, group in predictions.groupby(column, sort=True):
            row: dict[str, Any] = {column: value, "events": int(len(group))}
            for state in ("REVERSAL", "CONTINUATION"):
                selected = group.loc[group["decision"].eq(state)]
                row[f"{state.lower()}_decisions"] = int(len(selected))
                row[f"{state.lower()}_precision"] = (
                    float(selected["triage_state"].eq(state).mean())
                    if len(selected)
                    else math.nan
                )
            rows.append(row)
        tables[column] = pd.DataFrame(rows)
    actionable = predictions.loc[predictions["decision"].ne("ABSTAIN")]
    concentration = 1.0
    if len(actionable):
        concentration = max(
            float(actionable[column].value_counts(normalize=True).max())
            for column in ("instrument", "weekday", "decision")
        )
    summary["max_action_concentration"] = concentration
    return summary, tables


def role_passes(
    summary: dict[str, Any],
    pair_table: pd.DataFrame,
    year_table: pd.DataFrame,
    *,
    role: Literal["continuation", "reversal"],
) -> bool:
    minimum_precision = 0.45 if role == "continuation" else 0.40
    return bool(
        summary[f"{role}_precision"] >= minimum_precision
        and summary[f"{role}_coverage"] >= 0.05
        and pair_table[f"{role}_decisions"].gt(0).all()
        and year_table[f"{role}_decisions"].gt(0).sum() >= 4
        and summary[f"{role}_calibration_better"]
        and summary["max_action_concentration"] <= 0.70
    )
