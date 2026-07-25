from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.fingerprint_engine import (
    build_fingerprint_ledgers,
    write_fingerprint_outputs,
)
from dtr_lab.strategies.asia_sweep.fingerprint_labels import (
    enforce_window_and_two_sided_labels,
)
from dtr_lab.strategies.asia_sweep.fx_ten_pair import load_midpoint_minutes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    minutes = load_midpoint_minutes(
        args.data,
        args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    events, levels, sessions = build_fingerprint_ledgers(
        args.symbol,
        minutes,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    events = enforce_window_and_two_sided_labels(events)
    summary = write_fingerprint_outputs(
        args.out,
        symbol=args.symbol,
        events=events,
        levels=levels,
        sessions=sessions,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
