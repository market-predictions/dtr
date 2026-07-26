from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.staged_exit_simulator import (
    simulate_pair_staged_exits,
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
    staged = simulate_pair_staged_exits(
        execution_orders,
        events,
        args.data,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    staged.to_csv(args.out / "staged_exit_orders.csv", index=False)
    summary = {
        "programme": "ASIAN_SWEEP_STAGED_EXIT_V3",
        "symbol": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "order_rows": int(len(staged)),
        "filled_rows": int(staged["filled"].astype(bool).sum()),
        "variants": sorted(staged["staged_variant"].unique().tolist()),
    }
    (args.out / "pair_staged_exit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
