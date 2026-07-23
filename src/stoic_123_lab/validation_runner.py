from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .config import NQ_SPEC, SequenceConfig
from .reporting import classify, date_block_bootstrap, summarize
from .review import independent_trade_review
from .validation import evaluate_trades, run_scenario


def load_design(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Validation design must be a mapping")
    return payload


def annual_rows(trades: pd.DataFrame, scenario_id: str) -> list[dict[str, object]]:
    if trades.empty:
        return []
    years = pd.to_datetime(trades["entry_time"]).dt.year
    rows = []
    for year in sorted(years.unique()):
        group = trades.loc[years == year]
        rows.append(
            {
                "scenario_id": scenario_id,
                "year": int(year),
                **summarize(group, instrument="NQ", arm_id=scenario_id),
            }
        )
    return rows


def return_to_drawdown(summary: dict[str, object]) -> float:
    drawdown = float(summary["max_drawdown_r"])
    return float(summary["net_r"]) / drawdown if drawdown > 0 else np.nan


def run_evaluated_scenario(
    *,
    scenario_id: str,
    one_minute: pd.DataFrame,
    events: pd.DataFrame,
    management_events: pd.DataFrame,
    config: SequenceConfig,
    source_start: pd.Timestamp,
    source_end: pd.Timestamp,
    iterations: int,
    seed: int,
    out: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], pd.DataFrame]:
    scenario_config = replace(config, arm_id=scenario_id, description=scenario_id)
    trades = run_scenario(
        one_minute=one_minute,
        events=events,
        management_events=management_events,
        spec=NQ_SPEC,
        config=scenario_config,
    )
    summary = evaluate_trades(
        trades,
        instrument="NQ",
        arm_id=scenario_id,
        source_start=source_start,
        source_end=source_end,
    )
    summary["return_to_drawdown"] = return_to_drawdown(summary)
    inference = date_block_bootstrap(trades, iterations=iterations, seed=seed)
    summary["classification"] = classify(summary, inference)
    review = independent_trade_review(
        trades,
        summary,
        instrument="NQ",
        arm_id=scenario_id,
    )
    events.to_csv(out / f"{scenario_id}__events.csv", index=False)
    trades.to_csv(out / f"{scenario_id}__trades.csv", index=False)
    return summary, {"scenario_id": scenario_id, **inference}, review, trades


def _positive_year_count(summary: dict[str, object]) -> int:
    return sum(
        float(value) > 0
        for key, value in summary.items()
        if key.startswith("net_20") and np.isfinite(float(value))
    )


def _full_years_positive(summary: dict[str, object]) -> bool:
    return all(float(summary.get(f"net_{year}", np.nan)) > 0 for year in (2023, 2024, 2025))


def gate_rows(
    arm_id: str,
    scenarios: dict[str, dict[str, object]],
    inference: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    long_full = scenarios[f"{arm_id}__LONG_FULL"]
    both_full = scenarios[f"{arm_id}__BOTH_FULL"]
    break_only = scenarios[f"{arm_id}__LONG_EMA_BREAK"]
    stress = scenarios[f"{arm_id}__LONG_FULL_COST_2T"]
    delay_1m = scenarios[f"{arm_id}__LONG_FULL_DELAY_1M"]
    full_inference = inference[f"{arm_id}__LONG_FULL"]
    dd_improvement = (
        1 - float(long_full["max_drawdown_r"]) / float(both_full["max_drawdown_r"])
        if float(both_full["max_drawdown_r"]) > 0
        else np.nan
    )
    expectancy_gain = float(long_full["expectancy_r"]) - float(break_only["expectancy_r"])
    break_rdd = float(break_only["return_to_drawdown"])
    rdd_gain = (
        float(long_full["return_to_drawdown"]) / break_rdd - 1
        if np.isfinite(break_rdd) and break_rdd > 0
        else np.nan
    )
    checks = {
        "positive_expectancy": float(long_full["expectancy_r"]) > 0,
        "three_of_four_years_positive": _positive_year_count(long_full) >= 3,
        "all_full_years_2023_2025_positive": _full_years_positive(long_full),
        "largest_positive_year_share_le_60pct": (
            np.isfinite(float(long_full["largest_positive_year_share"]))
            and float(long_full["largest_positive_year_share"]) <= 0.60
        ),
        "positive_two_tick_cost_stress": float(stress["expectancy_r"]) > 0,
        "positive_one_minute_delay": float(delay_1m["expectancy_r"]) > 0,
        "drawdown_at_least_25pct_below_both_direction": (
            np.isfinite(dd_improvement) and dd_improvement >= 0.25
        ),
        "mechanism_value_over_ema_break": (
            expectancy_gain >= 0.05 or (np.isfinite(rdd_gain) and rdd_gain >= 0.20)
        ),
        "positive_date_block_lower_bound": float(full_inference["lo95_expectancy_r"]) > 0,
    }
    return [
        {
            "arm_id": arm_id,
            "gate": gate,
            "passed": bool(passed),
            "dd_improvement_fraction": dd_improvement,
            "expectancy_gain_vs_ema_break": expectancy_gain,
            "return_dd_gain_vs_ema_break": rdd_gain,
        }
        for gate, passed in checks.items()
    ]
