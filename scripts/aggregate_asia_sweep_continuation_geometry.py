from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.asia_sweep.continuation_geometry import (
    OBJECTIVE_ORDER,
    select_continuation_objective,
    summarize_objective,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    files = sorted(args.inputs.rglob("continuation_geometry.csv"))
    if len(files) != 2:
        raise ValueError(f"expected two pair geometry ledgers, found {files}")
    geometry = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    if tuple(sorted(geometry["instrument"].unique())) != ("EURUSD", "GBPUSD"):
        raise ValueError("continuation geometry must contain EURUSD and GBPUSD")
    if geometry.duplicated(["event_id", "objective"]).any():
        raise ValueError("pooled continuation geometry keys must be unique")

    rows: list[dict[str, Any]] = []
    for objective in OBJECTIVE_ORDER:
        if objective not in set(geometry["objective"]):
            continue
        summary, tables = summarize_objective(geometry, objective)
        rows.append(summary)
        for name, table in tables.items():
            table.to_csv(
                args.out / f"{name}_{objective}.csv",
                index=False,
            )
    serializable: list[dict[str, Any]] = []
    for row in rows:
        flattened = {key: value for key, value in row.items() if key != "gates"}
        flattened["failed_predicates"] = ";".join(
            key for key, passed in row["gates"].items() if not passed
        )
        serializable.append(flattened)
    summaries = pd.DataFrame(serializable)
    summaries.to_csv(args.out / "continuation_objective_summary.csv", index=False)
    geometry.to_csv(args.out / "continuation_geometry_ledger.csv", index=False)
    selected_objective = select_continuation_objective(summaries)
    decision_name = (
        "PASS_CONTINUATION_GEOMETRY_AUTHORIZE_EXECUTION_DISCOVERY"
        if selected_objective is not None
        else "FAIL_CONTINUATION_GEOMETRY_STOP_BEFORE_EXECUTION_PNL"
    )
    decision = {
        "programme": "ASIAN_SWEEP_CONTINUATION_GEOMETRY_V6_3",
        "decision": decision_name,
        "selected_family": "elastic_net",
        "selected_landmark": "T2",
        "selected_objective": selected_objective,
        "development_years": [2015, 2016, 2017, 2018, 2019],
        "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "execution_pnl_opened": False,
        "objective_count": int(len(summaries)),
    }
    (args.out / "continuation_geometry_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
