from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
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

SYMBOL = "USATECHIDXUSD"
RECORD = struct.Struct(">5if")
DIVISOR = 1000.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fetch_day(day: dt.date) -> tuple[dt.date, list[tuple[str, float, float, float, float, float]], str, int]:
    url = (
        f"https://datafeed.dukascopy.com/datafeed/{SYMBOL}/"
        f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}/BID_candles_min_1.bi5"
    )
    last_error = "unknown"
    for attempt in range(8):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Stoic123-private-research/1.0"},
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read()
            if not raw:
                return day, [], "empty", 0
            payload = lzma.decompress(raw)
            if len(payload) % RECORD.size:
                raise ValueError(f"record-size mismatch on {day}")

            midnight = dt.datetime.combine(day, dt.time(), tzinfo=dt.timezone.utc)
            rows: list[tuple[str, float, float, float, float, float]] = []
            zero_volume = 0
            for offset in range(0, len(payload), RECORD.size):
                seconds, open_raw, close_raw, low_raw, high_raw, volume_raw = RECORD.unpack_from(
                    payload,
                    offset,
                )
                volume = float(volume_raw) * 1_000_000.0
                if volume <= 0:
                    zero_volume += 1
                    continue
                open_ = open_raw / DIVISOR
                high = high_raw / DIVISOR
                low = low_raw / DIVISOR
                close = close_raw / DIVISOR
                if high < max(open_, close, low) or low > min(open_, close, high):
                    raise ValueError(f"OHLC integrity failure on {day}")
                timestamp = midnight + dt.timedelta(seconds=seconds)
                rows.append(
                    (
                        timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        open_,
                        high,
                        low,
                        close,
                        volume,
                    )
                )
            return day, rows, "ok", zero_volume
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return day, [], "404", 0
            last_error = f"HTTP {error.code}"
        except Exception as error:  # noqa: BLE001
            last_error = repr(error)
        time.sleep(min(90, 3 * (2**attempt)) + random.random())
    raise RuntimeError(f"{day}: {last_error}")


def _open_deterministic_gzip_text(path: Path) -> io.TextIOWrapper:
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(compressed, encoding="utf-8", newline="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire a fixed USATECH M1 BID partition")
    parser.add_argument("--start", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--end", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.start >= args.end:
        raise ValueError("start must be before end")

    days: list[dt.date] = []
    current = args.start
    while current < args.end:
        days.append(current)
        current += dt.timedelta(days=1)

    results: dict[dt.date, list[tuple[str, float, float, float, float, float]]] = {}
    statuses: dict[str, int] = {}
    zero_volume_rows = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_fetch_day, day): day for day in days}
        for future in as_completed(futures):
            day, rows, status, zero_volume = future.result()
            results[day] = rows
            statuses[status] = statuses.get(status, 0) + 1
            zero_volume_rows += zero_volume

    output = Path(f"usatechidxusd_m1_bid_{args.label}.csv.gz")
    row_count = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    seen: set[str] = set()
    with _open_deterministic_gzip_text(output) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["timestamp UTC", "open", "high", "low", "close", "volume", "is_active_quote"])
        for day in sorted(results):
            for timestamp, open_, high, low, close, volume in results[day]:
                if timestamp in seen:
                    raise ValueError(f"duplicate timestamp: {timestamp}")
                seen.add(timestamp)
                writer.writerow([timestamp, open_, high, low, close, volume, 1])
                row_count += 1
                first_timestamp = first_timestamp or timestamp
                last_timestamp = timestamp

    audit = {
        "classification": "Dukascopy USATECH bid-CFD proxy; not CME NQ futures",
        "label": args.label,
        "start_inclusive_utc": args.start.isoformat(),
        "end_exclusive_utc": args.end.isoformat(),
        "requested_days": len(days),
        "active_rows": row_count,
        "zero_volume_rows_removed": zero_volume_rows,
        "duplicate_timestamps": 0,
        "first_timestamp_utc": first_timestamp,
        "last_timestamp_utc": last_timestamp,
        "statuses": dict(sorted(statuses.items())),
        "file": output.name,
        "sha256": _sha256(output),
    }
    audit_path = Path(f"usatechidxusd_m1_bid_{args.label}_audit.json")
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
