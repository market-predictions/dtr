from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from stacey_burke_lab.fx_source import qualify_symbol_directory, write_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Qualify canonical Dukascopy BID/ASK source without strategy execution"
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--ytd-end-exclusive",
        type=dt.date.fromisoformat,
        default=dt.date(2026, 7, 24),
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = qualify_symbol_directory(
        directory=args.data,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
        ytd_end_exclusive=args.ytd_end_exclusive,
    )
    write_json(result, args.out)
    if not result["qualified"]:
        raise SystemExit(f"source qualification failed for {result['symbol']}")


if __name__ == "__main__":
    main()
