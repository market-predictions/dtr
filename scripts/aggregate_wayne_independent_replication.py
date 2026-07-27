from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

import aggregate_wayne_staged_sequence as base
from dtr_lab.strategies.wayne_direction.cluster_stats import (
    cluster_permutation_p_value,
)

PANEL = ("EURGBP", "EURJPY", "GBPJPY", "NZDUSD")
PRIMARY_RULE = "CLOSE_IN_ZONE"
RANDOM_SEED = 20260728
COMPARISONS = (
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
        description="Aggregate the frozen independent day-10 FX replication."
    )
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--ledgers", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _clustered_permutation(
    data: pd.DataFrame,
    *,
    treatment_column: str,
    outcome_column: str,
    observed_effect: float,
    seed: int,
) -> float:
    return cluster_permutation_p_value(
        data,
        treatment_column=treatment_column,
        outcome_column=outcome_column,
        observed_effect=observed_effect,
        seed=seed,
        samples=base.PERMUTATION_SAMPLES,
    )


def _load_summaries(paths: list[Path]) -> list[dict[str, Any]]:
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    symbols = tuple(sorted(item["instrument"] for item in summaries))
    if symbols != PANEL:
        raise ValueError(f"expected frozen panel {PANEL}, found {symbols}")
    return summaries


def _load_ledgers(paths: list[Path]) -> pd.DataFrame:
    ledger = pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    if tuple(sorted(ledger["instrument"].unique())) != PANEL:
        raise ValueError("pooled replication ledger does not contain the frozen panel")
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
        ledger[column] = base._as_bool(ledger[column])
    return ledger


def _available_treatment_counts(ledger: pd.DataFrame) -> pd.Series:
    data = ledger.loc[
        ledger["location_rule"].eq(PRIMARY_RULE)
        & ledger["target_tier"].eq("CONSERVATIVE")
        & ledger["sensitivity_target_available"].astype(bool)
        & ledger["sequence_active_sensitivity"].astype(bool)
    ]
    return data.groupby("instrument", sort=True).size()


def _sample_gate(
    opportunities: pd.DataFrame,
    comparison: dict[str, Any],
    available_counts: pd.Series,
) -> dict[str, Any]:
    primary = opportunities.loc[opportunities["location_rule"].eq(PRIMARY_RULE)]
    active = primary.loc[primary["sequence_active_sensitivity"].astype(bool)]
    active_counts = active.groupby("instrument", sort=True).size()
    active_breadth = int(active_counts.ge(8).sum())
    available_breadth = int(available_counts.ge(5).sum())
    passed = bool(
        len(active) >= 80
        and comparison["treatment_n"] >= 40
        and comparison["control_n"] >= 120
        and active_breadth >= 4
        and available_breadth >= 4
    )
    return {
        "passed": passed,
        "active_opportunities": int(len(active)),
        "active_pair_counts": {key: int(value) for key, value in active_counts.items()},
        "available_treatment_pair_counts": {
            key: int(value) for key, value in available_counts.items()
        },
        "active_pair_breadth": active_breadth,
        "available_treatment_pair_breadth": available_breadth,
        "available_treatment": int(comparison["treatment_n"]),
        "available_control": int(comparison["control_n"]),
        "minimum_active": 80,
        "minimum_available_treatment": 40,
        "minimum_control": 120,
        "minimum_pairs_with_8_active": 4,
        "minimum_pairs_with_5_available_treatment": 4,
    }


def _treatment_concentration(available_counts: pd.Series) -> float:
    total = int(available_counts.sum())
    return math.nan if total == 0 else float(available_counts.max() / total)


def _leave_one_pair_out(ledger: pd.DataFrame) -> list[dict[str, Any]]:
    data = ledger.loc[
        ledger["location_rule"].eq(PRIMARY_RULE)
        & ledger["target_tier"].eq("CONSERVATIVE")
        & ledger["sensitivity_target_available"].astype(bool)
    ].copy()
    records = []
    for pair in PANEL:
        subset = data.loc[data["instrument"].ne(pair)]
        effect = base._effect(
            subset,
            "sequence_active_sensitivity",
            "sensitivity_reached_by_month_end",
        )
        treatment = subset["sequence_active_sensitivity"].astype(bool)
        records.append(
            {
                "removed_pair": pair,
                "treatment_n": int(treatment.sum()),
                "control_n": int((~treatment).sum()),
                "effect": effect,
            }
        )
    return records


def _eligible_positive_pair_fraction(
    comparison: dict[str, Any],
) -> tuple[int, int, float]:
    eligible = [
        item
        for item in comparison["pair_effects"]
        if math.isfinite(float(item["effect"]))
    ]
    positive = sum(float(item["effect"]) > 0 for item in eligible)
    fraction = math.nan if not eligible else positive / len(eligible)
    return positive, len(eligible), fraction


def _markdown(decision: dict[str, Any], comparisons: pd.DataFrame) -> str:
    payload = decision["decision"]
    gate = decision["sample_gate"]
    lines = [
        "# Wayne Independent FX Replication — Decision",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Sample gate: `{payload['sample_passed']}`  ",
        f"Effect criteria: `{payload['effect_passed']}`  ",
        "",
        "## Frozen panel",
        "",
        ", ".join(PANEL),
        "",
        "## Sample",
        "",
        f"- active day-10 sequences: {gate['active_opportunities']};",
        f"- available conservative treatment rows: {gate['available_treatment']};",
        f"- available controls: {gate['available_control']};",
        f"- pairs with at least eight active sequences: {gate['active_pair_breadth']};",
        f"- pairs with at least five available treatment rows: {gate['available_treatment_pair_breadth']}.",
        "",
        "## Frozen comparisons",
        "",
        "| Test | Treatment N | Control N | Treatment | Control | Lift | 90% low | 90% high | p | q |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparisons.itertuples(index=False):
        lines.append(
            f"| {row.name} | {row.treatment_n} | {row.control_n} | "
            f"{row.treatment_rate:.2%} | {row.control_rate:.2%} | "
            f"{row.effect:.2%} | {row.bootstrap_p05:.2%} | "
            f"{row.bootstrap_p95:.2%} | {row.permutation_p:.4f} | "
            f"{row.q_value:.4f} |"
        )
    lines.extend(
        [
            "",
            "The independent estimate is reported separately from the six-pair development result. ",
            "No yield, VIX, macro, seasonality, execution or Pine layer is included.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summaries = _load_summaries(args.summaries)
    ledger = _load_ledgers(args.ledgers)
    if not set(ledger["year"].unique()).issubset(range(2015, 2022)):
        raise ValueError("post-development year entered independent replication ledger")
    opportunities = ledger.drop_duplicates(["instrument", "opportunity_id"])

    original_permutation = base._permutation_p_value
    base._permutation_p_value = _clustered_permutation
    try:
        comparisons = [
            base._comparison(
                ledger,
                name=name,
                treatment_column=treatment,
                available_column=available,
                outcome_column=outcome,
                target_tier=tier,
                seed=RANDOM_SEED + offset,
            )
            for offset, (name, treatment, available, outcome, tier) in enumerate(
                COMPARISONS
            )
        ]
    finally:
        base._permutation_p_value = original_permutation

    q_values = base._bh_q_values(
        [float(comparison["permutation_p"]) for comparison in comparisons]
    )
    for comparison, q_value in zip(comparisons, q_values, strict=True):
        comparison["q_value"] = q_value

    conservative = comparisons[0]
    available_counts = _available_treatment_counts(ledger)
    sample_gate = _sample_gate(opportunities, conservative, available_counts)
    concentration = _treatment_concentration(available_counts)
    leave_one_out = _leave_one_pair_out(ledger)
    largest_pair = available_counts.idxmax() if not available_counts.empty else None
    largest_removed = next(
        (item for item in leave_one_out if item["removed_pair"] == largest_pair),
        None,
    )
    positive_pairs, eligible_pairs, positive_pair_fraction = (
        _eligible_positive_pair_fraction(conservative)
    )
    effect_passed = bool(
        sample_gate["passed"]
        and float(conservative["effect"]) > 0
        and float(conservative["permutation_p"]) <= 0.05
        and float(conservative["q_value"]) <= 0.10
        and float(conservative["bootstrap_p05"]) > 0
        and math.isfinite(positive_pair_fraction)
        and positive_pair_fraction >= 0.60
        and int(conservative["positive_years"]) >= 4
        and math.isfinite(concentration)
        and concentration <= 0.35
        and largest_removed is not None
        and math.isfinite(float(largest_removed["effect"]))
        and float(largest_removed["effect"]) > 0
    )
    if not sample_gate["passed"]:
        decision_code = "FAIL_INDEPENDENT_REPLICATION_SAMPLE"
    elif effect_passed:
        decision_code = "PASS_INDEPENDENT_TECHNICAL_REPLICATION"
    else:
        decision_code = "FAIL_INDEPENDENT_REPLICATION_EFFECT"

    comparison_frame = pd.DataFrame(comparisons)
    stage = base._stage_table(opportunities, "stage_sensitivity")
    decision = {
        "decision": {
            "decision": decision_code,
            "instruments": list(PANEL),
            "years": list(range(2015, 2022)),
            "sample_passed": bool(sample_gate["passed"]),
            "effect_passed": effect_passed,
            "treatment_concentration": concentration,
            "largest_treatment_pair": largest_pair,
            "positive_pairs": positive_pairs,
            "eligible_pairs": eligible_pairs,
            "positive_pair_fraction": positive_pair_fraction,
            "positive_years": int(conservative["positive_years"]),
            "yield_phase_opened": effect_passed,
            "vix_phase_opened": False,
            "execution_stage_opened": False,
        },
        "sample_gate": sample_gate,
        "comparisons": comparisons,
        "leave_one_pair_out": leave_one_out,
        "pair_summaries": summaries,
    }
    safe = base._json_safe(decision)
    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "wayne_independent_pooled_ledger.csv", index=False)
    comparison_frame.to_csv(
        args.out / "wayne_independent_comparisons.csv", index=False
    )
    stage.to_csv(args.out / "wayne_independent_stage_census.csv", index=False)
    pd.DataFrame(leave_one_out).to_csv(
        args.out / "wayne_independent_leave_one_pair_out.csv", index=False
    )
    (args.out / "wayne_independent_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_INDEPENDENT_REPLICATION_DECISION.md").write_text(
        _markdown(safe, comparison_frame),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
