from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.weekly_profile_regime import (
    _event_context,
    build_daily_context,
)

PAIRS = ("EURUSD", "GBPUSD")
PRIMARY_TARGET = "EXT_OPPOSING_LIQUIDITY_1400"
FIXED_4R_TARGET = "EXT_FIXED_4R_1400"
DIAGNOSTIC_TARGETS = (
    PRIMARY_TARGET,
    FIXED_4R_TARGET,
    "EXT_FIXED_3R_1200",
    "EXT_OPPOSITE_BOUNDARY_1100",
    "EXT_FIXED_2R_1100",
)
BOOTSTRAP_SEED = 20260726
BOOTSTRAP_ITERATIONS = 10_000


@dataclass(frozen=True)
class StageGate:
    name: str
    years: tuple[int, ...]
    min_events: int
    min_positives: int
    min_pair_events: int
    min_positive_years: int
    min_bootstrap_probability: float
    min_bootstrap_p10: float


CONFIRMATION_GATE = StageGate(
    name="confirmation",
    years=(2020, 2021, 2022),
    min_events=40,
    min_positives=10,
    min_pair_events=15,
    min_positive_years=2,
    min_bootstrap_probability=0.80,
    min_bootstrap_p10=-0.10,
)
FINAL_GATE = StageGate(
    name="final",
    years=(2023, 2024, 2025),
    min_events=40,
    min_positives=10,
    min_pair_events=15,
    min_positive_years=2,
    min_bootstrap_probability=0.90,
    min_bootstrap_p10=-0.05,
)
COMBINED_YEARS = tuple(range(2020, 2026))


def enrich_transition_target_ledger(
    targets: pd.DataFrame,
    midpoint_minutes: pd.DataFrame,
    *,
    symbol: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "side",
        "landmark",
        "entry_timestamp_utc",
        "extended_target",
        "extended_target_hit",
        "extended_reward_risk_stress_010",
    }
    missing = sorted(required - set(targets.columns))
    if missing:
        raise ValueError(f"missing weekly-transition target columns: {missing}")
    symbol = symbol.upper()
    source = targets.loc[
        targets["instrument"].eq(symbol)
        & targets["landmark"].eq("T0")
        & targets["year"].between(start_year, end_year)
    ].copy()
    if source.empty:
        raise ValueError(
            f"{symbol}: no T0 targets in partition {start_year}-{end_year}"
        )
    source["entry_timestamp_utc"] = pd.to_datetime(
        source["entry_timestamp_utc"], utc=True, errors="raise"
    )
    events = source.drop_duplicates("event_id").loc[
        :, ["event_id", "entry_timestamp_utc", "side"]
    ]
    daily = build_daily_context(midpoint_minutes)
    rows: list[dict[str, Any]] = []
    for row in events.sort_values("entry_timestamp_utc").itertuples(index=False):
        try:
            context = _event_context(
                midpoint_minutes,
                daily,
                entry_time=pd.Timestamp(row.entry_timestamp_utc),
                side=str(row.side),
            )
        except ValueError:
            continue
        rows.append({"event_id": str(row.event_id), **context})
    context_frame = pd.DataFrame(rows)
    if context_frame.empty:
        raise ValueError(f"{symbol}: transition context is empty")
    enriched = source.merge(
        context_frame,
        on="event_id",
        how="inner",
        validate="many_to_one",
    )
    enriched["observed_stressed_ev_proxy"] = (
        enriched["extended_target_hit"].astype(float)
        * enriched["extended_reward_risk_stress_010"].astype(float)
        - (1.0 - enriched["extended_target_hit"].astype(float))
    )
    counter_direction = np.where(
        enriched["structural_trend"].eq("UP"),
        "DOWN",
        np.where(enriched["structural_trend"].eq("DOWN"), "UP", "NEUTRAL"),
    )
    enriched["transition_population"] = (
        enriched["weekly_phase"].eq("MIDWEEK_REVERSAL_OR_TRANSITION")
        & enriched["trade_opposes_structural"].astype(bool)
    )
    enriched["transition_reference"] = (
        enriched["structural_trend"].isin(["UP", "DOWN"])
        & enriched["event_weekday"].ge(2)
        & enriched["current_week_direction"].eq(counter_direction)
        & enriched["trade_opposes_structural"].astype(bool)
    )
    if bool((enriched["transition_population"] & ~enriched["transition_reference"]).any()):
        raise ValueError(f"{symbol}: transition population is not a reference subset")
    years = tuple(sorted(pd.to_numeric(enriched["year"]).astype(int).unique()))
    expected = tuple(range(start_year, end_year + 1))
    if years != expected:
        raise ValueError(f"{symbol}: expected years {expected}, found {years}")
    if enriched.duplicated(["event_id", "extended_target"]).any():
        raise ValueError(f"{symbol}: duplicate event-target keys after enrichment")
    return enriched.sort_values(
        ["extended_target", "entry_timestamp_utc", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def _population_metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    clean = frame.dropna(
        subset=[
            "extended_target_hit",
            "extended_reward_risk_stress_010",
            "observed_stressed_ev_proxy",
        ]
    )
    if clean.empty:
        return {
            "events": 0,
            "positives": 0,
            "hit_rate": math.nan,
            "mean_ev_proxy": math.nan,
            "median_stressed_rr": math.nan,
            "rr_125_breadth": math.nan,
        }
    return {
        "events": int(len(clean)),
        "positives": int(clean["extended_target_hit"].sum()),
        "hit_rate": float(clean["extended_target_hit"].mean()),
        "mean_ev_proxy": float(clean["observed_stressed_ev_proxy"].mean()),
        "median_stressed_rr": float(
            clean["extended_reward_risk_stress_010"].median()
        ),
        "rr_125_breadth": float(
            (clean["extended_reward_risk_stress_010"] >= 1.25).mean()
        ),
    }


def _block_bootstrap_ev(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {
            "bootstrap_probability_positive": math.nan,
            "bootstrap_p10": math.nan,
            "bootstrap_p50": math.nan,
            "bootstrap_p90": math.nan,
        }
    blocks = [
        group["observed_stressed_ev_proxy"].to_numpy(dtype=float)
        for _, group in frame.groupby("trade_date", sort=True)
    ]
    if not blocks:
        raise ValueError("bootstrap requires at least one trade-date block")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.empty(BOOTSTRAP_ITERATIONS, dtype=float)
    block_count = len(blocks)
    for iteration in range(BOOTSTRAP_ITERATIONS):
        selected = rng.integers(0, block_count, size=block_count)
        values = np.concatenate([blocks[index] for index in selected])
        means[iteration] = float(values.mean())
    return {
        "bootstrap_probability_positive": float((means > 0.0).mean()),
        "bootstrap_p10": float(np.quantile(means, 0.10)),
        "bootstrap_p50": float(np.quantile(means, 0.50)),
        "bootstrap_p90": float(np.quantile(means, 0.90)),
    }


def _subgroup_metrics(
    subset: pd.DataFrame,
    *,
    key: str,
    expected: tuple[Any, ...],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in expected:
        metrics = _population_metrics(subset.loc[subset[key].eq(value)])
        rows.append({key: value, **metrics})
    return rows


def evaluate_target(
    ledger: pd.DataFrame,
    *,
    target: str,
    years: tuple[int, ...],
) -> dict[str, Any]:
    frame = ledger.loc[
        ledger["extended_target"].eq(target) & ledger["year"].isin(years)
    ].copy()
    subset = frame.loc[frame["transition_population"].astype(bool)]
    reference = frame.loc[frame["transition_reference"].astype(bool)]
    metrics = _population_metrics(subset)
    reference_metrics = _population_metrics(reference)
    hit_rate = float(metrics["hit_rate"])
    reference_hit = float(reference_metrics["hit_rate"])
    mean_ev = float(metrics["mean_ev_proxy"])
    reference_ev = float(reference_metrics["mean_ev_proxy"])
    hit_lift = (
        hit_rate - reference_hit
        if np.isfinite(hit_rate) and np.isfinite(reference_hit)
        else math.nan
    )
    ev_lift = (
        mean_ev - reference_ev
        if np.isfinite(mean_ev) and np.isfinite(reference_ev)
        else math.nan
    )
    pair_metrics = _subgroup_metrics(subset, key="instrument", expected=PAIRS)
    year_metrics = _subgroup_metrics(subset, key="year", expected=years)
    event_count = int(metrics["events"])
    pair_concentration = (
        max((int(row["events"]) for row in pair_metrics), default=0) / event_count
        if event_count
        else math.nan
    )
    year_concentration = (
        max((int(row["events"]) for row in year_metrics), default=0) / event_count
        if event_count
        else math.nan
    )
    return {
        "target": target,
        "years": list(years),
        **metrics,
        "reference_events": int(reference_metrics["events"]),
        "reference_positives": int(reference_metrics["positives"]),
        "reference_hit_rate": reference_hit,
        "reference_mean_ev_proxy": reference_ev,
        "absolute_hit_rate_lift": hit_lift,
        "mean_ev_lift": ev_lift,
        "pair_event_min": min(int(row["events"]) for row in pair_metrics),
        "positive_ev_pairs": sum(
            np.isfinite(row["mean_ev_proxy"])
            and float(row["mean_ev_proxy"]) > 0.0
            for row in pair_metrics
        ),
        "positive_ev_years": sum(
            np.isfinite(row["mean_ev_proxy"])
            and float(row["mean_ev_proxy"]) > 0.0
            for row in year_metrics
        ),
        "pair_concentration": pair_concentration,
        "year_concentration": year_concentration,
        **_block_bootstrap_ev(subset),
        "pair_metrics": pair_metrics,
        "year_metrics": year_metrics,
    }


def evaluate_stage(
    ledger: pd.DataFrame,
    *,
    gate: StageGate,
) -> dict[str, Any]:
    _validate_ledger(ledger, gate.years)
    results = {
        target: evaluate_target(ledger, target=target, years=gate.years)
        for target in DIAGNOSTIC_TARGETS
    }
    primary = results[PRIMARY_TARGET]
    fixed4 = results[FIXED_4R_TARGET]
    checks = {
        "sample_events": int(primary["events"]) >= gate.min_events,
        "sample_positives": int(primary["positives"]) >= gate.min_positives,
        "pair_event_min": int(primary["pair_event_min"]) >= gate.min_pair_events,
        "pooled_ev": float(primary["mean_ev_proxy"]) > 0.0,
        "pair_ev_breadth": int(primary["positive_ev_pairs"]) == 2,
        "year_ev_breadth": (
            int(primary["positive_ev_years"]) >= gate.min_positive_years
        ),
        "hit_rate_lift": float(primary["absolute_hit_rate_lift"]) >= 0.03,
        "mean_ev_lift": float(primary["mean_ev_lift"]) >= 0.15,
        "median_rr": float(primary["median_stressed_rr"]) >= 2.50,
        "rr_breadth": float(primary["rr_125_breadth"]) >= 0.90,
        "pair_concentration": float(primary["pair_concentration"]) <= 0.70,
        "year_concentration": float(primary["year_concentration"]) <= 0.50,
        "bootstrap_probability": (
            float(primary["bootstrap_probability_positive"])
            >= gate.min_bootstrap_probability
        ),
        "bootstrap_p10": float(primary["bootstrap_p10"]) > gate.min_bootstrap_p10,
        "fixed4_corroboration": float(fixed4["mean_ev_proxy"]) > 0.0,
    }
    failures = [name for name, passed in checks.items() if not passed]
    if gate.name == "confirmation":
        decision = (
            "PASS_WEEKLY_TRANSITION_CONFIRMATION_OPEN_FINAL_HOLDOUT"
            if not failures
            else "FAIL_WEEKLY_TRANSITION_CONFIRMATION_STOP"
        )
    elif gate.name == "final":
        decision = (
            "PASS_WEEKLY_TRANSITION_FINAL_STAGE"
            if not failures
            else "FAIL_WEEKLY_TRANSITION_FINAL_HOLDOUT_STOP"
        )
    else:
        raise ValueError(f"unknown gate stage: {gate.name}")
    return {
        "stage": gate.name,
        "decision": decision,
        "years": list(gate.years),
        "protected_later_years_opened": gate.name == "final",
        "passed": not failures,
        "checks": checks,
        "failed_gates": failures,
        "primary_target": PRIMARY_TARGET,
        "results": results,
    }


def evaluate_combined(ledger: pd.DataFrame) -> dict[str, Any]:
    _validate_ledger(ledger, COMBINED_YEARS)
    results = {
        target: evaluate_target(ledger, target=target, years=COMBINED_YEARS)
        for target in DIAGNOSTIC_TARGETS
    }
    primary = results[PRIMARY_TARGET]
    fixed4 = results[FIXED_4R_TARGET]
    checks = {
        "sample_events": int(primary["events"]) >= 80,
        "pooled_ev": float(primary["mean_ev_proxy"]) >= 0.10,
        "pair_ev_breadth": int(primary["positive_ev_pairs"]) == 2,
        "year_ev_breadth": int(primary["positive_ev_years"]) >= 4,
        "bootstrap_probability": (
            float(primary["bootstrap_probability_positive"]) >= 0.95
        ),
        "fixed4_corroboration": float(fixed4["mean_ev_proxy"]) > 0.0,
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {
        "stage": "combined",
        "years": list(COMBINED_YEARS),
        "passed": not failures,
        "checks": checks,
        "failed_gates": failures,
        "primary_target": PRIMARY_TARGET,
        "results": results,
    }


def final_programme_decision(
    final_stage: dict[str, Any],
    combined: dict[str, Any],
) -> str:
    if bool(final_stage["passed"]) and bool(combined["passed"]):
        return "PASS_WEEKLY_TRANSITION_FINAL_HOLDOUT_OPEN_EXECUTION_PNL"
    return "FAIL_WEEKLY_TRANSITION_FINAL_HOLDOUT_STOP"


def _validate_ledger(ledger: pd.DataFrame, years: tuple[int, ...]) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "extended_target",
        "extended_target_hit",
        "extended_reward_risk_stress_010",
        "observed_stressed_ev_proxy",
        "transition_population",
        "transition_reference",
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing weekly-transition ledger columns: {missing}")
    pairs = tuple(sorted(ledger["instrument"].unique()))
    if pairs != PAIRS:
        raise ValueError(f"expected pairs {PAIRS}, found {pairs}")
    found_years = tuple(sorted(pd.to_numeric(ledger["year"]).astype(int).unique()))
    if found_years != years:
        raise ValueError(f"expected years {years}, found {found_years}")
    present_targets = set(ledger["extended_target"].unique())
    missing_targets = sorted(set(DIAGNOSTIC_TARGETS) - present_targets)
    if missing_targets:
        raise ValueError(f"missing transition targets: {missing_targets}")
    if ledger.duplicated(["event_id", "extended_target"]).any():
        raise ValueError("duplicate weekly-transition event-target keys")
