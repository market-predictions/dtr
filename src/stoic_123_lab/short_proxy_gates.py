from __future__ import annotations

import numpy as np


def _mechanism_value(
    short: dict[str, object],
    control: dict[str, object],
) -> tuple[float, float, bool]:
    expectancy_gain = float(short["expectancy_r"]) - float(control["expectancy_r"])
    control_rdd = float(control["return_to_drawdown"])
    rdd_gain = (
        float(short["return_to_drawdown"]) / control_rdd - 1
        if np.isfinite(control_rdd) and control_rdd > 0
        else np.nan
    )
    passed = expectancy_gain >= 0.05 or (np.isfinite(rdd_gain) and rdd_gain >= 0.20)
    return expectancy_gain, rdd_gain, bool(passed)


def _promotion_gates(
    older: dict[str, object],
    forward: dict[str, object],
) -> list[dict[str, object]]:
    older_summaries = older["summaries"]
    forward_summaries = forward["summaries"]
    older_short = older_summaries["SHORT_FULL"]
    forward_short = forward_summaries["SHORT_FULL"]
    older_gain, older_rdd_gain, older_mechanism = _mechanism_value(
        older_short,
        older_summaries["SHORT_EMA_BREAK"],
    )
    forward_gain, forward_rdd_gain, forward_mechanism = _mechanism_value(
        forward_short,
        forward_summaries["SHORT_EMA_BREAK"],
    )
    positive_older_years = sum(
        float(older_short.get(f"net_{year}", np.nan)) > 0
        for year in range(2015, 2022)
    )
    checks = {
        "older_history_trade_count_gte_500": int(older_short["trades"]) >= 500,
        "older_history_expectancy_positive": float(older_short["expectancy_r"]) > 0,
        "older_history_date_block_lo95_positive": (
            float(older["inferences"]["SHORT_FULL"]["lo95_expectancy_r"]) > 0
        ),
        "at_least_five_of_seven_older_years_positive": positive_older_years >= 5,
        "largest_positive_year_share_lte_0_40": (
            np.isfinite(float(older_short["largest_positive_year_share"]))
            and float(older_short["largest_positive_year_share"]) <= 0.40
        ),
        "older_history_two_tick_expectancy_positive": (
            float(older_summaries["SHORT_FULL_COST_2T"]["expectancy_r"]) > 0
        ),
        "older_history_one_minute_delay_expectancy_positive": (
            float(older_summaries["SHORT_FULL_DELAY_1M"]["expectancy_r"]) > 0
        ),
        "forward_2026_trade_count_gte_30": int(forward_short["trades"]) >= 30,
        "forward_2026_expectancy_positive": float(forward_short["expectancy_r"]) > 0,
        "forward_2026_two_tick_expectancy_positive": (
            float(forward_summaries["SHORT_FULL_COST_2T"]["expectancy_r"]) > 0
        ),
        "full_sequence_mechanism_value_over_ema_break": (
            older_mechanism and forward_mechanism and forward_gain >= 0
        ),
        "matched_time_short_control_passes": (
            bool(older["matched"]["matched_control_passed"])
            and bool(forward["matched"]["matched_control_passed"])
        ),
    }
    return [
        {
            "gate": name,
            "passed": bool(passed),
            "older_expectancy_gain_vs_ema_break": older_gain,
            "older_return_dd_gain_vs_ema_break": older_rdd_gain,
            "forward_expectancy_gain_vs_ema_break": forward_gain,
            "forward_return_dd_gain_vs_ema_break": forward_rdd_gain,
        }
        for name, passed in checks.items()
    ]
