from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class IntervalIntegrity:
    start: pd.Timestamp
    end: pd.Timestamp
    expected_minutes: int
    observed_minutes: int
    missing_minutes: int
    duplicate_minutes: int
    off_grid_timestamps: int
    first_missing_timestamp: pd.Timestamp | None
    last_missing_timestamp: pd.Timestamp | None
    complete: bool


def audit_minute_interval(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> IntervalIntegrity:
    """Audit exact one-minute coverage over a half-open interval.

    The audit is descriptive and does not infer or synthesize missing prices. Timestamps
    must lie exactly on the one-minute grid. Duplicate timestamps make the interval unsafe.
    """

    if "timestamp" not in frame.columns:
        raise ValueError("frame missing required column: timestamp")
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    if end <= start:
        raise ValueError("end must be after start")

    timestamps = pd.to_datetime(frame["timestamp"])
    scoped = timestamps[(timestamps >= start) & (timestamps < end)]
    duplicate_minutes = int(scoped.duplicated().sum())
    unique = pd.DatetimeIndex(scoped.drop_duplicates().sort_values())
    expected = pd.date_range(start, end, freq="1min", inclusive="left")
    off_grid = unique.difference(expected)
    on_grid = unique.intersection(expected)
    missing = expected.difference(on_grid)
    complete = (
        duplicate_minutes == 0
        and len(off_grid) == 0
        and len(missing) == 0
        and len(on_grid) == len(expected)
    )
    return IntervalIntegrity(
        start=start,
        end=end,
        expected_minutes=int(len(expected)),
        observed_minutes=int(len(on_grid)),
        missing_minutes=int(len(missing)),
        duplicate_minutes=duplicate_minutes,
        off_grid_timestamps=int(len(off_grid)),
        first_missing_timestamp=pd.Timestamp(missing[0]) if len(missing) else None,
        last_missing_timestamp=pd.Timestamp(missing[-1]) if len(missing) else None,
        complete=bool(complete),
    )
