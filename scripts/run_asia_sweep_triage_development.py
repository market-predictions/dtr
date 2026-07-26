from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.triage_modeling_v2 import run_development


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    ledger = pd.read_csv(args.ledger)
    decision = run_development(ledger, args.out)
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
