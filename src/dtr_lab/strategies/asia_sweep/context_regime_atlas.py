from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.context_regime import FACTOR_FAMILIES

RANDOM_SEED = 20260726
BOOTSTRAP_DRAWS = 5000
PERMUTATION_DRAWS = 5000


@dataclass(frozen=True)
class AtlasGate:
    min_events: int = 150
    min_events_per_pair: int = 50
    min_years: int = 5
    max_pair_concentration: float = 0.70
    max_year_concentration: float = 0.35
    min_absolute_hit_lift: float = 0.05
    min_relative_hit_lift: float = 0.35
    min_positive_pairs: int = 2
    min_positive_years: int = 4
    min_bootstrap_probability: float = 0.90
    max_q_value: float = 0.10


GATE = AtlasGate()


def _safe_mean(values: pd.Series) -> float:
    sample = pd.to_numeric(values, errors="coerce").dropna()
    return float(sample.mean()) if len(sample) else math.nan


def _safe_ratio(numerator: float, denominator: float) -> float:
    if (
        not np.isfinite(numerator)
        or not np.isfinite(denominator)
        or denominator == 0.0
    ):
        return math.nan
    return float(numerator / denominator)


def _date_arrays(
    frame: pd.DataFrame,
    membership: pd.Series,
    value_column: str,
    date_order: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    work = frame.loc[pd.to_numeric(frame[value_column], errors="coerce").notna()].copy()
    work["_value"] = pd.to_numeric(work[value_column], errors="raise").astype(float)
    work["_member"] = membership.loc[work.index].astype(bool).to_numpy()
    all_agg = work.groupby("trade_date", sort=False)["_value"].agg(["sum", "count"])
    state_agg = (
        work.loc[work["_member"]]
        .groupby("trade_date", sort=False)["_value"]
        .agg(["sum", "count"])
    )
    all_sum = all_agg["sum"].reindex(date_order, fill_value=0.0).to_numpy(float)
    all_count = all_agg["count"].reindex(date_order, fill_value=0).to_numpy(float)
    state_sum = state_agg["sum"].reindex(date_order, fill_value=0.0).to_numpy(float)
    state_count = state_agg["count"].reindex(date_order, fill_value=0).to_numpy(float)
    return state_sum, state_count, all_sum, all_count


def _bootstrap_effect(
    state_sum: np.ndarray,
    state_count: np.ndarray,
    all_sum: np.ndarray,
    all_count: np.ndarray,
    bootstrap_indices: np.ndarray,
) -> np.ndarray:
    selected_state_sum = state_sum[bootstrap_indices].sum(axis=1)
    selected_state_count = state_count[bootstrap_indices].sum(axis=1)
    selected_all_sum = all_sum[bootstrap_indices].sum(axis=1)
    selected_all_count = all_count[bootstrap_indices].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        effect = (
            selected_state_sum / selected_state_count
            - selected_all_sum / selected_all_count
        )
    return effect[np.isfinite(effect)]


def _sign_permutation_pvalue(
    frame: pd.DataFrame,
    membership: pd.Series,
    value_column: str,
    date_order: list[str],
    sign_matrix: np.ndarray,
    observed_effect: float,
) -> float:
    work = frame.loc[pd.to_numeric(frame[value_column], errors="coerce").notna()].copy()
    values = pd.to_numeric(work[value_column], errors="raise").to_numpy(float)
    member = membership.loc[work.index].astype(bool).to_numpy()
    n_state = int(member.sum())
    n_all = len(work)
    if n_state == 0 or n_all == 0 or not np.isfinite(observed_effect):
        return math.nan
    weights = member.astype(float) / n_state - 1.0 / n_all
    work["_contribution"] = weights * values
    contributions = (
        work.groupby("trade_date", sort=False)["_contribution"]
        .sum()
        .reindex(date_order, fill_value=0.0)
        .to_numpy(float)
    )
    null = sign_matrix @ contributions
    return float(
        (1.0 + np.sum(np.abs(null) >= abs(observed_effect))) / (len(null) + 1.0)
    )


def _benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    result = pd.Series(math.nan, index=p_values.index, dtype=float)
    valid = p_values.dropna().astype(float)
    if valid.empty:
        return result
    ordered = valid.sort_values()
    count = len(ordered)
    adjusted = ordered.to_numpy() * count / np.arange(1, count + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    result.loc[ordered.index] = adjusted
    return result


def _subgroup_effects(
    frame: pd.DataFrame,
    membership: pd.Series,
    dimension: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(dimension, sort=True):
        member = membership.loc[group.index].astype(bool)
        state = group.loc[member & group["economic_proxy_eligible"].astype(bool)]
        baseline = group.loc[group["economic_proxy_eligible"].astype(bool)]
        state_payoff = _safe_mean(state["stressed_payoff_proxy"])
        baseline_payoff = _safe_mean(baseline["stressed_payoff_proxy"])
        rows.append(
            {
                "key": str(key),
                "events": int(member.sum()),
                "economic_events": int(len(state)),
                "hit_rate": _safe_mean(group.loc[member, "target"]),
                "baseline_hit_rate": _safe_mean(group["target"]),
                "mean_payoff": state_payoff,
                "baseline_mean_payoff": baseline_payoff,
                "economic_effect": state_payoff - baseline_payoff,
            }
        )
    return rows


def evaluate_single_factor_atlas(
    ledger: pd.DataFrame,
    *,
    gate: AtlasGate = GATE,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "target",
        "stressed_payoff_proxy",
        "economic_proxy_eligible",
        *FACTOR_FAMILIES,
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"context ledger missing atlas columns: {missing}")
    frame = ledger.copy()
    frame["trade_date"] = pd.to_datetime(
        frame["trade_date"], errors="raise"
    ).dt.date.astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["target"] = pd.to_numeric(frame["target"], errors="raise").astype(int)
    if frame["event_id"].duplicated().any():
        raise ValueError("atlas ledger event ids must be unique")
    date_order = sorted(frame["trade_date"].unique().tolist())
    rng = np.random.default_rng(RANDOM_SEED)
    bootstrap_indices = rng.integers(
        0,
        len(date_order),
        size=(BOOTSTRAP_DRAWS, len(date_order)),
        dtype=np.int32,
    )
    sign_matrix = rng.choice(
        np.array([-1.0, 1.0]),
        size=(PERMUTATION_DRAWS, len(date_order)),
        replace=True,
    )
    baseline_hit = _safe_mean(frame["target"])
    economic_base = frame.loc[frame["economic_proxy_eligible"].astype(bool)]
    baseline_payoff = _safe_mean(economic_base["stressed_payoff_proxy"])
    summary_rows: list[dict[str, Any]] = []
    subgroup_rows: list[dict[str, Any]] = []
    for factor, family in FACTOR_FAMILIES.items():
        values = frame[factor].astype("string").fillna("WARMUP")
        for state in sorted(values.unique().tolist()):
            member = values.eq(state)
            selected = frame.loc[member]
            selected_econ = selected.loc[
                selected["economic_proxy_eligible"].astype(bool)
            ]
            hit_rate = _safe_mean(selected["target"])
            hit_lift = hit_rate - baseline_hit
            relative_hit_lift = _safe_ratio(hit_lift, baseline_hit)
            mean_payoff = _safe_mean(selected_econ["stressed_payoff_proxy"])
            economic_effect = mean_payoff - baseline_payoff
            state_sum, state_count, all_sum, all_count = _date_arrays(
                frame, member, "stressed_payoff_proxy", date_order
            )
            bootstrap = _bootstrap_effect(
                state_sum,
                state_count,
                all_sum,
                all_count,
                bootstrap_indices,
            )
            probability_positive = (
                float(np.mean(bootstrap > 0.0)) if len(bootstrap) else math.nan
            )
            p10 = float(np.quantile(bootstrap, 0.10)) if len(bootstrap) else math.nan
            p90 = float(np.quantile(bootstrap, 0.90)) if len(bootstrap) else math.nan
            permutation_p = _sign_permutation_pvalue(
                frame,
                member,
                "stressed_payoff_proxy",
                date_order,
                sign_matrix,
                economic_effect,
            )
            pair_metrics = _subgroup_effects(frame, member, "instrument")
            year_metrics = _subgroup_effects(frame, member, "year")
            pair_counts = selected["instrument"].value_counts()
            year_counts = selected["year"].value_counts()
            min_pair_events = int(pair_counts.min()) if len(pair_counts) == 2 else 0
            pair_concentration = (
                float(pair_counts.max() / len(selected)) if len(selected) else math.nan
            )
            year_concentration = (
                float(year_counts.max() / len(selected)) if len(selected) else math.nan
            )
            positive_pairs = sum(
                np.isfinite(item["economic_effect"]) and item["economic_effect"] > 0.0
                for item in pair_metrics
            )
            positive_years = sum(
                np.isfinite(item["economic_effect"]) and item["economic_effect"] > 0.0
                for item in year_metrics
            )
            checks = {
                "not_warmup": state != "WARMUP",
                "events": len(selected) >= gate.min_events,
                "events_per_pair": min_pair_events >= gate.min_events_per_pair,
                "year_representation": selected["year"].nunique() >= gate.min_years,
                "pair_concentration": pair_concentration <= gate.max_pair_concentration,
                "year_concentration": year_concentration <= gate.max_year_concentration,
                "hit_lift": (
                    hit_lift >= gate.min_absolute_hit_lift
                    or relative_hit_lift >= gate.min_relative_hit_lift
                ),
                "positive_economic_effect": economic_effect > 0.0,
                "pair_breadth": positive_pairs >= gate.min_positive_pairs,
                "year_breadth": positive_years >= gate.min_positive_years,
                "bootstrap_probability": (
                    probability_positive >= gate.min_bootstrap_probability
                ),
            }
            row_id = f"{factor}::{state}"
            summary_rows.append(
                {
                    "row_id": row_id,
                    "family": family,
                    "factor": factor,
                    "state": state,
                    "events": int(len(selected)),
                    "positive_cases": int(selected["target"].sum()),
                    "economic_events": int(len(selected_econ)),
                    "pairs": int(selected["instrument"].nunique()),
                    "years": int(selected["year"].nunique()),
                    "min_pair_events": min_pair_events,
                    "pair_concentration": pair_concentration,
                    "year_concentration": year_concentration,
                    "hit_rate": hit_rate,
                    "baseline_hit_rate": baseline_hit,
                    "absolute_hit_lift": hit_lift,
                    "relative_hit_lift": relative_hit_lift,
                    "mean_payoff": mean_payoff,
                    "baseline_mean_payoff": baseline_payoff,
                    "economic_effect": economic_effect,
                    "positive_pairs": int(positive_pairs),
                    "positive_years": int(positive_years),
                    "bootstrap_probability_positive": probability_positive,
                    "bootstrap_p10": p10,
                    "bootstrap_p90": p90,
                    "permutation_p_value": permutation_p,
                    "pre_fdr_pass": bool(all(checks.values())),
                    "failed_pre_fdr_gates": ";".join(
                        key for key, passed in checks.items() if not passed
                    ),
                    "evidence_score": int(sum(checks.values())),
                }
            )
            for dimension, records in (
                ("pair", pair_metrics),
                ("year", year_metrics),
            ):
                for record in records:
                    subgroup_rows.append(
                        {
                            "row_id": row_id,
                            "family": family,
                            "factor": factor,
                            "state": state,
                            "dimension": dimension,
                            **record,
                        }
                    )
    summary = pd.DataFrame(summary_rows)
    fdr_mask = summary["state"].ne("WARMUP")
    summary["q_value"] = math.nan
    summary.loc[fdr_mask, "q_value"] = _benjamini_hochberg(
        summary.loc[fdr_mask, "permutation_p_value"]
    )
    summary["passes_fdr"] = summary["q_value"].le(gate.max_q_value).fillna(False)
    summary["passes_all_gates"] = summary["pre_fdr_pass"] & summary["passes_fdr"]
    summary["failed_gates"] = summary.apply(
        lambda row: ";".join(
            item
            for item in (
                str(row["failed_pre_fdr_gates"]),
                "fdr" if not bool(row["passes_fdr"]) else "",
            )
            if item
        ),
        axis=1,
    )
    family_rows: list[dict[str, Any]] = []
    for family, group in summary.groupby("family", sort=True):
        ranked = group.sort_values(
            [
                "passes_all_gates",
                "evidence_score",
                "economic_effect",
                "absolute_hit_lift",
            ],
            ascending=[False, False, False, False],
            kind="mergesort",
        )
        best = ranked.iloc[0]
        family_rows.append(
            {
                "family": family,
                "states_tested": int(len(group)),
                "passing_states": int(group["passes_all_gates"].sum()),
                "status": (
                    "PROMISING_FOR_REPLICATION"
                    if group["passes_all_gates"].any()
                    else "DESCRIPTIVE_ONLY"
                ),
                "best_row_id": str(best["row_id"]),
                "best_evidence_score": int(best["evidence_score"]),
                "best_economic_effect": float(best["economic_effect"]),
                "best_absolute_hit_lift": float(best["absolute_hit_lift"]),
                "best_q_value": (
                    float(best["q_value"])
                    if np.isfinite(best["q_value"])
                    else math.nan
                ),
            }
        )
    family_summary = pd.DataFrame(family_rows)
    passing_families = family_summary.loc[
        family_summary["status"].eq("PROMISING_FOR_REPLICATION"), "family"
    ].tolist()
    decision = (
        "PASS_SINGLE_FACTOR_ATLAS_AUTHORIZE_INTERACTION_FREEZE"
        if len(passing_families) >= 2
        else "FAIL_SINGLE_FACTOR_ATLAS_STOP_BEFORE_INTERACTIONS"
    )
    payload = {
        "programme": "ASIAN_SWEEP_CONTEXT_REGIME_ATLAS_V10",
        "stage": "SINGLE_FACTOR_ATTRIBUTION",
        "events": int(len(frame)),
        "economic_events": int(frame["economic_proxy_eligible"].sum()),
        "dates": int(frame["trade_date"].nunique()),
        "pairs": sorted(frame["instrument"].unique().tolist()),
        "years": sorted(frame["year"].unique().astype(int).tolist()),
        "baseline_hit_rate": baseline_hit,
        "baseline_mean_payoff": baseline_payoff,
        "states_tested": int(len(summary)),
        "states_passing": int(summary["passes_all_gates"].sum()),
        "passing_families": passing_families,
        "decision": decision,
        "interaction_outcomes_opened": False,
        "router_model_opened": False,
        "strategy_pnl_calculated": False,
    }
    return summary, pd.DataFrame(subgroup_rows), {
        "decision": payload,
        "families": family_rows,
    }
