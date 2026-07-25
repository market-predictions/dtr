from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.amsterdam_window import (
    WINDOW_END_MINUTE,
    WINDOW_START_MINUTE,
    build_amsterdam_window_matches,
)
from dtr_lab.strategies.asia_sweep.fx_ten_pair import (
    PAIR_SPECS,
    load_midpoint_minutes,
    write_pair_outputs,
)
from dtr_lab.strategies.asia_sweep.fx_ten_pair_runtime import (
    prepare_boundary_rows_fast,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", required=True, choices=("EURUSD", "GBPUSD"))
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.symbol not in PAIR_SPECS:
        raise ValueError(f"unsupported symbol: {args.symbol}")
    minutes = load_midpoint_minutes(
        args.data,
        args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    all_rows = prepare_boundary_rows_fast(
        args.symbol,
        minutes,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    rows, matched_events, matched_controls = build_amsterdam_window_matches(
        all_rows,
        start_minute=WINDOW_START_MINUTE,
        end_minute=WINDOW_END_MINUTE,
    )
    summary = write_pair_outputs(
        args.out,
        symbol=args.symbol,
        boundary_rows=rows,
        matched_events=matched_events,
        matched_controls=matched_controls,
    )
    summary.update(
        {
            "programme": "ASIAN_SWEEP_AMSTERDAM_0900_1000_V1",
            "window_timezone": "Europe/Amsterdam",
            "window_start": "09:00:00",
            "window_end_exclusive": "10:00:00",
            "analysis_start_year": args.start_year,
            "analysis_end_year": args.end_year,
        }
    )
    (args.out / "pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
