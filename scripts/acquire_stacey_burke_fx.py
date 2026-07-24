from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import io
import json
import lzma
import random
import struct
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from stacey_burke_lab.fx_source import (
    SourcePartition,
    annual_partitions,
    instrument,
    sha256_file,
    source_filename,
    write_json,
)

RECORD = struct.Struct(">5if")
BI5_FIELD_ORDER = ("seconds", "open", "close", "low", "high", "volume")


def _days(partition: SourcePartition) -> list[dt.date]:
    days: list[dt.date] = []
    current = partition.start_inclusive
    while current < partition.end_exclusive:
        days.append(current)
        current += dt.timedelta(days=1)
    return days


def fetch_day(
    *,
    symbol: str,
    divisor: float,
    day: dt.date,
    side: str,
) -> tuple[dt.date, list[tuple[Any, ...]], str]:
    month = day.month - 1
    url = (
        f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{day.year:04d}/{month:02d}/{day.day:02d}/"
        f"{side}_candles_min_1.bi5"
    )
    last_error: str | None = None
    for attempt in range(9):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Stacey-Burke-private-research/1.0"},
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read()
            if not raw:
                return day, [], "empty"
            payload = lzma.decompress(raw)
            if len(payload) % RECORD.size:
                raise ValueError(f"record-size mismatch {len(payload)}")
            midnight = dt.datetime.combine(day, dt.time(), tzinfo=dt.UTC)
            rows: list[tuple[Any, ...]] = []
            for offset in range(0, len(payload), RECORD.size):
                seconds, open_, close, low, high, volume = RECORD.unpack_from(payload, offset)
                timestamp = midnight + dt.timedelta(seconds=seconds)
                rows.append(
                    (
                        timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        open_ / divisor,
                        high / divisor,
                        low / divisor,
                        close / divisor,
                        float(volume),
                        int(volume > 0),
                    )
                )
            return day, rows, "ok"
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return day, [], "404"
            last_error = f"HTTP {error.code}"
        except Exception as error:  # noqa: BLE001
            last_error = repr(error)
        time.sleep(min(120, 2 * (2**attempt)) + random.random())
    raise RuntimeError(f"{symbol} {day} {side}: {last_error}")


def _write_deterministic_gzip(
    path: Path,
    rows_by_day: dict[dt.date, list[tuple[Any, ...]]],
) -> int:
    row_count = 0
    with path.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                writer = csv.writer(text, lineterminator="\n")
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
                for day in sorted(rows_by_day):
                    writer.writerows(rows_by_day[day])
                    row_count += len(rows_by_day[day])
    return row_count


def acquire_partition(
    *,
    symbol: str,
    partition: SourcePartition,
    out_dir: Path,
    workers: int,
) -> dict[str, Any]:
    item = instrument(symbol)
    days = _days(partition)
    audit: dict[str, Any] = {
        "symbol": item.symbol,
        "factor_block": item.factor_block,
        "partition": {
            "label": partition.label,
            "start_inclusive": partition.start_inclusive.isoformat(),
            "end_exclusive": partition.end_exclusive.isoformat(),
            "monitoring_only": partition.monitoring_only,
        },
        "calendar_days": len(days),
        "divisor": item.divisor,
        "pip_size": item.pip_size,
        "bi5_field_order": list(BI5_FIELD_ORDER),
        "inactive_records_preserved": True,
        "performance_execution": False,
        "sides": {},
    }
    for side in ("BID", "ASK"):
        rows_by_day: dict[dt.date, list[tuple[Any, ...]]] = {}
        statuses: dict[str, int] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    fetch_day,
                    symbol=item.symbol,
                    divisor=item.divisor,
                    day=day,
                    side=side,
                ): day
                for day in days
            }
            for future in as_completed(futures):
                day, rows, status = future.result()
                rows_by_day[day] = rows
                statuses[status] = statuses.get(status, 0) + 1
        path = out_dir / source_filename(item.symbol, side, partition.label)
        row_count = _write_deterministic_gzip(path, rows_by_day)
        active_rows = sum(int(row[6]) for rows in rows_by_day.values() for row in rows)
        audit["sides"][side.lower()] = {
            "file": path.name,
            "rows": row_count,
            "active_rows": active_rows,
            "zero_volume_rows": row_count - active_rows,
            "statuses": dict(sorted(statuses.items())),
            "sha256": sha256_file(path),
        }
    write_json(audit, out_dir / f"{item.symbol.lower()}_m1_{partition.label}_audit.json")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Acquire canonical Dukascopy BID/ASK M1 for Stacey Burke FX research"
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--ytd-end-exclusive",
        type=dt.date.fromisoformat,
        default=dt.date(2026, 7, 24),
    )
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    item = instrument(args.symbol)
    partitions = annual_partitions(
        start_year=args.start_year,
        end_year=args.end_year,
        ytd_end_exclusive=args.ytd_end_exclusive,
    )
    audits = []
    for partition in partitions:
        audit = acquire_partition(
            symbol=item.symbol,
            partition=partition,
            out_dir=args.out,
            workers=args.workers,
        )
        audits.append(audit)
        print(json.dumps(audit, sort_keys=True), flush=True)

    manifest = {
        "programme": "stacey_burke_fx_source_universe_v1",
        "symbol": item.symbol,
        "factor_block": item.factor_block,
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "annual_audits": audits,
        "performance_execution": False,
    }
    write_json(manifest, args.out / f"{item.symbol.lower()}_source_manifest.json")


if __name__ == "__main__":
    main()
