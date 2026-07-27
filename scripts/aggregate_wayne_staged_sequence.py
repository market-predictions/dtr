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
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
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
    normalized = series.astype(str).str.strip().str.lower()
    invalid = ~normalized.isin({"true", "false", "1", "0"})
    if invalid.any():
        values = sorted(normalized.loc[invalid].unique())
        raise ValueError(f"invalid boolean values: {values}")
    return normalized.isin({"true", "1"})


def _load_ledgers(paths: list[Path]) -> pd.DataFrame:
    frames = [pd.read_csv(path) for path in paths]
    ledger = pd.concat(frames, ignore_index=True)
    symbols = tuple(sorted(ledger["instrument"].unique()))
    if symbols != PRIMARY_PAIRS:
        raise ValueError("pooled staged ledger does not contain all primary pairs")
    bool_columns = [
        column
        for column in ledger.columns
        if column.startswith("sequence_")
        or column.startswith("preexisting_")
        or column.startswith("dual_zone_")
        or column.startswith("health_same_")
        or column.startswith("health_strictly_")
        or column.endswith("_target_pre_start")
        or column.endswith("_target_same_bar")
        or column.endswith("_target_available")
        or column.endswith("_target_invalidation_same_bar")
        or column.endswith("_reached_by_month_end")
        or column.endswith("_reached_before_invalidation")
    ]
    for column in bool_columns:
        ledger[column] = _as_bool(ledger[column])
    return ledger


def _effect(data: pd.DataFrame, treatment_column: str, outcome_column: str) -> float:
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
        work["instrument"].astype(str)
        + "::"
        + work["month_id"].astype(str)
    )
    treatment = work[treatment_column].astype(bool)
    work["t_success"] = np.where(
        treatment,
        work[outcome_column].astype(float),
        0.0,
    )
    work["t_n"] = treatment.astype(int)
    work["c_success"] = np.where(
        ~treatment,
        work[outcome_column].astype(float),
        0.0,
    )
    work["c_n"] = (~treatment).astype(int)
    grouped = work.groupby("cluster", sort=False)[
        ["t_success", "t_n", "c_success", "c_n"]
    ].sum()
    values = grouped.to_numpy(dtype=float)
    if len(values) == 0:
        return math.nan, math.nan

    rng = np.random.default_rng(seed)
    effects: list[float] = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sampled = values[rng.integers(0, len(values), size=len(values))]
        totals = sampled.sum(axis=0)
        if totals[1] == 0 or totals[3] == 0:
            continue
        effects.append(totals[0] / totals[1] - totals[2] / totals[3])
    if not effects:
        return math.nan, math.nan
    return (
        float(np.quantile(effects, 0.05)),
        float(np.quantile(effects, 0.95)),
    )


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
    strata = (
        data["instrument"].astype(str)
        + "::"
        + data["year"].astype(str)
    )
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
        if permuted.sum() == 0 or (~permuted).sum() == 0:
            continue
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
    rows: list[dict[str, Any]] = []
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
        rows.append(
            {
                group_column: key,
                "treatment_n": treatment_n,
                "control_n": control_n,
                "effect": effect,
            }
        )
    positive = sum(
        1
        for row in rows
        if row["effect"] is not None
        and math.isfinite(float(row["effect"]))
        and float(row["effect"]) > 0.0
    )
    return positive, rows


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
    treatment_rate = (
        float(data.loc[treatment, outcome_column].mean())
        if treatment_n
        else math.nan
    )
    control_rate = (
        float(data.loc[~treatment, outcome_column].mean())
        if control_n
        else math.nan
    )
    effect = _effect(data, treatment_column, outcome_column)
    ci_low, ci_high = _cluster_bootstrap(
        data,
        treatment_column=treatment_column,
        outcome_column=outcome_column,
        seed=seed,
    )
    p_value = _permutation_p_value(
        data,
        treatment_column=treatment_column,
        outcome_column=outcome_column,
        observed_effect=effect,
        seed=seed + 1000,
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
        "treatment_rate": treatment_rate,
        "control_rate": control_rate,
        "effect": effect,
        "bootstrap_p05": ci_low,
        "bootstrap_p95": ci_high,
        "permutation_p": p_value,
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
    adjusted = np.empty(len(order), dtype=float)
    running = 1.0
    total = len(order)
    for reverse_rank, index in enumerate(order[::-1], start=1):
        rank = total - reverse_rank + 1
        running = min(running, values[index] * total / rank)
        adjusted[rank - 1] = running
    for rank, index in enumerate(order):
        output[index] = adjusted[rank]
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
    primary = opportunities.loc[
        opportunities["location_rule"].eq(PRIMARY_RULE)
    ].copy()
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
    *,
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


def _stage_table(
    opportunities: pd.DataFrame,
    *,
    stage_column: str,
) -> pd.DataFrame:
    return (
        opportunities.groupby(
            ["location_rule", "side", stage_column],
            sort=True,
        )
        .size()
        .rename("opportunities")
        .reset_index()
    )


def _signal_table(
    ledger: pd.DataFrame,
    *,
    maximum_day: int,
) -> pd.DataFrame:
    eligible = ledger.loc[
        ledger["health_pivot_day"].le(maximum_day)
        & ledger["signal_target_available"].astype(bool)
    ].copy()
    if eligible.empty:
        return pd.DataFrame()
    return (
        eligible.groupby(
            ["location_rule", "target_tier", "side"],
            sort=True,
        )
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
    stages_primary: pd.DataFrame,
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
            f"{row.effect:.2%} | {row.permutation_p:.4f} | {row.q_value:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Stage census",
            "",
            "| Location rule | Side | Stage | Opportunities |",
            "|---|---|---|---:|",
        ]
    )
    for row in stages_primary.itertuples(index=False):
        lines.append(
            f"| {row.location_rule} | {row.side} | "
            f"{getattr(row, 'stage_primary')} | {row.opportunities} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This study evaluates technical sequencing and monthly reach. "
            "It does not authorize entries, stops, sizing, Pine or deployment. "
            "Macro, policy regime and seasonality remain unopened.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summaries = _load_summaries(args.summaries)
    ledger = _load_ledgers(args.ledgers)
    if not set(ledger["year"].unique()).issubset(set(range(2015, 2022))):
        raise ValueError("post-development year entered staged sequence ledger")

    opportunities = ledger.drop_duplicates(
        ["instrument", "opportunity_id"]
    ).copy()
    comparisons = []
    for offset, spec in enumerate(TEST_SPECS):
        name, treatment, available, outcome, tier = spec
        comparisons.append(
            _comparison(
                ledger,
                name=name,
                treatment_column=treatment,
                available_column=available,
                outcome_column=outcome,
                target_tier=tier,
                seed=RANDOM_SEED + offset,
            )
        )
    q_values = _bh_q_values(
        [float(item["permutation_p"]) for item in comparisons]
    )
    for item, q_value in zip(comparisons, q_values, strict=True):
        item["q_value"] = q_value

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
    primary_concentration = _pair_concentration(
        opportunities,
        active_column="sequence_active_primary",
    )

    primary_effect_passed = (
        primary_gate["passed"]
        and float(primary_comparison["effect"]) >= 0.10
        and float(primary_comparison["permutation_p"]) <= 0.05
        and float(primary_comparison["q_value"]) <= 0.10
        and int(primary_comparison["positive_pairs"]) >= 4
        and int(primary_comparison["positive_years"]) >= 5
        and math.isfinite(primary_concentration)
        and primary_concentration <= 0.35
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

    stages_primary = _stage_table(
        opportunities,
        stage_column="stage_primary",
    )
    stages_sensitivity = _stage_table(
        opportunities,
        stage_column="stage_sensitivity",
    )
    signal_day5 = _signal_table(ledger, maximum_day=5)
    signal_day10 = _signal_table(ledger, maximum_day=10)
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
            "primary_pair_concentration": primary_concentration,
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
    ledger.to_csv(
        args.out / "wayne_staged_pooled_ledger.csv",
        index=False,
    )
    stages_primary.to_csv(
        args.out / "wayne_staged_primary_stage_census.csv",
        index=False,
    )
    stages_sensitivity.to_csv(
        args.out / "wayne_staged_sensitivity_stage_census.csv",
        index=False,
    )
    comparison_frame.to_csv(
        args.out / "wayne_staged_planned_comparisons.csv",
        index=False,
    )
    signal_day5.to_csv(
        args.out / "wayne_staged_signal_reach_day5.csv",
        index=False,
    )
    signal_day10.to_csv(
        args.out / "wayne_staged_signal_reach_day10.csv",
        index=False,
    )
    safe = _json_safe(decision)
    (args.out / "wayne_staged_sequence_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_STAGED_SEQUENCE_DECISION.md").write_text(
        _markdown(safe, comparison_frame, stages_primary),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
