from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.early_entry_landmarks import (
    POSITION_STRUCTURES,
    add_cross_pair_landmark_features,
    build_pair_landmark_ledger,
)
from dtr_lab.strategies.asia_sweep.early_entry_modeling import select_landmark


def _write_quotes(directory: Path, *, end_minute: int = 7) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    timestamps = pd.date_range(
        "2015-01-06T08:00:00Z",
        periods=end_minute + 1,
        freq="1min",
    )
    mid = np.array([1.0992, 1.0995, 1.0998, 1.1001, 1.1003, 1.1006, 1.1013, 1.1014])[
        : len(timestamps)
    ]
    for side, offset in (("bid", -0.00005), ("ask", 0.00005)):
        price = mid + offset
        frame = pd.DataFrame(
            {
                "timestamp_utc": timestamps.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": price,
                "high": price + 0.00008,
                "low": price - 0.00008,
                "close": price + 0.00001,
                "volume": 1.0,
                "is_active_quote": 1,
            }
        )
        frame.to_csv(
            directory / f"eurusd_m1_{side}_2015.csv.gz",
            index=False,
            compression="gzip",
        )


def _event(*, midpoint_time: str = "2015-01-06T08:06:00Z") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "EURUSD_2015-01-06_DOWN_0800",
                "instrument": "EURUSD",
                "trade_date": "2015-01-06",
                "week_key": "2015-W02",
                "weekday": 1,
                "week_of_month": 1,
                "side": "DOWN",
                "sweep_timestamp_utc": "2015-01-06T08:00:00Z",
                "t5_timestamp_utc": "2015-01-06T08:04:00Z",
                "midpoint_first_passage_utc": midpoint_time,
                "barrier_first_passage_utc": None,
                "two_sided_ambiguous": False,
                "asian_high": 1.1020,
                "asian_low": 1.1000,
                "asian_midpoint": 1.1010,
                "asian_range_price": 0.0020,
                "sweep_extreme": 1.0990,
            }
        ]
    )


def _levels() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "EURUSD_2015-01-06_DOWN_0800",
                "level_side": "LOW",
                "level_price": 1.0988,
            },
            {
                "event_id": "EURUSD_2015-01-06_DOWN_0800",
                "level_side": "HIGH",
                "level_price": 1.1024,
            },
        ]
    )


def test_position_structure_manifest_is_frozen() -> None:
    assert POSITION_STRUCTURES == (
        "TP1_50_RUNNER_50",
        "TP1_25_RUNNER_75",
        "NO_TP1_FULL_RUNNER",
    )


def test_landmark_clock_and_long_quote_side(tmp_path: Path) -> None:
    _write_quotes(tmp_path)
    ledger = build_pair_landmark_ledger(
        _event(),
        _levels(),
        tmp_path,
        symbol="EURUSD",
        start_year=2015,
        end_year=2015,
    ).set_index("landmark")

    assert ledger.loc["T0", "landmark_timestamp_utc"] == "2015-01-06T08:00:00+00:00"
    assert ledger.loc["T0", "entry_timestamp_utc"] == "2015-01-06T08:01:00+00:00"
    assert ledger.loc["T1", "entry_timestamp_utc"] == "2015-01-06T08:02:00+00:00"
    assert ledger.loc["T2", "entry_timestamp_utc"] == "2015-01-06T08:03:00+00:00"
    assert ledger.loc["T3", "entry_timestamp_utc"] == "2015-01-06T08:04:00+00:00"
    assert ledger.loc["LEGACY_T5", "landmark_timestamp_utc"] == (
        "2015-01-06T08:04:00+00:00"
    )
    assert ledger.loc["LEGACY_T5", "entry_timestamp_utc"] == (
        "2015-01-06T08:05:00+00:00"
    )
    assert np.isclose(ledger.loc["T0", "entry_price"], 1.09955)
    assert ledger.loc["T0", "landmark_bar_count"] == 1
    assert ledger.loc["T3", "landmark_bar_count"] == 4
    assert ledger.loc["LEGACY_T5", "landmark_bar_count"] == 5


def test_resolved_event_is_removed_from_later_landmarks(tmp_path: Path) -> None:
    _write_quotes(tmp_path)
    ledger = build_pair_landmark_ledger(
        _event(midpoint_time="2015-01-06T08:02:00Z"),
        _levels(),
        tmp_path,
        symbol="EURUSD",
        start_year=2015,
        end_year=2015,
    )
    assert set(ledger["landmark"]) == {"T0", "T1"}


def test_future_append_does_not_change_t0_to_t3(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_quotes(first, end_minute=6)
    _write_quotes(second, end_minute=7)
    one = build_pair_landmark_ledger(
        _event(), _levels(), first, symbol="EURUSD", start_year=2015, end_year=2015
    )
    two = build_pair_landmark_ledger(
        _event(), _levels(), second, symbol="EURUSD", start_year=2015, end_year=2015
    )
    columns = [
        "landmark",
        "landmark_timestamp_utc",
        "entry_timestamp_utc",
        "entry_price",
        "reward_risk",
        "reclaim",
        "reclaim_depth_range_fraction",
        "landmark_return_range_fraction",
    ]
    one = one.loc[one["landmark"].isin(("T0", "T1", "T2", "T3")), columns]
    two = two.loc[two["landmark"].isin(("T0", "T1", "T2", "T3")), columns]
    pd.testing.assert_frame_equal(one.reset_index(drop=True), two.reset_index(drop=True))


def test_cross_pair_state_uses_only_known_landmark() -> None:
    ledger = pd.DataFrame(
        [
            {
                "event_id": "E1",
                "instrument": "EURUSD",
                "trade_date": "2015-01-06",
                "side": "UP",
                "landmark": "T1",
                "landmark_timestamp_utc": "2015-01-06T08:02:00Z",
                "landmark_bar_count": 2,
                "reclaim": 1.0,
                "landmark_return_range_fraction": 0.2,
            },
            {
                "event_id": "G1",
                "instrument": "GBPUSD",
                "trade_date": "2015-01-06",
                "side": "UP",
                "landmark": "T0",
                "landmark_timestamp_utc": "2015-01-06T08:01:00Z",
                "landmark_bar_count": 1,
                "reclaim": 0.0,
                "landmark_return_range_fraction": -0.1,
            },
            {
                "event_id": "G1",
                "instrument": "GBPUSD",
                "trade_date": "2015-01-06",
                "side": "UP",
                "landmark": "T3",
                "landmark_timestamp_utc": "2015-01-06T08:04:00Z",
                "landmark_bar_count": 4,
                "reclaim": 1.0,
                "landmark_return_range_fraction": 0.5,
            },
        ]
    )
    result = add_cross_pair_landmark_features(ledger).set_index(["event_id", "landmark"])
    eur = result.loc[("E1", "T1")]
    assert eur["other_pair_known"] == 1.0
    assert eur["other_pair_reclaim"] == 0.0
    assert eur["other_pair_return_range_fraction"] == -0.1


def test_landmark_selection_stops_when_no_candidate_passes() -> None:
    candidates = pd.DataFrame(
        [
            {"landmark": "T0", "family": "elastic_net", "passes": False},
            {"landmark": "T3", "family": "hgb", "passes": False},
        ]
    )
    decision = select_landmark(candidates)
    assert decision["decision"] == (
        "FAIL_EARLY_ENTRY_INFORMATION_FRONTIER_STOP_BEFORE_POLICY_PNL"
    )
    assert decision["selected_landmark"] is None
