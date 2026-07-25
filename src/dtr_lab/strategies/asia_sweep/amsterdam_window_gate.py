from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PAIRS = ("EURUSD", "GBPUSD")
YEARS = (2020, 2021)
BOOTSTRAP_ITERATIONS = 10_000
PERMUTATION_ITERATIONS = 10_000
SEED = 20260725


def _date_block_bootstrap(frame: pd.DataFrame) -> dict[str, float | int]:
    grouped = frame.groupby("trade_date", sort=True)["effect"].agg(["sum", "count"])
    block_sums = grouped["sum"].to_numpy(float)
    block_counts = grouped["count"].to_numpy(np.int64)
    rng = np.random.default_rng(SEED)
    means = np.empty(BOOTSTRAP_ITERATIONS, dtype=float)
    blocks = len(grouped)
    for start in range(0, BOOTSTRAP_ITERATIONS, 512):
        end = min(start + 512, BOOTSTRAP_ITERATIONS)
        selected = rng.integers(0, blocks, size=(end - start, blocks))
        means[start:end] = (
            block_sums[selected].sum(axis=1)
            / block_counts[selected].sum(axis=1)
        )
    return {
        "blocks": blocks,
        "iterations": BOOTSTRAP_ITERATIONS,
        "lo95": float(np.quantile(means, 0.025)),
        "hi95": float(np.quantile(means, 0.975)),
        "probability_positive": float(np.mean(means > 0)),
    }


def _date_clustered_sign_permutation(frame: pd.DataFrame) -> dict[str, float | int]:
    grouped = frame.groupby("trade_date", sort=True)["effect"].agg(["sum", "count"])
    sums = grouped["sum"].to_numpy(float)
    counts = grouped["count"].to_numpy(np.int64)
    observed = float(sums.sum() / counts.sum())
    rng = np.random.default_rng(SEED + 1)
    simulated = np.empty(PERMUTATION_ITERATIONS, dtype=float)
    for start in range(0, PERMUTATION_ITERATIONS, 1024):
        end = min(start + 1024, PERMUTATION_ITERATIONS)
        signs = rng.choice((-1.0, 1.0), size=(end - start, len(sums)))
        simulated[start:end] = (signs * sums).sum(axis=1) / counts.sum()
    return {
        "iterations": PERMUTATION_ITERATIONS,
        "observed_mean": observed,
        "one_sided_p_value": float(
            (1 + np.sum(simulated >= observed)) / (PERMUTATION_ITERATIONS + 1)
        ),
    }


def _attribution(frame: pd.DataFrame, column: str) -> list[dict[str, object]]:
    return [
        {
            column: str(key),
            "events": int(len(group)),
            "mean_effect": float(group["effect"].mean()),
            "positive": bool(group["effect"].mean() > 0),
        }
        for key, group in frame.groupby(column, sort=True)
    ]


def build_decision(inputs: Path) -> tuple[dict[str, object], pd.DataFrame]:
    files = sorted(inputs.rglob("matched_events.csv"))
    if not files:
        raise RuntimeError("no matched-event ledgers found")
    matched = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    observed_pairs = set(matched["instrument"].astype(str))
    if observed_pairs != set(PAIRS):
        raise RuntimeError(
            f"expected pair evidence {sorted(PAIRS)}, observed {sorted(observed_pairs)}"
        )
    if matched["event_id"].duplicated().any():
        raise RuntimeError("duplicate event IDs in pooled ledger")
    matched["trade_date"] = matched["trade_date"].astype(str)
    matched["year"] = pd.to_numeric(matched["year"], errors="raise").astype(int)

    bootstrap = _date_block_bootstrap(matched)
    permutation = _date_clustered_sign_permutation(matched)
    pair_rows = _attribution(matched, "instrument")
    year_rows = _attribution(matched, "year")
    pair_counts = matched.groupby("instrument").size()
    mean_effect = float(matched["effect"].mean())
    positive_pairs = sum(bool(row["positive"]) for row in pair_rows)
    positive_years = sum(bool(row["positive"]) for row in year_rows)

    gates = {
        "minimum_40_matched_events": len(matched) >= 40,
        "both_pairs_minimum_15_events": len(pair_counts) == 2
        and bool((pair_counts >= 15).all()),
        "no_pair_over_70_percent": float(pair_counts.max() / len(matched)) <= 0.70,
        "mean_effect_at_least_0_02_range": mean_effect >= 0.02,
        "bootstrap_lower_bound_positive": float(bootstrap["lo95"]) > 0,
        "permutation_p_no_greater_0_05": float(
            permutation["one_sided_p_value"]
        )
        <= 0.05,
        "both_pairs_positive": positive_pairs == 2,
        "both_years_positive": set(matched["year"].unique()) == set(YEARS)
        and positive_years == 2,
    }
    passed = all(gates.values())
    decision = {
        "programme": "ASIAN_SWEEP_AMSTERDAM_0900_1000_V1",
        "stage": "UNTOUCHED_CONFIRMATION_2020_2021",
        "decision": (
            "PASS_AUTHORIZE_EXECUTION_PREREGISTRATION"
            if passed
            else "FAIL_STOP_AMSTERDAM_WINDOW_FORMULATION"
        ),
        "window_timezone": "Europe/Amsterdam",
        "window_start": "09:00:00",
        "window_end_exclusive": "10:00:00",
        "pairs": list(PAIRS),
        "matched_events": int(len(matched)),
        "matched_controls": int(len(matched) * 5),
        "mean_event_return": float(matched["event_return"].mean()),
        "mean_control_return": float(matched["control_mean_return"].mean()),
        "mean_effect": mean_effect,
        "bootstrap": bootstrap,
        "permutation": permutation,
        "pair_attribution": pair_rows,
        "year_attribution": year_rows,
        "gates": gates,
        "passed": passed,
        "strategy_pnl_calculated": False,
        "later_partitions_opened": False,
    }
    return decision, matched


def write_decision(
    output: Path, decision: dict[str, object], matched: pd.DataFrame
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    matched.to_csv(output / "pooled_matched_events.csv", index=False)
    (output / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
