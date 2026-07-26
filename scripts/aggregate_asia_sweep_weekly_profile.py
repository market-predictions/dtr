from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.weekly_profile_regime import (
    aggregate_mechanism_decision,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the preregistered Asian Sweep weekly-profile mechanism study."
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


def _decision_markdown(decision: dict[str, Any], summary: pd.DataFrame) -> str:
    lines = [
        "# Asian Sweep Weekly-Profile Mechanism — Decision",
        "",
        f"Decision: `{decision['decision']}`  ",
        "Development: EURUSD and GBPUSD, 2015–2019  ",
        "Protected: 2020–2025 unopened",
        "",
        "## Frozen hierarchical results",
        "",
        "| Hypothesis | Target | Events | Hit rate | Reference | Abs lift | Rel lift "
        "| Mean EV | Median R:R | Passed | Failed gates |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in summary.itertuples(index=False):
        failed = ", ".join(row.failed_gates) if row.failed_gates else "—"
        lines.append(
            "| {hypothesis} | {target} | {events} | {hit:.2%} | {reference:.2%} | "
            "{absolute:+.2%} | {relative:.2f}x | {ev:+.3f}R | {rr:.2f}R "
            "| {passed} | {failed} |".format(
                hypothesis=row.hypothesis,
                target=row.target,
                events=int(row.events),
                hit=float(row.hit_rate) if pd.notna(row.hit_rate) else 0.0,
                reference=(
                    float(row.reference_hit_rate)
                    if pd.notna(row.reference_hit_rate)
                    else 0.0
                ),
                absolute=(
                    float(row.absolute_lift) if pd.notna(row.absolute_lift) else 0.0
                ),
                relative=(
                    float(row.relative_lift) if pd.notna(row.relative_lift) else 0.0
                ),
                ev=float(row.mean_ev_proxy) if pd.notna(row.mean_ev_proxy) else 0.0,
                rr=(
                    float(row.median_stressed_rr)
                    if pd.notna(row.median_stressed_rr)
                    else 0.0
                ),
                passed="YES" if bool(row.passed) else "NO",
                failed=failed,
            )
        )
    lines.extend(
        [
            "",
            "## Authorization",
            "",
            f"- selected hypothesis: `{decision['selected_hypothesis']}`;",
            f"- selected target: `{decision['selected_target']}`;",
            f"- regime-aware modelling authorized: `{decision['modeling_authorized']}`;",
            "- position-structure P&L remains closed;",
            "- protected 2020–2025 remains unopened.",
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
    decision, summary = aggregate_mechanism_decision(ledger)
    output = args.out
    output.mkdir(parents=True, exist_ok=True)

    ledger.to_csv(output / "weekly_profile_pooled_ledger.csv", index=False)
    summary.to_csv(output / "weekly_profile_mechanism_summary.csv", index=False)
    safe_decision = _json_safe(decision)
    (output / "weekly_profile_mechanism_decision.json").write_text(
        json.dumps(safe_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "WEEKLY_PROFILE_MECHANISM_DECISION.md").write_text(
        _decision_markdown(safe_decision, summary),
        encoding="utf-8",
    )

    subgroup_rows: list[dict[str, Any]] = []
    for result in decision["results"]:
        for dimension, rows in (
            ("pair", result["pair_metrics"]),
            ("year", result["year_metrics"]),
        ):
            for row in rows:
                subgroup_rows.append(
                    {
                        "hypothesis": result["hypothesis"],
                        "target": result["target"],
                        "dimension": dimension,
                        **row,
                    }
                )
    pd.DataFrame(subgroup_rows).to_csv(
        output / "weekly_profile_subgroup_metrics.csv",
        index=False,
    )
    print(json.dumps(safe_decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
