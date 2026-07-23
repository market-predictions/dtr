from __future__ import annotations

import inspect
from copy import deepcopy
from decimal import Decimal

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep import proxy_normalization as normalization_module
from dtr_lab.strategies.asia_sweep.execution import (
    ExecutionConfig,
    ExecutionReason,
)
from dtr_lab.strategies.asia_sweep.integration import (
    IntegrationConfig,
    execute_mapped_event,
    stable_event_key,
)
from dtr_lab.strategies.asia_sweep.model import AsiaSweepVariant
from dtr_lab.strategies.asia_sweep.proxy_normalization import (
    ProxyNormalizationConfig,
    mark_synthetic_proxy_event,
    mark_synthetic_proxy_minute_frame,
    normalization_digest,
    normalize_proxy_event,
    normalize_proxy_fixture,
    normalize_proxy_minute_frame,
    source_event_digest,
    source_frame_digest,
    validate_normalized_integration_contract,
)

_EXECUTION = ExecutionConfig(
    tick_size=0.25,
    point_value=20.0,
    commission_per_side=2.25,
)
_INTEGRATION = IntegrationConfig(
    instrument="NQ_PROXY",
    execution=_EXECUTION,
)
_CONFIG = ProxyNormalizationConfig(
    integration=_INTEGRATION,
    source_instrument="usatechidxusd",
)


def _event(
    *,
    instrument: str = "NQ_PROXY",
    trade_date: str = "2024-01-02",
    execution_window: str = "LONDON",
    variant: str = AsiaSweepVariant.AGGRESSIVE_RECLAIM.value,
    status: str = "SIGNAL",
    direction: object = 1,
    entry_timestamp: object = "2024-01-02 02:05:00-05:00",
    entry: object = 100.123,
    stop: object = 99.123,
    target: object = 102.123,
    cfg: ProxyNormalizationConfig = _CONFIG,
) -> dict[str, object]:
    return mark_synthetic_proxy_event(
        {
            "instrument": instrument,
            "trade_date": trade_date,
            "execution_window": execution_window,
            "variant": variant,
            "status": status,
            "direction": direction,
            "entry_timestamp": entry_timestamp,
            "entry_price_raw": entry,
            "stop_price_raw": stop,
            "target_price_raw": target,
        },
        cfg,
    )


def _short_event(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "execution_window": "NEW_YORK",
        "variant": AsiaSweepVariant.DISPLACEMENT.value,
        "direction": -1,
        "entry_timestamp": "2024-01-02 08:35:00-05:00",
        "entry": 100.123,
        "stop": 101.123,
        "target": 98.123,
    }
    values.update(overrides)
    return _event(**values)


def _raw_frame(
    event: dict[str, object],
    *,
    timestamps: list[str] | None = None,
    rows: list[tuple[float, float, float, float, int]] | None = None,
    cfg: ProxyNormalizationConfig = _CONFIG,
) -> pd.DataFrame:
    if timestamps is None:
        timestamps = [
            str(event["entry_timestamp"]),
            str(pd.Timestamp(event["entry_timestamp"]) + pd.Timedelta(minutes=1)),
            str(pd.Timestamp(event["entry_timestamp"]) + pd.Timedelta(minutes=2)),
        ]
    if rows is None:
        rows = [
            (100.123, 100.249, 100.001, 100.111, 1),
            (100.249, 100.499, 99.999, 100.251, 1),
            (100.251, 100.501, 100.001, 100.249, 1),
        ]
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [row[0] for row in rows],
            "high": [row[1] for row in rows],
            "low": [row[2] for row in rows],
            "close": [row[3] for row in rows],
            "is_active_quote": [row[4] for row in rows],
            "volume": [1.0 for _ in rows],
        }
    )
    return mark_synthetic_proxy_minute_frame(frame, event, cfg)


def test_config_locks_source_identity_side_policy_grid_and_activity() -> None:
    with pytest.raises(ValueError, match="source_instrument must be non-empty"):
        ProxyNormalizationConfig(
            integration=_INTEGRATION,
            source_instrument="",
        )
    with pytest.raises(ValueError, match="frozen BID"):
        ProxyNormalizationConfig(
            integration=_INTEGRATION,
            source_instrument="usatechidxusd",
            price_side="ASK",
        )
    with pytest.raises(ValueError, match="frozen normalization policy"):
        ProxyNormalizationConfig(
            integration=_INTEGRATION,
            source_instrument="usatechidxusd",
            policy_version="DIRECTIONAL_PESSIMISTIC_V2",
        )
    with pytest.raises(ValueError, match="integer multiple"):
        ProxyNormalizationConfig(
            integration=_INTEGRATION,
            source_instrument="usatechidxusd",
            source_quote_increment="0.003",
        )
    with pytest.raises(ValueError, match="source_quote_increment must be positive"):
        ProxyNormalizationConfig(
            integration=_INTEGRATION,
            source_instrument="usatechidxusd",
            source_quote_increment="0",
        )
    no_activity = ExecutionConfig(
        tick_size=0.25,
        point_value=20.0,
        commission_per_side=2.25,
        activity_column=None,
    )
    with pytest.raises(ValueError, match="requires an activity column"):
        ProxyNormalizationConfig(
            integration=IntegrationConfig(
                instrument="NQ_PROXY",
                execution=no_activity,
            ),
            source_instrument="usatechidxusd",
        )
    assert _CONFIG.source_quote_increment == Decimal("0.001")
    assert _CONFIG.execution_tick == Decimal("0.25")
    assert _CONFIG.source_instrument == "usatechidxusd"
    assert _CONFIG.price_side == "BID"


def test_event_marker_returns_a_source_bound_copy_and_unmarked_is_rejected() -> None:
    raw = {
        "instrument": "NQ_PROXY",
        "trade_date": "2024-01-02",
        "execution_window": "LONDON",
        "variant": AsiaSweepVariant.AGGRESSIVE_RECLAIM.value,
        "status": "SIGNAL",
        "direction": 1,
        "entry_timestamp": "2024-01-02 02:05:00-05:00",
        "entry_price_raw": 100.123,
        "stop_price_raw": 99.123,
        "target_price_raw": 102.123,
    }
    marked = mark_synthetic_proxy_event(raw, _CONFIG)
    assert "proxy_source_kind" not in raw
    assert marked is not raw
    assert marked["proxy_source_instrument"] == "usatechidxusd"
    assert marked["proxy_price_side"] == "BID"
    with pytest.raises(ValueError, match="missing required fields"):
        normalize_proxy_event(raw, _CONFIG)


def test_source_event_digest_is_deterministic_and_sensitive_to_payload() -> None:
    event = _event()
    copied = dict(reversed(list(event.items())))
    assert source_event_digest(event, _CONFIG) == source_event_digest(copied, _CONFIG)
    revised = _event(stop=98.873, target=102.623)
    assert stable_event_key(event) == stable_event_key(revised)
    assert source_event_digest(event, _CONFIG) != source_event_digest(revised, _CONFIG)
    assert normalization_digest(event, _CONFIG) != normalization_digest(revised, _CONFIG)


def test_source_instrument_and_price_side_must_match_config() -> None:
    wrong_source = dict(_event())
    wrong_source["proxy_source_instrument"] = "usa500idxusd"
    with pytest.raises(ValueError, match="source instrument does not match"):
        normalize_proxy_event(wrong_source, _CONFIG)

    wrong_side = dict(_event())
    wrong_side["proxy_price_side"] = "ASK"
    with pytest.raises(ValueError, match="price side does not match"):
        normalize_proxy_event(wrong_side, _CONFIG)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"instrument": "ES_PROXY"}, "does not match integration economics"),
        ({"status": "REJECTED"}, "only SIGNAL"),
        ({"variant": "AS_X"}, "unknown proxy Asia Sweep variant"),
        ({"direction": 1.5}, "direction must be -1 or 1"),
        ({"direction": True}, "direction must be -1 or 1"),
        ({"entry_timestamp": "2024-01-02 02:05"}, "timezone-aware"),
        ({"entry_timestamp": "2024-01-02 02:05:30-05:00"}, "one-minute aligned"),
        ({"entry_timestamp": "2024-01-02 01:59:00-05:00"}, "inside its execution window"),
        ({"entry": 100.1234}, "off the source quote grid"),
        ({"entry": -100.123}, "must be positive"),
        ({"stop": float("inf")}, "must be finite"),
        ({"target": 102.124}, "inconsistent with source-grid 2.0R"),
        ({"stop": 101.123, "target": 102.123}, "risk must be positive"),
    ],
)
def test_invalid_raw_event_contract_fails_loudly(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_proxy_event(_event(**overrides), _CONFIG)


def test_derived_target_float_noise_is_canonicalized_but_market_prices_are_not() -> None:
    noisy = _event(target=102.12300000000001)
    normalized = normalize_proxy_event(noisy, _CONFIG)
    assert normalized["proxy_target_price_source"] == pytest.approx(102.123)
    assert normalized["proxy_target_price_reported"] == pytest.approx(
        102.12300000000001
    )

    with pytest.raises(ValueError, match="off the source quote grid"):
        normalize_proxy_event(_event(entry="100.1230001"), _CONFIG)


def test_long_event_normalization_is_directionally_adverse_and_exact_2r() -> None:
    normalized = normalize_proxy_event(_event(), _CONFIG)
    assert normalized["entry_price_raw"] == pytest.approx(100.25)
    assert normalized["stop_price_raw"] == pytest.approx(99.25)
    assert normalized["target_price_raw"] == pytest.approx(102.25)
    assert normalized["proxy_entry_price_source"] == pytest.approx(100.123)
    assert normalized["proxy_stop_price_source"] == pytest.approx(99.123)
    assert normalized["proxy_target_price_source"] == pytest.approx(102.123)
    assert normalized["proxy_source_instrument"] == "usatechidxusd"
    assert normalized["proxy_price_side"] == "BID"


def test_short_event_normalization_is_directionally_adverse_and_exact_2r() -> None:
    normalized = normalize_proxy_event(_short_event(), _CONFIG)
    assert normalized["entry_price_raw"] == pytest.approx(100.0)
    assert normalized["stop_price_raw"] == pytest.approx(101.0)
    assert normalized["target_price_raw"] == pytest.approx(98.0)


def test_exact_execution_grid_values_remain_unchanged() -> None:
    event = _event(entry=100.25, stop=99.0, target=102.75)
    normalized = normalize_proxy_event(event, _CONFIG)
    assert normalized["entry_price_raw"] == pytest.approx(100.25)
    assert normalized["stop_price_raw"] == pytest.approx(99.0)
    assert normalized["target_price_raw"] == pytest.approx(102.75)


def test_normalized_risk_collapse_is_rejected() -> None:
    event = _event(entry=100.249, stop=100.001, target=100.745)
    with pytest.raises(ValueError, match="risk must exceed one execution tick"):
        normalize_proxy_event(event, _CONFIG)


def test_distinct_nq_es_sources_and_economics_remain_separate() -> None:
    es_execution = ExecutionConfig(
        tick_size=0.25,
        point_value=50.0,
        commission_per_side=2.25,
    )
    es_integration = IntegrationConfig(
        instrument="ES_PROXY",
        execution=es_execution,
    )
    es_config = ProxyNormalizationConfig(
        integration=es_integration,
        source_instrument="usa500idxusd",
    )
    es_event = _event(instrument="ES_PROXY", cfg=es_config)
    es_result = normalize_proxy_fixture(
        es_event,
        _raw_frame(es_event, cfg=es_config),
        es_config,
    )
    assert es_result.event["proxy_source_instrument"] == "usa500idxusd"
    assert es_result.one_minute.attrs["asia_sweep_proxy_source_instrument"] == (
        "usa500idxusd"
    )
    assert es_config.integration.execution.point_value == pytest.approx(50.0)
    assert _CONFIG.integration.execution.point_value == pytest.approx(20.0)


def test_proxy_frame_marker_returns_copy_and_binds_source_event() -> None:
    event = _event()
    raw = pd.DataFrame(
        {
            "timestamp": [event["entry_timestamp"]],
            "open": [100.123],
            "high": [100.249],
            "low": [100.001],
            "close": [100.111],
            "is_active_quote": [1],
        }
    )
    marked = mark_synthetic_proxy_minute_frame(raw, event, _CONFIG)
    assert raw.attrs == {}
    assert marked is not raw
    assert marked.attrs["asia_sweep_proxy_event_key"] == stable_event_key(event)
    assert marked.attrs["asia_sweep_proxy_source_instrument"] == "usatechidxusd"
    assert marked.attrs["asia_sweep_proxy_price_side"] == "BID"


def test_unmarked_swapped_stale_payload_and_source_frames_are_rejected() -> None:
    event = _event()
    unmarked = pd.DataFrame(
        {
            "timestamp": [event["entry_timestamp"]],
            "open": [100.123],
            "high": [100.249],
            "low": [100.001],
            "close": [100.111],
            "is_active_quote": [1],
        }
    )
    with pytest.raises(ValueError, match="not a marked synthetic proxy fixture"):
        normalize_proxy_minute_frame(unmarked, event, _CONFIG)

    other = _event(
        execution_window="NEW_YORK",
        entry_timestamp="2024-01-02 08:35:00-05:00",
    )
    with pytest.raises(ValueError, match="event key does not match"):
        normalize_proxy_minute_frame(_raw_frame(other), event, _CONFIG)

    revised = _event(stop=98.873, target=102.623)
    with pytest.raises(ValueError, match="event digest does not match"):
        normalize_proxy_minute_frame(_raw_frame(event), revised, _CONFIG)

    wrong_source = _raw_frame(event)
    wrong_source.attrs["asia_sweep_proxy_source_instrument"] = "usa500idxusd"
    with pytest.raises(ValueError, match="source instrument does not match"):
        normalize_proxy_minute_frame(wrong_source, event, _CONFIG)

    wrong_side = _raw_frame(event)
    wrong_side.attrs["asia_sweep_proxy_price_side"] = "ASK"
    with pytest.raises(ValueError, match="price side does not match"):
        normalize_proxy_minute_frame(wrong_side, event, _CONFIG)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda frame: frame.assign(open=100.1234), "off the source quote grid"),
        (lambda frame: frame.assign(high=float("inf")), "must be finite"),
        (lambda frame: frame.assign(is_active_quote=2), "exactly 0 or 1"),
    ],
)
def test_invalid_proxy_frame_values_fail_loudly(mutator, message: str) -> None:
    event = _event()
    frame = mutator(_raw_frame(event))
    frame = mark_synthetic_proxy_minute_frame(frame, event, _CONFIG)
    with pytest.raises(ValueError, match=message):
        normalize_proxy_minute_frame(frame, event, _CONFIG)


def test_invalid_ohlc_duplicate_naive_and_off_minute_timestamps_fail() -> None:
    event = _event()
    invalid_ohlc = _raw_frame(event)
    invalid_ohlc.loc[0, "high"] = 100.0
    invalid_ohlc = mark_synthetic_proxy_minute_frame(invalid_ohlc, event, _CONFIG)
    with pytest.raises(ValueError, match="invalid raw OHLC"):
        normalize_proxy_minute_frame(invalid_ohlc, event, _CONFIG)

    duplicate = _raw_frame(event)
    duplicate.loc[1, "timestamp"] = duplicate.loc[0, "timestamp"]
    duplicate = mark_synthetic_proxy_minute_frame(duplicate, event, _CONFIG)
    with pytest.raises(ValueError, match="duplicate timestamps"):
        normalize_proxy_minute_frame(duplicate, event, _CONFIG)

    naive = _raw_frame(event)
    naive["timestamp"] = pd.to_datetime(naive["timestamp"]).dt.tz_localize(None)
    naive = mark_synthetic_proxy_minute_frame(naive, event, _CONFIG)
    with pytest.raises(ValueError, match="timezone-aware"):
        normalize_proxy_minute_frame(naive, event, _CONFIG)

    off_minute = _raw_frame(event)
    off_minute.loc[0, "timestamp"] = pd.Timestamp(event["entry_timestamp"]) + pd.Timedelta(
        seconds=30
    )
    off_minute = mark_synthetic_proxy_minute_frame(off_minute, event, _CONFIG)
    with pytest.raises(ValueError, match="one-minute aligned"):
        normalize_proxy_minute_frame(off_minute, event, _CONFIG)


def test_rows_before_entry_or_after_window_end_are_rejected() -> None:
    event = _event()
    before = _raw_frame(
        event,
        timestamps=["2024-01-02 02:04:00-05:00"],
        rows=[(100.123, 100.249, 100.001, 100.111, 1)],
    )
    with pytest.raises(ValueError, match="before event entry"):
        normalize_proxy_minute_frame(before, event, _CONFIG)

    after = _raw_frame(
        event,
        timestamps=["2024-01-02 06:01:00-05:00"],
        rows=[(100.123, 100.249, 100.001, 100.111, 1)],
    )
    with pytest.raises(ValueError, match="after execution-window end"):
        normalize_proxy_minute_frame(after, event, _CONFIG)


def test_long_bar_normalization_is_pessimistic_and_repairs_minimal_envelope() -> None:
    event = _event()
    normalized = normalize_proxy_minute_frame(_raw_frame(event), event, _CONFIG)
    entry = normalized.iloc[0]
    later = normalized.iloc[1]

    assert entry["open"] == pytest.approx(100.25)
    assert entry["high"] == pytest.approx(100.25)
    assert entry["low"] == pytest.approx(100.0)
    assert entry["close"] == pytest.approx(100.0)
    assert bool(entry["proxy_high_envelope_repaired"]) is True
    assert bool(entry["proxy_low_envelope_repaired"]) is False

    assert later["open"] == pytest.approx(100.0)
    assert later["high"] == pytest.approx(100.25)
    assert later["low"] == pytest.approx(99.75)
    assert later["close"] == pytest.approx(100.25)
    assert later["high"] <= later["proxy_high_source"]
    assert later["low"] <= later["proxy_low_source"]


def test_short_bar_normalization_is_pessimistic_and_repairs_minimal_envelope() -> None:
    event = _short_event()
    normalized = normalize_proxy_minute_frame(_raw_frame(event), event, _CONFIG)
    entry = normalized.iloc[0]
    later = normalized.iloc[1]

    assert entry["open"] == pytest.approx(100.0)
    assert entry["high"] == pytest.approx(100.25)
    assert entry["low"] == pytest.approx(100.0)
    assert entry["close"] == pytest.approx(100.25)
    assert bool(entry["proxy_high_envelope_repaired"]) is False
    assert bool(entry["proxy_low_envelope_repaired"]) is True

    assert later["open"] == pytest.approx(100.25)
    assert later["high"] == pytest.approx(100.5)
    assert later["low"] == pytest.approx(100.0)
    assert later["close"] == pytest.approx(100.5)
    assert later["high"] >= later["proxy_high_source"]
    assert later["low"] >= later["proxy_low_source"]


def test_timestamps_activity_and_missing_minutes_are_preserved_exactly() -> None:
    event = _event()
    timestamps = [
        "2024-01-02 02:05:00-05:00",
        "2024-01-02 02:07:00-05:00",
    ]
    rows = [
        (100.123, 100.249, 100.001, 100.111, 1),
        (100.249, 100.499, 99.999, 100.251, 0),
    ]
    raw = _raw_frame(event, timestamps=timestamps, rows=rows)
    normalized = normalize_proxy_minute_frame(raw, event, _CONFIG)
    assert list(normalized["timestamp"]) == [
        pd.Timestamp(value).tz_convert("America/New_York") for value in timestamps
    ]
    assert list(normalized["is_active_quote"]) == [1, 0]
    assert pd.Timestamp("2024-01-02 02:06:00-05:00") not in set(
        normalized["timestamp"]
    )


def test_source_frame_digest_is_order_invariant_and_data_sensitive() -> None:
    event = _event()
    frame = _raw_frame(event)
    reversed_frame = frame.iloc[::-1].copy()
    reversed_frame = mark_synthetic_proxy_minute_frame(reversed_frame, event, _CONFIG)
    assert source_frame_digest(frame, event, _CONFIG) == source_frame_digest(
        reversed_frame,
        event,
        _CONFIG,
    )

    changed = frame.copy(deep=True)
    changed.loc[1, "high"] = 100.500
    changed = mark_synthetic_proxy_minute_frame(changed, event, _CONFIG)
    assert source_frame_digest(frame, event, _CONFIG) != source_frame_digest(
        changed,
        event,
        _CONFIG,
    )


def test_normalized_fixture_is_deterministic_and_satisfies_wp5_binding() -> None:
    event = _event()
    frame = _raw_frame(event)
    first = normalize_proxy_fixture(event, frame, _CONFIG)
    reversed_frame = mark_synthetic_proxy_minute_frame(
        frame.iloc[::-1].copy(),
        event,
        _CONFIG,
    )
    second = normalize_proxy_fixture(event, reversed_frame, _CONFIG)

    pd.testing.assert_frame_equal(first.one_minute, second.one_minute)
    assert first.event == second.event
    assert first.source_event_digest == second.source_event_digest
    assert first.normalization_digest == second.normalization_digest
    assert first.source_frame_digest == second.source_frame_digest
    assert validate_normalized_integration_contract(first, _CONFIG) is True


def test_normalized_output_can_enter_frozen_synthetic_execution_contract() -> None:
    event = _event()
    frame = _raw_frame(
        event,
        rows=[
            (100.123, 103.249, 100.001, 100.111, 1),
            (100.249, 100.499, 99.999, 100.251, 1),
            (100.251, 100.501, 100.001, 100.249, 1),
        ],
    )
    result = normalize_proxy_fixture(event, frame, _CONFIG)
    key, _, outcome = execute_mapped_event(
        result.event,
        result.one_minute,
        _INTEGRATION,
    )
    assert key == stable_event_key(event)
    assert outcome.reason == ExecutionReason.TARGET
    assert outcome.gross_r == pytest.approx(2.0)


def test_raw_inputs_remain_immutable() -> None:
    event = _event()
    event_before = deepcopy(event)
    frame = _raw_frame(event)
    frame_before = frame.copy(deep=True)
    attrs_before = dict(frame.attrs)

    normalize_proxy_fixture(event, frame, _CONFIG)
    assert event == event_before
    pd.testing.assert_frame_equal(frame, frame_before)
    assert frame.attrs == attrs_before


def test_normalization_module_never_calls_execution_or_private_loaders() -> None:
    source = inspect.getsource(normalization_module)
    assert "simulate_execution" not in source
    assert "execute_mapped_event" not in source
    assert "load_one_minute_zip" not in source
    assert "dtr_lab.research.engine" not in source
