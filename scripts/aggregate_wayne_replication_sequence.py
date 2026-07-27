from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import REPLICATION_PAIRS
from dtr_lab.strategies.wayne_direction.replication_decision import (
    build_replication_decision,
    normalize_replication_ledger,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the unchanged Wayne independent FX replication."
    )
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--ledgers", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _load_summaries(paths: list[Path]) -> list[dict[str, Any]]:
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    symbols = tuple(sorted(str(item["instrument"]) for item in summaries))
    if symbols != REPLICATION_PAIRS:
        raise ValueError(f"expected {REPLICATION_PAIRS}, found {symbols}")
    return summaries


def _markdown(decision: dict[str, Any]) -> str:
    conservative = decision["conservative"]
    stretch = decision["stretch_supportive"]
    lines = [
        "# Wayne Independent FX Replication Decision",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        "Panel: EURGBP, EURJPY, GBPJPY and NZDUSD; 2015–2021 only.",
        "",
        "## Day-10 sample",
        "",
        f"- primary opportunities: {decision['primary_opportunities']};",
        f"- active day-10 sequences: {decision['active_day10']};",
        f"- active pair breadth: {decision['active_pair_breadth']};",
        f"- maximum pair concentration: {decision['maximum_pair_concentration']:.2%}.",
        "",
        "| Pair | Active day-10 opportunities |",
        "|---|---:|",
    ]
    for pair, count in decision["active_day10_by_pair"].items():
        lines.append(f"| {pair} | {count} |")
    lines.extend(
        [
            "",
            "## Fixed-landmark comparison",
            "",
            "| Target | Treatment | Control | Lift | Cluster p | Bootstrap 90% interval |",
            "|---|---:|---:|---:|---:|---:|",
            "| Conservative | {tr:.2%} ({tn}) | {cr:.2%} ({cn}) | {ef:+.2%} | "
            "{p:.4f} | [{lo:+.2%}, {hi:+.2%}] |".format(
                tr=conservative["treatment_rate"],
                tn=conservative["treatment_n"],
                cr=conservative["control_rate"],
                cn=conservative["control_n"],
                ef=conservative["effect"],
                p=conservative["permutation_p"],
                lo=conservative["bootstrap_p05"],
                hi=conservative["bootstrap_p95"],
            ),
            "| Stretch, supportive | {tr:.2%} ({tn}) | {cr:.2%} ({cn}) | {ef:+.2%} | "
            "{p:.4f} | [{lo:+.2%}, {hi:+.2%}] |".format(
                tr=stretch["treatment_rate"],
                tn=stretch["treatment_n"],
                cr=stretch["control_rate"],
                cn=stretch["control_n"],
                ef=stretch["effect"],
                p=stretch["permutation_p"],
                lo=stretch["bootstrap_p05"],
                hi=stretch["bootstrap_p95"],
            ),
            "",
            "## Frozen gates",
            "",
        ]
    )
    for family in ("sample_gates", "effect_gates", "breadth_gates"):
        lines.append(f"### {family.replace('_', ' ').title()}")
        lines.append("")
        for name, passed in decision[family].items():
            lines.append(f"- {'PASS' if passed else 'FAIL'} — `{name}`")
        lines.append("")
    lines.extend(
        [
            "## Boundaries",
            "",
            "- Exact parent sequence and target definitions were unchanged.",
            "- Protected 2022–2025 outcomes were not opened.",
            "- No execution, costs, sizing or P&L were calculated.",
            "- Yield and VIX attribution opens only after a replication pass.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    summaries = _load_summaries(args.summaries)
    ledger = pd.concat([pd.read_csv(path) for path in args.ledgers], ignore_index=True)
    ledger = normalize_replication_ledger(ledger)
    decision = build_replication_decision(ledger)
    decision["pair_summaries"] = summaries
    safe = _json_safe(decision)

    args.out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.out / "wayne_replication_pooled_ledger.csv", index=False)
    pd.DataFrame(
        [
            {
                "target_tier": safe["conservative"]["target_tier"],
                "treatment_n": safe["conservative"]["treatment_n"],
                "control_n": safe["conservative"]["control_n"],
                "treatment_rate": safe["conservative"]["treatment_rate"],
                "control_rate": safe["conservative"]["control_rate"],
                "effect": safe["conservative"]["effect"],
                "permutation_p": safe["conservative"]["permutation_p"],
                "bootstrap_p05": safe["conservative"]["bootstrap_p05"],
                "bootstrap_p95": safe["conservative"]["bootstrap_p95"],
            },
            {
                "target_tier": safe["stretch_supportive"]["target_tier"],
                "treatment_n": safe["stretch_supportive"]["treatment_n"],
                "control_n": safe["stretch_supportive"]["control_n"],
                "treatment_rate": safe["stretch_supportive"]["treatment_rate"],
                "control_rate": safe["stretch_supportive"]["control_rate"],
                "effect": safe["stretch_supportive"]["effect"],
                "permutation_p": safe["stretch_supportive"]["permutation_p"],
                "bootstrap_p05": safe["stretch_supportive"]["bootstrap_p05"],
                "bootstrap_p95": safe["stretch_supportive"]["bootstrap_p95"],
            },
        ]
    ).to_csv(args.out / "wayne_replication_comparisons.csv", index=False)
    pd.DataFrame(safe["conservative"]["pair_effects"]).to_csv(
        args.out / "wayne_replication_pair_effects.csv",
        index=False,
    )
    pd.DataFrame(safe["conservative"]["year_effects"]).to_csv(
        args.out / "wayne_replication_year_effects.csv",
        index=False,
    )
    (args.out / "wayne_replication_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_INDEPENDENT_FX_REPLICATION_DECISION.md").write_text(
        _markdown(safe),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
