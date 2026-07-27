from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .cluster_stats import cluster_permutation_p_value
from .data import REPLICATION_PAIRS

BOOTSTRAP_SAMPLES = 2000
PERMUTATION_SAMPLES = 5000
RANDOM_SEED = 20260727
PRIMARY_RULE = "CLOSE_IN_ZONE"
TREATMENT_COLUMN = "sequence_active_sensitivity"
AVAILABLE_COLUMN = "sensitivity_target_available"
OUTCOME_COLUMN = "sensitivity_reached_by_month_end"
ORIGINAL_CONSERVATIVE_EFFECT = 0.3569


def as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    values = series.astype(str).str.strip().str.lower()
    invalid = ~values.isin({"true", "false", "1", "0"})
    if invalid.any():
        raise ValueError(f"invalid boolean values: {sorted(values.loc[invalid].unique())}")
    return values.isin({"true", "1"})


def normalize_replication_ledger(ledger: pd.DataFrame) -> pd.DataFrame:
    required = {
        "instrument",
        "opportunity_id",
        "month_id",
        "year",
        "side",
        "location_rule",
        "target_tier",
        TREATMENT_COLUMN,
        AVAILABLE_COLUMN,
        OUTCOME_COLUMN,
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"replication ledger missing columns: {missing}")
    symbols = tuple(sorted(str(value) for value in ledger["instrument"].unique()))
    if symbols != REPLICATION_PAIRS:
        raise ValueError(f"expected replication pairs {REPLICATION_PAIRS}, found {symbols}")

    work = ledger.copy()
    boolean_columns = [
        column
        for column in work.columns
        if column.startswith(
            (
                "sequence_",
                "preexisting_",
                "dual_zone_",
                "health_same_",
                "health_strictly_",
            )
        )
        or column.endswith(
            (
                "_target_pre_start",
                "_target_same_bar",
                "_target_available",
                "_target_invalidation_same_bar",
                "_reached_by_month_end",
                "_reached_before_invalidation",
            )
        )
    ]
    for column in boolean_columns:
        work[column] = as_bool(work[column])
    if work.duplicated(["instrument", "opportunity_id", "target_tier"]).any():
        duplicates = work.loc[
            work.duplicated(
                ["instrument", "opportunity_id", "target_tier"],
                keep=False,
            ),
            ["instrument", "opportunity_id", "target_tier"],
        ]
        raise ValueError(f"duplicate replication rows: {duplicates.head().to_dict('records')}")
    return work


def _effect(
    data: pd.DataFrame,
    treatment_column: str,
    outcome_column: str,
) -> float:
    treatment = data[treatment_column].astype(bool)
    if treatment.sum() == 0 or (~treatment).sum() == 0:
        return math.nan
    return float(
        data.loc[treatment, outcome_column].mean()
        - data.loc[~treatment, outcome_column].mean()
    )


def _cluster_bootstrap(
    data: pd.DataFrame,
    *,
    treatment_column: str,
    outcome_column: str,
    seed: int,
) -> tuple[float, float]:
    work = data.copy()
    work["cluster"] = (
        work["instrument"].astype(str) + "::" + work["month_id"].astype(str)
    )
    treatment = work[treatment_column].astype(bool)
    work["t_y"] = np.where(treatment, work[outcome_column].astype(float), 0.0)
    work["t_n"] = treatment.astype(int)
    work["c_y"] = np.where(~treatment, work[outcome_column].astype(float), 0.0)
    work["c_n"] = (~treatment).astype(int)
    values = (
        work.groupby("cluster", sort=False)[["t_y", "t_n", "c_y", "c_n"]]
        .sum()
        .to_numpy(dtype=float)
    )
    if len(values) == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    effects: list[float] = []
    for _ in range(BOOTSTRAP_SAMPLES):
        totals = values[rng.integers(0, len(values), size=len(values))].sum(axis=0)
        if totals[1] and totals[3]:
            effects.append(totals[0] / totals[1] - totals[2] / totals[3])
    if not effects:
        return math.nan, math.nan
    return float(np.quantile(effects, 0.05)), float(np.quantile(effects, 0.95))


def _breadth(
    data: pd.DataFrame,
    *,
    group_column: str,
) -> tuple[int, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    for key, group in data.groupby(group_column, sort=True):
        treatment = group[TREATMENT_COLUMN].astype(bool)
        treatment_n = int(treatment.sum())
        control_n = int((~treatment).sum())
        treatment_rate = (
            float(group.loc[treatment, OUTCOME_COLUMN].mean())
            if treatment_n
            else math.nan
        )
        control_rate = (
            float(group.loc[~treatment, OUTCOME_COLUMN].mean())
            if control_n
            else math.nan
        )
        effect = (
            treatment_rate - control_rate
            if treatment_n >= 3 and control_n >= 3
            else math.nan
        )
        records.append(
            {
                group_column: key,
                "treatment_n": treatment_n,
                "control_n": control_n,
                "treatment_rate": treatment_rate,
                "control_rate": control_rate,
                "effect": effect,
                "eligible": treatment_n >= 3 and control_n >= 3,
            }
        )
    positive = sum(
        bool(record["eligible"])
        and math.isfinite(float(record["effect"]))
        and float(record["effect"]) > 0.0
        for record in records
    )
    return int(positive), records


def build_comparison(
    ledger: pd.DataFrame,
    *,
    target_tier: str,
    seed: int,
) -> dict[str, Any]:
    data = ledger.loc[
        ledger["location_rule"].eq(PRIMARY_RULE)
        & ledger["target_tier"].eq(target_tier)
        & ledger[AVAILABLE_COLUMN].astype(bool)
    ].copy()
    treatment = data[TREATMENT_COLUMN].astype(bool)
    treatment_n = int(treatment.sum())
    control_n = int((~treatment).sum())
    treatment_rate = (
        float(data.loc[treatment, OUTCOME_COLUMN].mean()) if treatment_n else math.nan
    )
    control_rate = (
        float(data.loc[~treatment, OUTCOME_COLUMN].mean()) if control_n else math.nan
    )
    effect = _effect(data, TREATMENT_COLUMN, OUTCOME_COLUMN)
    ci_low, ci_high = _cluster_bootstrap(
        data,
        treatment_column=TREATMENT_COLUMN,
        outcome_column=OUTCOME_COLUMN,
        seed=seed,
    )
    positive_pairs, pair_effects = _breadth(data, group_column="instrument")
    positive_years, year_effects = _breadth(data, group_column="year")
    return {
        "target_tier": target_tier,
        "observations": int(len(data)),
        "treatment_n": treatment_n,
        "control_n": control_n,
        "treatment_rate": treatment_rate,
        "control_rate": control_rate,
        "effect": effect,
        "bootstrap_p05": ci_low,
        "bootstrap_p95": ci_high,
        "permutation_p": cluster_permutation_p_value(
            data,
            treatment_column=TREATMENT_COLUMN,
            outcome_column=OUTCOME_COLUMN,
            observed_effect=effect,
            seed=seed + 1000,
            samples=PERMUTATION_SAMPLES,
        ),
        "positive_pairs": positive_pairs,
        "positive_years": positive_years,
        "pair_effects": pair_effects,
        "year_effects": year_effects,
    }


def build_replication_decision(ledger: pd.DataFrame) -> dict[str, Any]:
    work = normalize_replication_ledger(ledger)
    opportunities = work.drop_duplicates(["instrument", "opportunity_id"]).copy()
    primary = opportunities.loc[opportunities["location_rule"].eq(PRIMARY_RULE)]
    active = primary.loc[primary[TREATMENT_COLUMN].astype(bool)]
    pair_counts = active.groupby("instrument", sort=True).size().reindex(
        REPLICATION_PAIRS,
        fill_value=0,
    )
    active_total = int(len(active))
    pair_breadth = int(pair_counts.ge(3).sum())
    concentration = (
        float(pair_counts.max() / pair_counts.sum()) if pair_counts.sum() else math.nan
    )

    conservative = build_comparison(
        work,
        target_tier="CONSERVATIVE",
        seed=RANDOM_SEED,
    )
    stretch = build_comparison(
        work,
        target_tier="STRETCH",
        seed=RANDOM_SEED + 10,
    )

    sample_gates = {
        "active_day10_at_least_20": active_total >= 20,
        "available_treatment_at_least_15": conservative["treatment_n"] >= 15,
        "controls_at_least_200": conservative["control_n"] >= 200,
        "three_pairs_have_at_least_three_active": pair_breadth >= 3,
    }
    effect_gates = {
        "conservative_lift_at_least_10pp": conservative["effect"] >= 0.10,
        "cluster_permutation_p_at_most_0_10": conservative["permutation_p"] <= 0.10,
        "agrees_with_original_positive_direction": conservative["effect"] > 0.0
        and ORIGINAL_CONSERVATIVE_EFFECT > 0.0,
    }
    breadth_gates = {
        "no_pair_above_40pct": math.isfinite(concentration)
        and concentration <= 0.40,
        "positive_effect_in_three_pairs": conservative["positive_pairs"] >= 3,
        "positive_effect_in_four_years": conservative["positive_years"] >= 4,
    }

    if not all(sample_gates.values()):
        decision = "FAIL_REPLICATION_SAMPLE_INSUFFICIENT"
    elif not all(effect_gates.values()):
        decision = "FAIL_REPLICATION_EFFECT_NOT_REPRODUCED"
    elif not all(breadth_gates.values()):
        decision = "FAIL_REPLICATION_BREADTH_OR_CONCENTRATION"
    else:
        decision = "PASS_REPLICATION_AUTHORIZE_MINIMAL_CONTEXT_PHASE"

    stage_counts = (
        primary.groupby(["instrument", "stage_sensitivity"], sort=True)
        .size()
        .rename("opportunities")
        .reset_index()
        .to_dict(orient="records")
    )
    return {
        "decision": decision,
        "candidate_pairs": list(REPLICATION_PAIRS),
        "primary_opportunities": int(len(primary)),
        "active_day10": active_total,
        "active_day10_by_pair": {key: int(value) for key, value in pair_counts.items()},
        "active_pair_breadth": pair_breadth,
        "maximum_pair_concentration": concentration,
        "sample_gates": sample_gates,
        "effect_gates": effect_gates,
        "breadth_gates": breadth_gates,
        "conservative": conservative,
        "stretch_supportive": stretch,
        "original_reference": {
            "panel": ["AUDUSD", "EURUSD", "GBPUSD", "USDCAD", "USDCHF", "USDJPY"],
            "available_treatment": 25,
            "treatment_rate": 0.48,
            "control_rate": 0.1231,
            "effect": ORIGINAL_CONSERVATIVE_EFFECT,
            "cluster_permutation_p": 0.0002,
            "binding_decision": "FAIL_STAGED_SEQUENCE_PRIMARY_SAMPLE",
        },
        "stage_sensitivity_counts": stage_counts,
        "protected_years_opened": False,
        "execution_or_pnl": False,
    }
