from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.extended_target_modeling import (
    FAMILIES,
    fit_extended_candidate,
)
from dtr_lab.strategies.asia_sweep.extended_targets import LANDMARKS, TARGETS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledgers", type=Path, required=True)
    parser.add_argument("--landmark", choices=LANDMARKS, required=True)
    parser.add_argument("--target", choices=TARGETS, required=True)
    parser.add_argument("--family", choices=FAMILIES, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    paths = sorted(args.ledgers.rglob("extended_target_ledger_*.csv"))
    if len(paths) != 2:
        raise ValueError(f"expected two pair ledgers, found {len(paths)}")
    ledger = pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    summary = fit_extended_candidate(
        ledger,
        landmark=args.landmark,
        target=args.target,
        family=args.family,
        output_directory=args.out,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
