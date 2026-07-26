from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.extended_reversal_liquidity import (
    install_opposing_liquidity_level_recorder,
    select_opposing_liquidity_levels,
)
from dtr_lab.strategies.asia_sweep.fingerprint_engine import (
    build_fingerprint_ledgers,
    write_fingerprint_outputs,
)
from dtr_lab.strategies.asia_sweep.fingerprint_labels import (
    enforce_window_and_two_sided_labels,
)
from dtr_lab.strategies.asia_sweep.fingerprint_performance import (
    install_indexed_pivot_selector,
)
from dtr_lab.strategies.asia_sweep.fx_ten_pair import load_midpoint_minutes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build fingerprint anatomy and opposing liquidity in one causal pass."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    install_indexed_pivot_selector()
    install_opposing_liquidity_level_recorder()
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
    opposing = select_opposing_liquidity_levels(levels)
    opposing.to_csv(args.out / "opposing_liquidity_levels.csv", index=False)
    summary["opposing_liquidity_levels"] = int(len(opposing))
    summary["opposing_liquidity_events"] = int(opposing["event_id"].nunique())
    (args.out / "transition_anatomy_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
