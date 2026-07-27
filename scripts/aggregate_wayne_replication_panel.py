from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.wayne_direction.data import REPLICATION_PAIRS

MINIMUM_QUALIFIED_PAIRS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze the Wayne independent FX replication panel."
    )
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def build_panel_decision(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    by_symbol = {str(item["instrument"]): item for item in summaries}
    expected = set(REPLICATION_PAIRS)
    received = set(by_symbol)
    if received != expected:
        raise ValueError(
            f"expected replication candidates {sorted(expected)}, found {sorted(received)}"
        )
    qualified = [symbol for symbol in REPLICATION_PAIRS if by_symbol[symbol]["qualified"]]
    excluded = [symbol for symbol in REPLICATION_PAIRS if symbol not in qualified]
    decision = (
        "PASS_PANEL_QUALIFICATION_OPEN_REPLICATION_OUTCOMES"
        if len(qualified) >= MINIMUM_QUALIFIED_PAIRS
        else "FAIL_PANEL_QUALIFICATION_DATA_WALL"
    )
    return {
        "decision": decision,
        "outcome_inspection": False,
        "candidate_pairs": list(REPLICATION_PAIRS),
        "qualified_pairs": qualified,
        "excluded_pairs": excluded,
        "minimum_qualified_pairs": MINIMUM_QUALIFIED_PAIRS,
        "pair_summaries": [by_symbol[symbol] for symbol in REPLICATION_PAIRS],
    }


def _markdown(decision: dict[str, Any]) -> str:
    lines = [
        "# Wayne Independent FX Replication Panel Decision",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        "No Wayne sequence outcomes, target reaches, returns or P&L were inspected.",
        "",
        "## Frozen candidates",
        "",
        ", ".join(decision["candidate_pairs"]),
        "",
        "## Qualification",
        "",
        "| Pair | Qualified | Active % | Median spread | P95 spread | Full D1 | Full H4 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in decision["pair_summaries"]:
        lines.append(
            "| {instrument} | {qualified} | {active:.2%} | {median:.3f}p | "
            "{p95:.3f}p | {d1:.2%} | {h4:.2%} |".format(
                instrument=item["instrument"],
                qualified="yes" if item["qualified"] else "no",
                active=item["active_fraction"],
                median=item["spread_median_pips"],
                p95=item["spread_p95_pips"],
                d1=item["full_daily_fraction"],
                h4=item["full_h4_fraction"],
            )
        )
    lines.extend(
        [
            "",
            f"Qualified panel: {', '.join(decision['qualified_pairs']) or 'none'}",
            "",
            f"Excluded: {', '.join(decision['excluded_pairs']) or 'none'}",
            "",
            "The exact day-10 Wayne sequence may be opened only for the qualified panel.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in args.summaries]
    decision = build_panel_decision(summaries)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "wayne_replication_panel_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_REPLICATION_PANEL_DECISION.md").write_text(
        _markdown(decision),
        encoding="utf-8",
    )
    rows = []
    for item in decision["pair_summaries"]:
        rows.append(
            {
                "instrument": item["instrument"],
                "qualified": item["qualified"],
                "active_fraction": item["active_fraction"],
                "spread_median_pips": item["spread_median_pips"],
                "spread_p95_pips": item["spread_p95_pips"],
                "spread_p99_pips": item["spread_p99_pips"],
                "full_daily_fraction": item["full_daily_fraction"],
                "full_h4_fraction": item["full_h4_fraction"],
            }
        )
    pd.DataFrame(rows).to_csv(
        args.out / "wayne_replication_panel_quality.csv",
        index=False,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
