from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.fx_ten_pair import (
    PAIR_SPECS,
    load_midpoint_minutes,
    write_pair_outputs,
)
from dtr_lab.strategies.asia_sweep.fx_ten_pair_runtime import (
    match_controls_safe,
    prepare_boundary_rows_fast,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", required=True, choices=sorted(PAIR_SPECS))
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2019)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    minutes = load_midpoint_minutes(
        args.data,
        args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    rows = prepare_boundary_rows_fast(
        args.symbol,
        minutes,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    matched_events, matched_controls = match_controls_safe(rows)
    summary = write_pair_outputs(
        args.out,
        symbol=args.symbol,
        boundary_rows=rows,
        matched_events=matched_events,
        matched_controls=matched_controls,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
