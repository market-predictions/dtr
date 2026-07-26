from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.runner_optimization_simulator import (
    runner_policy_manifest,
    simulate_pair_runner_grid,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--execution-orders", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2019)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    execution_orders = pd.read_csv(args.execution_orders)
    events = pd.read_csv(args.events)
    grid = simulate_pair_runner_grid(
        execution_orders,
        events,
        args.data,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    grid.to_csv(args.out / "runner_policy_grid.csv", index=False)
    summary = {
        "programme": "ASIAN_SWEEP_RUNNER_ENTRY_OPTIMISATION_V4",
        "symbol": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "policy_count": len(runner_policy_manifest()),
        "rows": int(len(grid)),
        "filled_rows": int(grid["filled"].astype(bool).sum()),
        "unique_events": int(grid["event_id"].nunique()),
    }
    (args.out / "pair_runner_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
