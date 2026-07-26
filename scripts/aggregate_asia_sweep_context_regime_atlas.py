from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.context_regime_atlas import (
    evaluate_single_factor_atlas,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the frozen Asian Sweep single-factor context atlas."
    )
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _decision_markdown(
    decision: dict[str, Any],
    family_summary: pd.DataFrame,
    state_summary: pd.DataFrame,
) -> str:
    payload = decision["decision"]
    lines = [
        "# Asian Sweep Context and Regime Atlas — Single-Factor Decision",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Events: `{payload['events']}`  ",
        f"Economic events: `{payload['economic_events']}`  ",
        f"Baseline hit rate: `{payload['baseline_hit_rate']:.4%}`  ",
        f"Baseline stressed payoff proxy: `{payload['baseline_mean_payoff']:+.4f}R`",
        "",
        "## Factor-family decisions",
        "",
        (
            "| Family | States | Passing states | Status | Best state | "
            "Best EV effect | Best hit lift | Best q |"
        ),
        "|---|---:|---:|---|---|---:|---:|---:|",
    ]
    for row in family_summary.itertuples(index=False):
        best_q = "n/a" if pd.isna(row.best_q_value) else f"{row.best_q_value:.4f}"
        lines.append(
            f"| {row.family} | {row.states_tested} | {row.passing_states} | "
            f"{row.status} | {row.best_row_id} | {row.best_economic_effect:+.4f}R | "
            f"{row.best_absolute_hit_lift:+.2%} | {best_q} |"
        )
    lines.extend(
        [
            "",
            "## Strongest individual states",
            "",
            (
                "| State | Events | Hit rate | Hit lift | Mean payoff | EV effect | "
                "P(EV>0) | q | Pass |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    ranked = state_summary.sort_values(
        ["passes_all_gates", "evidence_score", "economic_effect"],
        ascending=[False, False, False],
        kind="mergesort",
    ).head(15)
    for row in ranked.itertuples(index=False):
        q_value = "n/a" if pd.isna(row.q_value) else f"{row.q_value:.4f}"
        lines.append(
            f"| {row.row_id} | {row.events} | {row.hit_rate:.2%} | "
            f"{row.absolute_hit_lift:+.2%} | {row.mean_payoff:+.4f}R | "
            f"{row.economic_effect:+.4f}R | "
            f"{row.bootstrap_probability_positive:.2%} | {q_value} | "
            f"{'YES' if row.passes_all_gates else 'NO'} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"Passing families: `{payload['passing_families']}`  ",
            f"Interaction outcomes opened: `{payload['interaction_outcomes_opened']}`  ",
            f"Router model opened: `{payload['router_model_opened']}`  ",
            f"Strategy P&L calculated: `{payload['strategy_pnl_calculated']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if len(args.inputs) != 2:
        raise ValueError(f"expected exactly two pair ledgers, found {len(args.inputs)}")
    frames = [pd.read_csv(path) for path in sorted(args.inputs)]
    ledger = pd.concat(frames, ignore_index=True)
    pairs = tuple(sorted(ledger["instrument"].unique().tolist()))
    if pairs != ("EURUSD", "GBPUSD"):
        raise ValueError(f"expected EURUSD and GBPUSD, found {pairs}")
    if ledger["event_id"].duplicated().any():
        raise ValueError("pooled context ledger contains duplicate event ids")
    state_summary, subgroup_summary, decision = evaluate_single_factor_atlas(ledger)
    family_summary = pd.DataFrame(decision["families"])
    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "context_regime_pooled_ledger.csv", index=False)
    state_summary.to_csv(args.out / "context_regime_state_summary.csv", index=False)
    subgroup_summary.to_csv(
        args.out / "context_regime_subgroup_summary.csv", index=False
    )
    family_summary.to_csv(args.out / "context_regime_family_summary.csv", index=False)
    safe = _json_safe(decision)
    (args.out / "context_regime_atlas_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "CONTEXT_REGIME_ATLAS_DECISION.md").write_text(
        _decision_markdown(safe, family_summary, state_summary),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
