from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from dtr_lab.strategies.asia_sweep.early_entry_landmarks import PRE_T5_LANDMARKS

RANDOM_SEED = 20260726
YEARS = tuple(range(2015, 2020))
PAIRS = ("EURUSD", "GBPUSD")
FAMILIES = ("elastic_net", "hgb")

CATEGORICAL_FEATURES = (
    "instrument",
    "side",
    "weekday",
    "week_of_month",
    "sweep_half_hour",
    "asian_compression_bucket",
    "sweep_consumption_class",
)
BASE_NUMERIC_FEATURES = (
    "sweep_minute",
    "sweep_before_0900",
    "asian_range_pips",
    "asian_range_atr20",
    "asian_range_adr20",
    "asian_range_vs_median20",
    "asian_range_percentile20",
    "asian_range_percentile60",
    "asian_range_zscore60",
    "asian_range_under_20_pip_flag",
    "asian_range_20_30_pip_flag",
    "asian_range_over_30_pip_flag",
    "asian_close_location",
    "asian_return_range_fraction",
    "asian_realized_vol_range_fraction",
    "asian_high_formation_minute",
    "asian_low_formation_minute",
    "asian_high_zone_touches",
    "asian_low_zone_touches",
    "asian_direction_changes",
    "asian_first_half_range_fraction",
    "asian_second_half_range_fraction",
    "pre_sweep_return_range_fraction",
    "pre_sweep_reversal_signed_return",
    "pre_sweep_realized_vol_range_fraction",
    "pre_sweep_boundary_tests",
    "pre_sweep_minutes_from_0800",
    "pre_sweep_trailing_15m_range_fraction",
    "sweep_depth_pips",
    "sweep_depth_range_fraction",
    "sweep_body_range_fraction",
    "sweep_wick_range_fraction",
    "sweep_close_beyond_boundary_fraction",
    "sweep_close_location_in_bar",
    "sweep_displacement_vs_trailing_vol",
    "prior_day_return_atr20",
    "same_side_level_count",
    "same_side_source_diversity",
    "nearest_same_side_distance_atr",
    "second_same_side_distance_atr",
    "third_same_side_distance_atr",
    "same_side_levels_within_0_05_atr",
    "same_side_levels_within_0_10_atr",
    "same_side_levels_within_0_20_atr",
    "same_side_levels_within_0_25_range",
    "same_side_source_families_within_0_10_atr",
    "same_side_weighted_density",
    "stack_present",
    "stack_member_count",
    "stack_source_diversity",
    "stack_centroid_distance_atr",
    "stack_span_atr",
    "stack_contains_equal_cluster",
    "levels_consumed_before_sweep",
    "levels_consumed_by_sweep",
    "stack_fraction_consumed_t0",
    "full_stack_exhausted_t0",
    "remaining_levels_beyond_t0",
    "nearest_remaining_distance_atr_t0",
    "residual_density_t0",
    "sweep_stops_inside_stack",
    "opposite_level_count",
    "opposite_source_diversity",
    "nearest_opposite_distance_atr",
    "midpoint_before_nearest_opposite",
)
INCREMENTAL_FEATURES = (
    "landmark_elapsed_minutes",
    "landmark_bar_count",
    "closes_outside",
    "closes_inside",
    "reclaim",
    "reclaim_delay_bars",
    "reclaim_depth_range_fraction",
    "landmark_return_range_fraction",
    "landmark_mfe_range_fraction",
    "landmark_mae_range_fraction",
    "extreme_extension_range_fraction",
    "retest_touch",
    "retest_hold",
    "reversal_swing_break",
    "current_close_from_boundary_range",
    "levels_consumed_through_landmark",
    "remaining_levels_beyond_landmark",
    "residual_density_landmark",
    "other_pair_known",
    "other_pair_same_side",
    "other_pair_reclaim",
    "other_pair_return_range_fraction",
)
NUMERIC_FEATURES = BASE_NUMERIC_FEATURES + INCREMENTAL_FEATURES
LOGISTIC_GRID = tuple(
    (alpha, l1_ratio)
    for alpha in (0.0001, 0.0003, 0.001)
    for l1_ratio in (0.25, 0.50)
)
HGB_GRID = ((0.04, 7), (0.08, 15))


def validate_frontier_ledger(ledger: pd.DataFrame) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "side",
        "weekday",
        "landmark",
        "target",
        "reward_risk",
        "reward_risk_stress_010",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing early-entry frontier columns: {missing}")
    pairs = tuple(sorted(ledger["instrument"].unique()))
    if pairs != PAIRS:
        raise ValueError(f"expected pairs {PAIRS}, found {pairs}")
    years = tuple(sorted(pd.to_numeric(ledger["year"]).astype(int).unique()))
    if years != YEARS:
        raise ValueError(f"expected years {YEARS}, found {years}")
    if ledger.duplicated(["event_id", "landmark"]).any():
        raise ValueError("event-landmark keys must be unique")


def _make_elastic_net(config: tuple[float, float]) -> Pipeline:
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


def _make_model(family: str, config: tuple[float, float | int]) -> Pipeline:
    if family == "elastic_net":
        return _make_elastic_net((float(config[0]), float(config[1])))
    if family == "hgb":
        return _make_hgb((float(config[0]), int(config[1])))
    raise ValueError(f"unsupported early-entry model family: {family}")


def _fit_platt(target: np.ndarray, probabilities: np.ndarray) -> LogisticRegression:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    return LogisticRegression(C=1e4, solver="lbfgs").fit(logits, target)


def _apply_platt(model: LogisticRegression, probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    return model.predict_proba(logits)[:, 1]


def _calibration_coefficients(
    target: np.ndarray,
    probability: np.ndarray,
) -> tuple[float, float]:
    clipped = np.clip(probability, 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    model = LogisticRegression(C=1e4, solver="lbfgs").fit(logits, target)
    return float(model.intercept_[0]), float(model.coef_[0, 0])


def fit_outer_predictions(
    ledger: pd.DataFrame,
    *,
    landmark: str,
    family: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    population = ledger.loc[ledger["landmark"].eq(landmark)].reset_index(drop=True)
    grid = LOGISTIC_GRID if family == "elastic_net" else HGB_GRID
    predictions: list[pd.DataFrame] = []
    tuning_rows: list[dict[str, Any]] = []
    for outer_year in YEARS:
        train = population.loc[population["year"].ne(outer_year)].reset_index(drop=True)
        test = population.loc[population["year"].eq(outer_year)].copy()
        groups = train["week_key"].astype(str)
        inner = GroupKFold(n_splits=3)
        best: tuple[float, float, tuple[float, float | int], np.ndarray] | None = None
        for config in grid:
            inner_probability = np.full(len(train), math.nan, dtype=float)
            for fit_index, validation_index in inner.split(train, train["target"], groups):
                model = _make_model(family, config)
                model.fit(train.iloc[fit_index], train.iloc[fit_index]["target"])
                inner_probability[validation_index] = model.predict_proba(
                    train.iloc[validation_index]
                )[:, 1]
            clipped = np.clip(inner_probability, 1e-6, 1.0 - 1e-6)
            loss = float(log_loss(train["target"], clipped))
            pr_auc = float(average_precision_score(train["target"], clipped))
            candidate = (loss, -pr_auc, config, inner_probability)
            if best is None or candidate[:2] < best[:2]:
                best = candidate
        if best is None:
            raise RuntimeError(f"{landmark}/{family}/{outer_year}: no fitted configuration")
        loss, negative_pr_auc, config, inner_probability = best
        calibrator = _fit_platt(train["target"].to_numpy(), inner_probability)
        model = _make_model(family, config)
        model.fit(train, train["target"])
        probability = _apply_platt(calibrator, model.predict_proba(test)[:, 1])
        output_columns = [
            "event_id",
            "instrument",
            "trade_date",
            "week_key",
            "year",
            "side",
            "weekday",
            "target",
            "reward_risk",
            "reward_risk_stress_010",
            "spread_risk_fraction",
            "entry_price",
            "stop_price",
            "asian_midpoint",
            "entry_timestamp_utc",
        ]
        output = test.loc[:, output_columns].copy()
        output["probability"] = probability
        output["outer_year"] = outer_year
        output["landmark"] = landmark
        output["family"] = family
        predictions.append(output)
        tuning_rows.append(
            {
                "landmark": landmark,
                "family": family,
                "outer_year": outer_year,
                "config": repr(config),
                "inner_log_loss": loss,
                "inner_pr_auc": -negative_pr_auc,
            }
        )
    return pd.concat(predictions, ignore_index=True), pd.DataFrame(tuning_rows)


def _year_block_quintiles(predictions: pd.DataFrame) -> pd.DataFrame:
    result = predictions.copy()
    result["quintile"] = result.groupby("year")["probability"].transform(
        lambda values: pd.qcut(values.rank(method="first"), 5, labels=False) + 1
    )
    return result


def _breadth_table(predictions: pd.DataFrame, column: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for value, group in predictions.groupby(column, sort=True):
        rows.append(
            {
                column: value,
                "events": int(len(group)),
                "base_rate": float(group["target"].mean()),
                "top_quintile_rate": float(
                    group.loc[group["quintile"].eq(5), "target"].mean()
                ),
            }
        )
    table = pd.DataFrame(rows)
    table["positive_top_lift"] = table["top_quintile_rate"] > table["base_rate"]
    return table


def summarize_predictions(
    predictions: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    scored = _year_block_quintiles(predictions)
    target = scored["target"].to_numpy(dtype=int)
    probability = scored["probability"].to_numpy(dtype=float)
    base_rate = float(target.mean())
    top = scored.loc[scored["quintile"].eq(5)].copy()
    bottom = scored.loc[scored["quintile"].eq(1)].copy()
    pair_table = _breadth_table(scored, "instrument")
    year_table = _breadth_table(scored, "year")
    side_table = _breadth_table(scored, "side")
    weekday_table = _breadth_table(scored, "weekday")
    calibration_intercept, calibration_slope = _calibration_coefficients(
        target, probability
    )
    expected_value = (
        top["probability"] * top["reward_risk_stress_010"]
        - (1.0 - top["probability"])
    )
    weekly_rows: list[dict[str, Any]] = []
    for week_key, group in scored.groupby("week_key", sort=True):
        selected = group.sort_values(
            ["probability", "event_id"], ascending=[False, True], kind="mergesort"
        ).iloc[0]
        weekly_rows.append(
            {
                "week_key": week_key,
                "selected_event_id": selected["event_id"],
                "selected_target": int(selected["target"]),
                "candidate_count": int(len(group)),
                "candidate_base_rate": float(group["target"].mean()),
            }
        )
    weekly = pd.DataFrame(weekly_rows)
    hit_at_1 = float(weekly["selected_target"].mean())
    naive_hit_at_1 = float(
        np.average(weekly["candidate_base_rate"], weights=weekly["candidate_count"])
    )
    concentration = max(
        float(top["instrument"].value_counts(normalize=True).max()),
        float(top["weekday"].value_counts(normalize=True).max()),
        float(top["side"].value_counts(normalize=True).max()),
    )
    pr_auc = float(average_precision_score(target, probability))
    summary = {
        "events": int(len(scored)),
        "base_rate": base_rate,
        "pr_auc": pr_auc,
        "pr_auc_relative_lift": pr_auc / base_rate - 1.0,
        "roc_auc": float(roc_auc_score(target, probability)),
        "brier": float(brier_score_loss(target, probability)),
        "constant_brier": base_rate * (1.0 - base_rate),
        "calibration_intercept": calibration_intercept,
        "calibration_slope": calibration_slope,
        "top_quintile_rate": float(top["target"].mean()),
        "top_quintile_lift": float(top["target"].mean() / base_rate),
        "bottom_quintile_rate": float(bottom["target"].mean()),
        "bottom_quintile_ratio": float(bottom["target"].mean() / base_rate),
        "median_reward_risk": float(scored["reward_risk"].median()),
        "median_top_quintile_reward_risk": float(top["reward_risk"].median()),
        "top_quintile_rr_at_least_1_0": float(top["reward_risk"].ge(1.0).mean()),
        "top_quintile_rr_at_least_1_5": float(top["reward_risk"].ge(1.5).mean()),
        "top_quintile_rr_at_least_2_0": float(top["reward_risk"].ge(2.0).mean()),
        "median_top_quintile_ev_stress_010": float(expected_value.median()),
        "median_spread_risk_fraction": float(scored["spread_risk_fraction"].median()),
        "pair_positive_top_lift_count": int(pair_table["positive_top_lift"].sum()),
        "year_positive_top_lift_count": int(year_table["positive_top_lift"].sum()),
        "hit_at_1": hit_at_1,
        "naive_hit_at_1": naive_hit_at_1,
        "hit_at_1_relative_lift": hit_at_1 / naive_hit_at_1 - 1.0,
        "max_top_success_concentration": concentration,
    }
    gates = {
        "events": summary["events"] >= 400,
        "events_per_pair": all(
            len(group) >= 150 for _, group in scored.groupby("instrument")
        ),
        "pr_auc_lift": summary["pr_auc_relative_lift"] >= 0.50,
        "top_quintile_lift": summary["top_quintile_lift"] >= 1.75,
        "bottom_quintile": summary["bottom_quintile_ratio"] < 0.60,
        "brier": summary["brier"] < summary["constant_brier"],
        "pair_breadth": summary["pair_positive_top_lift_count"] == 2,
        "year_breadth": summary["year_positive_top_lift_count"] >= 4,
        "top_quintile_rr": summary["median_top_quintile_reward_risk"] >= 1.00,
        "top_quintile_rr_1_5": summary["top_quintile_rr_at_least_1_5"] >= 0.35,
        "expected_value_proxy": summary["median_top_quintile_ev_stress_010"] > 0.0,
        "concentration": summary["max_top_success_concentration"] <= 0.70,
    }
    summary["gates"] = gates
    summary["passes"] = bool(all(gates.values()))
    return summary, {
        "predictions": scored,
        "pair": pair_table,
        "year": year_table,
        "side": side_table,
        "weekday": weekday_table,
        "weekly": weekly,
    }


def _legacy_predictions(
    ledger: pd.DataFrame,
    frozen_predictions: pd.DataFrame,
) -> pd.DataFrame:
    geometry = ledger.loc[
        ledger["landmark"].eq("LEGACY_T5"),
        [
            "event_id",
            "reward_risk",
            "reward_risk_stress_010",
            "spread_risk_fraction",
            "entry_price",
            "stop_price",
            "asian_midpoint",
            "entry_timestamp_utc",
        ],
    ]
    frozen = frozen_predictions.copy()
    frozen = frozen.loc[
        frozen["year"].between(YEARS[0], YEARS[-1])
        & frozen["landmark"].eq("T5")
        & frozen["family"].eq("hgb")
    ].rename(columns={"prediction": "probability"})
    merged = frozen.merge(geometry, on="event_id", how="inner", validate="one_to_one")
    merged["landmark"] = "LEGACY_T5"
    merged["family"] = "frozen_hgb"
    return merged


def select_landmark(candidate_summary: pd.DataFrame) -> dict[str, Any]:
    passing = candidate_summary.loc[candidate_summary["passes"].astype(bool)].copy()
    if passing.empty:
        return {
            "selected_landmark": None,
            "selected_family": None,
            "decision": "FAIL_EARLY_ENTRY_INFORMATION_FRONTIER_STOP_BEFORE_POLICY_PNL",
        }
    order = {landmark: index for index, landmark in enumerate(PRE_T5_LANDMARKS)}
    passing["landmark_order"] = passing["landmark"].map(order)
    passing["family_order"] = passing["family"].map({"elastic_net": 0, "hgb": 1})
    passing = passing.sort_values(
        ["landmark_order", "family_order"], kind="mergesort"
    ).reset_index(drop=True)
    selected = passing.iloc[0]
    for _, challenger in passing.iloc[1:].iterrows():
        if challenger["landmark_order"] <= selected["landmark_order"]:
            continue
        pr_improvement = (
            challenger["pr_auc_relative_lift"]
            - selected["pr_auc_relative_lift"]
        )
        rr_decline = (
            selected["median_top_quintile_reward_risk"]
            - challenger["median_top_quintile_reward_risk"]
        )
        if pr_improvement >= 0.20 and rr_decline <= 0.20:
            selected = challenger
    return {
        "selected_landmark": str(selected["landmark"]),
        "selected_family": str(selected["family"]),
        "decision": "PASS_EARLY_ENTRY_FRONTIER_AUTHORIZE_POLICY_AMENDMENT",
    }


def run_information_frontier(
    ledger: pd.DataFrame,
    frozen_t5_predictions: pd.DataFrame,
    output_directory: Path,
) -> dict[str, Any]:
    validate_frontier_ledger(ledger)
    output_directory.mkdir(parents=True, exist_ok=True)
    candidate_rows: list[dict[str, Any]] = []
    tuning_frames: list[pd.DataFrame] = []
    for landmark in PRE_T5_LANDMARKS:
        for family in FAMILIES:
            predictions, tuning = fit_outer_predictions(
                ledger,
                landmark=landmark,
                family=family,
            )
            summary, tables = summarize_predictions(predictions)
            summary.update({"landmark": landmark, "family": family})
            candidate_rows.append(summary)
            tuning_frames.append(tuning)
            prefix = f"{landmark}_{family}"
            for name, table in tables.items():
                table.to_csv(output_directory / f"{name}_{prefix}.csv", index=False)
    legacy = _legacy_predictions(ledger, frozen_t5_predictions)
    legacy_summary, legacy_tables = summarize_predictions(legacy)
    legacy_summary.update({"landmark": "LEGACY_T5", "family": "frozen_hgb"})
    candidate_rows.append(legacy_summary)
    for name, table in legacy_tables.items():
        table.to_csv(output_directory / f"{name}_LEGACY_T5_frozen_hgb.csv", index=False)

    serializable_rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        flattened = {key: value for key, value in row.items() if key != "gates"}
        flattened["failed_predicates"] = ";".join(
            key for key, passed in row["gates"].items() if not passed
        )
        serializable_rows.append(flattened)
    candidate_summary = pd.DataFrame(serializable_rows)
    candidate_summary.to_csv(output_directory / "candidate_summary.csv", index=False)
    pd.concat(tuning_frames, ignore_index=True).to_csv(
        output_directory / "outer_fold_tuning.csv", index=False
    )
    selection = select_landmark(
        candidate_summary.loc[candidate_summary["landmark"].isin(PRE_T5_LANDMARKS)]
    )
    decision = {
        "programme": "ASIAN_SWEEP_EARLY_ENTRY_INFORMATION_FRONTIER_V5",
        **selection,
        "development_years": list(YEARS),
        "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "position_structures_reserved_for_phase_2": [
            "TP1_50_RUNNER_50",
            "TP1_25_RUNNER_75",
            "NO_TP1_FULL_RUNNER",
        ],
        "policy_pnl_opened": False,
        "candidate_count": int(len(candidate_summary)),
    }
    (output_directory / "early_entry_frontier_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return decision
