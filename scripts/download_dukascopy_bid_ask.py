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
from dataclasses import dataclass
from pathlib import Path

_RECORD = struct.Struct(">5if")
_ENGINE_INSTRUMENT_ID = "gbpusd"
_TRANSIENT_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class SideResult:
    rows: list[tuple[int, float, float, float, float, float]]
    status: str


@dataclass(frozen=True)
class DayResult:
    day: dt.date
    bid_rows: list[tuple[int, float, float, float, float, float]]
    ask_rows: list[tuple[int, float, float, float, float, float]]
    audit: dict


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _decode_payload(
    payload: bytes,
    day: dt.date,
    divisor: float,
    normalization_scale: float,
) -> list[tuple[int, float, float, float, float, float]]:
    if len(payload) % _RECORD.size:
        raise ValueError(f"record-size mismatch on {day}")
    midnight = dt.datetime.combine(day, dt.time(), tzinfo=dt.UTC)
    rows: list[tuple[int, float, float, float, float, float]] = []
    for offset in range(0, len(payload), _RECORD.size):
        seconds, open_, close, low, high, volume = _RECORD.unpack_from(payload, offset)
        timestamp = midnight + dt.timedelta(seconds=seconds)
        rows.append(
            (
                int(timestamp.timestamp() * 1000),
                open_ / divisor * normalization_scale,
                high / divisor * normalization_scale,
                low / divisor * normalization_scale,
                close / divisor * normalization_scale,
                float(volume),
            )
        )
    return rows


def _retry_delay(error: urllib.error.HTTPError | None, attempt: int, base: float) -> float:
    if error is not None:
        retry_after = error.headers.get("Retry-After")
        if retry_after:
            try:
                return min(180.0, max(base, float(retry_after)))
            except ValueError:
                pass
    return min(120.0, base * (2**attempt)) + random.uniform(0.0, 1.0)


def _fetch_side(
    day: dt.date,
    *,
    symbol: str,
    side: str,
    divisor: float,
    normalization_scale: float,
    attempts: int,
    base_delay: float,
) -> SideResult:
    url = (
        f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}/"
        f"{side}_candles_min_1.bi5"
    )
    last_error = "unknown"
    for attempt in range(attempts):
        http_error: urllib.error.HTTPError | None = None
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "DTR-quarters-replication/1.1"},
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read()
            if not raw:
                return SideResult([], "empty")
            rows = _decode_payload(
                lzma.decompress(raw), day, divisor, normalization_scale
            )
            return SideResult(rows, "ok")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return SideResult([], "404")
            if error.code not in _TRANSIENT_HTTP_CODES:
                raise
            http_error = error
            last_error = f"HTTP {error.code}"
        except Exception as error:  # noqa: BLE001
            last_error = repr(error)
        if attempt + 1 < attempts:
            time.sleep(_retry_delay(http_error, attempt, base_delay))
    raise RuntimeError(f"{day} {side}: {last_error}")


def _fetch_day(
    day: dt.date,
    *,
    symbol: str,
    divisor: float,
    normalization_scale: float,
    attempts: int,
    base_delay: float,
) -> DayResult:
    bid = _fetch_side(
        day,
        symbol=symbol,
        side="BID",
        divisor=divisor,
        normalization_scale=normalization_scale,
        attempts=attempts,
        base_delay=base_delay,
    )
    ask = _fetch_side(
        day,
        symbol=symbol,
        side="ASK",
        divisor=divisor,
        normalization_scale=normalization_scale,
        attempts=attempts,
        base_delay=base_delay,
    )
    if not bid.rows and not ask.rows:
        status = bid.status if bid.status == ask.status else "closed"
        return DayResult(
            day,
            [],
            [],
            {
                "status": status,
                "bid_rows": 0,
                "ask_rows": 0,
                "common_rows": 0,
                "bid_only": 0,
                "ask_only": 0,
            },
        )
    if not bid.rows or not ask.rows:
        raise RuntimeError(
            f"One-sided data on {day}: bid={bid.status}/{len(bid.rows)}, "
            f"ask={ask.status}/{len(ask.rows)}"
        )

    bid_by_timestamp = {row[0]: row for row in bid.rows}
    ask_by_timestamp = {row[0]: row for row in ask.rows}
    common_timestamps = sorted(bid_by_timestamp.keys() & ask_by_timestamp.keys())
    return DayResult(
        day,
        [bid_by_timestamp[timestamp] for timestamp in common_timestamps],
        [ask_by_timestamp[timestamp] for timestamp in common_timestamps],
        {
            "status": "ok",
            "bid_rows": len(bid.rows),
            "ask_rows": len(ask.rows),
            "common_rows": len(common_timestamps),
            "bid_only": len(bid_by_timestamp.keys() - ask_by_timestamp.keys()),
            "ask_only": len(ask_by_timestamp.keys() - bid_by_timestamp.keys()),
        },
    )


def _fetch_batch(
    days: list[dt.date],
    *,
    symbol: str,
    divisor: float,
    normalization_scale: float,
    workers: int,
    attempts: int,
    base_delay: float,
) -> tuple[dict[dt.date, DayResult], dict[dt.date, str]]:
    results: dict[dt.date, DayResult] = {}
    failures: dict[dt.date, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _fetch_day,
                day,
                symbol=symbol,
                divisor=divisor,
                normalization_scale=normalization_scale,
                attempts=attempts,
                base_delay=base_delay,
            ): day
            for day in days
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            day = futures[future]
            try:
                results[day] = future.result()
            except Exception as error:  # noqa: BLE001
                failures[day] = repr(error)
            if completed % 50 == 0 or completed == len(days):
                print(
                    f"  batch {completed}/{len(days)} days; "
                    f"failures={len(failures)}",
                    flush=True,
                )
    return results, failures


def _acquire_year(
    days: list[dt.date],
    *,
    symbol: str,
    divisor: float,
    normalization_scale: float,
    workers: int,
) -> dict[dt.date, DayResult]:
    results: dict[dt.date, DayResult] = {}
    remaining = list(days)
    retry_plan = (
        (workers, 3, 1.5),
        (min(2, workers), 8, 5.0),
        (1, 12, 10.0),
    )
    last_failures: dict[dt.date, str] = {}
    for pass_number, (pass_workers, attempts, base_delay) in enumerate(
        retry_plan, start=1
    ):
        if not remaining:
            break
        print(
            f"  acquisition pass {pass_number}: days={len(remaining)}, "
            f"workers={pass_workers}, attempts={attempts}",
            flush=True,
        )
        pass_results, failures = _fetch_batch(
            remaining,
            symbol=symbol,
            divisor=divisor,
            normalization_scale=normalization_scale,
            workers=pass_workers,
            attempts=attempts,
            base_delay=base_delay,
        )
        results.update(pass_results)
        last_failures = failures
        remaining = sorted(failures)
        if remaining and pass_number < len(retry_plan):
            print(
                f"  cooling down before retrying {len(remaining)} failed days",
                flush=True,
            )
            time.sleep(30.0)
    if remaining:
        sample = {day.isoformat(): last_failures[day] for day in remaining[:10]}
        raise RuntimeError(
            f"Persistent source failures for {len(remaining)} days: {sample}"
        )
    if len(results) != len(days):
        raise RuntimeError(
            f"Acquisition completeness failure: {len(results)} of {len(days)} days"
        )
    return results


def _write_side(
    path: Path,
    rows_by_day: dict[dt.date, list[tuple[int, float, float, float, float, float]]],
) -> int:
    row_count = 0
    with gzip.open(path, "wt", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for day in sorted(rows_by_day):
            writer.writerows(rows_by_day[day])
            row_count += len(rows_by_day[day])
    return row_count


def _cache_is_valid(output_directory: Path, year: int) -> bool:
    bid_path = output_directory / f"{_ENGINE_INSTRUMENT_ID}_m1_bid_{year}.csv.gz"
    ask_path = output_directory / f"{_ENGINE_INSTRUMENT_ID}_m1_ask_{year}.csv.gz"
    manifest_path = output_directory / f"{_ENGINE_INSTRUMENT_ID}_m1_{year}_audit.json"
    if not bid_path.exists() or not ask_path.exists() or not manifest_path.exists():
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return (
        _sha256(bid_path) == manifest["sides"]["bid"]["sha256"]
        and _sha256(ask_path) == manifest["sides"]["ask"]["sha256"]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download aligned Dukascopy M1 bid/ask and normalize the quote scale so the "
            "unchanged GBPUSD Stage-1 engine operates in an identical pip domain."
        )
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--pair-label", required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--divisor", type=float, required=True)
    parser.add_argument("--normalization-scale", type=float, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    if args.end_year < args.start_year:
        raise ValueError("end-year must not precede start-year")
    if args.divisor <= 0 or args.normalization_scale <= 0:
        raise ValueError("divisor and normalization-scale must be positive")
    if args.workers < 1:
        raise ValueError("workers must be positive")

    args.output_directory.mkdir(parents=True, exist_ok=True)
    for year in range(args.start_year, args.end_year + 1):
        if _cache_is_valid(args.output_directory, year):
            print(f"Reusing qualified cache for {args.pair_label} {year}", flush=True)
            continue

        start = dt.date(year, 1, 1)
        end = dt.date(year + 1, 1, 1)
        days = [start + dt.timedelta(days=offset) for offset in range((end - start).days)]
        print(f"Downloading {args.pair_label} {year}", flush=True)
        day_results = _acquire_year(
            days,
            symbol=args.symbol,
            divisor=args.divisor,
            normalization_scale=args.normalization_scale,
            workers=args.workers,
        )
        bid_rows_by_day = {day: result.bid_rows for day, result in day_results.items()}
        ask_rows_by_day = {day: result.ask_rows for day, result in day_results.items()}
        day_audits = {day: result.audit for day, result in day_results.items()}

        bid_only = sum(audit["bid_only"] for audit in day_audits.values())
        ask_only = sum(audit["ask_only"] for audit in day_audits.values())
        if bid_only or ask_only:
            raise RuntimeError(
                f"Unmatched source timestamps for {args.pair_label} {year}: "
                f"bid_only={bid_only}, ask_only={ask_only}"
            )

        bid_path = args.output_directory / f"{_ENGINE_INSTRUMENT_ID}_m1_bid_{year}.csv.gz"
        ask_path = args.output_directory / f"{_ENGINE_INSTRUMENT_ID}_m1_ask_{year}.csv.gz"
        bid_rows = _write_side(bid_path, bid_rows_by_day)
        ask_rows = _write_side(ask_path, ask_rows_by_day)
        if bid_rows != ask_rows:
            raise RuntimeError(f"Aligned row-count mismatch for {args.pair_label} {year}")

        statuses: dict[str, int] = {}
        for audit in day_audits.values():
            statuses[audit["status"]] = statuses.get(audit["status"], 0) + 1
        manifest = {
            "source_symbol": args.symbol,
            "pair_label": args.pair_label,
            "year": year,
            "source_divisor": args.divisor,
            "source_quote_normalization_scale": args.normalization_scale,
            "engine_instrument_id": _ENGINE_INSTRUMENT_ID,
            "analysis_pip_size": 0.0001,
            "acquisition_policy": {
                "initial_workers": args.workers,
                "retry_passes": [
                    {"workers": args.workers, "attempts": 3},
                    {"workers": min(2, args.workers), "attempts": 8},
                    {"workers": 1, "attempts": 12},
                ],
            },
            "source_status": statuses,
            "source_unmatched": {"bid_only": bid_only, "ask_only": ask_only},
            "sides": {
                "bid": {
                    "file": bid_path.name,
                    "rows": bid_rows,
                    "sha256": _sha256(bid_path),
                },
                "ask": {
                    "file": ask_path.name,
                    "rows": ask_rows,
                    "sha256": _sha256(ask_path),
                },
            },
        }
        manifest_path = (
            args.output_directory / f"{_ENGINE_INSTRUMENT_ID}_m1_{year}_audit.json"
        )
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
