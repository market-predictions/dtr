from __future__ import annotations

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.execution import ExecutionConfig
from dtr_lab.strategies.asia_sweep.integration import IntegrationConfig, execute_mapped_event
from dtr_lab.strategies.asia_sweep.proxy_normalization import (
    ProxyNormalizationConfig,
    mark_synthetic_proxy_event,
    mark_synthetic_proxy_minute_frame,
    normalize_proxy_fixture,
)
from dtr_lab.strategies.asia_sweep.shadow_baseline import (
    ShadowExecutionConfig,
    classify_variant,
    max_drawdown_r,
    simulate_event,
)

_EXECUTION = ExecutionConfig(
    tick_size=0.25,
    point_value=20.0,
    commission_per_side=2.25,
)
_INTEGRATION = IntegrationConfig(instrument="NQ_PROXY", execution=_EXECUTION)
_PROXY = ProxyNormalizationConfig(
    integration=_INTEGRATION,
    source_instrument="usatechidxusd",
)
_SHADOW = ShadowExecutionConfig(
    instrument="NQ_PROXY",
    source_instrument="usatechidxusd",
    point_value=20.0,
)


def _event() -> dict[str, object]:
    return {
        "instrument": "NQ_PROXY",
        "trade_date": "2024-01-02",
        "execution_window": "LONDON",
        "variant": "AS_A_AGGRESSIVE_RECLAIM",
        "status": "SIGNAL",
        "direction": 1,
        "entry_timestamp": "2024-01-02 02:05:00-05:00",
        "entry_price_raw": 100.123,
        "stop_price_raw": 99.123,
        "target_price_raw": 102.123,
    }


def _frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame


def _production(event: dict[str, object], frame: pd.DataFrame):
    marked_event = mark_synthetic_proxy_event(event, _PROXY)
    marked_frame = mark_synthetic_proxy_minute_frame(frame, marked_event, _PROXY)
    normalized = normalize_proxy_fixture(marked_event, marked_frame, _PROXY)
    return execute_mapped_event(normalized.event, normalized.one_minute, _INTEGRATION)[2]


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        (
            [
                {
                    "timestamp": "2024-01-02 02:05:00-05:00",
                    "open": 100.123,
                    "high": 100.623,
                    "low": 99.623,
                    "close": 100.123,
                    "is_active_quote": 1,
                },
                {
                    "timestamp": "2024-01-02 02:06:00-05:00",
                    "open": 100.623,
                    "high": 103.123,
                    "low": 100.123,
                    "close": 102.623,
                    "is_active_quote": 1,
                },
            ],
            "TARGET",
        ),
        (
            [
                {
                    "timestamp": "2024-01-02 02:05:00-05:00",
                    "open": 100.123,
                    "high": 100.623,
                    "low": 99.123,
                    "close": 99.623,
                    "is_active_quote": 1,
                }
            ],
            "STOP",
        ),
    ],
)
def test_shadow_matches_frozen_production_target_and_stop(
    rows: list[dict[str, object]],
    reason: str,
) -> None:
    event = _event()
    frame = _frame(rows)
    production = _production(event, frame)
    shadow = simulate_event(event, frame, _SHADOW)
    assert production.reason == reason
    assert shadow["reason"] == reason
    assert shadow["status"] == production.status
    assert shadow["entry_price"] == pytest.approx(production.entry_price)
    assert shadow["stop_price"] == pytest.approx(production.stop_price)
    assert shadow["target_price"] == pytest.approx(production.target_price)
    assert shadow["exit_price"] == pytest.approx(production.exit_price)
    assert shadow["net_r"] == pytest.approx(production.net_r)


def test_shadow_matches_frozen_production_time_exit() -> None:
    event = _event()
    timestamps = pd.date_range(
        "2024-01-02 02:05:00-05:00",
        "2024-01-02 06:00:00-05:00",
        freq="1min",
    )
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": 100.123,
            "high": 100.623,
            "low": 99.623,
            "close": 100.123,
            "is_active_quote": 1,
        }
    )
    production = _production(event, frame)
    shadow = simulate_event(event, frame, _SHADOW)
    assert production.reason == "TIME_EXIT"
    assert shadow["reason"] == "TIME_EXIT"
    assert shadow["net_r"] == pytest.approx(production.net_r)
    assert shadow["holding_minutes"] == production.holding_minutes


def test_shadow_matches_inactive_entry_block() -> None:
    event = _event()
    frame = _frame(
        [
            {
                "timestamp": "2024-01-02 02:05:00-05:00",
                "open": 100.123,
                "high": 100.123,
                "low": 100.123,
                "close": 100.123,
                "is_active_quote": 0,
            }
        ]
    )
    production = _production(event, frame)
    shadow = simulate_event(event, frame, _SHADOW)
    assert production.reason == "INACTIVE_ENTRY_MINUTE"
    assert shadow["reason"] == "INACTIVE_ENTRY_MINUTE"
    assert shadow["status"] == production.status


def test_max_drawdown_uses_running_equity() -> None:
    values = pd.Series([1.0, -2.0, -3.0, 2.0])
    assert max_drawdown_r(values) == pytest.approx(5.0)


def test_classification_is_not_promising_when_pooled_expectancy_is_negative() -> None:
    common = {
        "signals": 100,
        "exited": 100,
        "blocked": 0,
        "unresolved": 0,
        "expectancy_r": -0.01,
        "net_r": -1.0,
        "profit_factor": 0.98,
    }
    result = classify_variant(common, common, common, {"2023": common, "2024_H1": common})
    assert result == "NOT_PROMISING_CURRENT_SPEC"
