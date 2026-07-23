from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from dtr_lab.research.engine import resample_5m
from dtr_lab.strategies.asia_sweep.data import ZipCsvSchema, load_one_minute_zip
from dtr_lab.strategies.asia_sweep.integrity import (
    audit_activity_interval,
    audit_minute_interval,
)
from dtr_lab.strategies.asia_sweep.model import (
    AsiaSweepConfig,
    AsiaSweepVariant,
    ExecutionWindow,
)
from dtr_lab.strategies.asia_sweep.signals import _asia_bounds, build_event_ledger

_LONDON_ONLY = (ExecutionWindow("LONDON", 2, 0, 6, 0),)


def _write_zip(path: Path, frame: pd.DataFrame) -> None:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("bars.csv", frame.to_csv(index=False))


def _proxy_schema() -> ZipCsvSchema:
    return ZipCsvSchema(
        timestamp_column="timestamp UTC",
        timestamp_format="%Y-%m-%dT%H:%M:%SZ",
        required_columns=(
            "open",
            "high",
            "low",
            "close",
            "volume",
            "is_active_quote",
        ),
        source_timezone="UTC",
        session_timezone="America/New_York",
    )


def _config(variant: AsiaSweepVariant = AsiaSweepVariant.AGGRESSIVE_RECLAIM) -> AsiaSweepConfig:
    return AsiaSweepConfig(
        name="proxy-test",
        variant=variant,
        tick_size=0.25,
        point_value=20.0,
        commission_per_side=2.25,
        windows=_LONDON_ONLY,
        activity_column="is_active_quote",
        minimum_active_minutes=1,
        maximum_consecutive_inactive_minutes=10,
    )


def _minute_frame(
    *,
    trade_date: str,
    sweep_time: str,
    future_inactive_start: str | None = None,
    future_inactive_minutes: int = 0,
) -> pd.DataFrame:
    day = pd.Timestamp(trade_date)
    start = day - pd.DateOffset(days=1) + pd.Timedelta(hours=18)
    end = day + pd.Timedelta(hours=6)
    timestamps = pd.date_range(start, end, freq="1min", inclusive="left")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": 100.0,
            "high": 100.8,
            "low": 99.2,
            "close": 100.0,
            "volume": 1.0,
            "is_active_quote": 1,
        }
    )
    asia_end = day + pd.Timedelta(hours=2)
    asia_mask = frame["timestamp"] < asia_end
    frame.loc[asia_mask, "high"] = 101.0
    frame.loc[asia_mask, "low"] = 99.0

    sweep_start = pd.Timestamp(f"{trade_date} {sweep_time}")
    sweep_end = sweep_start + pd.Timedelta(minutes=5)
    sweep_mask = (frame["timestamp"] >= sweep_start) & (frame["timestamp"] < sweep_end)
    frame.loc[sweep_mask, ["open", "high", "low", "close"]] = [
        99.4,
        99.6,
        98.4,
        99.2,
    ]

    if future_inactive_start is not None:
        inactive_start = pd.Timestamp(f"{trade_date} {future_inactive_start}")
        inactive_end = inactive_start + pd.Timedelta(minutes=future_inactive_minutes)
        inactive_mask = (
            (frame["timestamp"] >= inactive_start)
            & (frame["timestamp"] < inactive_end)
        )
        frame.loc[inactive_mask, ["volume", "is_active_quote"]] = [0.0, 0]
    return frame


def test_proxy_loader_preserves_dst_offsets_and_unique_instants(tmp_path: Path) -> None:
    path = tmp_path / "proxy.zip"
    frame = pd.DataFrame(
        {
            "timestamp UTC": [
                "2024-03-10T06:59:00Z",
                "2024-03-10T07:00:00Z",
                "2024-11-03T05:59:00Z",
                "2024-11-03T06:00:00Z",
            ],
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 1.0,
            "is_active_quote": 1,
        }
    )
    _write_zip(path, frame)
    result = load_one_minute_zip(path, _proxy_schema())
    labels = result["timestamp"].dt.strftime("%Y-%m-%d %H:%M %z").tolist()
    assert labels == [
        "2024-03-10 01:59 -0500",
        "2024-03-10 03:00 -0400",
        "2024-11-03 01:59 -0400",
        "2024-11-03 01:00 -0500",
    ]
    assert not bool(result["timestamp"].duplicated().any())
    assert str(result["timestamp_source"].dt.tz) == "UTC"


def test_asia_bounds_use_wall_calendar_across_dst_weekends() -> None:
    spring = pd.Timestamp("2024-03-11", tz="America/New_York")
    autumn = pd.Timestamp("2024-11-04", tz="America/New_York")
    spring_start, spring_end = _asia_bounds(spring, _config())
    autumn_start, autumn_end = _asia_bounds(autumn, _config())
    assert spring_start.isoformat() == "2024-03-10T18:00:00-04:00"
    assert spring_end.isoformat() == "2024-03-11T02:00:00-04:00"
    assert autumn_start.isoformat() == "2024-11-03T18:00:00-05:00"
    assert autumn_end.isoformat() == "2024-11-04T02:00:00-05:00"


def test_activity_gate_accepts_ten_inactive_minutes_and_rejects_eleven() -> None:
    timestamps = pd.date_range("2024-01-02 02:00", periods=12, freq="1min")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "is_active_quote": [1, *([0] * 11)],
        }
    )
    accepted = audit_activity_interval(
        frame.iloc[:11],
        timestamps[0],
        timestamps[11],
        activity_column="is_active_quote",
        minimum_active_minutes=1,
        maximum_consecutive_inactive_minutes=10,
    )
    rejected = audit_activity_interval(
        frame,
        timestamps[0],
        timestamps[-1] + pd.Timedelta(minutes=1),
        activity_column="is_active_quote",
        minimum_active_minutes=1,
        maximum_consecutive_inactive_minutes=10,
    )
    assert accepted.eligible is True
    assert accepted.maximum_consecutive_inactive_minutes == 10
    assert rejected.eligible is False
    assert rejected.failure_reason == "stale_quote_run_exceeded"


def test_all_zero_activity_is_distinct_from_missing_grid() -> None:
    timestamps = pd.date_range("2024-01-02 02:00", periods=5, freq="1min")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "is_active_quote": 0,
        }
    )
    grid = audit_minute_interval(frame.iloc[:-1], timestamps[0], timestamps[-1] + pd.Timedelta(minutes=1))
    activity = audit_activity_interval(
        frame,
        timestamps[0],
        timestamps[-1] + pd.Timedelta(minutes=1),
        activity_column="is_active_quote",
        minimum_active_minutes=1,
        maximum_consecutive_inactive_minutes=10,
    )
    assert grid.complete is False
    assert activity.failure_reason == "no_positive_volume_activity"


def test_future_stale_run_does_not_erase_prior_signal() -> None:
    one = _minute_frame(
        trade_date="2024-01-08",
        sweep_time="02:00",
        future_inactive_start="03:00",
        future_inactive_minutes=12,
    )
    ledger = build_event_ledger("NQ_PROXY", one, resample_5m(one), _config())
    event = ledger.iloc[0]
    assert event["status"] == "SIGNAL"
    assert event["entry_timestamp"] == pd.Timestamp("2024-01-08 02:05")
    assert event["execution_activity_eligible"] == False  # noqa: E712
    assert event["pre_signal_activity_eligible"] == True  # noqa: E712


def test_reclaim_closing_at_window_end_is_rejected() -> None:
    one = _minute_frame(trade_date="2024-01-08", sweep_time="05:55")
    ledger = build_event_ledger("NQ_PROXY", one, resample_5m(one), _config())
    event = ledger.iloc[0]
    assert event["status"] == "REJECTED"
    assert event["rejection_reason"] == "entry_at_or_after_window_end"
    assert event["entry_timestamp"] == pd.Timestamp("2024-01-08 06:00")
