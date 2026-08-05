from __future__ import annotations

import datetime as dt
import importlib.util
import struct
import sys
from pathlib import Path

import pytest


def _load_downloader_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "download_dukascopy_bid_ask.py"
    spec = importlib.util.spec_from_file_location("quarters_downloader", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
