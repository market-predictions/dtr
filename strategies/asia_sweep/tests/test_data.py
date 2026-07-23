from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pytest

from dtr_lab.strategies.asia_sweep.data import (
    ZipCsvSchema,
    load_one_minute_zip,
)


_SCHEMA = ZipCsvSchema(
    timestamp_column="timestamp ET",
    timestamp_format="%m/%d/%Y %H:%M",
)


def _write_zip(path: Path, frame: pd.DataFrame) -> None:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("bars.csv", frame.to_csv(index=False))


def _frame(timestamps: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp ET": timestamps,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 10.0,
        }
    )


def test_loader_sorts_and_preserves_final_date(tmp_path: Path) -> None:
    path = tmp_path / "bars.zip"
    _write_zip(
        path,
        _frame(["01/02/2024 09:31", "01/02/2024 09:30"]),
    )
    result = load_one_minute_zip(path, _SCHEMA)
    assert result["timestamp"].tolist() == [
        pd.Timestamp("2024-01-02 09:30"),
        pd.Timestamp("2024-01-02 09:31"),
    ]
    assert len(result) == 2


def test_loader_rejects_duplicate_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "bars.zip"
    _write_zip(
        path,
        _frame(["01/02/2024 09:30", "01/02/2024 09:30"]),
    )
    with pytest.raises(ValueError, match="duplicate timestamps"):
        load_one_minute_zip(path, _SCHEMA)


def test_loader_requires_one_csv_member(tmp_path: Path) -> None:
    path = tmp_path / "bars.zip"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        csv = _frame(["01/02/2024 09:30"]).to_csv(index=False)
        archive.writestr("a.csv", csv)
        archive.writestr("b.csv", csv)
    with pytest.raises(ValueError, match="exactly one CSV"):
        load_one_minute_zip(path, _SCHEMA)
