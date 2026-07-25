from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import (
    YEARS,
    CandidateSummary,
    build_population,
    feature_spec,
    validate_development_events,
)
from dtr_lab.strategies.asia_sweep.fingerprint_model_freeze import (
    fit_final_bundle,
    select_final_parameters,
    stable_hgb_fingerprints,
    stable_logistic_fingerprints,
)
from dtr_lab.strategies.asia_sweep.fingerprint_model_metrics import (
    choose_final_candidate,
    evaluate_abstention,
    summarize_candidate,
)
from dtr_lab.strategies.asia_sweep.fingerprint_model_tuning import outer_cross_validate


def run_development_models(events: pd.DataFrame) -> dict[str, Any]:
    validate_development_events(events)
    outputs: dict[str, Any] = {}
    summaries: list[CandidateSummary] = []
    for landmark in ("T0", "T5"):
        population = build_population(events, landmark)
        outputs[f"population_{landmark}"] = population
        for family in ("elastic_net", "hgb"):
            predictions, tuning, fitted, fold_params = outer_cross_validate(
                population, landmark, family
            )
            summary, tables = summarize_candidate(predictions, landmark, family)
            key = f"{landmark}_{family}"
            outputs[f"predictions_{key}"] = tables["predictions"]
            outputs[f"weekly_{key}"] = tables["weekly"]
            outputs[f"pair_top_lift_{key}"] = tables["pair_top_lift"]
            outputs[f"year_top_lift_{key}"] = tables["year_top_lift"]
            outputs[f"side_top_lift_{key}"] = tables["side_top_lift"]
            outputs[f"weekday_top_lift_{key}"] = tables["weekday_top_lift"]
            outputs[f"calibration_{key}"] = tables["calibration"]
            outputs[f"tuning_{key}"] = tuning
            outputs[f"fold_params_{key}"] = fold_params
            if family == "elastic_net":
                stability = stable_logistic_fingerprints(fitted)
            else:
                stability = stable_hgb_fingerprints(fitted)
            outputs[f"stability_{key}"] = stability
            stable_count = int(stability["stable"].sum())
            if stable_count < 5:
                summary = replace(
                    summary,
                    eligible=False,
                    failed_predicates=summary.failed_predicates
                    + ("five_stable_directional_fingerprints",),
                )
            outputs[f"summary_{key}"] = summary
            summaries.append(summary)

    selected = choose_final_candidate(summaries)
    outputs["candidate_summaries"] = summaries
    outputs["selected"] = selected
    if selected is not None:
        selected_key = f"{selected.landmark}_{selected.family}"
        abstention, threshold = evaluate_abstention(outputs[f"predictions_{selected_key}"])
        outputs["abstention"] = abstention
        outputs["abstention_rule"] = threshold
        stability = outputs[f"stability_{selected_key}"]
        outputs["stable_fingerprints"] = stability
        final_parameters = select_final_parameters(
            outputs[f"fold_params_{selected_key}"],
            outputs[f"tuning_{selected_key}"],
            selected.family,
        )
        outputs["final_parameters"] = final_parameters
        outputs["final_bundle"] = fit_final_bundle(
            outputs[f"population_{selected.landmark}"],
            selected.landmark,
            selected.family,
            final_parameters,
            stability,
            threshold,
        )
    return outputs


def write_development_outputs(output_dir: Path, outputs: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows = [asdict(item) for item in outputs["candidate_summaries"]]
    for row in summary_rows:
        row["failed_predicates"] = json.dumps(row["failed_predicates"])
    pd.DataFrame(summary_rows).to_csv(output_dir / "candidate_model_summary.csv", index=False)
    for key, value in outputs.items():
        if isinstance(value, pd.DataFrame) and key.startswith(
            (
                "predictions_",
                "weekly_",
                "pair_top_lift_",
                "year_top_lift_",
                "side_top_lift_",
                "weekday_top_lift_",
                "calibration_",
                "tuning_",
                "stability_",
            )
        ):
            value.to_csv(output_dir / f"{key}.csv", index=False)
    fold_rows = []
    for key, value in outputs.items():
        if key.startswith("fold_params_"):
            for row in value:
                fold_rows.append(
                    {
                        "candidate": key.removeprefix("fold_params_"),
                        "outer_year": row["outer_year"],
                        "landmark": row["landmark"],
                        "family": row["family"],
                        "parameters": json.dumps(row["parameters"], sort_keys=True),
                    }
                )
    pd.DataFrame(fold_rows).to_csv(
        output_dir / "outer_fold_hyperparameters.csv", index=False
    )

    selected: CandidateSummary | None = outputs["selected"]
    if selected is None:
        decision = "FAIL_DEVELOPMENT_STOP_BEFORE_2022_2023"
        selected_payload = None
        stable_payload: list[dict[str, Any]] = []
        abstention_rule = {"status": "NO_ABSTENTION_THRESHOLD"}
    else:
        decision = "PASS_DEVELOPMENT_FREEZE_AUTHORIZE_2022_2023_VALIDATION"
        selected_payload = asdict(selected)
        selected_payload["failed_predicates"] = list(selected_payload["failed_predicates"])
        outputs["abstention"].to_csv(
            output_dir / "abstention_thresholds.csv", index=False
        )
        outputs["stable_fingerprints"].to_csv(
            output_dir / "stable_fingerprints.csv", index=False
        )
        stable_payload = (
            outputs["stable_fingerprints"]
            .loc[outputs["stable_fingerprints"]["stable"]]
            .head(5)
            .to_dict("records")
        )
        abstention_rule = outputs["abstention_rule"]
        joblib.dump(outputs["final_bundle"], output_dir / "frozen_validation_model.joblib")

    feature_manifest = {}
    for landmark in ("T0", "T5"):
        numeric, categorical, interactions = feature_spec(landmark)
        feature_manifest[landmark] = {
            "numeric": list(numeric),
            "categorical": list(categorical),
            "interactions": [list(pair) for pair in interactions],
        }
    (output_dir / "feature_manifest.json").write_text(
        json.dumps(feature_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    decision_payload = {
        "programme": "ASIAN_SWEEP_FINGERPRINT_V1",
        "stage": "GROUPED_DEVELOPMENT_MODEL",
        "development_years": list(YEARS),
        "validation_2022_2023_opened": False,
        "holdout_2024_2025_opened": False,
        "strategy_pnl_calculated": False,
        "decision": decision,
        "selected_model": selected_payload,
        "final_parameters": outputs.get("final_parameters"),
        "abstention_rule": abstention_rule,
        "top_stable_fingerprints": stable_payload,
        "candidate_models": [
            {**asdict(item), "failed_predicates": list(item.failed_predicates)}
            for item in outputs["candidate_summaries"]
        ],
    }
    (output_dir / "development_model_decision.json").write_text(
        json.dumps(decision_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return decision_payload
