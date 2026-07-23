from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import numpy as np
import pandas as pd

_REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
_ET_ZONE = "America/New_York"


@dataclass(frozen=True)
class ProxySpec:
    research_id: str
    source_instrument: str
    display_name: str
    raw_directory: Path


@dataclass(frozen=True)
class PreparedDataset:
    research_id: str
    source_instrument: str
    display_name: str
    source_files: tuple[str, ...]
    source_rows: int
    first_timestamp_utc: str
    last_timestamp_utc: str
    first_timestamp_et: str
    last_timestamp_et: str
    duplicate_timestamps: int
    off_grid_timestamps: int
    observed_min_quote_increment: float | None
    normalized_zip: str
    normalized_zip_sha256: str
    normalized_gzip: str
    normalized_gzip_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_csv_files(directory: Path) -> list[Path]:
    files = sorted(directory.rglob("*.csv"))
    if not files:
        raise ValueError(f"Expected CSV files in {directory}")
    return files


def _parse_utc_timestamps(values: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(values):
        parsed = pd.to_datetime(values, unit="ms", utc=True, errors="raise")
    else:
        parsed = pd.to_datetime(values, utc=True, errors="raise")
    return pd.Series(parsed, index=values.index, name="timestamp_utc")


def _minimum_quote_increment(frame: pd.DataFrame) -> float | None:
    candidates: list[float] = []
    for column in ("open", "high", "low", "close"):
        values = frame[column].dropna().to_numpy(dtype=float)
        if not len(values):
            continue
        differences = np.diff(np.unique(values))
        positive = differences[differences > 1e-12]
        if len(positive):
            candidates.append(float(positive.min()))
    return min(candidates) if candidates else None


def _write_deterministic_gzip(source: Path, destination: Path) -> None:
    with source.open("rb") as source_handle:
        with destination.open("wb") as raw_destination:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw_destination,
                mtime=0,
            ) as compressed:
                shutil.copyfileobj(source_handle, compressed)


def _write_deterministic_zip(source: Path, destination: Path) -> None:
    info = ZipInfo(filename=source.name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with ZipFile(destination, "w") as archive:
        archive.writestr(info, source.read_bytes())


def _read_sources(spec: ProxySpec) -> tuple[pd.DataFrame, tuple[str, ...]]:
    sources = _find_csv_files(spec.raw_directory)
    frames: list[pd.DataFrame] = []
    source_names: list[str] = []
    for source in sources:
        frame = pd.read_csv(source)
        missing = set(_REQUIRED_COLUMNS).difference(frame.columns)
        if missing:
            raise ValueError(f"{source} missing required columns: {sorted(missing)}")
        frames.append(frame.loc[:, list(_REQUIRED_COLUMNS)])
        source_names.append(str(source.relative_to(spec.raw_directory)))
    return pd.concat(frames, ignore_index=True), tuple(source_names)


def _prepare(spec: ProxySpec, output_directory: Path) -> PreparedDataset:
    frame, source_names = _read_sources(spec)
    timestamp_utc = _parse_utc_timestamps(frame["timestamp"])
    duplicate_count = int(timestamp_utc.duplicated(keep=False).sum())
    if duplicate_count:
        duplicate_values = timestamp_utc[timestamp_utc.duplicated(keep=False)]
        preview = ", ".join(duplicate_values.astype(str).unique()[:3])
        raise ValueError(
            f"{spec.source_instrument} contains {duplicate_count} duplicate timestamps: "
            f"{preview}"
        )

    off_grid = (
        (timestamp_utc.dt.second != 0)
        | (timestamp_utc.dt.microsecond != 0)
        | (timestamp_utc.dt.nanosecond != 0)
    )
    off_grid_count = int(off_grid.sum())
    if off_grid_count:
        raise ValueError(
            f"{spec.source_instrument} contains {off_grid_count} off-grid timestamps"
        )

    normalized = pd.DataFrame(
        {
            "timestamp ET": timestamp_utc.dt.tz_convert(_ET_ZONE).dt.strftime(
                "%Y-%m-%d %H:%M"
            ),
            "timestamp UTC": timestamp_utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": pd.to_numeric(frame["open"], errors="raise"),
            "high": pd.to_numeric(frame["high"], errors="raise"),
            "low": pd.to_numeric(frame["low"], errors="raise"),
            "close": pd.to_numeric(frame["close"], errors="raise"),
            "volume": pd.to_numeric(frame["volume"], errors="raise"),
        }
    )
    normalized = normalized.sort_values("timestamp UTC").reset_index(drop=True)
    if normalized.empty:
        raise ValueError(f"{spec.source_instrument} produced no normalized rows")

    output_directory.mkdir(parents=True, exist_ok=True)
    csv_name = f"{spec.research_id}_M1_BID_UTC_ET.csv"
    csv_path = output_directory / csv_name
    normalized.to_csv(csv_path, index=False)

    gzip_path = output_directory / f"{csv_name}.gz"
    zip_path = output_directory / f"{spec.research_id}_M1_BID_UTC_ET.zip"
    _write_deterministic_gzip(csv_path, gzip_path)
    _write_deterministic_zip(csv_path, zip_path)

    utc_series = pd.to_datetime(normalized["timestamp UTC"], utc=True)
    et_series = pd.to_datetime(normalized["timestamp ET"])
    result = PreparedDataset(
        research_id=spec.research_id,
        source_instrument=spec.source_instrument,
        display_name=spec.display_name,
        source_files=source_names,
        source_rows=int(len(normalized)),
        first_timestamp_utc=utc_series.iloc[0].isoformat(),
        last_timestamp_utc=utc_series.iloc[-1].isoformat(),
        first_timestamp_et=et_series.iloc[0].isoformat(),
        last_timestamp_et=et_series.iloc[-1].isoformat(),
        duplicate_timestamps=duplicate_count,
        off_grid_timestamps=off_grid_count,
        observed_min_quote_increment=_minimum_quote_increment(normalized),
        normalized_zip=zip_path.name,
        normalized_zip_sha256=_sha256(zip_path),
        normalized_gzip=gzip_path.name,
        normalized_gzip_sha256=_sha256(gzip_path),
    )
    csv_path.unlink()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--date-from", required=True)
    parser.add_argument("--date-to", required=True)
    parser.add_argument("--package-version", required=True)
    args = parser.parse_args()

    specs = (
        ProxySpec(
            research_id="NQ_PROXY_DUKASCOPY_USATECH",
            source_instrument="usatechidxusd",
            display_name="Dukascopy USA 100 Technical Index CFD proxy",
            raw_directory=args.raw_root / "usatechidxusd",
        ),
        ProxySpec(
            research_id="ES_PROXY_DUKASCOPY_USA500",
            source_instrument="usa500idxusd",
            display_name="Dukascopy USA 500 Index CFD proxy",
            raw_directory=args.raw_root / "usa500idxusd",
        ),
    )
    prepared = [_prepare(spec, args.output_root) for spec in specs]
    inventory = {
        "purpose": "Asia Sweep proxy data registration; no P&L",
        "provider": "Dukascopy public historical data API",
        "downloader": "dukascopy-node",
        "downloader_version": args.package_version,
        "date_from_argument": args.date_from,
        "date_to_argument": args.date_to,
        "timeframe": "m1",
        "price_type": "bid",
        "source_timezone": "UTC",
        "normalized_session_timezone": _ET_ZONE,
        "include_volumes": True,
        "volume_units": "units",
        "include_flat_bars": True,
        "datasets": [asdict(item) for item in prepared],
    }
    inventory_path = args.output_root / "dukascopy_proxy_inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n")
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
