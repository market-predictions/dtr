from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.extended_reversal_modeling import (
    fit_outer_predictions,
    summarize_predictions,
    validate_extended_ledger,
)
from dtr_lab.strategies.asia_sweep.extended_reversal_targets import LANDMARKS, TARGET_ORDER


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--target", choices=TARGET_ORDER, required=True)
    parser.add_argument("--landmark", choices=LANDMARKS, required=True)
    parser.add_argument("--family", choices=("elastic_net", "hgb"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    ledger = pd.read_csv(args.ledger)
    validate_extended_ledger(ledger)
    population = ledger.loc[
        ledger["extended_target"].eq(args.target)
        & ledger["landmark"].eq(args.landmark)
    ]
    if population.empty:
        raise ValueError(
            f"{args.target}/{args.landmark}: frozen target population is absent"
        )
    predictions, tuning = fit_outer_predictions(
        ledger,
        target_name=args.target,
        landmark=args.landmark,
        family=args.family,
    )
    summary, tables = summarize_predictions(predictions)
    summary.update(
        {
            "extended_target": args.target,
            "landmark": args.landmark,
            "family": args.family,
        }
    )
    prefix = f"{args.target}_{args.landmark}_{args.family}"
    tuning.to_csv(args.out / f"tuning_{prefix}.csv", index=False)
    for name, table in tables.items():
        table.to_csv(args.out / f"{name}_{prefix}.csv", index=False)
    serializable = {key: value for key, value in summary.items() if key != "gates"}
    serializable["failed_predicates"] = ";".join(
        key for key, passed in summary["gates"].items() if not passed
    )
    pd.DataFrame([serializable]).to_csv(
        args.out / "candidate_summary.csv", index=False
    )
    (args.out / "candidate_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
