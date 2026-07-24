from __future__ import annotations

from stoic_123_lab import usa500_forward_gates


def _partition(
    *,
    years: tuple[int, ...],
    positive: bool,
    trades: int = 150,
) -> dict[str, object]:
    sign = 1.0 if positive else -1.0
    full = {
        "trades": trades,
        "net_r": 30.0 * sign,
        "expectancy_r": 0.20 * sign,
        "max_drawdown_r": 15.0,
        "return_to_drawdown": 2.0 * sign,
        "largest_positive_year_share": 0.30 if positive else float("nan"),
    }
    for year in years:
        full[f"net_{year}"] = 6.0 * sign
    return {
        "summaries": {
            "RTH_LONG_FULL": full,
            "RTH_LONG_FULL_COST_2T": {"expectancy_r": 0.10 * sign},
            "RTH_LONG_FULL_DELAY_1M": {"expectancy_r": 0.12 * sign},
        },
        "inferences": {
            "RTH_LONG_FULL": {
                "lo95_expectancy_r": 0.05 if positive else -0.25,
            }
        },
        "matched_rows": [
            {
                "candidate": "RTH_LONG_FULL",
                "matched_control_passed": positive,
            }
        ],
    }


def _combined(*, positive: bool) -> dict[str, object]:
    sign = 1.0 if positive else -1.0
    return {
        "expectancy_r": 0.18 * sign,
        "return_to_drawdown": 2.2 * sign,
    }


def test_positive_forward_structure_passes_all_gates() -> None:
    rows = usa500_forward_gates.promotion_gates(
        _partition(years=(2015, 2016, 2017, 2018, 2019), positive=True),
        _partition(years=(2020, 2021, 2022), positive=True),
        _partition(years=(2023, 2024, 2025), positive=True),
        _combined(positive=True),
    )
    assert len(rows) == 19
    assert all(bool(row["passed"]) for row in rows)


def test_negative_recent_holdout_fails_cross_block_gates() -> None:
    rows = usa500_forward_gates.promotion_gates(
        _partition(years=(2015, 2016, 2017, 2018, 2019), positive=True),
        _partition(years=(2020, 2021, 2022), positive=True),
        _partition(years=(2023, 2024, 2025), positive=False),
        _combined(positive=True),
    )
    by_name = {str(row["gate"]): bool(row["passed"]) for row in rows}
    assert not by_name["recent_holdout_expectancy_positive"]
    assert not by_name["recent_holdout_positive_years_gte_2_of_3"]
    assert not by_name["recent_holdout_two_tick_expectancy_positive"]


def test_primary_uncertainty_fails_confidence_and_control_gates() -> None:
    primary = _partition(
        years=(2015, 2016, 2017, 2018, 2019),
        positive=True,
    )
    primary["inferences"]["RTH_LONG_FULL"]["lo95_expectancy_r"] = -0.01
    primary["matched_rows"][0]["matched_control_passed"] = False
    rows = usa500_forward_gates.promotion_gates(
        primary,
        _partition(years=(2020, 2021, 2022), positive=True),
        _partition(years=(2023, 2024, 2025), positive=True),
        _combined(positive=True),
    )
    by_name = {str(row["gate"]): bool(row["passed"]) for row in rows}
    assert not by_name["primary_forward_date_block_lo95_positive"]
    assert not by_name["primary_forward_matched_time_control_passed"]
