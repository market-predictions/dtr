from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PAIR_SPECS = {
    "EURUSD": "usd_europe",
    "GBPUSD": "usd_europe",
    "USDCHF": "usd_europe",
    "AUDUSD": "usd_commodity",
    "NZDUSD": "usd_commodity",
    "USDCAD": "usd_commodity",
    "USDJPY": "jpy",
    "EURJPY": "jpy",
    "GBPJPY": "jpy",
    "EURGBP": "europe_cross",
}
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
    p_value = float(
        (1 + np.sum(simulated >= observed)) / (PERMUTATION_ITERATIONS + 1)
    )
    return {
        "iterations": PERMUTATION_ITERATIONS,
        "observed_mean": observed,
        "one_sided_p_value": p_value,
    }


def _attribution(frame: pd.DataFrame, column: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key, group in frame.groupby(column, sort=True):
        rows.append(
            {
                column: str(key),
                "events": int(len(group)),
                "mean_effect": float(group["effect"].mean()),
                "positive": bool(group["effect"].mean() > 0),
            }
        )
    return rows


def build_decision(inputs: Path) -> tuple[dict[str, object], pd.DataFrame]:
    files = sorted(inputs.rglob("matched_events.csv"))
    if not files:
        raise RuntimeError("no matched event ledgers found")
    frames = [pd.read_csv(path) for path in files]
    matched = pd.concat(frames, ignore_index=True)
    observed_pairs = set(matched["instrument"].astype(str))
    missing_pairs = sorted(set(PAIR_SPECS) - observed_pairs)
    if missing_pairs:
        raise RuntimeError(f"missing pair evidence: {missing_pairs}")
    if matched["event_id"].duplicated().any():
        raise RuntimeError("duplicate event IDs in pooled ledger")
    matched["trade_date"] = matched["trade_date"].astype(str)
    bootstrap = _date_block_bootstrap(matched)
    permutation = _date_clustered_sign_permutation(matched)
    pair_rows = _attribution(matched, "instrument")
    factor_rows = _attribution(matched, "factor_block")
    mean_effect = float(matched["effect"].mean())
    positive_pairs = sum(bool(row["positive"]) for row in pair_rows)
    positive_factors = sum(bool(row["positive"]) for row in factor_rows)
    pair_counts = matched.groupby("instrument").size()
    factor_counts = matched.groupby("factor_block").size()
    date_counts = matched.groupby("trade_date").size()
    gates = {
        "minimum_400_matched_events": len(matched) >= 400,
        "minimum_8_pairs_with_20_events": int((pair_counts >= 20).sum()) >= 8,
        "all_4_factor_blocks_with_40_events": len(factor_counts) == 4
        and bool((factor_counts >= 40).all()),
        "no_pair_over_25_percent": float(pair_counts.max() / len(matched)) <= 0.25,
        "no_date_over_10_percent": float(date_counts.max() / len(matched)) <= 0.10,
        "mean_effect_at_least_0_02_range": mean_effect >= 0.02,
        "bootstrap_lower_bound_positive": float(bootstrap["lo95"]) > 0,
        "permutation_p_no_greater_0_05": float(
            permutation["one_sided_p_value"]
        )
        <= 0.05,
        "positive_at_least_7_pairs": positive_pairs >= 7,
        "positive_at_least_3_factor_blocks": positive_factors >= 3,
    }
    decision = {
        "programme": "ASIAN_SWEEP_FX_TEN_PAIR_V1",
        "stage": "DISCOVERY_2015_2019",
        "decision": (
            "PASS_DISCOVERY_AUTHORIZE_2020_2021_MECHANISM_VALIDATION"
            if all(gates.values())
            else "FAIL_DISCOVERY_STOP_OR_REDESIGN_BEFORE_VALIDATION"
        ),
        "matched_events": int(len(matched)),
        "matched_controls": int(len(matched) * 5),
        "mean_event_return": float(matched["event_return"].mean()),
        "mean_control_return": float(matched["control_mean_return"].mean()),
        "mean_effect": mean_effect,
        "bootstrap": bootstrap,
        "permutation": permutation,
        "positive_pairs": positive_pairs,
        "positive_factor_blocks": positive_factors,
        "pair_attribution": pair_rows,
        "factor_attribution": factor_rows,
        "gates": gates,
        "passed": all(gates.values()),
        "strategy_pnl_calculated": False,
        "holdout_2022_2025_opened": False,
    }
    return decision, matched


def write_decision(
    output: Path, decision: dict[str, object], matched: pd.DataFrame
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    matched.to_csv(output / "pooled_matched_events.csv", index=False)
    (output / "discovery_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
