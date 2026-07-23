from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import lzma
import random
import struct
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SYMBOL = "GBPUSD"
RECORD = struct.Struct(">5if")
DIVISOR = 100000.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_day(day: dt.date, side: str) -> tuple[dt.date, list[tuple], str]:
    month = day.month - 1
    url = (
        f"https://datafeed.dukascopy.com/datafeed/{SYMBOL}/"
        f"{day.year:04d}/{month:02d}/{day.day:02d}/"
        f"{side}_candles_min_1.bi5"
    )
    last_error: str | None = None
    for attempt in range(9):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "DTR-private-research/1.0"},
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read()
            if not raw:
                return day, [], "empty"
            payload = lzma.decompress(raw)
            if len(payload) % RECORD.size:
                raise ValueError(f"record-size mismatch {len(payload)}")
            midnight = dt.datetime.combine(day, dt.time(), tzinfo=dt.timezone.utc)
            rows = []
            for offset in range(0, len(payload), RECORD.size):
                seconds, open_, high, low, close, volume = RECORD.unpack_from(
                    payload, offset
                )
                timestamp = midnight + dt.timedelta(seconds=seconds)
                rows.append(
                    (
                        int(timestamp.timestamp() * 1000),
                        open_ / DIVISOR,
                        high / DIVISOR,
                        low / DIVISOR,
                        close / DIVISOR,
                        float(volume),
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
    raise RuntimeError(f"{day} {side}: {last_error}")


def acquire_year(year: int, out_dir: Path, workers: int) -> dict:
    start = dt.date(year, 1, 1)
    end = dt.date(year + 1, 1, 1)
    days = []
    current = start
    while current < end:
        days.append(current)
        current += dt.timedelta(days=1)

    audit: dict[str, object] = {
        "symbol": SYMBOL,
        "year": year,
        "calendar_days": len(days),
        "divisor": DIVISOR,
        "sides": {},
    }
    for side in ("BID", "ASK"):
        results: dict[dt.date, list[tuple]] = {}
        statuses: dict[str, int] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(fetch_day, day, side): day for day in days}
            for future in as_completed(futures):
                day, rows, status = future.result()
                results[day] = rows
                statuses[status] = statuses.get(status, 0) + 1

        path = out_dir / f"gbpusd_m1_{side.lower()}_{year}.csv.gz"
        row_count = 0
        with gzip.open(path, "wt", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            for day in sorted(results):
                writer.writerows(results[day])
                row_count += len(results[day])
        audit["sides"][side.lower()] = {
            "rows": row_count,
            "statuses": statuses,
            "sha256": sha256(path),
            "file": path.name,
        }
    (out_dir / f"gbpusd_m1_{year}_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--workers", type=int, default=24)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    audits = []
    for year in range(args.start_year, args.end_year + 1):
        audit = acquire_year(year, args.out, args.workers)
        audits.append(audit)
        print(json.dumps(audit), flush=True)

    manifest = {
        "symbol": SYMBOL,
        "period": [args.start_year, args.end_year],
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "annual_audits": audits,
    }
    (args.out / "gbpusd_2022_2025_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
