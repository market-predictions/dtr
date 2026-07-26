from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.weekly_transition_validation import (
    CONFIRMATION_GATE,
    FINAL_GATE,
    evaluate_combined,
    evaluate_stage,
    final_programme_decision,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the frozen weekly-transition validation stages."
    )
    parser.add_argument("--stage", choices=("confirmation", "final"), required=True)
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--prior-inputs", type=Path, nargs="*")
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _load_pair_ledgers(paths: list[Path]) -> pd.DataFrame:
    if len(paths) != 2:
        raise ValueError(f"expected exactly two pair ledgers, found {len(paths)}")
    return pd.concat([pd.read_csv(path) for path in sorted(paths)], ignore_index=True)


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


def _rows_from_results(scope: str, results: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target, payload in results.items():
        rows.append(
            {
                "scope": scope,
                "target": target,
                **{
                    key: value
                    for key, value in payload.items()
                    if key not in {"pair_metrics", "year_metrics", "target", "years"}
                },
            }
        )
    return rows


def _subgroup_rows(scope: str, results: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target, payload in results.items():
        for dimension, records in (
            ("pair", payload["pair_metrics"]),
            ("year", payload["year_metrics"]),
        ):
            for record in records:
                rows.append(
                    {
                        "scope": scope,
                        "target": target,
                        "dimension": dimension,
                        **record,
                    }
                )
    return rows


def _format_percent(value: Any) -> str:
    return (
        "n/a"
        if value is None or not math.isfinite(float(value))
        else f"{float(value):.2%}"
    )


def _format_number(value: Any, suffix: str = "") -> str:
    return (
        "n/a"
        if value is None or not math.isfinite(float(value))
        else f"{float(value):+.3f}{suffix}"
    )


def _decision_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Asian Sweep Weekly-Transition Continuation — Decision",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Stage: `{payload['stage']}`  ",
        f"Years: `{payload['years']}`",
        "",
        "## Target results",
        "",
        (
            "| Target | Events | Positives | Hit rate | Reference | Hit lift | "
            "Mean EV | Reference EV | EV lift | Bootstrap P(EV>0) |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    row_template = (
        "| {target} | {events} | {positives} | {hit} | {ref_hit} | "
        "{hit_lift} | {ev} | {ref_ev} | {ev_lift} | {prob} |"
    )
    for target, result in payload["results"].items():
        lines.append(
            row_template.format(
                target=target,
                events=result["events"],
                positives=result["positives"],
                hit=_format_percent(result["hit_rate"]),
                ref_hit=_format_percent(result["reference_hit_rate"]),
                hit_lift=_format_percent(result["absolute_hit_rate_lift"]),
                ev=_format_number(result["mean_ev_proxy"], "R"),
                ref_ev=_format_number(result["reference_mean_ev_proxy"], "R"),
                ev_lift=_format_number(result["mean_ev_lift"], "R"),
                prob=_format_percent(result["bootstrap_probability_positive"]),
            )
        )
    lines.extend(["", "## Gate", ""])
    for check, passed in payload["checks"].items():
        lines.append(f"- `{check}`: `{'PASS' if passed else 'FAIL'}`")
    lines.extend(
        [
            "",
            f"Failed gates: `{payload['failed_gates']}`",
            "",
        ]
    )
    if "combined" in payload:
        lines.extend(
            [
                "## Combined 2020–2025 gate",
                "",
                f"Combined passed: `{payload['combined']['passed']}`",
                f"Combined failed gates: `{payload['combined']['failed_gates']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ledger = _load_pair_ledgers(args.inputs)
    output = args.out
    output.mkdir(parents=True, exist_ok=True)

    if args.stage == "confirmation":
        stage = evaluate_stage(ledger, gate=CONFIRMATION_GATE)
        payload = {
            **stage,
            "protected_2023_2025_opened": False,
            "execution_pnl_authorized": False,
        }
        all_ledgers = ledger
        summaries = _rows_from_results("confirmation", stage["results"])
        subgroup_rows = _subgroup_rows("confirmation", stage["results"])
    else:
        if not args.prior_inputs:
            raise ValueError("final stage requires two prior confirmation ledgers")
        prior = _load_pair_ledgers(args.prior_inputs)
        final_stage = evaluate_stage(ledger, gate=FINAL_GATE)
        combined_ledger = pd.concat([prior, ledger], ignore_index=True)
        combined = evaluate_combined(combined_ledger)
        programme_decision = final_programme_decision(final_stage, combined)
        payload = {
            **final_stage,
            "decision": programme_decision,
            "protected_2023_2025_opened": True,
            "combined": combined,
            "execution_pnl_authorized": programme_decision
            == "PASS_WEEKLY_TRANSITION_FINAL_HOLDOUT_OPEN_EXECUTION_PNL",
        }
        all_ledgers = combined_ledger
        summaries = [
            *_rows_from_results("final", final_stage["results"]),
            *_rows_from_results("combined", combined["results"]),
        ]
        subgroup_rows = [
            *_subgroup_rows("final", final_stage["results"]),
            *_subgroup_rows("combined", combined["results"]),
        ]

    safe = _json_safe(payload)
    all_ledgers.to_csv(output / "weekly_transition_validation_ledger.csv", index=False)
    pd.DataFrame(summaries).to_csv(
        output / "weekly_transition_target_summary.csv", index=False
    )
    pd.DataFrame(subgroup_rows).to_csv(
        output / "weekly_transition_subgroup_metrics.csv", index=False
    )
    (output / "weekly_transition_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "WEEKLY_TRANSITION_DECISION.md").write_text(
        _decision_markdown(safe),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
