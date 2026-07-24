from __future__ import annotations

import csv
import gzip
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from stacey_burke_lab.fx_source import (
    INSTRUMENTS,
    SourcePartition,
    annual_partitions,
    instrument,
    pip_size,
    price_divisor,
    qualify_partition,
)


def test_fx_universe_is_factor_diverse_and_unique() -> None:
    symbols = [item.symbol for item in INSTRUMENTS]
    assert len(symbols) == 10
    assert len(symbols) == len(set(symbols))
    assert {item.factor_block for item in INSTRUMENTS} == {
        "usd_europe",
        "usd_commodity",
        "jpy",
        "europe_cross",
    }


def test_price_scaling_and_pips_are_quote_currency_aware() -> None:
    assert price_divisor("EURUSD") == 100_000.0
    assert pip_size("EURUSD") == 0.0001
    assert price_divisor("GBPJPY") == 1_000.0
    assert pip_size("GBPJPY") == 0.01
    with pytest.raises(ValueError, match="unsupported"):
        instrument("EXOTIC")


def test_annual_partitions_include_monitoring_ytd() -> None:
    partitions = annual_partitions(
        start_year=2024,
        end_year=2025,
        ytd_end_exclusive=date(2026, 7, 24),
    )
    assert [item.label for item in partitions] == ["2024", "2025", "2026_ytd"]
    assert partitions[-1].monitoring_only
    assert partitions[-1].end_exclusive == date(2026, 7, 24)


def _write_side(path: Path, *, ask_offset: float) -> None:
    timestamps = pd.date_range("2026-01-01", periods=30_000, freq="min", tz="UTC")
    with gzip.open(path, "wt", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "timestamp_utc",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "is_active_quote",
            ]
        )
        for index, timestamp in enumerate(timestamps):
            base = 1.10 + index * 0.0000001 + ask_offset
            volume = 1.0 if index % 10 else 0.0
            writer.writerow(
                [
                    timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    base,
                    base + 0.0002,
                    base - 0.0002,
                    base + 0.00005,
                    volume,
                    int(volume > 0),
                ]
            )


def test_bid_ask_qualification_preserves_inactive_rows_and_checks_spreads(
    tmp_path: Path,
) -> None:
    _write_side(tmp_path / "eurusd_m1_bid_2026_ytd.csv.gz", ask_offset=0.0)
    _write_side(tmp_path / "eurusd_m1_ask_2026_ytd.csv.gz", ask_offset=0.0001)
    result = qualify_partition(
        directory=tmp_path,
        item=instrument("EURUSD"),
        partition=SourcePartition(
            label="2026_ytd",
            start_inclusive=date(2026, 1, 1),
            end_exclusive=date(2026, 2, 1),
            monitoring_only=True,
        ),
    )
    assert result["qualified"]
    assert result["bid"]["zero_volume_rows"] == 3_000
    assert result["ask"]["zero_volume_rows"] == 3_000
    assert result["negative_open_spread_rows"] == 0
    assert result["bid_ask_synchronization_fraction"] == 1.0
