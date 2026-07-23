from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

from .config import (
    ES_PROXY_SPEC,
    GBPUSD_SPEC,
    NQ_PROXY_SPEC,
    NQ_SPEC,
    InstrumentSpec,
)

_REQUIRED_OHLCV = {"timestamp", "open", "high", "low", "close", "volume"}
_SIDE_COLUMNS = {
    f"{side}_{field}"
    for side in ("bid", "ask")
    for field in ("open", "high", "low", "close", "volume")
}
PRIMARY_START_ET = pd.Timestamp("2022-12-26 18:00:00")
PRIMARY_END_ET = pd.Timestamp("2025-12-10 23:58:00")

GBPUSD_NORMALIZED_SHA256 = "f1ed39cbe6538b605dad41f550e7512794a7799c01a056570e22c3de6c5012d4"


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def validate_one_minute(frame: pd.DataFrame) -> pd.DataFrame:
    missing = _REQUIRED_OHLCV.difference(frame.columns)
    if missing:
        raise ValueError(f"One-minute data missing columns: {sorted(missing)}")
    work = frame.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="raise")
    if getattr(work["timestamp"].dt, "tz", None) is not None:
        work["timestamp"] = work["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None)
    for column in ("open", "high", "low", "close", "volume"):
        work[column] = pd.to_numeric(work[column], errors="raise")
    work = work.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    if work.empty:
        raise ValueError("One-minute dataset is empty")
    if not work["timestamp"].is_monotonic_increasing:
        raise ValueError("Timestamps are not monotonic")
    if not np.isfinite(work[["open", "high", "low", "close", "volume"]].to_numpy()).all():
        raise ValueError("One-minute data contain non-finite values")
    valid_ohlc = (work["high"] >= work[["open", "close", "low"]].max(axis=1)) & (
        work["low"] <= work[["open", "close", "high"]].min(axis=1)
    )
    if not bool(valid_ohlc.all()):
        raise ValueError("OHLC integrity failed")
    return work


def validate_bid_ask(frame: pd.DataFrame) -> pd.DataFrame:
    missing = _SIDE_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Bid/ask data missing columns: {sorted(missing)}")
    work = validate_one_minute(frame)
    for column in sorted(_SIDE_COLUMNS):
        work[column] = pd.to_numeric(work[column], errors="raise")
    for side in ("bid", "ask"):
        high = work[f"{side}_high"]
        low = work[f"{side}_low"]
        valid = (high >= work[[f"{side}_open", f"{side}_close", f"{side}_low"]].max(axis=1)) & (
            low <= work[[f"{side}_open", f"{side}_close", f"{side}_high"]].min(axis=1)
        )
        if not bool(valid.all()):
            raise ValueError(f"{side.upper()} OHLC integrity failed")
    if bool((work["ask_open"] < work["bid_open"]).any()):
        raise ValueError("Negative bid/ask spread at open")
    if bool((work["ask_close"] < work["bid_close"]).any()):
        raise ValueError("Negative bid/ask spread at close")
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


def _load_full_grid_proxy(path: str | Path, spec: InstrumentSpec) -> pd.DataFrame:
    source = Path(path)
    observed = file_sha256(source)
    if observed != spec.source_sha256:
        raise ValueError(f"{spec.name} source checksum mismatch")
    with ZipFile(source) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"{spec.name} archive must contain exactly one CSV")
        with archive.open(csv_names[0]) as handle:
            raw = pd.read_csv(handle)
    required = {"timestamp UTC", "open", "high", "low", "close", "volume", "is_active_quote"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"{spec.name} proxy archive missing columns: {sorted(missing)}")
    source_rows = int(len(raw))
    active = pd.to_numeric(raw["is_active_quote"], errors="raise").astype(bool)
    frame = raw.loc[active, ["timestamp UTC", "open", "high", "low", "close", "volume"]].rename(
        columns={"timestamp UTC": "timestamp"}
    )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise").dt.tz_localize(
        None
    )
    frame = validate_one_minute(frame)
    frame.attrs.update(
        {
            "source_rows": source_rows,
            "active_rows": int(active.sum()),
            "inactive_rows": int((~active).sum()),
            "source_repair": "none; canonical corrected BI5 mapping",
            "source_sha256": observed,
        }
    )
    return frame


def load_nq_proxy(path: str | Path) -> pd.DataFrame:
    return _load_full_grid_proxy(path, NQ_PROXY_SPEC)


def load_es_proxy(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    observed = file_sha256(source)
    if observed == ES_PROXY_SPEC.source_sha256:
        return _load_full_grid_proxy(source, ES_PROXY_SPEC)

    legacy_sha = "199d63e6f284eb1ffb93003e9020bf2852f5d96bf78f0efe50c3bdd09c11a47b"
    if observed != legacy_sha:
        raise ValueError("ES proxy source checksum mismatch")
    from dtr_lab.research.cross_market import load_usa500_proxy

    frame = validate_one_minute(load_usa500_proxy(source))
    frame.attrs.update(
        {
            "source_rows": int(len(frame)),
            "active_rows": int(len(frame)),
            "inactive_rows": 0,
            "source_repair": "legacy active-row CSV adapter",
            "source_sha256": observed,
        }
    )
    return frame


def _read_gzip_csv(payload: bytes) -> pd.DataFrame:
    with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as handle:
        return pd.read_csv(handle)


def _repair_gbpusd_side(raw: pd.DataFrame, *, side: str) -> tuple[pd.DataFrame, int]:
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"GBPUSD {side} file missing columns: {sorted(missing)}")
    stored = raw.loc[:, ["timestamp", "open", "high", "low", "close", "volume"]].copy()
    repaired = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(stored["timestamp"], unit="ms", utc=True, errors="raise")
            .dt.tz_localize(None),
            f"{side}_open": pd.to_numeric(stored["open"], errors="raise"),
            # Source writer labelled BI5 close as high and BI5 high as close.
            f"{side}_high": pd.to_numeric(stored["close"], errors="raise"),
            f"{side}_low": pd.to_numeric(stored["low"], errors="raise"),
            f"{side}_close": pd.to_numeric(stored["high"], errors="raise"),
            f"{side}_volume": pd.to_numeric(stored["volume"], errors="raise"),
        }
    )
    high = repaired[f"{side}_high"]
    low = repaired[f"{side}_low"]
    invalid = (high < repaired[[f"{side}_open", f"{side}_close", f"{side}_low"]].max(axis=1)) | (
        low > repaired[[f"{side}_open", f"{side}_close", f"{side}_high"]].min(axis=1)
    )
    if bool(invalid.any()):
        raise ValueError(f"GBPUSD {side} repair left {int(invalid.sum())} invalid OHLC rows")
    return repaired, int(len(repaired))


def _load_gbpusd_normalized(source: Path, observed: str) -> pd.DataFrame:
    raw = pd.read_csv(source, compression="gzip")
    if "timestamp UTC" not in raw.columns:
        raise ValueError("Normalized GBPUSD source missing timestamp UTC")
    frame = raw.rename(columns={"timestamp UTC": "timestamp"})
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise").dt.tz_localize(None)
    frame = validate_bid_ask(frame)
    frame.attrs.update(
        {
            "source_rows": 2_103_840,
            "active_rows": int(len(frame)),
            "inactive_rows": 615_763,
            "source_repair": "pre-normalized corrected BI5 mapping",
            "source_sha256": observed,
            "verified_member_count": 8,
        }
    )
    return frame


def load_gbpusd(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    observed = file_sha256(source)
    if observed == GBPUSD_NORMALIZED_SHA256:
        return _load_gbpusd_normalized(source, observed)
    if observed != GBPUSD_SPEC.source_sha256:
        raise ValueError("GBPUSD source checksum mismatch")

    with ZipFile(source) as outer:
        nested = [name for name in outer.namelist() if name.endswith(".tar.gz")]
        if len(nested) != 1:
            raise ValueError("GBPUSD archive must contain exactly one TAR.GZ payload")
        tar_payload = outer.read(nested[0])

    yearly: list[pd.DataFrame] = []
    source_rows = 0
    inactive_rows = 0
    member_hashes: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(tar_payload), mode="r:gz") as archive:
        manifest_names = [name for name in archive.getnames() if name.endswith("manifest.json")]
        if len(manifest_names) != 1:
            raise ValueError("GBPUSD payload must contain exactly one manifest")
        manifest_handle = archive.extractfile(manifest_names[0])
        if manifest_handle is None:
            raise ValueError("GBPUSD manifest cannot be read")
        manifest = json.loads(manifest_handle.read())

        for annual in manifest.get("annual_audits", []):
            year = int(annual["year"])
            sides: dict[str, pd.DataFrame] = {}
            for side in ("bid", "ask"):
                meta = annual["sides"][side]
                member_name = f"gbpusd_data/{meta['file']}"
                member = archive.extractfile(member_name)
                if member is None:
                    raise ValueError(f"Missing GBPUSD member: {member_name}")
                compressed = member.read()
                digest = _bytes_sha256(compressed)
                if digest != meta["sha256"]:
                    raise ValueError(f"GBPUSD {side} {year} member checksum mismatch")
                member_hashes[member_name] = digest
                repaired, rows = _repair_gbpusd_side(_read_gzip_csv(compressed), side=side)
                if rows != int(meta["rows"]):
                    raise ValueError(f"GBPUSD {side} {year} row-count mismatch")
                sides[side] = repaired

            merged = sides["bid"].merge(
                sides["ask"], on="timestamp", how="inner", validate="one_to_one", sort=True
            )
            if len(merged) != len(sides["bid"]) or len(merged) != len(sides["ask"]):
                raise ValueError(f"GBPUSD bid/ask timestamp mismatch in {year}")
            source_rows += int(len(merged))
            active = (merged["bid_volume"] > 0) | (merged["ask_volume"] > 0)
            inactive_rows += int((~active).sum())
            merged = merged.loc[active].copy()
            for field in ("open", "high", "low", "close"):
                merged[field] = (merged[f"bid_{field}"] + merged[f"ask_{field}"]) / 2.0
            merged["volume"] = merged[["bid_volume", "ask_volume"]].max(axis=1)
            merged["is_active_quote"] = True
            yearly.append(merged)

    frame = pd.concat(yearly, ignore_index=True)
    frame = validate_bid_ask(frame)
    frame.attrs.update(
        {
            "source_rows": source_rows,
            "active_rows": int(len(frame)),
            "inactive_rows": inactive_rows,
            "source_repair": "stored high/close swapped to restore BI5 open-close-low-high mapping",
            "source_sha256": observed,
            "verified_member_count": len(member_hashes),
        }
    )
    return frame


def load_instrument(path: str | Path, spec: InstrumentSpec) -> pd.DataFrame:
    if spec.name == "NQ":
        return load_nq(path)
    if spec.name == "NQ_PROXY":
        return load_nq_proxy(path)
    if spec.name == "ES_PROXY":
        return load_es_proxy(path)
    if spec.name == "GBPUSD":
        return load_gbpusd(path)
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
    result: dict[str, object] = {
        "instrument": spec.name,
        "execution_model": spec.execution_model,
        "source_classification": spec.source_classification,
        "rows": int(len(frame)),
        "source_rows": int(frame.attrs.get("source_rows", len(frame))),
        "active_rows": int(frame.attrs.get("active_rows", len(frame))),
        "inactive_rows": int(frame.attrs.get("inactive_rows", 0)),
        "source_repair": str(frame.attrs.get("source_repair", "none")),
        "start": timestamps.min().isoformat(),
        "end": timestamps.max().isoformat(),
        "duplicate_timestamps": int(timestamps.duplicated().sum()),
        "nonpositive_or_missing_deltas": int((deltas.dropna() <= 0).sum()),
        "gaps_over_5_minutes": int((deltas > 5).sum()),
        "gaps_over_15_minutes": int((deltas > 15).sum()),
        "median_delta_minutes": float(np.nanmedian(deltas.to_numpy(float))),
    }
    if spec.execution_model == "fx_bid_ask":
        open_spread_pips = (frame["ask_open"] - frame["bid_open"]) / 0.0001
        close_spread_pips = (frame["ask_close"] - frame["bid_close"]) / 0.0001
        spread = pd.concat([open_spread_pips, close_spread_pips], ignore_index=True)
        result.update(
            {
                "median_spread_pips": float(spread.median()),
                "p95_spread_pips": float(spread.quantile(0.95)),
                "negative_spread_observations": int((spread < 0).sum()),
                "verified_member_count": int(frame.attrs.get("verified_member_count", 0)),
            }
        )
    return result
