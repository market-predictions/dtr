from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.sequential_triage_modeling import (
    CLASSES,
    fit_outer_predictions,
    prepare_triage_ledger,
    role_passes,
    summarize_predictions,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--landmark", choices=("T0", "T1", "T2", "T3"), required=True)
    parser.add_argument("--family", choices=("elastic_net", "hgb"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    ledger = prepare_triage_ledger(pd.read_csv(args.ledger))
    predictions, tuning, thresholds = fit_outer_predictions(
        ledger,
        landmark=args.landmark,
        family=args.family,
    )
    summary, tables = summarize_predictions(predictions)
    pair_table = tables["instrument"]
    year_table = tables["year"]
    summary.update(
        {
            "landmark": args.landmark,
            "family": args.family,
            "continuation_role_pass": role_passes(
                summary,
                pair_table,
                year_table,
                role="continuation",
            ),
            "reversal_role_pass": role_passes(
                summary,
                pair_table,
                year_table,
                role="reversal",
            ),
            "all_class_calibration_better": all(
                bool(summary[f"{state.lower()}_calibration_better"])
                for state in CLASSES
            ),
        }
    )
    prefix = f"{args.landmark}_{args.family}"
    predictions.to_csv(args.out / f"predictions_{prefix}.csv", index=False)
    tuning.to_csv(args.out / f"tuning_{prefix}.csv", index=False)
    thresholds.to_csv(args.out / f"thresholds_{prefix}.csv", index=False)
    for name, table in tables.items():
        table.to_csv(args.out / f"{name}_{prefix}.csv", index=False)
    pd.DataFrame([summary]).to_csv(args.out / "candidate_summary.csv", index=False)
    (args.out / "candidate_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
