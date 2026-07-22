from __future__ import annotations

import pandas as pd

from dtr_lab.research.validity import quarterly_roll_candidates, roll_adjacent_dates


def test_quarterly_roll_candidates_use_thursday_before_expiry_week() -> None:
    candidates = quarterly_roll_candidates(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31"))
    assert candidates["calendar_roll_candidate"].dt.weekday.eq(3).all()
    assert len(candidates) == 4
    assert pd.Timestamp("2024-03-07") in set(candidates["calendar_roll_candidate"])


def test_roll_adjacent_dates_use_market_sequence_not_calendar_days() -> None:
    candidates = pd.DataFrame({"nearest_market_date": [pd.Timestamp("2024-03-07")]})
    market_dates = pd.to_datetime(
        ["2024-03-05", "2024-03-06", "2024-03-07", "2024-03-08", "2024-03-11"]
    )
    excluded = roll_adjacent_dates(candidates, market_dates, window_sessions=1)
    assert excluded == {
        pd.Timestamp("2024-03-06"),
        pd.Timestamp("2024-03-07"),
        pd.Timestamp("2024-03-08"),
    }


def test_leave_one_group_out_reports_removed_contribution() -> None:
    from dtr_lab.research.validity import leave_one_group_out

    trades = pd.DataFrame(
        {
            "session": ["A", "A", "B"],
            "day_of_week": [1, 2, 1],
            "pnl_r": [1.0, -0.5, 0.25],
            "holding_minutes": [1, 1, 1],
            "mfe_r": [1.0, 1.0, 1.0],
            "mae_r": [0.5, 0.5, 0.5],
        }
    )
    result = leave_one_group_out(trades, ["session"])
    row_a = result[result["excluded_session"] == "A"].iloc[0]
    assert row_a["removed_trades"] == 2
    assert row_a["removed_net_r"] == 0.5
    assert row_a["trades"] == 1
    assert row_a["net_r"] == 0.25
