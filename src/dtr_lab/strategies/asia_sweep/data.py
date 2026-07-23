from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


@dataclass(frozen=True)
class ZipCsvSchema:
    timestamp_column: str
    timestamp_format: str | None
    required_columns: tuple[str, ...] = ("open", "high", "low", "close", "volume")


def load_one_minute_zip(path: str | Path, schema: ZipCsvSchema) -> pd.DataFrame:
    """Load one CSV from a ZIP without silently repairing source defects."""

    path = Path(path)
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected exactly one CSV member, found {members}")
        with archive.open(members[0]) as handle:
            frame = pd.read_csv(handle)

    required = {schema.timestamp_column, *schema.required_columns}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")

    timestamps = pd.to_datetime(
        frame[schema.timestamp_column],
        format=schema.timestamp_format,
        errors="raise",
    )
    if bool(timestamps.duplicated(keep=False).any()):
        duplicate_values = timestamps[timestamps.duplicated(keep=False)].astype(str).unique()
        preview = ", ".join(duplicate_values[:3])
        raise ValueError(f"Dataset has duplicate timestamps: {preview}")
    off_grid = (
        (timestamps.dt.second != 0)
        | (timestamps.dt.microsecond != 0)
        | (timestamps.dt.nanosecond != 0)
    )
    if bool(off_grid.any()):
        preview = ", ".join(timestamps[off_grid].astype(str).unique()[:3])
        raise ValueError(f"Dataset has off-grid timestamps: {preview}")

    out = frame.copy()
    out["timestamp"] = timestamps
    out = out.sort_values("timestamp").reset_index(drop=True)
    return out
