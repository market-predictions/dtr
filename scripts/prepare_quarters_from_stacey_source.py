from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_PREFIX = "gbpusd"
PRICE_COLUMNS = ("open", "high", "low", "close")
OUTPUT_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_and_normalize(path: Path, scale: float) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        compression="gzip",
        usecols=["timestamp_utc", *PRICE_COLUMNS, "volume", "is_active_quote"],
        dtype={
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
            "is_active_quote": "int8",
        },
    )
    timestamps = pd.to_datetime(frame.pop("timestamp_utc"), utc=True, errors="raise")
    timestamp_ms = timestamps.astype("int64") // 1_000_000
    for column in PRICE_COLUMNS:
        frame[column] *= scale
    expected_active = (frame["volume"] > 0).astype("int8")
    if not np.array_equal(
        frame.pop("is_active_quote").to_numpy(), expected_active.to_numpy()
    ):
        raise ValueError(f"Active-quote flag mismatch in {path.name}")
    frame.insert(0, "timestamp", timestamp_ms.astype("int64"))
    return frame.loc[:, OUTPUT_COLUMNS]


def write_normalized(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(
        path,
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "mtime": 0, "compresslevel": 6},
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Adapt retained Stacey Burke Dukascopy BID/ASK M1 source artifacts to the "
            "unchanged frozen Quarters Stage-1 engine schema."
        )
    )
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-symbol", required=True)
    parser.add_argument("--normalization-scale", type=float, required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    args = parser.parse_args()

    symbol = args.source_symbol.upper().strip()
    prefix = symbol.lower()
    if args.normalization_scale <= 0:
        raise ValueError("normalization-scale must be positive")
    if args.end_year < args.start_year:
        raise ValueError("end-year must not precede start-year")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for year in range(args.start_year, args.end_year + 1):
        source_audit_path = args.source_dir / f"{prefix}_m1_{year}_audit.json"
        source_audit = json.loads(source_audit_path.read_text(encoding="utf-8"))
        if source_audit["symbol"] != symbol:
            raise ValueError(f"Source symbol mismatch in {source_audit_path.name}")

        normalized: dict[str, pd.DataFrame] = {}
        output_sides: dict[str, dict] = {}
        for side in ("bid", "ask"):
            source_meta = source_audit["sides"][side]
            source_path = args.source_dir / source_meta["file"]
            if sha256_file(source_path) != source_meta["sha256"]:
                raise ValueError(f"Source checksum failure: {source_path.name}")
            frame = load_and_normalize(source_path, args.normalization_scale)
            if len(frame) != int(source_meta["rows"]):
                raise ValueError(f"Source row-count failure: {source_path.name}")
            normalized[side] = frame

        if not np.array_equal(
            normalized["bid"]["timestamp"].to_numpy(),
            normalized["ask"]["timestamp"].to_numpy(),
        ):
            raise ValueError(f"Bid/ask timestamp mismatch for {symbol} {year}")

        for side in ("bid", "ask"):
            output_path = (
                args.output_dir / f"{OUTPUT_PREFIX}_m1_{side}_{year}.csv.gz"
            )
            write_normalized(output_path, normalized[side])
            output_sides[side] = {
                "file": output_path.name,
                "rows": int(len(normalized[side])),
                "sha256": sha256_file(output_path),
                "source_file": source_audit["sides"][side]["file"],
                "source_sha256": source_audit["sides"][side]["sha256"],
            }

        output_audit = {
            "pair_label": symbol,
            "source_programme": "stacey_burke_fx_source_universe_v1",
            "source_artifact_schema": "canonical Dukascopy BID/ASK M1",
            "year": year,
            "source_pip_size": source_audit["pip_size"],
            "source_quote_normalization_scale": args.normalization_scale,
            "analysis_pip_size": 0.0001,
            "sides": output_sides,
        }
        audit_path = args.output_dir / f"{OUTPUT_PREFIX}_m1_{year}_audit.json"
        audit_path.write_text(
            json.dumps(output_audit, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(output_audit, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
