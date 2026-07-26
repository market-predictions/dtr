from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.extended_reversal_liquidity import (
    install_opposing_liquidity_level_recorder,
    select_opposing_liquidity_levels,
)
from dtr_lab.strategies.asia_sweep.fingerprint_engine import build_fingerprint_ledgers
from dtr_lab.strategies.asia_sweep.fingerprint_performance import (
    install_indexed_pivot_selector,
)
from dtr_lab.strategies.asia_sweep.fx_ten_pair import load_midpoint_minutes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2019)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    install_indexed_pivot_selector()
    install_opposing_liquidity_level_recorder()
    minutes = load_midpoint_minutes(
        args.data,
        args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    _, levels, _ = build_fingerprint_ledgers(
        args.symbol,
        minutes,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    opposing = select_opposing_liquidity_levels(levels)
    output = args.out / "opposing_liquidity_levels.csv"
    opposing.to_csv(output, index=False)
    role_counts = (
        opposing.groupby(["side", "level_side"], sort=True)
        .size()
        .rename("levels")
        .reset_index()
        .to_dict(orient="records")
    )
    summary = {
        "symbol": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "levels": int(len(opposing)),
        "events": int(opposing["event_id"].nunique()),
        "families": sorted(opposing["level_family"].unique().tolist()),
        "role_counts": role_counts,
    }
    (args.out / "opposing_liquidity_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
