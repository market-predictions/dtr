from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.cluster_challenger import (
    ClusterExecutionConfig,
    causal_range_percentile,
    classify_cluster_window,
    cluster_is_near,
    simulate_cluster_signal,
    summarize_cluster_results,
)


def _window(rows: list[dict[str, float]]) -> pd.DataFrame:
    index = pd.date_range(
        "2023-01-03 02:00", periods=len(rows), freq="5min", tz="America/New_York"
    )
    frame = pd.DataFrame(rows, index=index)
    frame["bar_end"] = frame.index + pd.Timedelta(minutes=5)
    return frame


def _long_rows() -> list[dict[str, float]]:
    return [
        {"open": 100.5, "high": 101.0, "low": 99.0, "close": 100.5, "active": 1, "source_bars": 5},
        {"open": 100.5, "high": 101.5, "low": 100.1, "close": 100.2, "active": 1, "source_bars": 5},
        {"open": 100.2, "high": 101.2, "low": 100.0, "close": 100.3, "active": 1, "source_bars": 5},
        {"open": 100.3, "high": 101.8, "low": 100.2, "close": 101.6, "active": 1, "source_bars": 5},
        {"open": 101.6, "high": 102.0, "low": 101.0, "close": 101.8, "active": 1, "source_bars": 5},
    ]


def test_causal_percentile_and_cluster_boundary() -> None:
    assert causal_range_percentile(10, list(range(20))) == 0.525
    assert cluster_is_near(100.0, 99.0, 10.0)
    assert not cluster_is_near(100.0, 98.999, 10.0)


def test_full_cluster_sweep_reclaim_hold_and_impulse_break() -> None:
    result = classify_cluster_window(
        _window(_long_rows()),
        reference_high=110.0,
        reference_low=100.0,
        prior_day_high=115.0,
        prior_day_low=99.5,
    )
    assert result["status"] == "SIGNAL"
    assert result["direction"] == 1
    assert result["entry_timestamp"] == pd.Timestamp(
        "2023-01-03 02:20", tz="America/New_York"
    )


def test_opposite_asia_side_before_confirmation_invalidates() -> None:
    rows = _long_rows()
    rows[1]["high"] = 111.0
    result = classify_cluster_window(
        _window(rows),
        reference_high=110.0,
        reference_low=100.0,
        prior_day_high=115.0,
        prior_day_low=99.5,
    )
    assert result["reason"] == "OPPOSITE_ASIA_SIDE_BREACHED"


def test_midpoint_target_execution_includes_costs() -> None:
    index = pd.date_range(
        "2023-01-03 02:20", "2023-01-03 06:00", freq="1min", tz="America/New_York"
    )
    source = pd.DataFrame(
        {
            "timestamp": index,
            "open": 102.0,
            "high": 102.2,
            "low": 101.8,
            "close": 102.0,
            "is_active_quote": 1,
        }
    )
    source.loc[
        source["timestamp"] == pd.Timestamp("2023-01-03 02:25", tz="America/New_York"),
        "high",
    ] = 105.2
    event = {
        "event_id": "event",
        "instrument": "NQ_PROXY",
        "trade_date": "2023-01-03",
        "execution_window": "LONDON",
        "variant": "AS_E_PDH_PDL_CLUSTER_MODERATE_RANGE",
        "direction": 1,
        "range_percentile_60": 0.5,
        "cluster_distance_fraction": 0.05,
        "reference_high": 110.0,
        "reference_low": 100.0,
        "reference_range": 10.0,
        "prior_day_high": 115.0,
        "prior_day_low": 99.5,
        "sweep_timestamp": pd.Timestamp("2023-01-03 02:05", tz="America/New_York"),
        "confirmation_timestamp": pd.Timestamp("2023-01-03 02:15", tz="America/New_York"),
        "entry_timestamp": pd.Timestamp("2023-01-03 02:20", tz="America/New_York"),
        "window_end": pd.Timestamp("2023-01-03 06:00", tz="America/New_York"),
        "stop_price_raw": 98.5,
        "target_price_raw": 105.0,
    }
    result = simulate_cluster_signal(
        event, source, ClusterExecutionConfig("NQ_PROXY", "usatechidxusd", 20.0)
    )
    assert result["reason"] == "TARGET"
    assert result["net_r"] < result["gross_r"]
    assert result["planned_reward_r"] > 0


def test_promotion_gate_rejects_tiny_sample() -> None:
    ledger = pd.DataFrame(
        [
            {
                "status": "EXITED",
                "instrument": "NQ_PROXY",
                "trade_date": "2023-01-03",
                "entry_timestamp": "2023-01-03T02:20:00-05:00",
                "net_r": 0.5,
                "gross_r": 0.6,
                "planned_reward_r": 0.8,
                "reason": "TARGET",
            }
        ]
    )
    summary = summarize_cluster_results(ledger)
    assert summary["decision"] == "STOP_FINAL_CLUSTER_CHALLENGER"
    assert "NQ_PROXY_INSUFFICIENT_SAMPLE" in summary["promotion_blockers"]
    assert "ES_PROXY_INSUFFICIENT_SAMPLE" in summary["promotion_blockers"]
