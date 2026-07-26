from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_metrics import (
    write_discovery_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(args.inputs.rglob("execution_orders.csv"))
    if len(files) != 2:
        raise ValueError(f"expected two pair order ledgers, found {len(files)}")
    orders = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    instruments = tuple(sorted(orders["instrument"].dropna().unique()))
    if instruments != ("EURUSD", "GBPUSD"):
        raise ValueError(f"unexpected execution instruments: {instruments}")
    payload = write_discovery_outputs(args.out, orders)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
