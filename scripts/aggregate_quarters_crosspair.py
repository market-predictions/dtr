from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

EXPECTED_PAIRS = {
    "EURUSD",
    "GBPUSD",
    "USDCHF",
    "AUDUSD",
    "NZDUSD",
    "USDCAD",
    "USDJPY",
    "EURJPY",
    "GBPJPY",
    "EURGBP",
}
REFERENCE_PAIRS = {"GBPUSD", "EURUSD", "USDJPY"}
CONFIRMATION_PAIRS = EXPECTED_PAIRS - REFERENCE_PAIRS
GBPUSD_FROZEN_REFERENCE = {
    "events": 6843,
    "lqp_events": 1373,
    "development_point": -0.789094775988071,
    "validation_point": -0.7538688626364902,
    "combined_point": -0.7799077709456929,
}


def _period(rows: list[dict], name: str) -> dict:
    matches = [row for row in rows if row["period"] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one {name} row, found {len(matches)}")
    return matches[0]


def _is_positive_stable(development: dict, validation: dict, combined: dict) -> bool:
    return bool(
        development["point"] > 0
        and validation["point"] > 0
        and combined["ci_low"] > 0
    )


def _confirmation_decision(positive_stable_count: int) -> str:
    if positive_stable_count == 0:
        return "CONFIRM_GLOBAL_DEMOTION_NO_PAIR_EXCEPTIONS"
    if positive_stable_count <= 2:
        return "GLOBAL_DEMOTION_STANDS_ISOLATED_PAIR_EXCEPTIONS_ONLY"
    return "GLOBAL_DEMOTION_STANDS_UNEXPECTED_BREADTH_REQUIRES_NEW_PREREGISTRATION"


def _assert_gbpusd_parity(result: dict) -> dict:
    checks = {
        "events": result["events"] == GBPUSD_FROZEN_REFERENCE["events"],
        "lqp_events": result["lqp_events"] == GBPUSD_FROZEN_REFERENCE["lqp_events"],
        "development_point": abs(
            result["development"]["point"]
            - GBPUSD_FROZEN_REFERENCE["development_point"]
        )
        <= 1e-12,
        "validation_point": abs(
            result["validation"]["point"]
            - GBPUSD_FROZEN_REFERENCE["validation_point"]
        )
        <= 1e-12,
        "combined_point": abs(
            result["combined"]["point"] - GBPUSD_FROZEN_REFERENCE["combined_point"]
        )
        <= 1e-12,
    }
    if not all(checks.values()):
        raise ValueError(f"GBPUSD frozen-reference parity failed: {checks}")
    return checks


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
        pair_results[pair] = {
            "events": result["events"],
            "lqp_events": result["lqp_events"],
            "development": development,
            "validation": validation,
            "combined": combined,
            "positive_stable": _is_positive_stable(
                development, validation, combined
            ),
            "normalization_scale": result["configuration"][
                "source_quote_normalization_scale"
            ],
        }

    if set(pair_results) != EXPECTED_PAIRS:
        raise ValueError(f"Expected {EXPECTED_PAIRS}, found {set(pair_results)}")

    gbpusd_parity = _assert_gbpusd_parity(pair_results["GBPUSD"])
    positive_stable_pairs = sorted(
        pair for pair, result in pair_results.items() if result["positive_stable"]
    )
    confirmation_positive_stable_pairs = sorted(
        pair
        for pair in CONFIRMATION_PAIRS
        if pair_results[pair]["positive_stable"]
    )
    decision = _confirmation_decision(len(confirmation_positive_stable_pairs))

    development_positive_pairs = sorted(
        pair for pair, result in pair_results.items() if result["development"]["point"] > 0
    )
    validation_positive_pairs = sorted(
        pair for pair, result in pair_results.items() if result["validation"]["point"] > 0
    )
    combined_positive_pairs = sorted(
        pair for pair, result in pair_results.items() if result["combined"]["point"] > 0
    )
    development_to_validation_sign_flips = sorted(
        pair
        for pair, result in pair_results.items()
        if (result["development"]["point"] > 0)
        != (result["validation"]["point"] > 0)
    )
    median_combined_effect = statistics.median(
        result["combined"]["point"] for result in pair_results.values()
    )

    summary = {
        "decision": decision,
        "canonical_250_pip_theory_status": "DEMOTED",
        "transition_census_authorized": False,
        "strategy_optimization_authorized": False,
        "reference_pairs": sorted(REFERENCE_PAIRS),
        "confirmation_pairs": sorted(CONFIRMATION_PAIRS),
        "positive_stable_pairs_all": positive_stable_pairs,
        "positive_stable_pairs_confirmation": confirmation_positive_stable_pairs,
        "development_positive_pairs": development_positive_pairs,
        "validation_positive_pairs": validation_positive_pairs,
        "combined_positive_pairs": combined_positive_pairs,
        "development_to_validation_sign_flips": development_to_validation_sign_flips,
        "median_combined_effect_pips": median_combined_effect,
        "gbpusd_frozen_reference_parity": gbpusd_parity,
        "pair_results": pair_results,
        "source": {
            "dataset": "Dukascopy FX Cache",
            "construction": "M1 separate BID/ASK UTC",
            "years_processed": [2015, 2021],
            "temporary_transport_run_id": 30129064261,
            "canonical_private_drive_folder_id": "160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU",
        },
        "holdout_2022_2025_opened": False,
        "strategy_optimization_performed": False,
    }
    (args.output_dir / "ten_pair_universe_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    lines = [
        "# Quarters Theory Ten-Pair Stage-1 Universe Confirmation",
        "",
        f"**Decision:** `{decision}`",
        "",
        "The canonical 250-pip theory had already failed the frozen GBPUSD plus EURUSD/USDJPY "
        "gate. This ten-pair run is confirmatory and cannot retrospectively rescue that "
        "decision. It tests whether isolated pair-specific exceptions exist.",
        "",
        "The unchanged Stage-1 engine was run on the registered Dukascopy FX Cache source. "
        "Every annual source file was checksum-verified before schema adaptation. No market "
        "data was reacquired.",
        "",
        "The 2022–2025 holdout remained unopened and no strategy optimization was performed.",
        "",
        "| Pair | Events | LQP events | Dev 60m | Validation 60m | Combined 60m | 95% CI | Positive/stable |",
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
            "## Universe diagnostics",
            "",
            f"- Positive/stable pairs across all ten: {len(positive_stable_pairs)} — "
            f"{', '.join(positive_stable_pairs) if positive_stable_pairs else 'none'}.",
            f"- Positive/stable pairs in the seven-pair confirmation panel: "
            f"{len(confirmation_positive_stable_pairs)} — "
            f"{', '.join(confirmation_positive_stable_pairs) if confirmation_positive_stable_pairs else 'none'}.",
            f"- Positive development estimates: {len(development_positive_pairs)} / 10.",
            f"- Positive validation estimates: {len(validation_positive_pairs)} / 10.",
            f"- Development-to-validation sign flips: "
            f"{len(development_to_validation_sign_flips)} / 10.",
            f"- Median combined canonical effect: {median_combined_effect:.3f} pips.",
            "- GBPUSD source/engine parity with the frozen reference: PASS.",
            "",
            "## Frozen interpretation rule",
            "",
            "A pair qualifies as positive and stable only when development and validation "
            "point estimates are both positive and the combined year-preserving weekly-block "
            "95% interval excludes zero on the positive side.",
            "",
            "Zero confirmation exceptions confirms global demotion. One or two exceptions may "
            "only be retained as isolated pair-specific hypotheses. Three or more exceptions "
            "would be an unexpected breadth anomaly requiring a new independent "
            "preregistration; it still would not reopen this failed research gate.",
            "",
        ]
    )
    (args.output_dir / "QUARTERS_THEORY_UNIVERSE_REPORT.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
