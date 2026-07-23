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
    source_timezone: str | None = None
    session_timezone: str | None = None


def _parse_timestamps(values: pd.Series, schema: ZipCsvSchema) -> pd.Series:
    use_utc = schema.source_timezone is not None and schema.source_timezone.upper() == "UTC"
    timestamps = pd.to_datetime(
        values,
        format=schema.timestamp_format,
        errors="raise",
        utc=use_utc,
    )

    if schema.source_timezone is None:
        if schema.session_timezone is not None:
            raise ValueError("session_timezone requires source_timezone")
        return pd.Series(timestamps, index=values.index)

    if timestamps.dt.tz is None:
        timestamps = timestamps.dt.tz_localize(
            schema.source_timezone,
            ambiguous="raise",
            nonexistent="raise",
        )
    else:
        timestamps = timestamps.dt.tz_convert(schema.source_timezone)

    source = timestamps
    if schema.session_timezone is not None:
        timestamps = timestamps.dt.tz_convert(schema.session_timezone)
    parsed = pd.Series(timestamps, index=values.index)
    parsed.attrs["source_timestamps"] = pd.Series(source, index=values.index)
    return parsed


def load_one_minute_zip(path: str | Path, schema: ZipCsvSchema) -> pd.DataFrame:
    """Load one CSV from a ZIP without silently repairing source defects.

    Legacy offset-free datasets remain naïve. A schema with ``source_timezone`` produces
    timezone-aware timestamps and may convert them to an explicit session timezone.
    """

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

    timestamps = _parse_timestamps(frame[schema.timestamp_column], schema)
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
    if schema.source_timezone is not None:
        source_timestamps = pd.to_datetime(
            frame[schema.timestamp_column],
            format=schema.timestamp_format,
            errors="raise",
            utc=schema.source_timezone.upper() == "UTC",
        )
        if source_timestamps.dt.tz is None:
            source_timestamps = source_timestamps.dt.tz_localize(
                schema.source_timezone,
                ambiguous="raise",
                nonexistent="raise",
            )
        else:
            source_timestamps = source_timestamps.dt.tz_convert(schema.source_timezone)
        out["timestamp_source"] = source_timestamps
    out = out.sort_values("timestamp").reset_index(drop=True)
    return out
