from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pandas as pd

REQUIRED_COLUMNS = (
    "timestamp ET",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


def _validate_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")


def load_market_data(path: str | Path, *, member: str | None = None) -> pd.DataFrame:
    """Load the supported CSV or single-member ZIP dataset.

    Timestamps are parsed but deliberately left timezone-naive until the source's
    bar-open/bar-close and daylight-saving semantics have been verified.
    """

    source = Path(path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)

    if source.suffix.lower() == ".zip":
        with ZipFile(source) as archive:
            csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            selected = member
            if selected is None:
                if len(csv_members) != 1:
                    raise ValueError(
                        "ZIP must contain exactly one CSV when member is not specified; "
                        f"found {len(csv_members)}"
                    )
                selected = csv_members[0]
            if selected not in archive.namelist():
                raise ValueError(f"ZIP member not found: {selected}")
            with archive.open(selected) as handle:
                frame = pd.read_csv(handle)
    elif source.suffix.lower() == ".csv":
        frame = pd.read_csv(source)
    else:
        raise ValueError(f"Unsupported market-data file type: {source.suffix}")

    _validate_columns(frame)

    frame = frame.copy()
    frame["timestamp_et"] = pd.to_datetime(
        frame["timestamp ET"],
        format="%m/%d/%Y %H:%M",
        errors="raise",
    )

    numeric_columns = [
        column
        for column in ("open", "high", "low", "close", "volume", "Vwap_RTH", "Vwap_ETH")
        if column in frame.columns
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    return frame


def resample_ohlcv(
    frame: pd.DataFrame,
    *,
    rule: str = "5min",
    label: str = "left",
    closed: str = "left",
) -> pd.DataFrame:
    """Resample source bars while preserving OHLCV semantics.

    The default uses left-labelled, left-closed intervals. TradingView parity must
    explicitly validate this convention before it becomes the production default.
    """

    if "timestamp_et" not in frame.columns:
        raise ValueError("Expected parsed timestamp_et column")

    indexed = frame.set_index("timestamp_et", drop=False).sort_index()
    result = indexed.resample(rule, label=label, closed=closed).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        source_bars=("close", "count"),
    )
    result = result.dropna(subset=["open", "high", "low", "close"])
    return result.reset_index()
