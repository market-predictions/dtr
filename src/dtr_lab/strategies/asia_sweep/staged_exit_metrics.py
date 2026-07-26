from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_metrics import (
    calendar_week_bootstrap,
    max_drawdown,
)
from dtr_lab.strategies.asia_sweep.staged_exit_simulator import STAGED_VARIANTS

PASS_DECISION = "PASS_STAGED_EXIT_DISCOVERY_AUTHORIZE_2020_2021_VALIDATION"
FAIL_DECISION = "FAIL_STAGED_EXIT_DISCOVERY_STOP_BEFORE_VALIDATION"


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
            tp1_hit_rate=("tp1_hit", "mean"),
            tp2_hit_rate=("tp2_hit", "mean"),
            tp1_leg_expectancy=("tp1_leg_r_0_0", "mean"),
            runner_leg_expectancy=("runner_leg_r_0_0", "mean"),
        )
        .sort_values(column)
    )


def summarize_staged_variant(orders: pd.DataFrame, variant: str) -> dict[str, Any]:
    variant_orders = orders.loc[orders["staged_variant"].eq(variant)].copy()
    trades = _filled(variant_orders)
    base = trades["net_r_0_0"].astype(float)
    stress = trades["net_r_0_1"].astype(float)
    severe = trades["net_r_0_25"].astype(float)
    net_r = float(base.sum()) if len(base) else math.nan
    expectancy = float(base.mean()) if len(base) else math.nan
    drawdown = max_drawdown(base)
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
    minimum_pair_trades = int(pair_table["trade_count"].min()) if len(pair_table) else 0
    median_annual = float(year_table["expectancy"].median()) if len(year_table) else math.nan
    predicates = {
        "at_least_150_filled_trades": len(trades) >= 150,
        "at_least_50_fills_per_pair": minimum_pair_trades >= 50,
        "expectancy_above_0_05r": bool(np.isfinite(expectancy) and expectancy > 0.05),
        "median_annual_expectancy_positive": bool(
            np.isfinite(median_annual) and median_annual > 0
        ),
        "four_of_five_years_positive": positive_years >= 4,
        "both_pairs_positive": positive_pairs == 2,
        "max_drawdown_below_20r": bool(np.isfinite(drawdown) and drawdown < 20.0),
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
        "positive_pairs": positive_pairs,
        "positive_years": positive_years,
        "median_annual_expectancy": median_annual,
        "tp1_hit_rate": float(trades["tp1_hit"].mean()) if len(trades) else math.nan,
        "tp2_hit_rate": float(trades["tp2_hit"].mean()) if len(trades) else math.nan,
        "tp1_leg_expectancy": (
            float(trades["tp1_leg_r_0_0"].mean()) if len(trades) else math.nan
        ),
        "runner_leg_expectancy": (
            float(trades["runner_leg_r_0_0"].mean()) if len(trades) else math.nan
        ),
        "tp1_leg_net_r": (
            float(0.5 * trades["tp1_leg_r_0_0"].sum()) if len(trades) else math.nan
        ),
        "runner_leg_net_r": (
            float(0.5 * trades["runner_leg_r_0_0"].sum()) if len(trades) else math.nan
        ),
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
        "tp1_exit_table": _group_table(trades, "tp1_exit_reason"),
        "runner_exit_table": _group_table(trades, "runner_exit_reason"),
    }


def choose_staged_variant(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    by_variant = {summary["variant"]: summary for summary in summaries}
    baseline = by_variant["MIDPOINT_50_RUNNER_ORIGINAL_STOP"]
    selected: dict[str, Any] | None = baseline if baseline["eligible"] else None
    if selected is None:
        challenger = by_variant["MIDPOINT_50_RUNNER_BE"]
        base_metrics = baseline["metrics"]
        challenger_metrics = challenger["metrics"]
        improves = (
            challenger["eligible"]
            and challenger_metrics["expectancy"] >= base_metrics["expectancy"] + 0.03
            and challenger_metrics["return_drawdown"]
            >= base_metrics["return_drawdown"] + 0.30
        )
        selected = challenger if improves else None
    return {
        "decision": PASS_DECISION if selected else FAIL_DECISION,
        "selected_variant": selected["variant"] if selected else None,
        "baseline_variant": baseline["variant"],
    }


def write_staged_discovery_outputs(
    output_directory: Path,
    orders: pd.DataFrame,
) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=True)
    orders.to_csv(output_directory / "staged_exit_orders.csv", index=False)
    summaries = [summarize_staged_variant(orders, variant) for variant in STAGED_VARIANTS]
    selection = choose_staged_variant(summaries)
    summary_rows: list[dict[str, Any]] = []
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
            "tp1_exit_table",
            "runner_exit_table",
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
        output_directory / "staged_variant_summary.csv", index=False
    )
    payload = {
        "programme": "ASIAN_SWEEP_STAGED_EXIT_V3",
        "stage": "DISCOVERY_2015_2019",
        "entry_provenance": "FROZEN_MKT_NEXT_OPEN_LEDGER_RUN_30192167763",
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
        "strategy_deployment_authorized": False,
    }
    (output_directory / "staged_exit_discovery_decision.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
