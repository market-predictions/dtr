from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import (
    PAIRS,
    build_population,
    transform_preprocessor,
)
from dtr_lab.strategies.asia_sweep.fingerprint_model_metrics import (
    calibration_intercept_slope,
    weekly_ranking,
)
from dtr_lab.strategies.asia_sweep.fingerprint_validation_contract import (
    EXPECTED_ABSTENTION_THRESHOLD,
    EXPECTED_ANATOMY_RUN,
    EXPECTED_DEVELOPMENT_RUN,
    EXPECTED_FAMILY,
    EXPECTED_LANDMARK,
    EXPECTED_PARAMETERS,
    FAIL_DECISION,
    PASS_DECISION,
    VALIDATION_YEARS,
    _add_year_quintiles,
    _fingerprint_direction_table,
    _relative_lift,
    _subgroup_lift,
    validate_validation_events,
)


def evaluate_validation(
    events: pd.DataFrame,
    bundle: dict[str, Any],
) -> dict[str, Any]:
    validate_validation_events(events)
    population = build_population(events, EXPECTED_LANDMARK)
    years = tuple(sorted(population["year"].unique()))
    pairs = tuple(sorted(population["instrument"].unique()))
    if years != VALIDATION_YEARS or pairs != PAIRS:
        raise ValueError("T5 landmark population lost a required pair or year")
    transformed = transform_preprocessor(population, bundle["preprocessor"])
    prediction = bundle["classifier"].predict_proba(transformed)[:, 1]
    if not np.isfinite(prediction).all() or ((prediction < 0) | (prediction > 1)).any():
        raise ValueError("invalid frozen probabilities")
    ledger = population[
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
    ledger["prediction"] = prediction
    ledger = _add_year_quintiles(ledger)

    y = ledger["target"].to_numpy(dtype=int)
    p = ledger["prediction"].to_numpy(dtype=float)
    base = float(y.mean())
    pr_auc = float(average_precision_score(y, p))
    roc_auc = float(roc_auc_score(y, p))
    brier = float(brier_score_loss(y, p))
    prevalence_brier = float(brier_score_loss(y, np.full(len(y), base)))
    development_rate = float(bundle["development_base_rate"])
    development_brier = float(
        brier_score_loss(y, np.full(len(y), development_rate))
    )
    calibration_intercept, calibration_slope = calibration_intercept_slope(y, p)
    top_rate = float(ledger.loc[ledger["quintile"] == 5, "target"].mean())
    bottom_rate = float(ledger.loc[ledger["quintile"] == 1, "target"].mean())

    weekly = weekly_ranking(ledger)
    hit_at_1 = float(weekly["selected_success"].mean())
    naive_hit = float(weekly["naive_random_success_probability"].mean())
    abstained = weekly.loc[
        weekly["selected_prediction"] >= EXPECTED_ABSTENTION_THRESHOLD
    ].copy()
    abstention = {
        "frozen_threshold": EXPECTED_ABSTENTION_THRESHOLD,
        "selected_pair_weeks": int(len(abstained)),
        "total_pair_weeks": int(len(weekly)),
        "coverage": float(len(abstained) / len(weekly)) if len(weekly) else 0.0,
        "selected_success_rate": (
            float(abstained["selected_success"].mean())
            if len(abstained)
            else float("nan")
        ),
    }

    pair_table = _subgroup_lift(ledger, "instrument")
    year_table = _subgroup_lift(ledger, "year")
    side_table = _subgroup_lift(ledger, "side")
    weekday_table = _subgroup_lift(ledger, "weekday")
    fingerprints = _fingerprint_direction_table(population, transformed, bundle)

    ledger["decile"] = 0
    for _, indices in ledger.groupby("year").groups.items():
        frame = ledger.loc[list(indices)].sort_values(["prediction", "event_id"])
        ranks = frame["prediction"].rank(method="first", pct=True)
        ledger.loc[frame.index, "decile"] = (
            np.ceil(ranks * 10).clip(1, 10).astype(int).to_numpy()
        )
    calibration = (
        ledger.groupby("decile", as_index=False)
        .agg(
            event_count=("target", "size"),
            mean_prediction=("prediction", "mean"),
            observed_success_rate=("target", "mean"),
        )
        .sort_values("decile")
    )

    candidate_count = int(len(ledger))
    success_count = int(ledger["target"].sum())
    pair_counts = ledger.groupby("instrument").size()
    year_counts = ledger.groupby("year").size()
    predicates = {
        "sample_at_least_100_and_30_successes": candidate_count >= 100
        and success_count >= 30,
        "both_pairs_at_least_30_candidates": bool((pair_counts >= 30).all()),
        "both_years_at_least_30_candidates": bool((year_counts >= 30).all()),
        "pr_auc_relative_lift_at_least_25pct": _relative_lift(pr_auc, base) >= 0.25,
        "top_quintile_at_least_1_75x_base": top_rate >= 1.75 * base,
        "bottom_quintile_below_base": bottom_rate < base,
        "hit_at_1_relative_lift_at_least_25pct": _relative_lift(hit_at_1, naive_hit)
        >= 0.25,
        "brier_improves_prevalence_baseline": brier < prevalence_brier,
        "calibration_slope_between_0_5_and_1_5": 0.5 <= calibration_slope <= 1.5,
        "both_pairs_positive_top_lift": bool(pair_table["positive_top_lift"].all()),
        "both_years_positive_top_lift": bool(year_table["positive_top_lift"].all()),
        "all_five_fingerprint_directions_preserved": bool(
            fingerprints["observed_direction_preserved"].all()
        ),
    }
    decision = PASS_DECISION if all(predicates.values()) else FAIL_DECISION
    metrics = {
        "candidate_count": candidate_count,
        "success_count": success_count,
        "base_rate": base,
        "pr_auc": pr_auc,
        "pr_auc_relative_lift": _relative_lift(pr_auc, base),
        "roc_auc": roc_auc,
        "brier": brier,
        "prevalence_baseline_brier": prevalence_brier,
        "development_rate_baseline_brier": development_brier,
        "calibration_intercept": calibration_intercept,
        "calibration_slope": calibration_slope,
        "top_quintile_rate": top_rate,
        "top_quintile_lift": _relative_lift(top_rate, base),
        "bottom_quintile_rate": bottom_rate,
        "hit_at_1": hit_at_1,
        "naive_hit_at_1": naive_hit,
        "hit_at_1_relative_lift": _relative_lift(hit_at_1, naive_hit),
    }
    return {
        "decision": decision,
        "metrics": metrics,
        "predicates": predicates,
        "ledger": ledger,
        "weekly": weekly,
        "abstention": abstention,
        "pair_table": pair_table,
        "year_table": year_table,
        "side_table": side_table,
        "weekday_table": weekday_table,
        "fingerprints": fingerprints,
        "calibration": calibration,
    }


def write_validation_outputs(output_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result["ledger"].to_csv(output_dir / "validation_predictions.csv", index=False)
    result["weekly"].to_csv(output_dir / "validation_weekly_ranking.csv", index=False)
    result["pair_table"].to_csv(output_dir / "validation_pair_lift.csv", index=False)
    result["year_table"].to_csv(output_dir / "validation_year_lift.csv", index=False)
    result["side_table"].to_csv(output_dir / "validation_side_lift.csv", index=False)
    result["weekday_table"].to_csv(
        output_dir / "validation_weekday_lift.csv", index=False
    )
    result["fingerprints"].to_csv(
        output_dir / "validation_fingerprint_directions.csv", index=False
    )
    result["calibration"].to_csv(
        output_dir / "validation_calibration.csv", index=False
    )
    payload = {
        "programme": "ASIAN_SWEEP_FINGERPRINT_V1",
        "stage": "UNTOUCHED_2022_2023_VALIDATION",
        "development_model_run_id": EXPECTED_DEVELOPMENT_RUN,
        "development_anatomy_run_id": EXPECTED_ANATOMY_RUN,
        "validation_years": list(VALIDATION_YEARS),
        "selected_landmark": EXPECTED_LANDMARK,
        "selected_family": EXPECTED_FAMILY,
        "selected_parameters": EXPECTED_PARAMETERS,
        "frozen_abstention": result["abstention"],
        "metrics": result["metrics"],
        "predicates": result["predicates"],
        "fingerprint_directions": result["fingerprints"].to_dict("records"),
        "pair_results": result["pair_table"].to_dict("records"),
        "year_results": result["year_table"].to_dict("records"),
        "decision": result["decision"],
        "holdout_2024_2025_opened": False,
        "strategy_pnl_calculated": False,
    }
    (output_dir / "validation_decision.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload
