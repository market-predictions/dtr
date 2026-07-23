from __future__ import annotations

import argparse
import subprocess
import time
from datetime import date
from pathlib import Path


def _month_starts(start: date, end: date) -> list[date]:
    starts: list[date] = []
    current = date(start.year, start.month, 1)
    if current < start:
        current = start
    while current < end:
        starts.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return starts


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _run_chunk(
    *,
    instrument: str,
    start: date,
    end: date,
    package_version: str,
    executable: Path,
    output_root: Path,
    cache_root: Path,
    log_path: Path,
    max_attempts: int,
) -> None:
    chunk_name = f"{start.isoformat()}_{end.isoformat()}"
    chunk_directory = output_root / chunk_name
    marker = chunk_directory / ".complete"
    existing = sorted(chunk_directory.rglob("*.csv")) if chunk_directory.exists() else []
    if marker.exists() and len(existing) == 1:
        with log_path.open("a") as log:
            log.write(f"SKIP {chunk_name}: {existing[0]}\n")
        return

    chunk_directory.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable),
        "-i",
        instrument,
        "-from",
        start.isoformat(),
        "-to",
        end.isoformat(),
        "-t",
        "m1",
        "-p",
        "bid",
        "-utc",
        "0",
        "-v",
        "-vu",
        "units",
        "-fl",
        "-f",
        "csv",
        "-df",
        "iso",
        "-dir",
        str(chunk_directory),
        "-bs",
        "1",
        "-bp",
        "3000",
        "-ch",
        "-chpath",
        str(cache_root),
        "-r",
        "8",
        "-re",
        "-rp",
        "10000",
    ]

    for attempt in range(1, max_attempts + 1):
        with log_path.open("a") as log:
            log.write(
                f"\nRUN {chunk_name} attempt={attempt}/{max_attempts}\n"
                f"PACKAGE_VERSION {package_version}\n"
                f"COMMAND {' '.join(command)}\n"
            )
            log.flush()
            result = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                text=True,
            )
        files = sorted(chunk_directory.rglob("*.csv"))
        if result.returncode == 0 and len(files) == 1:
            marker.write_text(files[0].name + "\n")
            with log_path.open("a") as log:
                log.write(f"SUCCESS {chunk_name}: {files[0]}\n")
            return

        with log_path.open("a") as log:
            log.write(
                f"FAIL {chunk_name}: returncode={result.returncode} csv_files={files}\n"
            )
        if attempt < max_attempts:
            cooldown = 60 * attempt
            time.sleep(cooldown)

    raise RuntimeError(f"Failed Dukascopy chunk {instrument} {chunk_name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--date-from", type=date.fromisoformat, required=True)
    parser.add_argument("--date-to", type=date.fromisoformat, required=True)
    parser.add_argument("--package-version", required=True)
    parser.add_argument(
        "--executable",
        type=Path,
        default=Path("node_modules/.bin/dukascopy-node"),
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--log-path", type=Path, required=True)
    parser.add_argument("--max-attempts", type=int, default=5)
    args = parser.parse_args()

    if args.date_to <= args.date_from:
        raise ValueError("date-to must be after date-from")
    if args.max_attempts < 1:
        raise ValueError("max-attempts must be positive")
    if not args.executable.exists():
        raise FileNotFoundError(f"Dukascopy executable not found: {args.executable}")

    args.output_root.mkdir(parents=True, exist_ok=True)
    args.cache_root.mkdir(parents=True, exist_ok=True)
    args.log_path.parent.mkdir(parents=True, exist_ok=True)

    starts = _month_starts(args.date_from, args.date_to)
    for index, start in enumerate(starts):
        end = min(_next_month(start), args.date_to)
        _run_chunk(
            instrument=args.instrument,
            start=start,
            end=end,
            package_version=args.package_version,
            executable=args.executable,
            output_root=args.output_root,
            cache_root=args.cache_root,
            log_path=args.log_path,
            max_attempts=args.max_attempts,
        )
        if index < len(starts) - 1:
            time.sleep(15)


if __name__ == "__main__":
    main()
