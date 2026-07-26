from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.runner_optimization_selection import (
    write_runner_discovery_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(args.inputs.rglob("runner_policy_grid.csv"))
    if len(files) != 2:
        raise ValueError(f"expected exactly two pair runner grids, found {len(files)}")
    frames = [pd.read_csv(path) for path in files]
    grid = pd.concat(frames, ignore_index=True)
    if sorted(grid["instrument"].unique().tolist()) != ["EURUSD", "GBPUSD"]:
        raise ValueError("runner grid must contain exactly EURUSD and GBPUSD")
    payload = write_runner_discovery_outputs(args.out, grid)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
