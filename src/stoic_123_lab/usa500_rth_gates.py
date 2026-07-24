from __future__ import annotations

import numpy as np


def mechanism_value(
    full: dict[str, object],
    control: dict[str, object],
) -> tuple[float, float, bool]:
    expectancy_gain = float(full["expectancy_r"]) - float(control["expectancy_r"])
    control_rdd = float(control["return_to_drawdown"])
    rdd_gain = (
        float(full["return_to_drawdown"]) / control_rdd - 1
        if np.isfinite(control_rdd) and control_rdd > 0
        else np.nan
    )
    passed = expectancy_gain >= 0.05 or (np.isfinite(rdd_gain) and rdd_gain >= 0.20)
    return expectancy_gain, rdd_gain, bool(passed)


def _matched(result: dict[str, object], candidate: str) -> dict[str, object]:
    rows = result.get("matched_rows")
    if not isinstance(rows, list):
        raise ValueError("matched_rows must be a list")
    matches = [row for row in rows if row.get("candidate") == candidate]
    if len(matches) != 1:
        raise ValueError(f"Expected one matched row for {candidate}, found {len(matches)}")
    return matches[0]


def promotion_gates(
    history: dict[str, object],
    holdout: dict[str, object],
) -> list[dict[str, object]]:
    history_summaries = history["summaries"]
    holdout_summaries = holdout["summaries"]
    history_break = history_summaries["RTH_LONG_EMA_BREAK"]
    holdout_break = holdout_summaries["RTH_LONG_EMA_BREAK"]
    history_full = history_summaries["RTH_LONG_FULL"]
    holdout_full = holdout_summaries["RTH_LONG_FULL"]

    history_gain, history_rdd_gain, history_mechanism = mechanism_value(
        history_full,
        history_break,
    )
    holdout_gain, holdout_rdd_gain, _ = mechanism_value(
        holdout_full,
        holdout_break,
    )
    positive_history_years = sum(
        float(history_break.get(f"net_{year}", np.nan)) > 0
        for year in (2012, 2013)
    )
    primary_checks = {
        "fresh_history_trade_count_gte_250": int(history_break["trades"]) >= 250,
        "fresh_history_expectancy_positive": float(history_break["expectancy_r"]) > 0,
        "fresh_history_date_block_lo95_positive": (
            float(history["inferences"]["RTH_LONG_EMA_BREAK"]["lo95_expectancy_r"])
            > 0
        ),
        "both_fresh_history_years_positive": positive_history_years == 2,
        "largest_positive_year_share_lte_0_60": (
            np.isfinite(float(history_break["largest_positive_year_share"]))
            and float(history_break["largest_positive_year_share"]) <= 0.60
        ),
        "fresh_history_two_tick_expectancy_positive": (
            float(history_summaries["RTH_LONG_EMA_BREAK_COST_2T"]["expectancy_r"])
            > 0
        ),
        "fresh_history_one_minute_delay_expectancy_positive": (
            float(history_summaries["RTH_LONG_EMA_BREAK_DELAY_1M"]["expectancy_r"])
            > 0
        ),
        "fresh_history_return_to_drawdown_gte_1_50": (
            float(history_break["return_to_drawdown"]) >= 1.50
        ),
        "fresh_history_max_drawdown_lte_50R": (
            float(history_break["max_drawdown_r"]) <= 50.0
        ),
        "fresh_holdout_trade_count_gte_75": int(holdout_break["trades"]) >= 75,
        "fresh_holdout_expectancy_positive": float(holdout_break["expectancy_r"]) > 0,
        "fresh_holdout_date_block_lo95_positive": (
            float(holdout["inferences"]["RTH_LONG_EMA_BREAK"]["lo95_expectancy_r"])
            > 0
        ),
        "fresh_holdout_two_tick_expectancy_positive": (
            float(holdout_summaries["RTH_LONG_EMA_BREAK_COST_2T"]["expectancy_r"])
            > 0
        ),
        "primary_matched_time_control_passes": (
            bool(_matched(history, "RTH_LONG_EMA_BREAK")["matched_control_passed"])
            and bool(
                _matched(holdout, "RTH_LONG_EMA_BREAK")["matched_control_passed"]
            )
        ),
    }
    secondary_checks = {
        "fresh_history_full_sequence_expectancy_positive": (
            float(history_full["expectancy_r"]) > 0
        ),
        "fresh_holdout_full_sequence_expectancy_positive": (
            float(holdout_full["expectancy_r"]) > 0
        ),
        "full_sequence_mechanism_value_over_ema_break": (
            history_mechanism and holdout_gain >= 0
        ),
        "secondary_matched_time_control_passes": (
            bool(_matched(history, "RTH_LONG_FULL")["matched_control_passed"])
            and bool(_matched(holdout, "RTH_LONG_FULL")["matched_control_passed"])
        ),
    }
    rows = []
    for group, checks in (("primary", primary_checks), ("secondary", secondary_checks)):
        for name, passed in checks.items():
            rows.append(
                {
                    "gate_group": group,
                    "gate": name,
                    "passed": bool(passed),
                    "history_full_expectancy_gain_vs_ema_break": history_gain,
                    "history_full_return_dd_gain_vs_ema_break": history_rdd_gain,
                    "holdout_full_expectancy_gain_vs_ema_break": holdout_gain,
                    "holdout_full_return_dd_gain_vs_ema_break": holdout_rdd_gain,
                }
            )
    return rows
