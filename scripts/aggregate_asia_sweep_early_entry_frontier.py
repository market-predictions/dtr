from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.early_entry_landmarks import (
    add_cross_pair_landmark_features,
)
from dtr_lab.strategies.asia_sweep.early_entry_modeling import (
    run_information_frontier,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--frozen-t5-predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(args.inputs.rglob("early_entry_landmarks.csv"))
    if len(files) != 2:
        raise ValueError(f"expected exactly two pair landmark ledgers, found {len(files)}")
    frames = [pd.read_csv(path) for path in files]
    ledger = pd.concat(frames, ignore_index=True)
    if tuple(sorted(ledger["instrument"].unique())) != ("EURUSD", "GBPUSD"):
        raise ValueError("early-entry ledger must contain exactly EURUSD and GBPUSD")
    ledger = add_cross_pair_landmark_features(ledger)
    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "early_entry_landmark_ledger.csv", index=False)
    frozen = pd.read_csv(args.frozen_t5_predictions)
    decision = run_information_frontier(ledger, frozen, args.out)
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
