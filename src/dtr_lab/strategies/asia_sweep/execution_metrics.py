from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import (
    BOOTSTRAP_ITERATIONS,
    BOOTSTRAP_SEED,
    ENTRY_VARIANTS,
)

PASS_DECISION = "PASS_DISCOVERY_FREEZE_AUTHORIZE_EXECUTION_VALIDATION_2020_2021"
FAIL_DECISION = "FAIL_DISCOVERY_STOP_BEFORE_EXECUTION_VALIDATION"


def _filled(orders: pd.DataFrame) -> pd.DataFrame:
    frame = orders.loc[orders["filled"].astype(bool)].copy()
    if not frame.empty:
        frame["entry_timestamp_utc"] = pd.to_datetime(
            frame["entry_timestamp_utc"], utc=True, errors="raise"
        )
        frame = frame.sort_values(
            ["entry_timestamp_utc", "instrument", "event_id"], kind="mergesort"
        )
    return frame


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return math.nan
    equity = values.astype(float).cumsum()
    peak = equity.cummax()
    return float((peak - equity).max())


def calendar_week_bootstrap(
    trades: pd.DataFrame,
    *,
    r_column: str = "net_r_0_0",
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float]:
    if trades.empty:
        return {
            "iterations": float(iterations),
            "probability_expectancy_positive": math.nan,
            "lower_95": math.nan,
            "upper_95": math.nan,
        }
    blocks = (
        trades.groupby("week_key", as_index=False)
        .agg(block_r=(r_column, "sum"), block_n=(r_column, "size"))
        .sort_values("week_key")
    )
    rng = np.random.default_rng(seed)
    estimates = np.empty(iterations, dtype=float)
    block_r = blocks["block_r"].to_numpy(dtype=float)
    block_n = blocks["block_n"].to_numpy(dtype=float)
    for index in range(iterations):
        sampled = rng.integers(0, len(blocks), size=len(blocks))
        estimates[index] = block_r[sampled].sum() / block_n[sampled].sum()
    return {
        "iterations": float(iterations),
        "probability_expectancy_positive": float((estimates > 0).mean()),
        "lower_95": float(np.quantile(estimates, 0.025)),
        "upper_95": float(np.quantile(estimates, 0.975)),
    }


def _group_table(trades: pd.DataFrame, column: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=[column, "trade_count", "net_r", "expectancy"])
    return (
        trades.groupby(column, as_index=False)
        .agg(
            trade_count=("net_r_0_0", "size"),
            net_r=("net_r_0_0", "sum"),
            expectancy=("net_r_0_0", "mean"),
            stress_0_10_expectancy=("net_r_0_1", "mean"),
            win_rate=("net_r_0_0", lambda values: float((values > 0).mean())),
        )
        .sort_values(column)
    )


def _probability_quintiles(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    frame = trades.copy()
    frame["probability_quintile"] = 0
    for _, indices in frame.groupby("year").groups.items():
        group = frame.loc[list(indices)].sort_values(["prediction", "event_id"])
        ranks = group["prediction"].rank(method="first", pct=True)
        frame.loc[group.index, "probability_quintile"] = (
            np.ceil(ranks * 5).clip(1, 5).astype(int).to_numpy()
        )
    return _group_table(frame, "probability_quintile")


def summarize_variant(orders: pd.DataFrame, variant: str) -> dict[str, Any]:
    variant_orders = orders.loc[orders["variant"].eq(variant)].copy()
    trades = _filled(variant_orders)
    base = trades["net_r_0_0"].astype(float)
    stress = trades["net_r_0_1"].astype(float)
    severe = trades["net_r_0_25"].astype(float)
    drawdown = max_drawdown(base)
    net_r = float(base.sum()) if len(base) else math.nan
    expectancy = float(base.mean()) if len(base) else math.nan
    return_drawdown = (
        float(net_r / drawdown)
        if np.isfinite(drawdown) and drawdown > 0
        else math.nan
    )
    pair_table = _group_table(trades, "instrument")
    year_table = _group_table(trades, "year")
    bootstrap = calendar_week_bootstrap(trades)
    positive_pairs = int((pair_table["expectancy"] > 0).sum()) if len(pair_table) else 0
    positive_years = int((year_table["expectancy"] > 0).sum()) if len(year_table) else 0
    per_pair_min = int(pair_table["trade_count"].min()) if len(pair_table) else 0
    median_annual = float(year_table["expectancy"].median()) if len(year_table) else math.nan
    largest_winner_share = math.nan
    positive = base.loc[base > 0]
    if len(positive) and net_r > 0:
        largest_winner_share = float(positive.max() / net_r)
    predicates = {
        "at_least_150_filled_trades": len(trades) >= 150,
        "at_least_50_fills_per_pair": per_pair_min >= 50,
        "expectancy_above_0_05r": bool(np.isfinite(expectancy) and expectancy > 0.05),
        "median_annual_expectancy_positive": bool(
            np.isfinite(median_annual) and median_annual > 0
        ),
        "four_of_five_years_positive": positive_years >= 4,
        "both_pairs_positive": positive_pairs == 2,
        "max_drawdown_below_20r": bool(
            np.isfinite(drawdown) and drawdown < 20.0
        ),
        "return_drawdown_at_least_1_50": bool(
            np.isfinite(return_drawdown) and return_drawdown >= 1.50
        ),
        "bootstrap_probability_positive_at_least_95pct": bool(
            bootstrap["probability_expectancy_positive"] >= 0.95
        ),
        "positive_under_0_10_pip_stress": bool(
            len(stress) and float(stress.mean()) > 0
        ),
    }
    metrics = {
        "attempted_orders": int(len(variant_orders)),
        "filled_trades": int(len(trades)),
        "unfilled_orders": int(variant_orders["status"].eq("UNFILLED").sum()),
        "invalid_geometry": int(
            variant_orders["status"].eq("INVALID_GEOMETRY").sum()
        ),
        "net_r": net_r,
        "expectancy": expectancy,
        "median_trade_r": float(base.median()) if len(base) else math.nan,
        "win_rate": float((base > 0).mean()) if len(base) else math.nan,
        "max_drawdown_r": drawdown,
        "return_drawdown": return_drawdown,
        "stress_0_10_expectancy": float(stress.mean()) if len(stress) else math.nan,
        "stress_0_25_expectancy": float(severe.mean()) if len(severe) else math.nan,
        "median_initial_reward_risk": (
            float(trades["reward_risk"].median()) if len(trades) else math.nan
        ),
        "positive_pairs": positive_pairs,
        "positive_years": positive_years,
        "median_annual_expectancy": median_annual,
        "largest_winner_share_of_net_r": largest_winner_share,
        **bootstrap,
    }
    return {
        "variant": variant,
        "eligible": all(predicates.values()),
        "metrics": metrics,
        "predicates": predicates,
        "trades": trades,
        "pair_table": pair_table,
        "year_table": year_table,
        "weekday_table": _group_table(trades, "weekday"),
        "side_table": _group_table(trades, "side"),
        "exit_table": _group_table(trades, "exit_reason"),
        "probability_table": _probability_quintiles(trades),
    }


def choose_discovery_variant(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    by_variant = {summary["variant"]: summary for summary in summaries}
    baseline = by_variant["MKT_NEXT_OPEN"]
    selected: dict[str, Any] | None = None
    if baseline["eligible"]:
        selected = baseline
    else:
        challengers: list[dict[str, Any]] = []
        baseline_metrics = baseline["metrics"]
        for variant in ("LIMIT_ASIAN_BOUNDARY", "LIMIT_HALF_RETRACE"):
            challenger = by_variant[variant]
            metrics = challenger["metrics"]
            improves = (
                challenger["eligible"]
                and metrics["expectancy"] >= baseline_metrics["expectancy"] + 0.05
                and metrics["return_drawdown"]
                >= baseline_metrics["return_drawdown"] + 0.50
            )
            if improves:
                challengers.append(challenger)
        challengers.sort(
            key=lambda value: (
                value["metrics"]["max_drawdown_r"],
                -value["metrics"]["filled_trades"],
                ENTRY_VARIANTS.index(value["variant"]),
            )
        )
        selected = challengers[0] if challengers else None
    return {
        "decision": PASS_DECISION if selected else FAIL_DECISION,
        "selected_variant": selected["variant"] if selected else None,
        "baseline_variant": baseline["variant"],
    }


def write_discovery_outputs(
    output_directory: Path,
    orders: pd.DataFrame,
) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=True)
    orders.to_csv(output_directory / "execution_orders.csv", index=False)
    summaries = [summarize_variant(orders, variant) for variant in ENTRY_VARIANTS]
    selection = choose_discovery_variant(summaries)
    summary_rows = []
    for summary in summaries:
        variant = summary["variant"]
        summary["trades"].to_csv(
            output_directory / f"filled_trades_{variant}.csv", index=False
        )
        for key in (
            "pair_table",
            "year_table",
            "weekday_table",
            "side_table",
            "exit_table",
            "probability_table",
        ):
            summary[key].to_csv(
                output_directory / f"{key}_{variant}.csv", index=False
            )
        summary_rows.append(
            {
                "variant": variant,
                "eligible": summary["eligible"],
                **summary["metrics"],
                **{
                    f"gate_{name}": passed
                    for name, passed in summary["predicates"].items()
                },
            }
        )
    pd.DataFrame(summary_rows).to_csv(
        output_directory / "variant_summary.csv", index=False
    )
    payload = {
        "programme": "ASIAN_SWEEP_EXECUTION_V2",
        "stage": "DISCOVERY_2015_2019",
        "prediction_provenance": "OUT_OF_FOLD_T5_HGB",
        "variants": [
            {
                "variant": summary["variant"],
                "eligible": summary["eligible"],
                "metrics": summary["metrics"],
                "predicates": summary["predicates"],
            }
            for summary in summaries
        ],
        **selection,
        "later_execution_partitions_opened": False,
        "continuation_model_tested": False,
        "strategy_deployment_authorized": False,
    }
    (output_directory / "execution_discovery_decision.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
