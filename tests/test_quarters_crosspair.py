from __future__ import annotations

import datetime as dt
import importlib.util
import struct
import sys
from pathlib import Path

import pandas as pd
import pytest


def _load_script_module(name: str, filename: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_downloader_module():
    return _load_script_module(
        "quarters_downloader", "download_dukascopy_bid_ask.py"
    )


def _load_retained_source_adapter():
    return _load_script_module(
        "quarters_retained_source_adapter",
        "prepare_quarters_from_stacey_source.py",
    )


def test_eurusd_quote_normalization_preserves_price() -> None:
    module = _load_downloader_module()
    payload = struct.pack(">5if", 60, 112345, 112355, 112300, 112400, 2.0)
    rows = module._decode_payload(payload, dt.date(2020, 1, 2), 100000.0, 1.0)
    assert rows[0][1:5] == (1.12345, 1.124, 1.123, 1.12355)


def test_usdjpy_quote_normalization_maps_source_pip_to_engine_pip() -> None:
    module = _load_downloader_module()
    payload = struct.pack(">5if", 60, 130000, 130010, 129990, 130020, 2.0)
    rows = module._decode_payload(payload, dt.date(2020, 1, 2), 1000.0, 0.01)
    open_, high, low, close = rows[0][1:5]
    assert open_ == pytest.approx(1.3)
    assert high == pytest.approx(1.3002)
    assert low == pytest.approx(1.2999)
    assert close == pytest.approx(1.3001)
    assert close - open_ == pytest.approx(0.0001)


def test_retained_source_adapter_converts_schema_and_jpy_scale(
    tmp_path: Path,
) -> None:
    module = _load_retained_source_adapter()
    source = pd.DataFrame(
        {
            "timestamp_utc": [
                "2020-01-02T00:00:00Z",
                "2020-01-02T00:01:00Z",
            ],
            "open": [130.00, 130.01],
            "high": [130.02, 130.03],
            "low": [129.99, 130.00],
            "close": [130.01, 130.02],
            "volume": [0.0, 2.0],
            "is_active_quote": [0, 1],
        }
    )
    source_path = tmp_path / "usdjpy_m1_bid_2020.csv.gz"
    source.to_csv(source_path, index=False, compression="gzip")

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
