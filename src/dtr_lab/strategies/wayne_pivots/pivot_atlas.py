from __future__ import annotations

import math
import zlib
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_pivots.pivot_geometry import STRUCTURES, TARGETS

PLACEBOS = tuple(name for name in STRUCTURES if name != "WAYNE")
MIN_MATCHED_EVENTS = 400
MIN_PAIR_EVENTS = 75
MIN_PAIR_BREADTH = 4
MIN_YEAR_BREADTH = 4
MIN_SUCCESS_LIFT = 0.05
MAX_PAIR_CONCENTRATION = 0.40
MAX_YEAR_CONCENTRATION = 0.30
MIN_BOOTSTRAP_PROBABILITY = 0.90
MAX_Q_VALUE = 0.10
BOOTSTRAP_ITERATIONS = 2000
PERMUTATION_ITERATIONS = 4000


def _stable_seed(text: str) -> int:
    return int(zlib.crc32(text.encode("utf-8")))


def _bh_qvalues(p_values: pd.Series) -> pd.Series:
    values = pd.to_numeric(p_values, errors="coerce").to_numpy(dtype=float)
    q_values = np.full(len(values), np.nan, dtype=float)
    valid = np.flatnonzero(np.isfinite(values))
    if len(valid) == 0:
        return pd.Series(q_values, index=p_values.index)
    ordered = valid[np.argsort(values[valid], kind="mergesort")]
    adjusted = np.empty(len(ordered), dtype=float)
    total = len(ordered)
    running = 1.0
    for reverse_rank, index in enumerate(ordered[::-1], start=1):
        rank = total - reverse_rank + 1
        candidate = values[index] * total / rank
        running = min(running, candidate)
        adjusted[rank - 1] = min(1.0, running)
    q_values[ordered] = adjusted
    return pd.Series(q_values, index=p_values.index)


def _cluster_inference(
    frame: pd.DataFrame,
    *,
    value_column: str,
    seed_text: str,
) -> tuple[float, float, float]:
    cluster = (
        frame.groupby("pivot_day_local_date", sort=True)[value_column]
        .mean()
        .dropna()
        .to_numpy(dtype=float)
    )
    if len(cluster) < 20:
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(_stable_seed(seed_text))
    sample_indices = rng.integers(
        0,
        len(cluster),
        size=(BOOTSTRAP_ITERATIONS, len(cluster)),
    )
    bootstrap_means = cluster[sample_indices].mean(axis=1)
    probability = float(np.mean(bootstrap_means > 0.0))
    percentile_10 = float(np.quantile(bootstrap_means, 0.10))
    observed = float(cluster.mean())
    exceedances = 0
    remaining = PERMUTATION_ITERATIONS
    batch_size = 500
    while remaining > 0:
        batch = min(batch_size, remaining)
        signs = rng.choice((-1.0, 1.0), size=(batch, len(cluster)))
        permuted = (signs * cluster).mean(axis=1)
        exceedances += int(np.sum(permuted >= observed))
        remaining -= batch
    p_value = (exceedances + 1.0) / (PERMUTATION_ITERATIONS + 1.0)
    return probability, percentile_10, float(p_value)


def _concentration(frame: pd.DataFrame, group: str, value_column: str) -> float:
    grouped = frame.groupby(group, sort=True)[value_column].agg(["mean", "size"])
    contribution = (grouped["mean"] * grouped["size"]).abs()
    total = float(contribution.sum())
    if total <= 0.0:
        return math.nan
    return float(contribution.max() / total)


def _matched_comparison(
    eligible: pd.DataFrame,
    *,
    side: str,
    target_name: str,
    placebo: str,
) -> tuple[dict[str, Any], pd.DataFrame]:
    key = ["instrument", "pivot_day_start_utc", "pivot_day_local_date", "year"]
    columns = key + ["success", "strict_payoff_r"]
    wayne = eligible.loc[
        eligible["structure"].eq("WAYNE")
        & eligible["side"].eq(side)
        & eligible["target_name"].eq(target_name),
        columns,
    ].rename(
        columns={
            "success": "wayne_success",
            "strict_payoff_r": "wayne_payoff",
        }
    )
    control = eligible.loc[
        eligible["structure"].eq(placebo)
        & eligible["side"].eq(side)
        & eligible["target_name"].eq(target_name),
        columns,
    ].rename(
        columns={
            "success": "placebo_success",
            "strict_payoff_r": "placebo_payoff",
        }
    )
    matched = wayne.merge(control, on=key, how="inner", validate="one_to_one")
    matched["success_diff"] = (
        matched["wayne_success"].astype(float)
        - matched["placebo_success"].astype(float)
    )
    matched["payoff_diff"] = matched["wayne_payoff"] - matched["placebo_payoff"]
    row_id = f"{side}:{target_name}:{placebo}"
    probability, percentile_10, p_value = _cluster_inference(
        matched,
        value_column="payoff_diff",
        seed_text=row_id,
    )
    pair = matched.groupby("instrument", sort=True).agg(
        events=("payoff_diff", "size"),
        success_lift=("success_diff", "mean"),
        payoff_effect=("payoff_diff", "mean"),
    )
    pair = pair.reset_index()
    pair["positive_both"] = pair["success_lift"].gt(0.0) & pair["payoff_effect"].gt(0.0)
    year = matched.groupby("year", sort=True).agg(
        events=("payoff_diff", "size"),
        success_lift=("success_diff", "mean"),
        payoff_effect=("payoff_diff", "mean"),
    )
    year = year.reset_index()
    year["positive_both"] = year["success_lift"].gt(0.0) & year["payoff_effect"].gt(0.0)
    subgroup = pd.concat(
        [
            pair.assign(subgroup_type="PAIR").rename(columns={"instrument": "subgroup"}),
            year.assign(subgroup_type="YEAR")
            .rename(columns={"year": "subgroup"})
            .assign(subgroup=lambda item: item["subgroup"].astype(str)),
        ],
        ignore_index=True,
    )
    pair_event_breadth = int(pair["events"].ge(MIN_PAIR_EVENTS).sum())
    metrics = {
        "row_id": row_id,
        "side": side,
        "target_name": target_name,
        "placebo": placebo,
        "events": int(len(matched)),
        "wayne_success_rate": float(matched["wayne_success"].mean()) if len(matched) else math.nan,
        "placebo_success_rate": (
            float(matched["placebo_success"].mean()) if len(matched) else math.nan
        ),
        "success_lift": float(matched["success_diff"].mean()) if len(matched) else math.nan,
        "wayne_mean_payoff": float(matched["wayne_payoff"].mean()) if len(matched) else math.nan,
        "placebo_mean_payoff": (
            float(matched["placebo_payoff"].mean()) if len(matched) else math.nan
        ),
        "payoff_effect": float(matched["payoff_diff"].mean()) if len(matched) else math.nan,
        "pair_event_breadth": pair_event_breadth,
        "pair_positive_breadth": int(pair["positive_both"].sum()),
        "year_positive_breadth": int(year["positive_both"].sum()),
        "eligible_years": int(len(year)),
        "max_pair_concentration": _concentration(matched, "instrument", "payoff_diff"),
        "max_year_concentration": _concentration(matched, "year", "payoff_diff"),
        "bootstrap_probability_positive": probability,
        "bootstrap_p10": percentile_10,
        "permutation_p_value": p_value,
    }
    return metrics, subgroup.assign(row_id=row_id)


def _comparison_gate(row: pd.Series) -> bool:
    values = (
        row["events"] >= MIN_MATCHED_EVENTS,
        row["pair_event_breadth"] >= MIN_PAIR_BREADTH,
        row["success_lift"] >= MIN_SUCCESS_LIFT,
        row["payoff_effect"] > 0.0,
        row["pair_positive_breadth"] >= MIN_PAIR_BREADTH,
        row["year_positive_breadth"] >= MIN_YEAR_BREADTH,
        row["max_pair_concentration"] <= MAX_PAIR_CONCENTRATION,
        row["max_year_concentration"] <= MAX_YEAR_CONCENTRATION,
        row["bootstrap_probability_positive"] >= MIN_BOOTSTRAP_PROBABILITY,
        row["q_value"] <= MAX_Q_VALUE,
    )
    return all(bool(value) for value in values)


def evaluate_geometry_atlas(
    ledger: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    required = {
        "instrument",
        "pivot_day_start_utc",
        "pivot_day_local_date",
        "year",
        "structure",
        "side",
        "target_name",
        "eligible_fresh",
        "success",
        "strict_payoff_r",
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"anatomy ledger missing columns: {missing}")
    eligible = ledger.loc[ledger["eligible_fresh"].astype(bool)].copy()
    comparisons: list[dict[str, Any]] = []
    subgroups: list[pd.DataFrame] = []
    for side, target_names in TARGETS.items():
        for target_name in target_names:
            for placebo in PLACEBOS:
                metrics, subgroup = _matched_comparison(
                    eligible,
                    side=side,
                    target_name=target_name,
                    placebo=placebo,
                )
                comparisons.append(metrics)
                subgroups.append(subgroup)
    comparison = pd.DataFrame(comparisons)
    comparison["q_value"] = _bh_qvalues(comparison["permutation_p_value"])
    comparison["passes_all_gates"] = comparison.apply(_comparison_gate, axis=1)
    subgroup_summary = pd.concat(subgroups, ignore_index=True)
    candidates: list[dict[str, Any]] = []
    for side, target_names in TARGETS.items():
        for target_name in target_names:
            candidate_id = f"{side}:{target_name}"
            rows = comparison.loc[
                comparison["side"].eq(side)
                & comparison["target_name"].eq(target_name)
            ].copy()
            wayne = eligible.loc[
                eligible["structure"].eq("WAYNE")
                & eligible["side"].eq(side)
                & eligible["target_name"].eq(target_name)
            ].copy()
            pair_counts = wayne.groupby("instrument").size()
            anchor_rows = rows.set_index("placebo")
            prior_close_positive = bool(
                anchor_rows.loc["PRIOR_CLOSE", "payoff_effect"] > 0.0
            )
            range_mid_positive = bool(
                anchor_rows.loc["RANGE_MID", "payoff_effect"] > 0.0
            )
            core_anchor_pass = bool(
                anchor_rows.loc[["PRIOR_CLOSE", "RANGE_MID"], "passes_all_gates"].any()
            )
            positive_success = int(rows["success_lift"].gt(0.0).sum())
            positive_payoff = int(rows["payoff_effect"].gt(0.0).sum())
            passing_comparisons = int(rows["passes_all_gates"].sum())
            passes = all(
                (
                    len(wayne) >= MIN_MATCHED_EVENTS,
                    int(pair_counts.ge(MIN_PAIR_EVENTS).sum()) >= MIN_PAIR_BREADTH,
                    positive_success >= 8,
                    positive_payoff >= 8,
                    passing_comparisons >= 5,
                    prior_close_positive,
                    range_mid_positive,
                    core_anchor_pass,
                )
            )
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "side": side,
                    "target_name": target_name,
                    "wayne_events": int(len(wayne)),
                    "wayne_pair_breadth": int(pair_counts.ge(MIN_PAIR_EVENTS).sum()),
                    "positive_success_comparisons": positive_success,
                    "positive_payoff_comparisons": positive_payoff,
                    "passing_comparisons": passing_comparisons,
                    "prior_close_positive": prior_close_positive,
                    "range_mid_positive": range_mid_positive,
                    "core_anchor_pass": core_anchor_pass,
                    "passes_geometry": passes,
                }
            )
    candidate_summary = pd.DataFrame(candidates)
    passing_candidates = candidate_summary.loc[
        candidate_summary["passes_geometry"]
    ]["candidate_id"].tolist()
    decision_code = (
        "PASS_DAILY_PIVOT_GEOMETRY_AUTHORIZE_BIAS_FREEZE"
        if passing_candidates
        else "FAIL_DAILY_PIVOT_GEOMETRY_STOP_BEFORE_BIAS"
    )
    decision = {
        "decision": {
            "decision": decision_code,
            "events_total": int(len(ledger)),
            "fresh_events": int(len(eligible)),
            "instruments": sorted(eligible["instrument"].unique().tolist()),
            "years": sorted(int(value) for value in eligible["year"].unique()),
            "comparisons": int(len(comparison)),
            "passing_comparisons": int(comparison["passes_all_gates"].sum()),
            "passing_candidates": passing_candidates,
            "bias_stage_opened": bool(passing_candidates),
            "execution_stage_opened": False,
            "strategy_pnl_calculated": False,
        },
        "candidates": candidate_summary.to_dict(orient="records"),
    }
    return comparison, candidate_summary, subgroup_summary, decision
