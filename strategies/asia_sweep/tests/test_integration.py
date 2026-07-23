from __future__ import annotations

import inspect
from copy import deepcopy

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep import integration as integration_module
from dtr_lab.strategies.asia_sweep.execution import (
    ExecutionConfig,
    ExecutionReason,
    mark_synthetic_fixture,
)
from dtr_lab.strategies.asia_sweep.integration import (
    IntegrationConfig,
    execute_mapped_event,
    map_event_to_execution_signal,
    mark_synthetic_event_packet,
    replay_synthetic_event_packet,
    stable_event_key,
    validate_integrated_prefix,
)
from dtr_lab.strategies.asia_sweep.model import AsiaSweepVariant

_EXECUTION = ExecutionConfig(
    tick_size=0.25,
    point_value=20.0,
    commission_per_side=2.25,
)
_CONFIG = IntegrationConfig(execution=_EXECUTION)


def _event(
    *,
    instrument: str = "NQ_SYNTHETIC",
    trade_date: str = "2024-01-02",
    execution_window: str = "LONDON",
    variant: str = AsiaSweepVariant.AGGRESSIVE_RECLAIM.value,
    status: str = "SIGNAL",
    direction: object = 1,
    entry_timestamp: object = "2024-01-02 02:05:00-05:00",
    entry: object = 100.0,
    stop: object = 99.0,
    target: object = 102.0,
) -> dict[str, object]:
    return {
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
    }


def _short_event(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "instrument": "ES_SYNTHETIC",
        "trade_date": "2024-01-02",
        "execution_window": "NEW_YORK",
        "variant": AsiaSweepVariant.DISPLACEMENT.value,
        "direction": -1,
        "entry_timestamp": "2024-01-02 08:35:00-05:00",
        "entry": 100.0,
        "stop": 101.0,
        "target": 98.0,
    }
    values.update(overrides)
    return _event(**values)


def _frame(
    *,
    start: str = "2024-01-02 02:05:00-05:00",
    periods: int = 3,
    price: float = 100.0,
) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=periods, freq="1min")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": price,
            "high": price + 0.25,
            "low": price - 0.25,
            "close": price,
            "is_active_quote": 1,
        }
    )
    return mark_synthetic_fixture(frame)


def _target_frame(event: dict[str, object]) -> pd.DataFrame:
    direction = int(event["direction"])
    frame = _frame(
        start=str(event["entry_timestamp"]),
        price=float(event["entry_price_raw"]),
    )
    if direction > 0:
        frame.loc[0, "high"] = 103.0
    else:
        frame.loc[0, "low"] = 97.0
    return frame


def _marked_packet(events: list[dict[str, object]]) -> pd.DataFrame:
    return mark_synthetic_event_packet(pd.DataFrame(events))


def test_integration_config_rejects_invalid_timezone_and_tolerance() -> None:
    with pytest.raises(ValueError, match="unknown session_timezone"):
        IntegrationConfig(execution=_EXECUTION, session_timezone="Mars/Olympus")
    with pytest.raises(ValueError, match="price_tolerance"):
        IntegrationConfig(execution=_EXECUTION, price_tolerance=0.0)


def test_stable_event_key_is_deterministic_and_identity_only() -> None:
    event = _event()
    changed_non_identity = {**event, "entry_price_raw": 250.0, "status": "REJECTED"}
    assert stable_event_key(event) == stable_event_key(dict(reversed(list(event.items()))))
    assert stable_event_key(event) == stable_event_key(changed_non_identity)
    assert stable_event_key(event) != stable_event_key({**event, "execution_window": "NEW_YORK"})


def test_identity_rejects_missing_dates_and_edge_whitespace() -> None:
    with pytest.raises(ValueError, match="trade_date is missing"):
        stable_event_key(_event(trade_date=pd.NaT))
    with pytest.raises(ValueError, match="edge whitespace"):
        stable_event_key(_event(instrument=" NQ_SYNTHETIC"))


@pytest.mark.parametrize("variant", [variant.value for variant in AsiaSweepVariant])
def test_all_preregistered_variants_map_without_selection(variant: str) -> None:
    signal = map_event_to_execution_signal(_event(variant=variant), _CONFIG)
    assert signal.target_rr == pytest.approx(2.0)
    assert signal.signal_timestamp == pd.Timestamp("2024-01-02 02:05:00-05:00")


def test_long_and_short_mapping_preserve_stop_and_window_end() -> None:
    long_signal = map_event_to_execution_signal(_event(), _CONFIG)
    short_signal = map_event_to_execution_signal(_short_event(), _CONFIG)
    assert long_signal.direction == 1
    assert long_signal.stop_price == pytest.approx(99.0)
    assert long_signal.window_end == pd.Timestamp("2024-01-02 06:00", tz="America/New_York")
    assert short_signal.direction == -1
    assert short_signal.stop_price == pytest.approx(101.0)
    assert short_signal.window_end == pd.Timestamp("2024-01-02 11:30", tz="America/New_York")


def test_timezone_aware_utc_entry_is_converted_to_new_york() -> None:
    event = _event(entry_timestamp="2024-01-02 07:05:00+00:00")
    signal = map_event_to_execution_signal(event, _CONFIG)
    assert signal.signal_timestamp == pd.Timestamp("2024-01-02 02:05", tz="America/New_York")


def test_dst_wall_calendar_mapping_uses_post_transition_offset() -> None:
    event = _event(
        trade_date="2024-03-11",
        entry_timestamp="2024-03-11 02:05:00-04:00",
    )
    signal = map_event_to_execution_signal(event, _CONFIG)
    assert signal.window_end == pd.Timestamp("2024-03-11 06:00:00-04:00")
    assert signal.window_end.utcoffset() == pd.Timedelta(hours=-4)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"status": "REJECTED"}, "only SIGNAL"),
        ({"variant": "AS_X"}, "unknown Asia Sweep variant"),
        ({"direction": 1.5}, "direction must be -1 or 1"),
        ({"direction": True}, "direction must be -1 or 1"),
        ({"direction": float("nan")}, "direction must be -1 or 1"),
        ({"entry_timestamp": "2024-01-02 02:05"}, "timezone-aware"),
        ({"entry_timestamp": "2024-01-02 02:05:30-05:00"}, "one-minute aligned"),
    ],
)
def test_invalid_event_semantics_fail_loudly(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        map_event_to_execution_signal(_event(**overrides), _CONFIG)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "trade_date": "2024-01-03",
                "entry_timestamp": "2024-01-02 02:05:00-05:00",
            },
            "local date must equal trade_date",
        ),
        ({"entry_timestamp": "2024-01-02 01:59:00-05:00"}, "inside its execution window"),
        ({"entry_timestamp": "2024-01-02 06:00:00-05:00"}, "inside its execution window"),
        ({"execution_window": "ASIA"}, "unknown execution window"),
    ],
)
def test_event_must_belong_to_declared_trade_date_and_window(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        map_event_to_execution_signal(_event(**overrides), _CONFIG)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"entry": 100.10}, "event entry is off"),
        ({"stop": float("inf")}, "event stop must be finite"),
        ({"stop": 99.75, "target": 100.50}, "risk must exceed one tick"),
        ({"target": 102.25}, "target is inconsistent"),
        ({"stop": 101.0, "target": 102.0}, "risk must exceed one tick"),
    ],
)
def test_event_price_geometry_is_strict(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        map_event_to_execution_signal(_event(**overrides), _CONFIG)


@pytest.mark.parametrize("event", [_event(), _short_event()])
def test_mapped_long_and_short_execute_on_synthetic_target_fixtures(
    event: dict[str, object],
) -> None:
    key, signal, outcome = execute_mapped_event(event, _target_frame(event), _CONFIG)
    assert key == stable_event_key(event)
    assert signal.direction == int(event["direction"])
    assert outcome.reason == ExecutionReason.TARGET
    assert outcome.gross_r == pytest.approx(2.0)
    assert outcome.net_r is not None


def test_unmarked_minute_source_and_off_grid_ohlc_are_rejected() -> None:
    frame = _target_frame(_event())
    frame.attrs.clear()
    with pytest.raises(ValueError, match="synthetic-test-only"):
        execute_mapped_event(_event(), frame, _CONFIG)

    frame = _target_frame(_event())
    frame.loc[0, "high"] = 102.13
    with pytest.raises(ValueError, match="minute high is off"):
        execute_mapped_event(_event(), frame, _CONFIG)


def test_unmarked_empty_and_incomplete_event_packets_are_rejected() -> None:
    unmarked = pd.DataFrame([_event()])
    with pytest.raises(ValueError, match="synthetic-packet-only"):
        replay_synthetic_event_packet(unmarked, {}, _CONFIG)

    empty = mark_synthetic_event_packet(pd.DataFrame(columns=sorted(_event())))
    with pytest.raises(ValueError, match="event packet is empty"):
        replay_synthetic_event_packet(empty, {}, _CONFIG)

    incomplete = mark_synthetic_event_packet(pd.DataFrame([{"instrument": "NQ"}]))
    with pytest.raises(ValueError, match="missing required columns"):
        replay_synthetic_event_packet(incomplete, {}, _CONFIG)


def test_packet_rejects_duplicate_missing_and_orphan_frame_keys() -> None:
    event = _event()
    duplicate_packet = _marked_packet([event, dict(event)])
    key = stable_event_key(event)
    with pytest.raises(ValueError, match="duplicate stable keys"):
        replay_synthetic_event_packet(duplicate_packet, {key: _target_frame(event)}, _CONFIG)

    packet = _marked_packet([event])
    with pytest.raises(ValueError, match="missing minute frame"):
        replay_synthetic_event_packet(packet, {}, _CONFIG)
    with pytest.raises(ValueError, match="orphan minute frame"):
        replay_synthetic_event_packet(
            packet,
            {key: _target_frame(event), "orphan": _target_frame(event)},
            _CONFIG,
        )


def test_batch_replay_is_order_independent_and_matches_row_execution() -> None:
    long_event = _event()
    short_event = _short_event()
    events = [short_event, long_event]
    packet = _marked_packet(events)
    frames = {stable_event_key(event): _target_frame(event) for event in events}

    first = replay_synthetic_event_packet(packet, frames, _CONFIG)
    shuffled = _marked_packet(pd.DataFrame(events).iloc[::-1].reset_index(drop=True))
    second = replay_synthetic_event_packet(shuffled, frames, _CONFIG)
    pd.testing.assert_frame_equal(first, second)
    assert first["stable_event_key"].is_monotonic_increasing

    for event in events:
        key, signal, outcome = execute_mapped_event(event, frames[stable_event_key(event)], _CONFIG)
        row = first.loc[first["stable_event_key"] == key].iloc[0]
        assert row["mapped_signal_timestamp"] == signal.signal_timestamp
        assert row["mapped_window_end"] == signal.window_end
        assert row["reason"] == outcome.reason
        assert row["net_r"] == pytest.approx(outcome.net_r)


def test_mapping_and_batch_replay_do_not_mutate_inputs() -> None:
    event = _event()
    event_before = deepcopy(event)
    frame = _target_frame(event)
    frame_before = frame.copy(deep=True)
    frame_attrs = dict(frame.attrs)
    packet = _marked_packet([event])
    packet_before = packet.copy(deep=True)
    packet_attrs = dict(packet.attrs)

    replay_synthetic_event_packet(packet, {stable_event_key(event): frame}, _CONFIG)
    assert event == event_before
    pd.testing.assert_frame_equal(frame, frame_before)
    pd.testing.assert_frame_equal(packet, packet_before)
    assert frame.attrs == frame_attrs
    assert packet.attrs == packet_attrs


def test_integrated_prefix_reproduces_target_and_data_gap_exit() -> None:
    event = _event()
    assert validate_integrated_prefix(event, _target_frame(event), _CONFIG) is True

    gap_frame = _frame(periods=4)
    gap_frame = gap_frame[
        gap_frame["timestamp"] != pd.Timestamp("2024-01-02 02:07:00-05:00")
    ].copy()
    mark_synthetic_fixture(gap_frame)
    assert validate_integrated_prefix(event, gap_frame, _CONFIG) is True
    _, _, outcome = execute_mapped_event(event, gap_frame, _CONFIG)
    assert outcome.reason == ExecutionReason.DATA_GAP_LIQUIDATION


def test_integration_module_never_calls_active_dtr_signal_generator() -> None:
    source = inspect.getsource(integration_module)
    assert "generate_signals" not in source
    assert "dtr_lab.research.engine" not in source
