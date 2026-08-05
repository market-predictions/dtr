from __future__ import annotations

import argparse
import json
from pathlib import Path


def _period(rows: list[dict], name: str) -> dict:
    matches = [row for row in rows if row["period"] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one {name} row, found {len(matches)}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    pair_results: dict[str, dict] = {}
    for key_path in sorted(args.artifacts_dir.rglob("key_results.json")):
        result = json.loads(key_path.read_text(encoding="utf-8"))
        pair = result["configuration"]["pair"]
        rows = result["canonical_60m_bootstrap"]
        development = _period(rows, "development_2015_2019")
        validation = _period(rows, "internal_validation_2020_2021")
        combined = _period(rows, "all_2015_2021")
        positive_stable = bool(
            development["point"] > 0
            and validation["point"] > 0
            and combined["ci_low"] > 0
        )
        pair_results[pair] = {
            "events": result["events"],
            "lqp_events": result["lqp_events"],
            "development": development,
            "validation": validation,
            "combined": combined,
            "positive_stable": positive_stable,
            "normalization_scale": result["configuration"][
                "source_quote_normalization_scale"
            ],
        }

    expected_pairs = {"EURUSD", "USDJPY"}
    if set(pair_results) != expected_pairs:
        raise ValueError(f"Expected {expected_pairs}, found {set(pair_results)}")

    positive_pairs = [
        pair for pair, result in pair_results.items() if result["positive_stable"]
    ]
    if len(positive_pairs) == 2:
        decision = "AUTHORIZE_TRANSITION_CENSUS"
    elif len(positive_pairs) == 1:
        decision = "PAIR_SPECIFIC_INVESTIGATION_ONLY"
    else:
        decision = "DEMOTE_CANONICAL_250_PIP_THEORY"

    summary = {
        "decision": decision,
        "positive_stable_pairs": positive_pairs,
        "pair_results": pair_results,
        "holdout_2022_2025_opened": False,
        "strategy_optimization_performed": False,
    }
    (args.output_dir / "cross_pair_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    table_header = (
        "| Pair | Events | LQP events | Dev 60m | Validation 60m | Combined 60m | "
        "95% CI | Positive/stable |"
    )
    lines = [
        "# Quarters Theory Cross-Pair Stage-1 Replication",
        "",
        f"**Decision:** `{decision}`",
        "",
        "The frozen GBP/USD Stage-1 engine was reused without signal, matching, reset or "
        "bootstrap changes. Pair quotes were deterministically normalized so one source pip "
        "equals 0.0001 in the unchanged engine.",
        "",
        "The 2022–2025 holdout remained unopened and no strategy optimization was performed.",
        "",
        table_header,
        "|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for pair in sorted(pair_results):
        result = pair_results[pair]
        lines.append(
            "| {pair} | {events} | {lqp} | {dev:.3f} | {val:.3f} | {all:.3f} | "
            "[{low:.3f}, {high:.3f}] | {stable} |".format(
                pair=pair,
                events=result["events"],
                lqp=result["lqp_events"],
                dev=result["development"]["point"],
                val=result["validation"]["point"],
                all=result["combined"]["point"],
                low=result["combined"]["ci_low"],
                high=result["combined"]["ci_high"],
                stable="yes" if result["positive_stable"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Frozen decision rule",
            "",
            "A pair qualifies as convincingly positive and stable only when development and "
            "validation point estimates are both positive and the combined year-preserving "
            "weekly-block 95% interval excludes zero on the positive side.",
            "",
        ]
    )
    (args.output_dir / "CROSS_PAIR_REPLICATION_REPORT.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
