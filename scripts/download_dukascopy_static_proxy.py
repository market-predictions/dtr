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

_RECORD = struct.Struct(">5if")


def _fetch_day(
    day: dt.date,
    *,
    symbol: str,
    divisor: float,
) -> tuple[dt.date, list[tuple[int, float, float, float, float, float]], str]:
    url = (
        f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}/BID_candles_min_1.bi5"
    )
    last_error = "unknown"
    for attempt in range(8):
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
            if len(payload) % _RECORD.size:
                raise ValueError(f"record-size mismatch on {day}")

            rows: list[tuple[int, float, float, float, float, float]] = []
            midnight = dt.datetime.combine(day, dt.time(), tzinfo=dt.UTC)
            for offset in range(0, len(payload), _RECORD.size):
                seconds, open_, close, low, high, volume = _RECORD.unpack_from(
                    payload,
                    offset,
                )
                timestamp = midnight + dt.timedelta(seconds=seconds)
                rows.append(
                    (
                        int(timestamp.timestamp() * 1000),
                        open_ / divisor,
                        high / divisor,
                        low / divisor,
                        close / divisor,
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
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--instrument-id", required=True)
    parser.add_argument("--start", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--end", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--divisor", type=float, default=1000.0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    if args.end <= args.start:
        raise ValueError("end must be after start")
    if args.divisor <= 0:
        raise ValueError("divisor must be positive")
    if args.workers < 1:
        raise ValueError("workers must be positive")

    days: list[dt.date] = []
    current = args.start
    while current < args.end:
        days.append(current)
        current += dt.timedelta(days=1)

    results: dict[
        dt.date,
        list[tuple[int, float, float, float, float, float]],
    ] = {}
    statuses: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                _fetch_day,
                day,
                symbol=args.symbol,
                divisor=args.divisor,
            ): day
            for day in days
        }
        for future in as_completed(futures):
            day, rows, status = future.result()
            results[day] = rows
            statuses[status] = statuses.get(status, 0) + 1

    args.output_directory.mkdir(parents=True, exist_ok=True)
    output = args.output_directory / (
        f"{args.instrument_id}_m1_bid_{args.label}.csv.gz"
    )
    row_count = 0
    with gzip.open(output, "wt", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for day in sorted(results):
            writer.writerows(results[day])
            row_count += len(results[day])

    audit = args.output_directory / (
        f"{args.instrument_id}_m1_bid_{args.label}_audit.txt"
    )
    audit.write_text(
        "\n".join(
            [
                f"symbol={args.symbol}",
                f"instrument_id={args.instrument_id}",
                f"label={args.label}",
                f"start={args.start}",
                f"end_exclusive={args.end}",
                f"days={len(days)}",
                f"rows={row_count}",
                f"workers={args.workers}",
                f"divisor={args.divisor}",
                *(f"status_{key}={value}" for key, value in sorted(statuses.items())),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(audit.read_text())


if __name__ == "__main__":
    main()
