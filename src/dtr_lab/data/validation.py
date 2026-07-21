from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

EXCEL_MAX_ROWS = 1_048_576


@dataclass(frozen=True)
class DataAudit:
    rows: int
    first_timestamp: str
    last_timestamp: str
    sorted_ascending: bool
    duplicate_timestamps: int
    missing_values: int
    invalid_ohlc_rows: int
    nonpositive_volume_rows: int
    one_minute_interval_pct: float
    gaps_over_one_minute: int
    gaps_over_five_minutes: int
    gaps_over_one_hour: int
    largest_gap: str
    likely_excel_row_cap: bool
    ends_mid_session: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_market_data(frame: pd.DataFrame) -> DataAudit:
    if "timestamp_et" not in frame.columns:
        raise ValueError("Expected parsed timestamp_et column")

    timestamps = frame["timestamp_et"]
    if timestamps.empty:
        raise ValueError("Dataset contains no rows")

    diffs = timestamps.diff()
    invalid_ohlc = (
        (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
    )

    last = timestamps.iloc[-1]
    return DataAudit(
        rows=len(frame),
        first_timestamp=timestamps.iloc[0].isoformat(),
        last_timestamp=last.isoformat(),
        sorted_ascending=bool(timestamps.is_monotonic_increasing),
        duplicate_timestamps=int(timestamps.duplicated().sum()),
        missing_values=int(frame.isna().sum().sum()),
        invalid_ohlc_rows=int(invalid_ohlc.sum()),
        nonpositive_volume_rows=int((frame["volume"] <= 0).sum()),
        one_minute_interval_pct=round(float((diffs == pd.Timedelta(minutes=1)).mean() * 100), 8),
        gaps_over_one_minute=int((diffs > pd.Timedelta(minutes=1)).sum()),
        gaps_over_five_minutes=int((diffs > pd.Timedelta(minutes=5)).sum()),
        gaps_over_one_hour=int((diffs > pd.Timedelta(hours=1)).sum()),
        largest_gap=str(diffs.max()),
        likely_excel_row_cap=len(frame) == EXCEL_MAX_ROWS - 1,
        ends_mid_session=not (last.hour == 17 and last.minute in {0, 1}),
    )
