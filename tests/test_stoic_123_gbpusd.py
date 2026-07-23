from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from dataclasses import replace
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd

from stoic_123_lab.backtest import simulate
from stoic_123_lab.config import GBPUSD_SPEC, SequenceConfig
from stoic_123_lab.data import load_gbpusd, validate_bid_ask
from stoic_123_lab.reporting import validate_no_pooling


def _fx_frame() -> pd.DataFrame:
    timestamp = pd.date_range("2025-01-02 09:00", periods=4, freq="min")
    bid_open = np.array([1.1000, 1.1010, 1.1020, 1.1030])
    bid_close = np.array([1.1005, 1.1015, 1.1025, 1.1035])
    ask_open = bid_open + 0.0002
    ask_close = bid_close + 0.0002
    frame = pd.DataFrame(
        {
            "timestamp": timestamp,
            "bid_open": bid_open,
            "bid_high": np.maximum(bid_open, bid_close) + 0.0001,
            "bid_low": np.minimum(bid_open, bid_close) - 0.0001,
            "bid_close": bid_close,
            "bid_volume": 1.0,
            "ask_open": ask_open,
            "ask_high": np.maximum(ask_open, ask_close) + 0.0001,
            "ask_low": np.minimum(ask_open, ask_close) - 0.0001,
            "ask_close": ask_close,
            "ask_volume": 1.0,
        }
    )
    for field in ("open", "high", "low", "close"):
        frame[field] = (frame[f"bid_{field}"] + frame[f"ask_{field}"]) / 2
    frame["volume"] = 1.0
    return validate_bid_ask(frame)


def _event() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "arm_id": ["TEST"],
            "direction": [1],
            "signal_time": [pd.Timestamp("2025-01-02 09:00")],
            "breakout_close": [1.1001],
            "protective_boundary": [1.0990],
            "base_lock_time": [pd.Timestamp("2025-01-02 08:59")],
        }
    )


def _config() -> SequenceConfig:
    return SequenceConfig(
        arm_id="TEST",
        description="test",
        stop_buffer_ticks=0,
        minimum_risk_ticks=1,
        slippage_ticks_each_side=0,
    )


def _gzip_csv(frame: pd.DataFrame) -> bytes:
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as handle:
        handle.write(frame.to_csv(index=False).encode())
    return raw.getvalue()


def _synthetic_archive(path: Path) -> str:
    timestamps = [1640995200000, 1640995260000]
    bid = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [1.1000, 1.1000],
            "high": [1.1000, 1.1002],
            "low": [1.1000, 1.0999],
            "close": [1.1000, 1.1004],
            "volume": [0.0, 2.0],
        }
    )
    ask = bid.copy()
    for column in ("open", "high", "low", "close"):
        ask[column] += 0.0002
    members = {
        "gbpusd_data/gbpusd_m1_bid_2022.csv.gz": _gzip_csv(bid),
        "gbpusd_data/gbpusd_m1_ask_2022.csv.gz": _gzip_csv(ask),
    }
    sides = {}
    for side in ("bid", "ask"):
        name = f"gbpusd_data/gbpusd_m1_{side}_2022.csv.gz"
        sides[side] = {
            "rows": 2,
            "sha256": hashlib.sha256(members[name]).hexdigest(),
            "file": f"gbpusd_m1_{side}_2022.csv.gz",
        }
    manifest = {"annual_audits": [{"year": 2022, "sides": sides}]}
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w:gz") as archive:
        manifest_bytes = json.dumps(manifest).encode()
        info = tarfile.TarInfo("gbpusd_data/gbpusd_2022_2025_manifest.json")
        info.size = len(manifest_bytes)
        archive.addfile(info, io.BytesIO(manifest_bytes))
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    with ZipFile(path, "w", ZIP_DEFLATED) as outer:
        outer.writestr("gbpusd_2022_2025_bid_ask_ohlc.tar.gz", tar_bytes.getvalue())
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fx_long_enters_ask_and_exits_bid() -> None:
    management = pd.DataFrame(
        {"direction": [-1], "signal_time": [pd.Timestamp("2025-01-02 09:01")]}
    )
    trades = simulate(_fx_frame(), _event(), management, GBPUSD_SPEC, _config())
    assert trades.iloc[0]["entry_price"] == 1.1002
    assert trades.iloc[0]["exit_price"] == 1.1010
    assert trades.iloc[0]["execution_model"] == "fx_bid_ask"
    assert np.isclose(trades.iloc[0]["gross_r"], 2 / 3)


def test_fx_long_stop_uses_bid_and_gap_through_open() -> None:
    frame = _fx_frame()
    frame.loc[1, ["bid_open", "bid_high", "bid_low", "bid_close"]] = [
        1.0980,
        1.0985,
        1.0975,
        1.0982,
    ]
    trades = simulate(frame, _event(), pd.DataFrame(), GBPUSD_SPEC, _config())
    assert trades.iloc[0]["exit_reason"] == "protective_stop"
    assert trades.iloc[0]["exit_price"] == 1.0980


def test_gbpusd_loader_repairs_mapping_and_filters_inactive(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "gbpusd.zip"
    digest = _synthetic_archive(source)
    import stoic_123_lab.data as data_module

    monkeypatch.setattr(
        data_module,
        "GBPUSD_SPEC",
        replace(GBPUSD_SPEC, source_sha256=digest),
    )
    frame = load_gbpusd(source)
    assert len(frame) == 1
    assert frame.iloc[0]["bid_high"] == 1.1004
    assert frame.iloc[0]["bid_close"] == 1.1002
    assert frame.attrs["inactive_rows"] == 1
    assert frame.attrs["verified_member_count"] == 2


def test_no_pooling_gate_accepts_gbpusd() -> None:
    validate_no_pooling(
        pd.DataFrame({"instrument": ["NQ_PROXY", "ES_PROXY", "GBPUSD"]})
    )
