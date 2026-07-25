from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_engine import (
    Level,
    _event_outcomes,
    _liquidity_features,
    _local_bounds,
    _t5_features,
    build_fingerprint_ledgers,
)


def _path(
    start: str,
    highs: list[float],
    lows: list[float],
    closes: list[float],
) -> pd.DataFrame:
    index = pd.date_range(start, periods=len(closes), freq="1min", tz="Europe/Amsterdam")
    opens = [closes[0], *closes[:-1]]
    return pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "is_active_quote": 1,
        },
        index=index,
    )


def test_amsterdam_clock_is_dst_native() -> None:
    winter = _local_bounds(pd.Timestamp("2020-01-15"))
    summer = _local_bounds(pd.Timestamp("2020-07-15"))
    assert winter["asian_end"].hour == 8
    assert summer["asian_end"].hour == 8
    assert winter["asian_end"].tz_convert("UTC").hour == 7
    assert summer["asian_end"].tz_convert("UTC").hour == 6


def test_first_passage_success_and_false_reversal_are_distinct() -> None:
    success_path = _path(
        "2020-01-15 09:00",
        [1.1022, 1.1020, 1.1014, 1.1009],
        [1.1019, 1.1015, 1.1008, 1.1007],
        [1.1020, 1.1016, 1.1010, 1.1008],
    )
    success = _event_outcomes(
        path_to_1000=success_path,
        path_to_1100=success_path,
        side="UP",
        sweep_extreme=1.1022,
        asian_high=1.1020,
        asian_low=1.1000,
        asian_range=0.0020,
    )
    assert success["midpoint_success_09_10"]
    assert success["primary_outcome"] == "MIDPOINT_SUCCESS_09_10"

    false_path = _path(
        "2020-01-15 09:00",
        [1.1022, 1.1020, 1.1021, 1.1027],
        [1.1019, 1.1016, 1.1015, 1.1018],
        [1.1020, 1.1017, 1.1019, 1.1026],
    )
    failed = _event_outcomes(
        path_to_1000=false_path,
        path_to_1100=false_path,
        side="UP",
        sweep_extreme=1.1022,
        asian_high=1.1020,
        asian_low=1.1000,
        asian_range=0.0020,
    )
    assert failed["false_reversal"]
    assert failed["primary_outcome"] == "FALSE_REVERSAL"


def test_same_minute_target_and_barrier_is_ambiguous() -> None:
    path = _path(
        "2020-01-15 09:00",
        [1.1027],
        [1.1008],
        [1.1015],
    )
    result = _event_outcomes(
        path_to_1000=path,
        path_to_1100=path,
        side="UP",
        sweep_extreme=1.1022,
        asian_high=1.1020,
        asian_low=1.1000,
        asian_range=0.0020,
    )
    assert result["two_sided_ambiguous"]
    assert result["primary_outcome"] == "TWO_SIDED_AMBIGUOUS"


def test_t5_reclaim_is_causal() -> None:
    path = _path(
        "2020-01-15 09:00",
        [1.1022, 1.1021, 1.1020, 1.1019, 1.1018],
        [1.1019, 1.1017, 1.1016, 1.1015, 1.1014],
        [1.1021, 1.1019, 1.1018, 1.1017, 1.1016],
    )
    result = _t5_features(
        side="UP",
        boundary=1.1020,
        asian_range=0.0020,
        sweep_extreme=1.1022,
        path=path,
    )
    assert result["t5_available"]
    assert result["t5_reclaim"]
    assert result["t5_reclaim_delay_minutes"] == 2.0
    assert result["t5_closes_inside"] == 4


def test_liquidity_features_separate_exhaustion_from_residual_levels() -> None:
    timestamp = pd.Timestamp("2020-01-15 08:00", tz="Europe/Amsterdam")
    levels = [
        Level("PDH", "PRIOR_DAY", "HIGH", 1.1021, timestamp),
        Level("NYH", "PREVIOUS_NY", "HIGH", 1.1022, timestamp),
        Level("PWH", "PRIOR_WEEK", "HIGH", 1.1028, timestamp),
        Level("PDL", "PRIOR_DAY", "LOW", 1.0995, timestamp),
    ]
    pre = _path(
        "2020-01-15 08:55",
        [1.1018, 1.1019],
        [1.1015, 1.1016],
        [1.1017, 1.1018],
    )
    sweep = _path(
        "2020-01-15 09:00",
        [1.1023],
        [1.1018],
        [1.1020],
    )
    t5 = _path(
        "2020-01-15 09:00",
        [1.1023, 1.1022, 1.1021, 1.1020, 1.1019],
        [1.1018, 1.1017, 1.1016, 1.1015, 1.1014],
        [1.1020, 1.1019, 1.1018, 1.1017, 1.1016],
    )
    features, ledger = _liquidity_features(
        event_id="x",
        instrument="EURUSD",
        trade_date=pd.Timestamp("2020-01-15").date(),
        side="UP",
        levels=levels,
        asian_high=1.1020,
        asian_low=1.1000,
        asian_range=0.0020,
        pip=0.0001,
        atr20=0.0100,
        pre_sweep_price=1.1018,
        sweep_extreme=1.1023,
        t5_price=1.1016,
        path_0800_pre=pre,
        sweep_bar=sweep,
        path_sweep_t5=t5,
    )
    assert features["levels_consumed_by_sweep"] == 2
    assert features["remaining_levels_beyond_t0"] == 1
    assert features["sweep_consumption_class"] == "MULTIPLE_EXTERNAL_LEVELS"
    assert len(ledger) == 3


def _synthetic_minutes() -> pd.DataFrame:
    index = pd.date_range(
        "2020-01-15 00:00",
        "2020-01-15 10:59",
        freq="1min",
        tz="Europe/Amsterdam",
    )
    base = np.full(len(index), 1.1010)
    high = base + 0.0001
    low = base - 0.0001
    high[60] = 1.1020
    low[120] = 1.1000
    sweep_pos = int(
        (
            pd.Timestamp("2020-01-15 08:30", tz="Europe/Amsterdam") - index[0]
        ).total_seconds()
        // 60
    )
    high[sweep_pos] = 1.1022
    base[sweep_pos] = 1.1020
    midpoint_pos = int(
        (
            pd.Timestamp("2020-01-15 09:10", tz="Europe/Amsterdam") - index[0]
        ).total_seconds()
        // 60
    )
    low[midpoint_pos] = 1.1009
    base[midpoint_pos] = 1.1010
    opens = np.r_[base[0], base[:-1]]
    return pd.DataFrame(
        {
            "timestamp": index.tz_convert("UTC"),
            "open": opens,
            "high": np.maximum.reduce([high, opens, base]),
            "low": np.minimum.reduce([low, opens, base]),
            "close": base,
            "is_active_quote": 1,
        }
    )


def test_engine_allows_pre_0900_sweep_and_0900_1000_reversal() -> None:
    events, levels, sessions = build_fingerprint_ledgers(
        "EURUSD",
        _synthetic_minutes(),
        start_year=2020,
        end_year=2020,
    )
    assert len(events) == 1
    event = events.iloc[0]
    assert bool(event["sweep_before_0900"])
    assert bool(event["midpoint_success_09_10"])
    assert event["primary_outcome"] == "MIDPOINT_SUCCESS_09_10"
    assert len(sessions) == 1
    assert levels.empty


def test_future_append_does_not_change_completed_event() -> None:
    original = _synthetic_minutes()
    first, _, _ = build_fingerprint_ledgers(
        "EURUSD",
        original,
        start_year=2020,
        end_year=2020,
    )
    future_index = pd.date_range(
        "2020-01-16 00:00",
        "2020-01-16 10:59",
        freq="1min",
        tz="Europe/Amsterdam",
    )
    future = pd.DataFrame(
        {
            "timestamp": future_index.tz_convert("UTC"),
            "open": 1.2000,
            "high": 1.2001,
            "low": 1.1999,
            "close": 1.2000,
            "is_active_quote": 1,
        }
    )
    second, _, _ = build_fingerprint_ledgers(
        "EURUSD",
        pd.concat([original, future], ignore_index=True),
        start_year=2020,
        end_year=2020,
    )
    columns = [
        "event_id",
        "sweep_timestamp_utc",
        "midpoint_success_09_10",
        "primary_outcome",
        "asian_range_pips",
    ]
    pd.testing.assert_frame_equal(
        first.loc[:, columns].reset_index(drop=True),
        second.loc[
            second["trade_date"] == "2020-01-15", columns
        ].reset_index(drop=True),
    )
