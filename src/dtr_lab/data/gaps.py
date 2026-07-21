from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class GapAuditSummary:
    total_gaps: int
    daily_maintenance: int
    weekend_or_monday_holiday: int
    holiday_or_early_close: int
    maintenance_offset: int
    small_missing_data: int
    medium_missing_data: int
    unclassified_long_gap: int
    unsafe_gaps: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def _classify_gap(previous: pd.Timestamp, current: pd.Timestamp, minutes: int) -> str:
    same_date = previous.normalize() == current.normalize()
    standard_resume = current.hour == 18 and current.minute == 1

    if (
        same_date
        and previous.hour == 17
        and previous.minute == 0
        and standard_resume
        and minutes == 61
    ):
        return "daily_maintenance"

    if (
        previous.weekday() == 4
        and previous.hour == 17
        and current.weekday() in (6, 0)
        and current.hour == 18
        and current.minute in (0, 1)
        and minutes >= 2_900
    ):
        return "weekend_or_monday_holiday"

    if current.hour == 18 and current.minute == 1 and minutes >= 240:
        return "holiday_or_early_close"

    if (
        previous.hour in (16, 17)
        and current.hour == 18
        and current.minute in (1, 2, 3, 4)
        and 61 <= minutes <= 70
    ):
        return "maintenance_offset"

    if minutes <= 5:
        return "small_missing_data"
    if minutes <= 60:
        return "medium_missing_data"
    return "unclassified_long_gap"


def classify_gaps(
    frame: pd.DataFrame,
    *,
    timestamp_column: str = "timestamp_et",
) -> pd.DataFrame:
    if timestamp_column not in frame.columns:
        raise ValueError(f"Missing timestamp column: {timestamp_column}")

    timestamps = pd.to_datetime(frame[timestamp_column], errors="raise").sort_values()
    previous = timestamps.shift(1)
    gap_minutes = (
        (timestamps - previous).dt.total_seconds().div(60).round().astype("Int64")
    )
    mask = gap_minutes > 1
    gaps = pd.DataFrame(
        {
            "previous_timestamp": previous[mask],
            "current_timestamp": timestamps[mask],
            "gap_minutes": gap_minutes[mask].astype(int),
        }
    ).reset_index(drop=True)

    if gaps.empty:
        gaps["classification"] = pd.Series(dtype="object")
        gaps["reset_strategy_state"] = pd.Series(dtype="bool")
        gaps["reject_trade_bridge"] = pd.Series(dtype="bool")
        return gaps

    gaps["classification"] = [
        _classify_gap(previous, current, int(minutes))
        for previous, current, minutes in gaps.itertuples(index=False, name=None)
    ]
    gaps["reset_strategy_state"] = True
    unsafe = {
        "maintenance_offset",
        "small_missing_data",
        "medium_missing_data",
        "unclassified_long_gap",
    }
    gaps["reject_trade_bridge"] = gaps["classification"].isin(unsafe)
    return gaps


def summarize_gaps(gaps: pd.DataFrame) -> GapAuditSummary:
    counts = gaps["classification"].value_counts().to_dict() if not gaps.empty else {}
    return GapAuditSummary(
        total_gaps=int(len(gaps)),
        daily_maintenance=int(counts.get("daily_maintenance", 0)),
        weekend_or_monday_holiday=int(
            counts.get("weekend_or_monday_holiday", 0)
        ),
        holiday_or_early_close=int(counts.get("holiday_or_early_close", 0)),
        maintenance_offset=int(counts.get("maintenance_offset", 0)),
        small_missing_data=int(counts.get("small_missing_data", 0)),
        medium_missing_data=int(counts.get("medium_missing_data", 0)),
        unclassified_long_gap=int(counts.get("unclassified_long_gap", 0)),
        unsafe_gaps=int(gaps["reject_trade_bridge"].sum()) if not gaps.empty else 0,
    )
