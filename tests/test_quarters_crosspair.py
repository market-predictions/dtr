from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest


def _load_retained_source_adapter():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "prepare_quarters_from_stacey_source.py"
    )
    spec = importlib.util.spec_from_file_location(
        "quarters_retained_source_adapter", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_source(path: Path, open_price: float, close_price: float) -> None:
    source = pd.DataFrame(
        {
            "timestamp_utc": [
                "2020-01-02T00:00:00Z",
                "2020-01-02T00:01:00Z",
            ],
            "open": [open_price, close_price],
            "high": [close_price + 0.01, close_price + 0.02],
            "low": [open_price - 0.01, close_price - 0.01],
            "close": [close_price, close_price + 0.01],
            "volume": [0.0, 2.0],
            "is_active_quote": [0, 1],
        }
    )
    source.to_csv(path, index=False, compression="gzip")


def test_retained_source_adapter_preserves_eurusd_quote_scale(
    tmp_path: Path,
) -> None:
    module = _load_retained_source_adapter()
    source_path = tmp_path / "eurusd_m1_bid_2020.csv.gz"
    _write_source(source_path, 1.1200, 1.1201)

    adapted = module.load_and_normalize(source_path, 1.0)

    assert adapted.open.iloc[0] == pytest.approx(1.1200)
    assert adapted.close.iloc[0] == pytest.approx(1.1201)
    assert adapted.close.iloc[0] - adapted.open.iloc[0] == pytest.approx(0.0001)


def test_retained_source_adapter_converts_schema_and_jpy_scale(
    tmp_path: Path,
) -> None:
    module = _load_retained_source_adapter()
    source_path = tmp_path / "usdjpy_m1_bid_2020.csv.gz"
    _write_source(source_path, 130.00, 130.01)

    adapted = module.load_and_normalize(source_path, 0.01)

    assert list(adapted.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert adapted.timestamp.iloc[1] - adapted.timestamp.iloc[0] == 60_000
    assert adapted.open.iloc[0] == pytest.approx(1.3)
    assert adapted.close.iloc[0] - adapted.open.iloc[0] == pytest.approx(0.0001)
    assert adapted.volume.tolist() == [0.0, 2.0]
