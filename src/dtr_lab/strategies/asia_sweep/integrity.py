from __future__ import annotations

from dataclasses import dataclass

import numpy as np
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


@dataclass(frozen=True)
class IntervalActivity:
    start: pd.Timestamp
    end: pd.Timestamp
    observed_minutes: int
    active_minutes: int
    inactive_minutes: int
    maximum_consecutive_inactive_minutes: int
    minimum_active_minutes: int
    maximum_allowed_inactive_run: int
    eligible: bool
    failure_reason: str | None


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


def _maximum_false_run(values: np.ndarray) -> int:
    if not len(values):
        return 0
    inactive = ~values.astype(bool)
    if not bool(inactive.any()):
        return 0
    changes = np.diff(np.r_[False, inactive, False].astype(np.int8))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return int((ends - starts).max())


def audit_activity_interval(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    activity_column: str,
    minimum_active_minutes: int,
    maximum_consecutive_inactive_minutes: int,
) -> IntervalActivity:
    """Audit source activity separately from timestamp-grid completeness.

    A zero activity value is treated as a source-provided inactive quote observation. The
    function does not infer missing timestamps, prices or tradability. Grid completeness is
    intentionally handled by :func:`audit_minute_interval`.
    """

    required = {"timestamp", activity_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"frame missing required columns: {sorted(missing)}")
    if minimum_active_minutes < 1:
        raise ValueError("minimum_active_minutes must be at least one")
    if maximum_consecutive_inactive_minutes < 0:
        raise ValueError("maximum_consecutive_inactive_minutes must be non-negative")

    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    if end <= start:
        raise ValueError("end must be after start")

    timestamps = pd.to_datetime(frame["timestamp"])
    mask = (timestamps >= start) & (timestamps < end)
    scoped = frame.loc[mask, ["timestamp", activity_column]].copy()
    scoped["timestamp"] = pd.to_datetime(scoped["timestamp"])
    scoped = scoped.sort_values("timestamp")
    activity = pd.to_numeric(scoped[activity_column], errors="raise").to_numpy() > 0
    active_minutes = int(activity.sum())
    inactive_minutes = int(len(activity) - active_minutes)
    maximum_run = _maximum_false_run(activity)

    if active_minutes < minimum_active_minutes:
        failure_reason = "no_positive_volume_activity"
    elif maximum_run > maximum_consecutive_inactive_minutes:
        failure_reason = "stale_quote_run_exceeded"
    else:
        failure_reason = None

    return IntervalActivity(
        start=start,
        end=end,
        observed_minutes=int(len(activity)),
        active_minutes=active_minutes,
        inactive_minutes=inactive_minutes,
        maximum_consecutive_inactive_minutes=maximum_run,
        minimum_active_minutes=minimum_active_minutes,
        maximum_allowed_inactive_run=maximum_consecutive_inactive_minutes,
        eligible=failure_reason is None,
        failure_reason=failure_reason,
    )
