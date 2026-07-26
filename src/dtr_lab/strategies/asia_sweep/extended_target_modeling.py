from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.utils.class_weight import compute_sample_weight

from dtr_lab.strategies.asia_sweep.early_entry_modeling import (
    HGB_GRID,
    LOGISTIC_GRID,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    _apply_platt,
    _fit_platt,
    _make_model,
)
from dtr_lab.strategies.asia_sweep.extended_targets import LANDMARKS, TARGETS

DEVELOPMENT_YEARS = tuple(range(2015, 2020))
FAMILIES = ("elastic_net", "hgb")
TARGET_REWARD = {
    "EXTENDED_1_5R_1300": 1.5,
    "EXTENDED_2R_1300": 2.0,
    "EXTENDED_3R_1600": 3.0,
    "LATE_TREND_HOLD_1600": 2.0,
}


def validate_extended_ledger(ledger: pd.DataFrame) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "side",
        "weekday",
        "landmark",
        "entry_slippage_r",
        *TARGETS,
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing extended-model columns: {missing}")
    if ledger.duplicated(["event_id", "landmark"]).any():
        raise ValueError("duplicate extended-target keys")


def _candidate_population(
    ledger: pd.DataFrame,
    *,
    landmark: str,
    target: str,
) -> pd.DataFrame:
    if landmark not in LANDMARKS or target not in TARGETS:
        raise ValueError(f"unsupported candidate: {landmark}/{target}")
    frame = ledger.loc[
        ledger["landmark"].eq(landmark) & ledger[target].notna()
    ].copy()
    frame["model_target"] = frame[target].astype(int)
    reward_column = f"{target}_reward_risk"
    if reward_column not in frame:
        if target not in TARGET_REWARD:
            raise ValueError(f"missing reward column for {target}")
        frame["target_reward_risk"] = TARGET_REWARD[target]
    else:
        frame["target_reward_risk"] = pd.to_numeric(
            frame[reward_column], errors="coerce"
        )
    frame = frame.loc[
        frame["target_reward_risk"].gt(0)
        & frame["year"].between(DEVELOPMENT_YEARS[0], DEVELOPMENT_YEARS[-1])
    ].copy()
    return frame.sort_values(["year", "event_id"], kind="mergesort").reset_index(drop=True)


def _fit_outer_predictions(
    population: pd.DataFrame,
    *,
    family: str,
    landmark: str,
    target: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid = LOGISTIC_GRID if family == "elastic_net" else HGB_GRID
    prediction_frames: list[pd.DataFrame] = []
    tuning_rows: list[dict[str, Any]] = []
    for outer_year in DEVELOPMENT_YEARS:
        train = population.loc[population["year"].ne(outer_year)].reset_index(drop=True)
        test = population.loc[population["year"].eq(outer_year)].reset_index(drop=True)
        groups = train["week_key"].astype(str)
        inner = GroupKFold(n_splits=3)
        best: tuple[float, float, tuple[float, float | int], np.ndarray] | None = None
        for config in grid:
            inner_probability = np.full(len(train), math.nan, dtype=float)
            for fit_index, validation_index in inner.split(
                train, train["model_target"], groups
            ):
                fit = train.iloc[fit_index]
                validation = train.iloc[validation_index]
                model = _make_model(family, config)
                weights = compute_sample_weight("balanced", fit["model_target"])
                model.fit(
                    fit,
                    fit["model_target"],
                    model__sample_weight=weights,
                )
                inner_probability[validation_index] = model.predict_proba(
                    validation
                )[:, 1]
            clipped = np.clip(inner_probability, 1e-6, 1.0 - 1e-6)
            loss = float(log_loss(train["model_target"], clipped))
            pr_auc = float(
                average_precision_score(train["model_target"], clipped)
            )
            candidate = (loss, -pr_auc, config, inner_probability)
            if best is None or candidate[:2] < best[:2]:
                best = candidate
        if best is None:
            raise RuntimeError(f"{landmark}/{target}/{family}: no fitted model")
        loss, negative_pr_auc, config, inner_probability = best
        calibrator = _fit_platt(
            train["model_target"].to_numpy(), inner_probability
        )
        model = _make_model(family, config)
        weights = compute_sample_weight("balanced", train["model_target"])
        model.fit(train, train["model_target"], model__sample_weight=weights)
        probability = _apply_platt(
            calibrator, model.predict_proba(test)[:, 1]
        )
        output = test[
            [
                "event_id",
                "instrument",
                "trade_date",
                "week_key",
                "year",
                "side",
                "weekday",
                "model_target",
                "target_reward_risk",
                "entry_slippage_r",
            ]
        ].copy()
        output["probability"] = probability
        output["outer_year"] = outer_year
        output["landmark"] = landmark
        output["target_name"] = target
        output["family"] = family
        prediction_frames.append(output)
        tuning_rows.append(
            {
                "landmark": landmark,
                "target_name": target,
                "family": family,
                "outer_year": outer_year,
                "config": repr(config),
                "inner_log_loss": loss,
                "inner_pr_auc": -negative_pr_auc,
            }
        )
    return pd.concat(prediction_frames, ignore_index=True), pd.DataFrame(tuning_rows)


def _year_quintiles(predictions: pd.DataFrame) -> pd.DataFrame:
    frame = predictions.copy()
    frame["quintile"] = frame.groupby("year")["probability"].transform(
        lambda values: pd.qcut(
            values.rank(method="first"), 5, labels=False
        )
        + 1
    )
    return frame


def summarize_extended_predictions(predictions: pd.DataFrame) -> dict[str, Any]:
    frame = _year_quintiles(predictions)
    target = frame["model_target"].to_numpy(dtype=int)
    probability = frame["probability"].to_numpy(dtype=float)
    base_rate = float(target.mean())
    top = frame.loc[frame["quintile"].eq(5)].copy()
    bottom = frame.loc[frame["quintile"].eq(1)].copy()
    target_name = str(frame.iloc[0]["target_name"])
    reward = top["target_reward_risk"].astype(float)
    slippage = top["entry_slippage_r"].astype(float)
    if target_name == "LATE_TREND_HOLD_1600":
        stressed_reward = reward - 2.0 * slippage
    else:
        stressed_reward = reward - slippage
    stressed_loss = 1.0 + 2.0 * slippage
    expected_value = (
        top["probability"] * stressed_reward
        - (1.0 - top["probability"]) * stressed_loss
    )
    pair_rows: list[dict[str, Any]] = []
    for instrument, group in frame.groupby("instrument", sort=True):
        pair_top = group.loc[group["quintile"].eq(5)]
        pair_rows.append(
            {
                "instrument": instrument,
                "events": int(len(group)),
                "positives": int(group["model_target"].sum()),
                "base_rate": float(group["model_target"].mean()),
                "top_rate": float(pair_top["model_target"].mean()),
            }
        )
    pair = pd.DataFrame(pair_rows)
    pair["positive_lift"] = pair["top_rate"] > pair["base_rate"]
    year_rows: list[dict[str, Any]] = []
    for year, group in frame.groupby("year", sort=True):
        year_top = group.loc[group["quintile"].eq(5)]
        year_rows.append(
            {
                "year": int(year),
                "events": int(len(group)),
                "base_rate": float(group["model_target"].mean()),
                "top_rate": float(year_top["model_target"].mean()),
            }
        )
    year_table = pd.DataFrame(year_rows)
    year_table["positive_lift"] = year_table["top_rate"] > year_table["base_rate"]
    summary = {
        "events": int(len(frame)),
        "positives": int(frame["model_target"].sum()),
        "minimum_pair_positives": int(pair["positives"].min()),
        "base_rate": base_rate,
        "pr_auc": float(average_precision_score(target, probability)),
        "pr_auc_relative_lift": float(
            average_precision_score(target, probability) / base_rate - 1.0
        ),
        "roc_auc": float(roc_auc_score(target, probability)),
        "brier": float(brier_score_loss(target, probability)),
        "constant_brier": base_rate * (1.0 - base_rate),
        "top_quintile_rate": float(top["model_target"].mean()),
        "top_quintile_lift": float(top["model_target"].mean() / base_rate),
        "bottom_quintile_rate": float(bottom["model_target"].mean()),
        "bottom_base_ratio": float(bottom["model_target"].mean() / base_rate),
        "pair_positive_lift_count": int(pair["positive_lift"].sum()),
        "year_positive_lift_count": int(year_table["positive_lift"].sum()),
        "median_top_stressed_ev": float(expected_value.median()),
        "median_top_reward_risk": float(reward.median()),
    }
    gates = {
        "positives": summary["positives"] >= 150,
        "pair_positives": summary["minimum_pair_positives"] >= 50,
        "pr_auc_lift": summary["pr_auc_relative_lift"] >= 0.50,
        "top_lift": summary["top_quintile_lift"] >= 1.75,
        "bottom": summary["bottom_base_ratio"] < 0.60,
        "pair_breadth": summary["pair_positive_lift_count"] == 2,
        "year_breadth": summary["year_positive_lift_count"] >= 4,
        "brier": summary["brier"] < summary["constant_brier"],
        "expected_value": summary["median_top_stressed_ev"] > 0.0,
    }
    summary["gates"] = gates
    summary["passes"] = bool(all(gates.values()))
    return summary


def fit_extended_candidate(
    ledger: pd.DataFrame,
    *,
    landmark: str,
    target: str,
    family: str,
    output_directory: Path,
) -> dict[str, Any]:
    validate_extended_ledger(ledger)
    if family not in FAMILIES:
        raise ValueError(family)
    population = _candidate_population(ledger, landmark=landmark, target=target)
    predictions, tuning = _fit_outer_predictions(
        population,
        family=family,
        landmark=landmark,
        target=target,
    )
    summary = summarize_extended_predictions(predictions)
    summary.update(
        {"landmark": landmark, "target_name": target, "family": family}
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    stem = f"{landmark}_{target}_{family}"
    predictions.to_csv(
        output_directory / f"extended_predictions_{stem}.csv", index=False
    )
    tuning.to_csv(
        output_directory / f"extended_tuning_{stem}.csv", index=False
    )
    serializable = {
        key: value for key, value in summary.items() if key != "gates"
    }
    serializable["failed_gates"] = ";".join(
        key for key, passed in summary["gates"].items() if not passed
    )
    (output_directory / f"extended_summary_{stem}.json").write_text(
        json.dumps(serializable, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return serializable


def aggregate_extended_summaries(
    input_directory: Path,
    output_directory: Path,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in sorted(input_directory.rglob("extended_summary_*.json")):
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    if len(rows) != len(LANDMARKS) * len(TARGETS) * len(FAMILIES):
        raise ValueError(f"expected 20 extended summaries, found {len(rows)}")
    table = pd.DataFrame(rows)
    output_directory.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_directory / "extended_candidate_summary.csv", index=False)
    passing = table.loc[table["passes"].astype(bool)].copy()
    if passing.empty:
        decision = {
            "decision": "FAIL_EXTENDED_TARGET_DISCOVERY_STOP_BEFORE_TP1_PNL",
            "selected_landmark": None,
            "selected_target": None,
            "selected_family": None,
        }
    else:
        target_order = {
            "EXTENDED_3R_1600": 3.0,
            "EXTENDED_2R_1300": 2.0,
            "LATE_TREND_HOLD_1600": 2.0,
            "EXTENDED_1_5R_1300": 1.5,
            "OPPOSITE_ASIAN_BOUNDARY_1300": 0.0,
        }
        passing["target_order"] = passing["target_name"].map(target_order)
        passing["landmark_order"] = passing["landmark"].map({"T0": 0, "T1": 1})
        passing["family_order"] = passing["family"].map(
            {"hgb": 0, "elastic_net": 1}
        )
        selected = passing.sort_values(
            [
                "median_top_stressed_ev",
                "target_order",
                "landmark_order",
                "family_order",
            ],
            ascending=[False, False, True, True],
            kind="mergesort",
        ).iloc[0]
        decision = {
            "decision": "PASS_EXTENDED_TARGET_DISCOVERY_FREEZE_TARGET",
            "selected_landmark": str(selected["landmark"]),
            "selected_target": str(selected["target_name"]),
            "selected_family": str(selected["family"]),
        }
    decision.update(
        {
            "programme": "ASIAN_SWEEP_EXTENDED_TARGET_DISCOVERY_V6_3",
            "development_years": list(DEVELOPMENT_YEARS),
            "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
            "candidate_count": int(len(table)),
            "tp1_policy_pnl_opened": False,
        }
    )
    (output_directory / "extended_target_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return decision
