from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.staged_execution_v3 import (
    load_hgb_triage_predictions,
    prepare_staged_population,
    simulate_staged_development,
    write_staged_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    ledger = pd.read_csv(args.ledger)
    predictions = load_hgb_triage_predictions(args.triage)
    population, counts = prepare_staged_population(ledger, predictions)
    results = simulate_staged_development(population, args.source_root)
    decision = write_staged_outputs(
        args.out,
        results=results,
        population_counts=counts,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
