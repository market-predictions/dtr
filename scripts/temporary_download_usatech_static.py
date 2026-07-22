from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
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


def fetch_day(day: dt.date) -> tuple[dt.date, list[tuple], str]:
    url = (
        f"https://datafeed.dukascopy.com/datafeed/{SYMBOL}/"
        f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}/BID_candles_min_1.bi5"
    )
    last_error = "unknown"
    for attempt in range(8):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "DTR-private-research/1.0"}
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read()
            if not raw:
                return day, [], "empty"
            payload = lzma.decompress(raw)
            if len(payload) % RECORD.size:
                raise ValueError(f"record-size mismatch on {day}")
            rows = []
            midnight = dt.datetime.combine(day, dt.time(), tzinfo=dt.timezone.utc)
            for offset in range(0, len(payload), RECORD.size):
                seconds, open_, close, low, high, volume = RECORD.unpack_from(
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
                        float(volume) * 1_000_000.0,
                    )
                )
            return day, rows, "ok"
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return day, [], "404"
            last_error = f"HTTP {error.code}"
        except Exception as error:  # noqa: BLE001
            last_error = repr(error)
        time.sleep(min(90, 3 * (2**attempt)) + random.random())
    raise RuntimeError(f"{day}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--end", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    days = []
    current = args.start
    while current < args.end:
        days.append(current)
        current += dt.timedelta(days=1)

    results: dict[dt.date, list[tuple]] = {}
    statuses: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_day, day): day for day in days}
        for future in as_completed(futures):
            day, rows, status = future.result()
            results[day] = rows
            statuses[status] = statuses.get(status, 0) + 1

    output = Path(f"usatechidxusd_m1_bid_{args.label}.csv.gz")
    row_count = 0
    with gzip.open(output, "wt", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for day in sorted(results):
            writer.writerows(results[day])
            row_count += len(results[day])

    audit = Path(f"usatechidxusd_m1_bid_{args.label}_audit.txt")
    audit.write_text(
        "\n".join(
            [
                f"label={args.label}",
                f"start={args.start}",
                f"end_exclusive={args.end}",
                f"days={len(days)}",
                f"rows={row_count}",
                *(f"status_{key}={value}" for key, value in sorted(statuses.items())),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(audit.read_text())


if __name__ == "__main__":
    main()
