from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import PRIMARY_PAIRS

BOOTSTRAP_SAMPLES = 2000
PERMUTATION_SAMPLES = 5000
RANDOM_SEED = 20260727
PRIMARY_RULE = "CLOSE_IN_ZONE"
TEST_SPECS = (
    (
        "DAY5_CONSERVATIVE",
        "sequence_active_primary",
        "primary_target_available",
        "primary_reached_by_month_end",
        "CONSERVATIVE",
    ),
    (
        "DAY5_STRETCH",
        "sequence_active_primary",
        "primary_target_available",
        "primary_reached_by_month_end",
        "STRETCH",
    ),
    (
        "DAY10_CONSERVATIVE",
        "sequence_active_sensitivity",
        "sensitivity_target_available",
        "sensitivity_reached_by_month_end",
        "CONSERVATIVE",
    ),
    (
        "DAY10_STRETCH",
        "sequence_active_sensitivity",
        "sensitivity_target_available",
        "sensitivity_reached_by_month_end",
        "STRETCH",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the Wayne staged monthly-sequence study."
    )
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--ledgers", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _load_summaries(paths: list[Path]) -> list[dict[str, Any]]:
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    symbols = tuple(sorted(item["instrument"] for item in summaries))
    if symbols != PRIMARY_PAIRS:
        raise ValueError(f"expected {PRIMARY_PAIRS}, found {symbols}")
    return summaries


def _as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    values = series.astype(str).str.strip().str.lower()
    invalid = ~values.isin({"true", "false", "1", "0"})
    if invalid.any():
        raise ValueError(
            f"invalid boolean values: {sorted(values.loc[invalid].unique())}"
        )
    return values.isin({"true", "1"})


def _load_ledgers(paths: list[Path]) -> pd.DataFrame:
    ledger = pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    if tuple(sorted(ledger["instrument"].unique())) != PRIMARY_PAIRS:
        raise ValueError("pooled staged ledger does not contain all primary pairs")
    boolean_columns = [
        column
        for column in ledger
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
        ledger[column] = _as_bool(ledger[column])
    return ledger


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
        totals = values[rng.integers(0, len(values), len(values))].sum(axis=0)
        if totals[1] and totals[3]:
            effects.append(totals[0] / totals[1] - totals[2] / totals[3])
    if not effects:
        return math.nan, math.nan
    return float(np.quantile(effects, 0.05)), float(np.quantile(effects, 0.95))


def _permutation_p_value(
    data: pd.DataFrame,
    *,
    treatment_column: str,
    outcome_column: str,
    observed_effect: float,
    seed: int,
) -> float:
    if not math.isfinite(observed_effect):
        return math.nan
    treatment = data[treatment_column].astype(bool).to_numpy()
    outcome = data[outcome_column].astype(float).to_numpy()
    strata = data["instrument"].astype(str) + "::" + data["year"].astype(str)
    groups = [
        np.asarray(index, dtype=int)
        for index in data.groupby(strata, sort=False).indices.values()
    ]
    rng = np.random.default_rng(seed)
    exceed = 0
    valid = 0
    for _ in range(PERMUTATION_SAMPLES):
        permuted = treatment.copy()
        for index in groups:
            permuted[index] = rng.permutation(permuted[index])
        if permuted.sum() and (~permuted).sum():
            effect = outcome[permuted].mean() - outcome[~permuted].mean()
            exceed += int(effect >= observed_effect)
            valid += 1
    return math.nan if valid == 0 else (exceed + 1.0) / (valid + 1.0)


def _breadth(
    data: pd.DataFrame,
    *,
    treatment_column: str,
    outcome_column: str,
    group_column: str,
) -> tuple[int, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    for key, group in data.groupby(group_column, sort=True):
        treatment = group[treatment_column].astype(bool)
        treatment_n = int(treatment.sum())
        control_n = int((~treatment).sum())
        effect = (
            float(
                group.loc[treatment, outcome_column].mean()
                - group.loc[~treatment, outcome_column].mean()
            )
            if treatment_n >= 3 and control_n >= 3
            else math.nan
        )
        records.append(
            {
                group_column: key,
                "treatment_n": treatment_n,
                "control_n": control_n,
                "effect": effect,
            }
        )
    positive = sum(
        math.isfinite(float(record["effect"])) and float(record["effect"]) > 0.0
        for record in records
    )
    return int(positive), records


def _comparison(
    ledger: pd.DataFrame,
    *,
    name: str,
    treatment_column: str,
    available_column: str,
    outcome_column: str,
    target_tier: str,
    seed: int,
) -> dict[str, Any]:
    data = ledger.loc[
        ledger["location_rule"].eq(PRIMARY_RULE)
        & ledger["target_tier"].eq(target_tier)
        & ledger[available_column].astype(bool)
    ].copy()
    treatment = data[treatment_column].astype(bool)
    treatment_n = int(treatment.sum())
    control_n = int((~treatment).sum())
    effect = _effect(data, treatment_column, outcome_column)
    ci_low, ci_high = _cluster_bootstrap(
        data,
        treatment_column=treatment_column,
        outcome_column=outcome_column,
        seed=seed,
    )
    positive_pairs, pair_effects = _breadth(
        data,
        treatment_column=treatment_column,
        outcome_column=outcome_column,
        group_column="instrument",
    )
    positive_years, year_effects = _breadth(
        data,
        treatment_column=treatment_column,
        outcome_column=outcome_column,
        group_column="year",
    )
    return {
        "name": name,
        "target_tier": target_tier,
        "treatment_n": treatment_n,
        "control_n": control_n,
        "treatment_rate": (
            float(data.loc[treatment, outcome_column].mean())
            if treatment_n
            else math.nan
        ),
        "control_rate": (
            float(data.loc[~treatment, outcome_column].mean())
            if control_n
            else math.nan
        ),
        "effect": effect,
        "bootstrap_p05": ci_low,
        "bootstrap_p95": ci_high,
        "permutation_p": _permutation_p_value(
            data,
            treatment_column=treatment_column,
            outcome_column=outcome_column,
            observed_effect=effect,
            seed=seed + 1000,
        ),
        "positive_pairs": positive_pairs,
        "positive_years": positive_years,
        "pair_effects": pair_effects,
        "year_effects": year_effects,
    }


def _bh_q_values(p_values: list[float]) -> list[float]:
    values = np.asarray(p_values, dtype=float)
    output = np.full(len(values), np.nan)
    valid = np.flatnonzero(np.isfinite(values))
    if len(valid) == 0:
        return output.tolist()
    order = valid[np.argsort(values[valid])]
    running = 1.0
    total = len(order)
    for position in range(total - 1, -1, -1):
        index = order[position]
        rank = position + 1
        running = min(running, values[index] * total / rank)
        output[index] = running
    return output.tolist()


def _sample_gate(
    opportunities: pd.DataFrame,
    comparison: dict[str, Any],
    *,
    active_column: str,
    minimum_active: int,
    minimum_pair: int,
    minimum_pair_breadth: int,
    minimum_available_treatment: int,
    minimum_control: int,
) -> dict[str, Any]:
    primary = opportunities.loc[opportunities["location_rule"].eq(PRIMARY_RULE)]
    active = primary.loc[primary[active_column].astype(bool)]
    pair_counts = active.groupby("instrument", sort=True).size()
    pair_breadth = int(pair_counts.ge(minimum_pair).sum())
    passed = (
        len(active) >= minimum_active
        and pair_breadth >= minimum_pair_breadth
        and comparison["treatment_n"] >= minimum_available_treatment
        and comparison["control_n"] >= minimum_control
    )
    return {
        "passed": passed,
        "active_opportunities": int(len(active)),
        "pair_counts": pair_counts.to_dict(),
        "pair_breadth": pair_breadth,
        "available_treatment": int(comparison["treatment_n"]),
        "available_control": int(comparison["control_n"]),
        "minimum_active": minimum_active,
        "minimum_pair": minimum_pair,
        "minimum_pair_breadth": minimum_pair_breadth,
        "minimum_available_treatment": minimum_available_treatment,
        "minimum_control": minimum_control,
    }


def _pair_concentration(
    opportunities: pd.DataFrame,
    active_column: str,
) -> float:
    active = opportunities.loc[
        opportunities["location_rule"].eq(PRIMARY_RULE)
        & opportunities[active_column].astype(bool)
    ]
    if active.empty:
        return math.nan
    counts = active.groupby("instrument", sort=True).size()
    return float(counts.max() / counts.sum())


def _stage_table(opportunities: pd.DataFrame, column: str) -> pd.DataFrame:
    return (
        opportunities.groupby(["location_rule", "side", column], sort=True)
        .size()
        .rename("opportunities")
        .reset_index()
    )


def _signal_table(ledger: pd.DataFrame, maximum_day: int) -> pd.DataFrame:
    data = ledger.loc[
        ledger["health_pivot_day"].le(maximum_day)
        & ledger["signal_target_available"].astype(bool)
    ]
    if data.empty:
        return pd.DataFrame()
    return (
        data.groupby(["location_rule", "target_tier", "side"], sort=True)
        .agg(
            observations=("signal_target_available", "size"),
            reached=("signal_reached_before_invalidation", "sum"),
            reach_rate=("signal_reached_before_invalidation", "mean"),
        )
        .reset_index()
    )


def _markdown(
    decision: dict[str, Any],
    comparisons: pd.DataFrame,
    stages: pd.DataFrame,
) -> str:
    payload = decision["decision"]
    lines = [
        "# Wayne Staged Monthly Sequence — Decision",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Primary sample gate: `{payload['primary_sample_passed']}`  ",
        f"Ten-day sensitivity gate: `{payload['sensitivity_sample_passed']}`  ",
        "",
        "## Planned comparisons",
        "",
        "| Test | Treatment N | Control N | Treatment | Control | Lift | p | q |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparisons.itertuples(index=False):
        lines.append(
            f"| {row.name} | {row.treatment_n} | {row.control_n} | "
            f"{row.treatment_rate:.2%} | {row.control_rate:.2%} | "
            f"{row.effect:.2%} | {row.permutation_p:.4f} | "
            f"{row.q_value:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Primary stage census",
            "",
            "| Location rule | Side | Stage | Opportunities |",
            "|---|---|---|---:|",
        ]
    )
    for row in stages.itertuples(index=False):
        lines.append(
            f"| {row.location_rule} | {row.side} | "
            f"{row.stage_primary} | {row.opportunities} |"
        )
    lines.extend(
        [
            "",
            "This is technical attribution, not an executable strategy. "
            "Macro, regime, seasonality, entries and deployment remain closed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summaries = _load_summaries(args.summaries)
    ledger = _load_ledgers(args.ledgers)
    if not set(ledger["year"].unique()).issubset(range(2015, 2022)):
        raise ValueError("post-development year entered staged sequence ledger")

    opportunities = ledger.drop_duplicates(["instrument", "opportunity_id"])
    comparisons = [
        _comparison(
            ledger,
            name=name,
            treatment_column=treatment,
            available_column=available,
            outcome_column=outcome,
            target_tier=tier,
            seed=RANDOM_SEED + offset,
        )
        for offset, (name, treatment, available, outcome, tier) in enumerate(
            TEST_SPECS
        )
    ]
    q_values = _bh_q_values(
        [float(comparison["permutation_p"]) for comparison in comparisons]
    )
    for comparison, q_value in zip(comparisons, q_values, strict=True):
        comparison["q_value"] = q_value

    primary_comparison = comparisons[0]
    sensitivity_comparison = comparisons[2]
    primary_gate = _sample_gate(
        opportunities,
        primary_comparison,
        active_column="sequence_active_primary",
        minimum_active=50,
        minimum_pair=5,
        minimum_pair_breadth=4,
        minimum_available_treatment=30,
        minimum_control=100,
    )
    sensitivity_gate = _sample_gate(
        opportunities,
        sensitivity_comparison,
        active_column="sequence_active_sensitivity",
        minimum_active=80,
        minimum_pair=8,
        minimum_pair_breadth=4,
        minimum_available_treatment=40,
        minimum_control=120,
    )
    concentration = _pair_concentration(
        opportunities,
        "sequence_active_primary",
    )
    primary_effect_passed = (
        primary_gate["passed"]
        and float(primary_comparison["effect"]) >= 0.10
        and float(primary_comparison["permutation_p"]) <= 0.05
        and float(primary_comparison["q_value"]) <= 0.10
        and int(primary_comparison["positive_pairs"]) >= 4
        and int(primary_comparison["positive_years"]) >= 5
        and math.isfinite(concentration)
        and concentration <= 0.35
    )
    sensitivity_effect_passed = (
        sensitivity_gate["passed"]
        and float(sensitivity_comparison["effect"]) >= 0.10
        and float(sensitivity_comparison["permutation_p"]) <= 0.05
        and float(sensitivity_comparison["q_value"]) <= 0.10
        and int(sensitivity_comparison["positive_pairs"]) >= 4
        and int(sensitivity_comparison["positive_years"]) >= 5
    )
    if primary_effect_passed:
        decision_code = "PASS_STAGED_SEQUENCE_OPEN_DIRECTION_LAYERS"
    elif not primary_gate["passed"] and sensitivity_effect_passed:
        decision_code = "SENSITIVITY_ONLY_DO_NOT_PROMOTE"
    elif not primary_gate["passed"]:
        decision_code = "FAIL_STAGED_SEQUENCE_PRIMARY_SAMPLE"
    else:
        decision_code = "FAIL_STAGED_SEQUENCE_NO_REACH_LIFT"

    stage_primary = _stage_table(opportunities, "stage_primary")
    stage_sensitivity = _stage_table(opportunities, "stage_sensitivity")
    comparison_frame = pd.DataFrame(comparisons)
    decision = {
        "decision": {
            "decision": decision_code,
            "instruments": list(PRIMARY_PAIRS),
            "years": list(range(2015, 2022)),
            "primary_location_rule": PRIMARY_RULE,
            "primary_sample_passed": bool(primary_gate["passed"]),
            "sensitivity_sample_passed": bool(sensitivity_gate["passed"]),
            "primary_effect_passed": primary_effect_passed,
            "sensitivity_effect_passed": sensitivity_effect_passed,
            "primary_pair_concentration": concentration,
            "macro_stage_opened": primary_effect_passed,
            "execution_stage_opened": False,
            "strategy_pnl_calculated": False,
        },
        "primary_sample_gate": primary_gate,
        "sensitivity_sample_gate": sensitivity_gate,
        "comparisons": comparisons,
        "pair_summaries": summaries,
    }

    args.out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "wayne_staged_pooled_ledger.csv": ledger,
        "wayne_staged_primary_stage_census.csv": stage_primary,
        "wayne_staged_sensitivity_stage_census.csv": stage_sensitivity,
        "wayne_staged_planned_comparisons.csv": comparison_frame,
        "wayne_staged_signal_reach_day5.csv": _signal_table(ledger, 5),
        "wayne_staged_signal_reach_day10.csv": _signal_table(ledger, 10),
    }
    for filename, frame in outputs.items():
        frame.to_csv(args.out / filename, index=False)
    safe = _json_safe(decision)
    (args.out / "wayne_staged_sequence_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_STAGED_SEQUENCE_DECISION.md").write_text(
        _markdown(safe, comparison_frame, stage_primary),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
