from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.staged_reversal import (
    POLICY_ORDER,
    maximum_drawdown,
    select_inner_policy,
    summarize_policy,
)

RANDOM_SEED = 20260726


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _bootstrap_probability_positive(
    trades: pd.DataFrame,
    *,
    iterations: int = 5000,
) -> float:
    if trades.empty:
        return math.nan
    rng = np.random.default_rng(RANDOM_SEED)
    week_groups = {
        key: group["net_r_0_1"].to_numpy(dtype=float)
        for key, group in trades.groupby("week_key", sort=True)
    }
    keys = np.array(list(week_groups), dtype=object)
    positive = 0
    for _ in range(iterations):
        sampled = rng.choice(keys, size=len(keys), replace=True)
        values = np.concatenate([week_groups[key] for key in sampled])
        positive += int(float(values.mean()) > 0.0)
    return positive / iterations


def _contribution_concentration(trades: pd.DataFrame, column: str) -> float:
    net = trades.groupby(column)["net_r_0_1"].sum()
    positive = net.loc[net.gt(0.0)]
    if positive.empty or positive.sum() <= 0.0:
        return math.inf
    return float(positive.max() / positive.sum())


def _run_nested_selection(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    heldout_frames: list[pd.DataFrame] = []
    rows: list[dict[str, Any]] = []
    for heldout_year in range(2015, 2020):
        training = trades.loc[trades["year"].ne(heldout_year)].copy()
        selected_policy = select_inner_policy(training)
        heldout = pd.DataFrame(columns=trades.columns)
        if selected_policy is not None:
            heldout = trades.loc[
                trades["year"].eq(heldout_year)
                & trades["policy"].eq(selected_policy)
            ].copy()
            heldout["heldout_year"] = heldout_year
            heldout["selected_policy"] = selected_policy
            heldout_frames.append(heldout)
        rows.append(
            {
                "heldout_year": heldout_year,
                "selected_policy": selected_policy,
                "heldout_trades": int(len(heldout)),
                "heldout_net_r_0_1": (
                    float(heldout["net_r_0_1"].sum()) if len(heldout) else math.nan
                ),
                "heldout_expectancy_0_1": (
                    float(heldout["net_r_0_1"].mean()) if len(heldout) else math.nan
                ),
            }
        )
    pooled = (
        pd.concat(heldout_frames, ignore_index=True)
        if heldout_frames
        else pd.DataFrame(columns=list(trades.columns) + ["heldout_year", "selected_policy"])
    )
    return pooled, pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    files = sorted(args.inputs.rglob("staged_reversal_trades.csv"))
    if len(files) != 2:
        raise ValueError(f"expected two staged pair ledgers, found {files}")
    trades = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    if tuple(sorted(trades["instrument"].unique())) != ("EURUSD", "GBPUSD"):
        raise ValueError("staged reversal ledger must contain both pairs")
    if trades.duplicated(["policy", "instrument", "trade_date"]).any():
        raise ValueError("staged reversal daily lockout keys must be unique")
    summaries = pd.DataFrame(
        [summarize_policy(group) for _, group in trades.groupby("policy", sort=False)]
    )
    summaries["policy_order"] = summaries["policy"].map(
        {policy: index for index, policy in enumerate(POLICY_ORDER)}
    )
    summaries = summaries.sort_values("policy_order").reset_index(drop=True)
    pooled, folds = _run_nested_selection(trades)
    selected_counts = Counter(folds["selected_policy"].dropna().astype(str))
    modal_policy = None
    modal_count = 0
    if selected_counts:
        modal_policy, modal_count = sorted(
            selected_counts.items(),
            key=lambda item: (-item[1], POLICY_ORDER.index(item[0])),
        )[0]

    if pooled.empty:
        pooled_metrics = {
            "trades": 0,
            "net_r_0_1": math.nan,
            "expectancy_0_1": math.nan,
            "expectancy_0_25": math.nan,
            "maximum_drawdown_0_1": math.nan,
            "return_drawdown_0_1": math.nan,
            "positive_pairs": 0,
            "positive_years": 0,
            "pair_concentration": math.inf,
            "year_concentration": math.inf,
            "bootstrap_probability_positive": math.nan,
        }
    else:
        ordered = pooled.sort_values(
            ["trade_date", "instrument", "event_id"], kind="mergesort"
        )
        net_r = float(ordered["net_r_0_1"].sum())
        drawdown = maximum_drawdown(ordered["net_r_0_1"].to_numpy(dtype=float))
        pooled_metrics = {
            "trades": int(len(ordered)),
            "net_r_0_1": net_r,
            "expectancy_0_1": float(ordered["net_r_0_1"].mean()),
            "expectancy_0_25": float(ordered["net_r_0_25"].mean()),
            "maximum_drawdown_0_1": drawdown,
            "return_drawdown_0_1": (
                net_r / drawdown if drawdown > 0.0 else math.nan
            ),
            "positive_pairs": int(
                ordered.groupby("instrument")["net_r_0_1"].sum().gt(0.0).sum()
            ),
            "positive_years": int(
                ordered.groupby("year")["net_r_0_1"].sum().gt(0.0).sum()
            ),
            "pair_concentration": _contribution_concentration(
                ordered, "instrument"
            ),
            "year_concentration": _contribution_concentration(ordered, "year"),
            "bootstrap_probability_positive": _bootstrap_probability_positive(
                ordered
            ),
        }
    gates = {
        "modal_policy": modal_policy is not None and modal_count >= 3,
        "sample_size": pooled_metrics["trades"] >= 250,
        "expectancy_010": pooled_metrics["expectancy_0_1"] > 0.0,
        "return_drawdown": pooled_metrics["return_drawdown_0_1"] >= 1.5,
        "pair_breadth": pooled_metrics["positive_pairs"] == 2,
        "year_breadth": pooled_metrics["positive_years"] >= 4,
        "concentration": pooled_metrics["pair_concentration"] <= 0.45
        and pooled_metrics["year_concentration"] <= 0.45,
        "drawdown": pooled_metrics["maximum_drawdown_0_1"] <= 12.0,
        "stress_025": pooled_metrics["expectancy_0_25"] > 0.0,
        "bootstrap": pooled_metrics["bootstrap_probability_positive"] >= 0.90,
    }
    decision_name = (
        "PASS_STAGED_REVERSAL_DISCOVERY_AUTHORIZE_VALIDATION"
        if all(gates.values())
        else "FAIL_STAGED_REVERSAL_DISCOVERY_STOP_BEFORE_VALIDATION"
    )
    decision = {
        "programme": "ASIAN_SWEEP_STAGED_REVERSAL_V6_4",
        "decision": decision_name,
        "modal_policy": modal_policy,
        "modal_policy_fold_count": modal_count,
        "pooled_metrics": pooled_metrics,
        "gates": gates,
        "development_years": [2015, 2016, 2017, 2018, 2019],
        "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "validation_opened": False,
    }
    trades.to_csv(args.out / "staged_reversal_policy_ledger.csv", index=False)
    summaries.to_csv(args.out / "staged_reversal_policy_summary.csv", index=False)
    folds.to_csv(args.out / "staged_reversal_outer_folds.csv", index=False)
    pooled.to_csv(args.out / "staged_reversal_oof_trades.csv", index=False)
    (args.out / "staged_reversal_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
