from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.runner_optimization_selection import (
    _fast_summary,
    build_nested_runner_decision,
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def write_runner_discovery_outputs(output_directory: Path, grid: pd.DataFrame) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=True)
    grid.to_csv(output_directory / "runner_policy_grid.csv", index=False)
    decision = build_nested_runner_decision(grid)
    decision["fold_table"].to_csv(output_directory / "outer_fold_selections.csv", index=False)
    decision["inner_table"].to_csv(output_directory / "inner_policy_metrics.csv", index=False)
    decision["oof_trades"].to_csv(output_directory / "oof_selected_trades.csv", index=False)
    decision["modal_trades"].to_csv(output_directory / "modal_policy_trades.csv", index=False)
    for prefix, tables in (
        ("oof", decision["oof_tables"]),
        ("modal", decision["modal_tables"]),
    ):
        for name, table in tables.items():
            table.to_csv(output_directory / f"{prefix}_{name}.csv", index=False)

    policy_rows: list[dict[str, Any]] = []
    for current_policy, trades in grid.groupby("policy_id", sort=True):
        summary = _fast_summary(trades)
        row = trades.iloc[0]
        policy_rows.append(
            {
                "policy_id": current_policy,
                "target_kind": row["target_kind"],
                "exit_hour": int(row["exit_hour"]),
                "stop_policy": row["stop_policy"],
                **{
                    key: value
                    for key, value in summary.items()
                    if not isinstance(value, pd.DataFrame)
                },
            }
        )
    pd.DataFrame(policy_rows).to_csv(output_directory / "policy_summary.csv", index=False)

    payload = _json_safe(
        {
            "programme": "ASIAN_SWEEP_RUNNER_ENTRY_OPTIMISATION_V4",
            "stage": "RUNNER_DISCOVERY_2015_2019",
            "decision": decision["decision"],
            "selected_policy_id": decision["selected_policy_id"],
            "modal_policy_id": decision["modal_policy_id"],
            "modal_policy_fold_count": decision["modal_policy_fold_count"],
            "gates": decision["gates"],
            "oof_metrics": decision["oof_metrics"],
            "modal_policy_metrics": decision["modal_policy_metrics"],
            "later_partitions_opened": False,
            "earlier_entry_research_authorized": (
                decision["decision"].startswith("PASS_RUNNER_DISCOVERY")
            ),
            "strategy_deployment_authorized": False,
        }
    )
    (output_directory / "runner_discovery_decision.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
