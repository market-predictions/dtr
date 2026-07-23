from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ES_PROXY_SPEC, NQ_SPEC, InstrumentSpec

_REQUIRED_OHLCV = {"timestamp", "open", "high", "low", "close", "volume"}
PRIMARY_START_ET = pd.Timestamp("2022-12-26 18:00:00")
PRIMARY_END_ET = pd.Timestamp("2025-12-10 23:58:00")


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_one_minute(frame: pd.DataFrame) -> pd.DataFrame:
    missing = _REQUIRED_OHLCV.difference(frame.columns)
    if missing:
        raise ValueError(f"One-minute data missing columns: {sorted(missing)}")
    work = frame.loc[:, ["timestamp", "open", "high", "low", "close", "volume"]].copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="raise")
    for column in ("open", "high", "low", "close", "volume"):
        work[column] = pd.to_numeric(work[column], errors="raise")
    work = work.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    if work.empty:
        raise ValueError("One-minute dataset is empty")
    if not work["timestamp"].is_monotonic_increasing:
        raise ValueError("Timestamps are not monotonic")
    valid_ohlc = (work["high"] >= work[["open", "close", "low"]].max(axis=1)) & (
        work["low"] <= work[["open", "close", "high"]].min(axis=1)
    )
    if not bool(valid_ohlc.all()):
        raise ValueError("OHLC integrity failed")
    return work


def load_nq(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if file_sha256(source) != NQ_SPEC.source_sha256:
        raise ValueError("NQ source checksum mismatch")
    from dtr_lab.research import engine

    frame = engine.load_zip(source)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="raise") - pd.Timedelta(
        minutes=1
    )
    frame = frame.loc[
        (frame["timestamp"] >= PRIMARY_START_ET) & (frame["timestamp"] <= PRIMARY_END_ET)
    ]
    return validate_one_minute(frame)


def load_es_proxy(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if file_sha256(source) != ES_PROXY_SPEC.source_sha256:
        raise ValueError("ES proxy source checksum mismatch")
    from dtr_lab.research.cross_market import load_usa500_proxy

    return validate_one_minute(load_usa500_proxy(source))


def load_instrument(path: str | Path, spec: InstrumentSpec) -> pd.DataFrame:
    if spec.name == "NQ":
        return load_nq(path)
    if spec.name == "ES_PROXY":
        return load_es_proxy(path)
    raise ValueError(f"Unsupported instrument: {spec.name}")


def resample_ohlcv(one_minute: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    work = validate_one_minute(one_minute).set_index("timestamp")
    bars = (
        work.resample(f"{minutes}min", label="left", closed="left", origin="start_day")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            active_minutes=("close", "count"),
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    bars["bar_end"] = bars["timestamp"] + pd.Timedelta(minutes=minutes)
    previous_end = bars["bar_end"].shift(1)
    bars["gap_minutes"] = (
        (bars["timestamp"] - previous_end).dt.total_seconds().div(60).clip(lower=0).fillna(0)
    )
    bars["full_bar"] = bars["active_minutes"] == minutes
    return bars


def data_audit(frame: pd.DataFrame, spec: InstrumentSpec) -> dict[str, object]:
    timestamps = pd.to_datetime(frame["timestamp"])
    deltas = timestamps.diff().dt.total_seconds().div(60)
    return {
        "instrument": spec.name,
        "source_classification": spec.source_classification,
        "rows": int(len(frame)),
        "start": timestamps.min().isoformat(),
        "end": timestamps.max().isoformat(),
        "duplicate_timestamps": int(timestamps.duplicated().sum()),
        "nonpositive_or_missing_deltas": int((deltas.dropna() <= 0).sum()),
        "gaps_over_5_minutes": int((deltas > 5).sum()),
        "gaps_over_15_minutes": int((deltas > 15).sum()),
        "median_delta_minutes": float(np.nanmedian(deltas.to_numpy(float))),
    }
