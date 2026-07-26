from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.runner_optimization_metrics import (
    max_drawdown,
    summarize_trades,
)
from dtr_lab.strategies.asia_sweep.runner_optimization_simulator import (
    EXIT_HOURS,
    STOP_POLICIES,
    TARGET_KINDS,
    runner_policy_manifest,
)

PASS_DECISION = "PASS_RUNNER_DISCOVERY_FREEZE_AUTHORIZE_2020_2021_VALIDATION"
FAIL_DECISION = "FAIL_RUNNER_DISCOVERY_STOP_BEFORE_VALIDATION"


def _policy_complexity(policy: pd.Series | dict[str, Any]) -> tuple[int, int, int]:
    return (
        TARGET_KINDS.index(str(policy["target_kind"])),
        EXIT_HOURS.index(int(policy["exit_hour"])),
        STOP_POLICIES.index(str(policy["stop_policy"])),
    )


def _fast_summary(trades: pd.DataFrame) -> dict[str, Any]:
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
    pair_table = (
        trades.groupby("instrument", as_index=False)
        .agg(trade_count=("net_r_0_0", "size"), expectancy=("net_r_0_0", "mean"))
        .sort_values("instrument")
    )
    year_table = (
        trades.groupby("year", as_index=False)
        .agg(trade_count=("net_r_0_0", "size"), expectancy=("net_r_0_0", "mean"))
        .sort_values("year")
    )
    return {
        "trade_count": int(len(trades)),
        "net_r": net_r,
        "expectancy": expectancy,
        "stress_0_10_expectancy": float(stress.mean()) if len(stress) else math.nan,
        "stress_0_25_expectancy": float(severe.mean()) if len(severe) else math.nan,
        "max_drawdown_r": drawdown,
        "return_drawdown": return_drawdown,
        "positive_pairs": int((pair_table["expectancy"] > 0).sum()),
        "positive_years": int((year_table["expectancy"] > 0).sum()),
        "median_annual_expectancy": (
            float(year_table["expectancy"].median()) if len(year_table) else math.nan
        ),
        "minimum_pair_trades": (
            int(pair_table["trade_count"].min()) if len(pair_table) else 0
        ),
        "tp1_hit_rate": float(trades["tp1_hit"].astype(bool).mean()) if len(trades) else math.nan,
        "runner_target_hit_rate": (
            float(trades["runner_target_hit"].astype(bool).mean())
            if len(trades)
            else math.nan
        ),
        "tp1_leg_expectancy": (
            float(trades["tp1_leg_r_0_0"].mean()) if len(trades) else math.nan
        ),
        "runner_leg_expectancy": (
            float(trades["runner_leg_r_0_0"].mean()) if len(trades) else math.nan
        ),
        "pair_table": pair_table,
        "year_table": year_table,
    }


def _inner_policy_table(grid: pd.DataFrame, outer_year: int) -> pd.DataFrame:
    inner = grid.loc[grid["year"].ne(outer_year)].copy()
    rows: list[dict[str, Any]] = []
    for current_policy, trades in inner.groupby("policy_id", sort=True):
        summary = _fast_summary(trades)
        policy = trades.iloc[0]
        rows.append(
            {
                "outer_year": outer_year,
                "policy_id": current_policy,
                "target_kind": policy["target_kind"],
                "exit_hour": int(policy["exit_hour"]),
                "stop_policy": policy["stop_policy"],
                "trade_count": summary["trade_count"],
                "expectancy": summary["expectancy"],
                "stress_0_10_expectancy": summary["stress_0_10_expectancy"],
                "max_drawdown_r": summary["max_drawdown_r"],
                "positive_pairs": summary["positive_pairs"],
                "positive_inner_years": summary["positive_years"],
            }
        )
    table = pd.DataFrame(rows)
    table["eligible"] = (
        table["positive_pairs"].eq(2)
        & table["positive_inner_years"].ge(3)
    )
    return table


def _select_inner_policy(table: pd.DataFrame) -> pd.Series | None:
    eligible = table.loc[table["eligible"]].copy()
    if eligible.empty:
        return None
    eligible["target_order"] = eligible["target_kind"].map(
        {value: index for index, value in enumerate(TARGET_KINDS)}
    )
    eligible["hour_order"] = eligible["exit_hour"].map(
        {value: index for index, value in enumerate(EXIT_HOURS)}
    )
    eligible["stop_order"] = eligible["stop_policy"].map(
        {value: index for index, value in enumerate(STOP_POLICIES)}
    )
    return eligible.sort_values(
        [
            "stress_0_10_expectancy",
            "max_drawdown_r",
            "target_order",
            "hour_order",
            "stop_order",
        ],
        ascending=[False, True, True, True, True],
        kind="mergesort",
    ).iloc[0]


def build_nested_runner_decision(grid: pd.DataFrame) -> dict[str, Any]:
    years = sorted(int(value) for value in grid["year"].unique())
    if years != [2015, 2016, 2017, 2018, 2019]:
        raise ValueError(f"unexpected runner development years: {years}")
    expected = sorted(row["policy_id"] for row in runner_policy_manifest())
    if sorted(grid["policy_id"].unique()) != expected:
        raise ValueError("runner policy manifest does not match frozen 40-policy grid")

    fold_rows: list[dict[str, Any]] = []
    inner_tables: list[pd.DataFrame] = []
    oof_parts: list[pd.DataFrame] = []
    for outer_year in years:
        table = _inner_policy_table(grid, outer_year)
        inner_tables.append(table)
        selected = _select_inner_policy(table)
        if selected is None:
            fold_rows.append(
                {
                    "outer_year": outer_year,
                    "selected_policy_id": None,
                    "selection_available": False,
                }
            )
            continue
        current_policy = str(selected["policy_id"])
        heldout = grid.loc[
            grid["year"].eq(outer_year) & grid["policy_id"].eq(current_policy)
        ].copy()
        heldout_summary = _fast_summary(heldout)
        oof_parts.append(heldout)
        fold_rows.append(
            {
                "outer_year": outer_year,
                "selected_policy_id": current_policy,
                "selection_available": True,
                "target_kind": selected["target_kind"],
                "exit_hour": int(selected["exit_hour"]),
                "stop_policy": selected["stop_policy"],
                "inner_stress_expectancy": float(selected["stress_0_10_expectancy"]),
                "heldout_trade_count": heldout_summary["trade_count"],
                "heldout_expectancy": heldout_summary["expectancy"],
                "heldout_stress_0_10_expectancy": heldout_summary[
                    "stress_0_10_expectancy"
                ],
            }
        )

    fold_table = pd.DataFrame(fold_rows)
    inner_table = pd.concat(inner_tables, ignore_index=True)
    oof = pd.concat(oof_parts, ignore_index=True) if oof_parts else grid.iloc[0:0]
    selected_ids = fold_table["selected_policy_id"].dropna().astype(str).tolist()
    modal_policy_id: str | None = None
    modal_count = 0
    if selected_ids:
        counts = Counter(selected_ids)
        modal_count = max(counts.values())
        tied = [policy for policy, count in counts.items() if count == modal_count]
        manifest = pd.DataFrame(runner_policy_manifest()).set_index("policy_id")
        tied.sort(key=lambda value: _policy_complexity(manifest.loc[value]))
        modal_policy_id = tied[0]

    oof_summary = summarize_trades(oof)
    modal_trades = (
        grid.loc[grid["policy_id"].eq(modal_policy_id)].copy()
        if modal_policy_id is not None
        else grid.iloc[0:0].copy()
    )
    modal_summary = summarize_trades(modal_trades)
    oof_pair = oof_summary["pair_table"]
    oof_year = oof_summary["year_table"]
    modal_pair = modal_summary["pair_table"]
    modal_year = modal_summary["year_table"]
    gates = {
        "all_outer_folds_selected": len(selected_ids) == 5,
        "at_least_150_oof_trades": oof_summary["trade_count"] >= 150,
        "at_least_50_oof_trades_per_pair": oof_summary["minimum_pair_trades"] >= 50,
        "oof_expectancy_above_0_03r": oof_summary["expectancy"] > 0.03,
        "oof_positive_under_0_10_pip_stress": (
            oof_summary["stress_0_10_expectancy"] > 0
        ),
        "oof_both_pairs_positive": (
            len(oof_pair) == 2 and bool((oof_pair["expectancy"] > 0).all())
        ),
        "oof_four_of_five_years_positive": (
            len(oof_year) == 5 and int((oof_year["expectancy"] > 0).sum()) >= 4
        ),
        "oof_median_annual_expectancy_positive": (
            oof_summary["median_annual_expectancy"] > 0
        ),
        "oof_max_drawdown_below_25r": oof_summary["max_drawdown_r"] < 25,
        "oof_return_drawdown_at_least_1_50": (
            oof_summary["return_drawdown"] >= 1.50
        ),
        "oof_bootstrap_probability_positive_at_least_95pct": (
            oof_summary["probability_expectancy_positive"] >= 0.95
        ),
        "modal_policy_selected_at_least_three_folds": modal_count >= 3,
        "oof_largest_winner_below_20pct_net": (
            np.isfinite(oof_summary["largest_winner_share_of_net_r"])
            and oof_summary["largest_winner_share_of_net_r"] <= 0.20
        ),
        "modal_policy_base_expectancy_positive": modal_summary["expectancy"] > 0,
        "modal_policy_stress_expectancy_positive": (
            modal_summary["stress_0_10_expectancy"] > 0
        ),
        "modal_policy_both_pairs_positive": (
            len(modal_pair) == 2 and bool((modal_pair["expectancy"] > 0).all())
        ),
        "modal_policy_four_of_five_years_positive": (
            len(modal_year) == 5 and int((modal_year["expectancy"] > 0).sum()) >= 4
        ),
    }
    decision = PASS_DECISION if all(gates.values()) else FAIL_DECISION
    return {
        "decision": decision,
        "selected_policy_id": modal_policy_id if decision == PASS_DECISION else None,
        "modal_policy_id": modal_policy_id,
        "modal_policy_fold_count": modal_count,
        "gates": gates,
        "oof_metrics": {
            key: value
            for key, value in oof_summary.items()
            if not isinstance(value, pd.DataFrame)
        },
        "modal_policy_metrics": {
            key: value
            for key, value in modal_summary.items()
            if not isinstance(value, pd.DataFrame)
        },
        "fold_table": fold_table,
        "inner_table": inner_table,
        "oof_trades": oof,
        "modal_trades": modal_trades,
        "oof_tables": {
            key: value
            for key, value in oof_summary.items()
            if isinstance(value, pd.DataFrame)
        },
        "modal_tables": {
            key: value
            for key, value in modal_summary.items()
            if isinstance(value, pd.DataFrame)
        },
    }


def write_runner_discovery_outputs(output_directory: Path, grid: pd.DataFrame) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=True)
    grid.to_csv(output_directory / "runner_policy_grid.csv", index=False)
    decision = build_nested_runner_decision(grid)
    decision["fold_table"].to_csv(output_directory / "outer_fold_selections.csv", index=False)
    decision["inner_table"].to_csv(output_directory / "inner_policy_metrics.csv", index=False)
    decision["oof_trades"].to_csv(output_directory / "oof_selected_trades.csv", index=False)
    decision["modal_trades"].to_csv(output_directory / "modal_policy_trades.csv", index=False)
    for prefix, tables in (
        ("oof", decision["oof_tables"]),
        ("modal", decision["modal_tables"]),
    ):
        for name, table in tables.items():
            table.to_csv(output_directory / f"{prefix}_{name}.csv", index=False)

    policy_rows: list[dict[str, Any]] = []
    for current_policy, trades in grid.groupby("policy_id", sort=True):
        summary = _fast_summary(trades)
        row = trades.iloc[0]
        policy_rows.append(
            {
                "policy_id": current_policy,
                "target_kind": row["target_kind"],
                "exit_hour": int(row["exit_hour"]),
                "stop_policy": row["stop_policy"],
                **{
                    key: value
                    for key, value in summary.items()
                    if not isinstance(value, pd.DataFrame)
                },
            }
        )
    pd.DataFrame(policy_rows).to_csv(output_directory / "policy_summary.csv", index=False)

    payload = {
        "programme": "ASIAN_SWEEP_RUNNER_ENTRY_OPTIMISATION_V4",
        "stage": "RUNNER_DISCOVERY_2015_2019",
        "decision": decision["decision"],
        "selected_policy_id": decision["selected_policy_id"],
        "modal_policy_id": decision["modal_policy_id"],
        "modal_policy_fold_count": decision["modal_policy_fold_count"],
        "gates": decision["gates"],
        "oof_metrics": decision["oof_metrics"],
        "modal_policy_metrics": decision["modal_policy_metrics"],
        "later_partitions_opened": False,
        "earlier_entry_research_authorized": decision["decision"] == PASS_DECISION,
        "strategy_deployment_authorized": False,
    }
    (output_directory / "runner_discovery_decision.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
