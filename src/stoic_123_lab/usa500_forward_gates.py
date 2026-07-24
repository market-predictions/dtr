from __future__ import annotations

import numpy as np


def _matched(result: dict[str, object], candidate: str = "RTH_LONG_FULL") -> dict[str, object]:
    rows = result.get("matched_rows")
    if not isinstance(rows, list):
        raise ValueError("matched_rows must be a list")
    matches = [row for row in rows if row.get("candidate") == candidate]
    if len(matches) != 1:
        raise ValueError(f"Expected one matched row for {candidate}, found {len(matches)}")
    return matches[0]


def _positive_years(summary: dict[str, object], years: tuple[int, ...]) -> int:
    return sum(float(summary.get(f"net_{year}", np.nan)) > 0 for year in years)


def promotion_gates(
    primary: dict[str, object],
    crisis: dict[str, object],
    recent: dict[str, object],
    combined_summary: dict[str, object],
) -> list[dict[str, object]]:
    primary_summaries = primary["summaries"]
    crisis_summaries = crisis["summaries"]
    recent_summaries = recent["summaries"]

    primary_full = primary_summaries["RTH_LONG_FULL"]
    crisis_full = crisis_summaries["RTH_LONG_FULL"]
    recent_full = recent_summaries["RTH_LONG_FULL"]

    primary_checks = {
        "primary_forward_trade_count_gte_100": int(primary_full["trades"]) >= 100,
        "primary_forward_expectancy_positive": float(primary_full["expectancy_r"]) > 0,
        "primary_forward_date_block_lo95_positive": (
            float(primary["inferences"]["RTH_LONG_FULL"]["lo95_expectancy_r"]) > 0
        ),
        "primary_forward_positive_years_gte_4_of_5": (
            _positive_years(primary_full, (2015, 2016, 2017, 2018, 2019)) >= 4
        ),
        "primary_forward_largest_positive_year_share_lte_0_50": (
            np.isfinite(float(primary_full["largest_positive_year_share"]))
            and float(primary_full["largest_positive_year_share"]) <= 0.50
        ),
        "primary_forward_two_tick_expectancy_positive": (
            float(primary_summaries["RTH_LONG_FULL_COST_2T"]["expectancy_r"]) > 0
        ),
        "primary_forward_one_minute_delay_expectancy_positive": (
            float(primary_summaries["RTH_LONG_FULL_DELAY_1M"]["expectancy_r"]) > 0
        ),
        "primary_forward_return_to_drawdown_gte_1_50": (
            float(primary_full["return_to_drawdown"]) >= 1.50
        ),
        "primary_forward_max_drawdown_lte_35R": (
            float(primary_full["max_drawdown_r"]) <= 35.0
        ),
        "primary_forward_matched_time_control_passed": bool(
            _matched(primary)["matched_control_passed"]
        ),
    }

    cross_checks = {
        "crisis_regime_expectancy_positive": float(crisis_full["expectancy_r"]) > 0,
        "crisis_regime_positive_years_gte_2_of_3": (
            _positive_years(crisis_full, (2020, 2021, 2022)) >= 2
        ),
        "recent_holdout_expectancy_positive": float(recent_full["expectancy_r"]) > 0,
        "recent_holdout_positive_years_gte_2_of_3": (
            _positive_years(recent_full, (2023, 2024, 2025)) >= 2
        ),
        "recent_holdout_two_tick_expectancy_positive": (
            float(recent_summaries["RTH_LONG_FULL_COST_2T"]["expectancy_r"]) > 0
        ),
        "crisis_regime_max_drawdown_lte_35R": (
            float(crisis_full["max_drawdown_r"]) <= 35.0
        ),
        "recent_holdout_max_drawdown_lte_35R": (
            float(recent_full["max_drawdown_r"]) <= 35.0
        ),
        "combined_2015_2025_expectancy_positive": (
            float(combined_summary["expectancy_r"]) > 0
        ),
        "combined_2015_2025_return_to_drawdown_gte_1_50": (
            float(combined_summary["return_to_drawdown"]) >= 1.50
        ),
    }

    diagnostic = {
        "primary_expectancy_r": float(primary_full["expectancy_r"]),
        "crisis_expectancy_r": float(crisis_full["expectancy_r"]),
        "recent_expectancy_r": float(recent_full["expectancy_r"]),
        "combined_expectancy_r": float(combined_summary["expectancy_r"]),
        "combined_return_to_drawdown": float(combined_summary["return_to_drawdown"]),
    }

    rows: list[dict[str, object]] = []
    for group, checks in (("primary", primary_checks), ("cross_block", cross_checks)):
        for name, passed in checks.items():
            rows.append(
                {
                    "gate_group": group,
                    "gate": name,
                    "passed": bool(passed),
                    **diagnostic,
                }
            )
    return rows
