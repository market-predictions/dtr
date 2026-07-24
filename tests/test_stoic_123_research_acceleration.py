from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from stoic_123_lab import ES_PROXY_SPEC
from stoic_123_lab.config import SequenceConfig
from stoic_123_lab.cost_repricing import reprice_single_stream_costs
from stoic_123_lab.research_cache import FrameCache, cache_key
from stoic_123_lab.research_runtime import StageTimer, plan_for_mode, primary_futility_reason
from stoic_123_lab.validation import run_scenario


def _config() -> SequenceConfig:
    return SequenceConfig(
        arm_id="TEST",
        description="test",
        map_mode="none",
        allow_long=True,
        allow_short=False,
        max_hold_minutes=1,
    )


def test_execution_modes_reduce_work_without_changing_certification_gate_scope() -> None:
    screen = plan_for_mode("screen")
    validate = plan_for_mode("validate")
    certify = plan_for_mode("certify")
    legacy = plan_for_mode("legacy")

    assert screen.matched_control_replicates == 0
    assert screen.candidate_bootstrap_iterations == 0
    assert screen.early_stop
    assert validate.candidate_bootstrap_iterations == 1_000
    assert validate.matched_control_candidates == ()
    assert certify.matched_control_candidates == ("RTH_LONG_FULL",)
    assert certify.candidate_bootstrap_iterations == 10_000
    assert not certify.early_stop
    assert legacy.matched_control_candidates == ("RTH_LONG_EMA_BREAK", "RTH_LONG_FULL")
    assert legacy.diagnostic_bootstrap_iterations == 10_000
    assert not legacy.exact_cost_repricing


def test_cache_key_is_order_independent() -> None:
    left = cache_key("bars", {"minutes": 5, "source": "abc"})
    right = cache_key("bars", {"source": "abc", "minutes": 5})
    assert left == right


def test_frame_cache_round_trip_avoids_second_build(tmp_path) -> None:
    calls = 0

    def build() -> pd.DataFrame:
        nonlocal calls
        calls += 1
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2026-01-01", periods=3, freq="min"),
                "close": [1.0, 2.0, 3.0],
            }
        )

    cache = FrameCache(tmp_path)
    first, first_hit, first_key = cache.get_or_build(
        "bars",
        {"source": "abc", "minutes": 1},
        build,
    )
    second, second_hit, second_key = cache.get_or_build(
        "bars",
        {"minutes": 1, "source": "abc"},
        build,
    )

    assert calls == 1
    assert not first_hit
    assert second_hit
    assert first_key == second_key
    pd.testing.assert_frame_equal(first, second)
    assert cache.summary()["hits"] == 1
    assert cache.summary()["misses"] == 1


def test_exact_cost_repricing_matches_full_single_stream_resimulation() -> None:
    one_minute = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-02 14:30", periods=4, freq="min"),
            "open": [100.0, 101.0, 102.0, 103.0],
            "high": [100.5, 102.0, 103.0, 104.0],
            "low": [99.5, 100.5, 101.5, 102.5],
            "close": [100.0, 101.5, 102.5, 103.5],
            "volume": [1.0, 1.0, 1.0, 1.0],
        }
    )
    events = pd.DataFrame(
        [
            {
                "arm_id": "TEST",
                "direction": 1,
                "signal_time": pd.Timestamp("2026-01-02 14:31"),
                "breakout_close": 101.0,
                "protective_boundary": 99.0,
                "base_lock_time": pd.Timestamp("2026-01-02 14:30"),
            }
        ]
    )
    management = pd.DataFrame()
    baseline_config = _config()
    stressed_config = replace(baseline_config, slippage_ticks_each_side=2.0)

    baseline = run_scenario(
        one_minute=one_minute,
        events=events,
        management_events=management,
        spec=ES_PROXY_SPEC,
        config=baseline_config,
    )
    stressed = run_scenario(
        one_minute=one_minute,
        events=events,
        management_events=management,
        spec=ES_PROXY_SPEC,
        config=stressed_config,
    )
    repriced = reprice_single_stream_costs(
        baseline,
        spec=ES_PROXY_SPEC,
        config=stressed_config,
        arm_id="TEST_STRESSED",
    )

    assert len(stressed) == len(repriced) == 1
    np.testing.assert_allclose(repriced["gross_r"], stressed["gross_r"], atol=0, rtol=0)
    np.testing.assert_allclose(repriced["cost_r"], stressed["cost_r"], atol=1e-15, rtol=0)
    np.testing.assert_allclose(repriced["pnl_r"], stressed["pnl_r"], atol=1e-15, rtol=0)


def test_primary_futility_stops_only_when_promotion_is_already_impossible() -> None:
    assert primary_futility_reason({"trades": 29, "expectancy_r": 1.0, "net_r": 1.0})
    assert primary_futility_reason({"trades": 100, "expectancy_r": 0.0, "net_r": 1.0})
    assert primary_futility_reason({"trades": 100, "expectancy_r": 0.1, "net_r": 5.0}) is None


def test_stage_timer_publishes_json_and_csv(tmp_path) -> None:
    timer = StageTimer()
    with timer.measure("unit", partition="test"):
        pass
    timer.write(tmp_path)
    assert (tmp_path / "timings.json").exists()
    assert (tmp_path / "timings.csv").exists()
    assert timer.records[0].stage == "unit"
    assert timer.records[0].elapsed_seconds >= 0
