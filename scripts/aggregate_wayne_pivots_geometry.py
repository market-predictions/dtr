from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_pivots import PRIMARY_PAIRS, evaluate_geometry_atlas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the frozen six-pair Wayne Pivots geometry atlas."
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
    candidate_summary: pd.DataFrame,
    comparison_summary: pd.DataFrame,
) -> str:
    payload = decision["decision"]
    candidate_header = (
        "| Candidate | Wayne events | Pair breadth | +success controls | "
        "+payoff controls | Full passes | Core anchor pass | Geometry pass |"
    )
    comparison_header = (
        "| Comparison | Events | Success lift | Payoff effect | Pair breadth | "
        "Year breadth | P(effect>0) | q | Pass |"
    )
    lines = [
        "# Wayne Pivots Daily Geometry — Decision",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Total ledger rows: `{payload['events_total']}`  ",
        f"Fresh event-target rows: `{payload['fresh_events']}`  ",
        f"Instruments: `{payload['instruments']}`  ",
        f"Years: `{payload['years']}`  ",
        f"Placebo comparisons: `{payload['comparisons']}`  ",
        f"Passing comparisons: `{payload['passing_comparisons']}`",
        "",
        "## Candidate gates",
        "",
        candidate_header,
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in candidate_summary.itertuples(index=False):
        lines.append(
            f"| {row.candidate_id} | {row.wayne_events} | {row.wayne_pair_breadth} | "
            f"{row.positive_success_comparisons} | {row.positive_payoff_comparisons} | "
            f"{row.passing_comparisons} | {'YES' if row.core_anchor_pass else 'NO'} | "
            f"{'PASS' if row.passes_geometry else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Strongest Wayne-versus-placebo comparisons",
            "",
            comparison_header,
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    ranked = comparison_summary.sort_values(
        ["passes_all_gates", "payoff_effect", "success_lift"],
        ascending=[False, False, False],
        kind="mergesort",
    ).head(20)
    for row in ranked.itertuples(index=False):
        lines.append(
            f"| {row.row_id} | {row.events} | {row.success_lift:+.2%} | "
            f"{row.payoff_effect:+.4f}R | {row.pair_positive_breadth} | "
            f"{row.year_positive_breadth} | "
            f"{row.bootstrap_probability_positive:.2%} | {row.q_value:.4f} | "
            f"{'YES' if row.passes_all_gates else 'NO'} |"
        )
    lines.extend(
        [
            "",
            "## Authorization boundary",
            "",
            f"Bias stage opened: `{payload['bias_stage_opened']}`  ",
            f"Execution stage opened: `{payload['execution_stage_opened']}`  ",
            f"Strategy P&L calculated: `{payload['strategy_pnl_calculated']}`",
            "",
            "This study evaluates causal price-path anatomy. The strict payoff "
            "measure is not executable strategy P&L.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if len(args.inputs) != len(PRIMARY_PAIRS):
        raise ValueError(
            f"expected {len(PRIMARY_PAIRS)} pair ledgers, found {len(args.inputs)}"
        )
    frames = [pd.read_csv(path) for path in sorted(args.inputs)]
    ledger = pd.concat(frames, ignore_index=True)
    instruments = tuple(sorted(ledger["instrument"].unique().tolist()))
    if instruments != PRIMARY_PAIRS:
        raise ValueError(f"expected {PRIMARY_PAIRS}, found {instruments}")
    key = [
        "instrument",
        "pivot_day_start_utc",
        "structure",
        "side",
        "target_name",
    ]
    if ledger.duplicated(key).any():
        raise ValueError("pooled Wayne anatomy ledger contains duplicate keys")
    comparison, candidate, subgroup, decision = evaluate_geometry_atlas(ledger)
    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "wayne_pivots_pooled_anatomy_ledger.csv", index=False)
    comparison.to_csv(args.out / "wayne_pivots_comparison_summary.csv", index=False)
    candidate.to_csv(args.out / "wayne_pivots_candidate_summary.csv", index=False)
    subgroup.to_csv(args.out / "wayne_pivots_subgroup_summary.csv", index=False)
    safe = _json_safe(decision)
    (args.out / "wayne_pivots_geometry_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_PIVOTS_GEOMETRY_DECISION.md").write_text(
        _decision_markdown(safe, candidate, comparison),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
