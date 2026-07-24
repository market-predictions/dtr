from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from stoic_123_lab import (
    date_block_bootstrap,
    independent_trade_review,
    load_config_family,
)
from stoic_123_lab import index_proxy_source, usa500_forward_gates, usa500_rth_study
from stoic_123_lab.data import file_sha256
from stoic_123_lab.validation import evaluate_trades

FROZEN_PHASE1_SHA256 = "5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805"
SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
SOURCE_PREFIX = "usa500idxusd_m1_bid"
MATCHED_REPLICATES = 50
CANDIDATE_SCENARIO = "RTH_LONG_FULL"
CANDIDATE_SCENARIO_ID = f"{SOURCE_ARM_ID}__{CANDIDATE_SCENARIO}"
PARTITIONS = (
    "primary_forward",
    "crisis_regime",
    "recent_holdout",
    "monitoring_2026_ytd",
)


def _validate_design(design: dict[str, object]) -> None:
    if str(design.get("status")) != "SOURCE_QUALIFIED_EXECUTION_AUTHORIZED":
        raise ValueError("USA500 forward design is not execution authorized")
    candidate = design.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a mapping")
    expected = {
        "id": "RTH_LONG_FULL_123_NO_MAP_NO_EMA200",
        "source_arm_id": SOURCE_ARM_ID,
        "direction_mode": "long_only",
        "entry_model": "full_123",
        "map_mode": "none",
        "ema200_filter": False,
        "parameter_changes_allowed": False,
    }
    for key, value in expected.items():
        if candidate.get(key) != value:
            raise ValueError(f"Frozen candidate mismatch for {key}")
    if int(design.get("matched_control_replicates", 0)) != MATCHED_REPLICATES:
        raise ValueError("Matched replicate count mismatch")


def _return_to_drawdown(summary: dict[str, object]) -> float:
    drawdown = float(summary["max_drawdown_r"])
    return float(summary["net_r"]) / drawdown if drawdown > 0 else np.nan


def _candidate_trades(out: Path, partition: str) -> pd.DataFrame:
    path = out / f"{partition}__{CANDIDATE_SCENARIO_ID}__trades.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing frozen candidate ledger: {path}")
    frame = pd.read_csv(path)
    if not frame.empty:
        frame["entry_time"] = pd.to_datetime(frame["entry_time"], errors="raise")
        frame["exit_time"] = pd.to_datetime(frame["exit_time"], errors="raise")
        frame["signal_time"] = pd.to_datetime(frame["signal_time"], errors="raise")
        frame["base_lock_time"] = pd.to_datetime(
            frame["base_lock_time"], errors="raise"
        )
    return frame


def _combined_candidate_summary(
    out: Path,
    frames_by_partition: dict[str, pd.DataFrame],
) -> tuple[dict[str, object], dict[str, object], dict[str, object], pd.DataFrame]:
    combined = pd.concat(
        [
            frames_by_partition["primary_forward"],
            frames_by_partition["crisis_regime"],
            frames_by_partition["recent_holdout"],
        ],
        ignore_index=True,
    ).sort_values("entry_time").reset_index(drop=True)
    if combined.empty:
        raise RuntimeError("Combined 2015-2025 candidate ledger is empty")
    summary = evaluate_trades(
        combined,
        instrument="ES_PROXY",
        arm_id="USA500_RTH_FULL_123_COMBINED_2015_2025",
        source_start=pd.Timestamp("2015-01-01"),
        source_end=pd.Timestamp("2026-01-01"),
    )
    summary["partition"] = "combined_2015_2025"
    summary["return_to_drawdown"] = _return_to_drawdown(summary)
    inference = {
        "partition": "combined_2015_2025",
        "scenario_id": "USA500_RTH_FULL_123_COMBINED_2015_2025",
        **date_block_bootstrap(combined, iterations=10_000, seed=20265724),
    }
    review = {
        "partition": "combined_2015_2025",
        **independent_trade_review(
            combined,
            summary,
            instrument="ES_PROXY",
            arm_id="USA500_RTH_FULL_123_COMBINED_2015_2025",
        ),
    }
    combined.to_csv(out / "combined_2015_2025__RTH_LONG_FULL__trades.csv", index=False)
    return summary, inference, review, combined


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen USA500 RTH full 1-2-3 validation on 2015+ data"
    )
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--phase1", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    design = index_proxy_source.load_design(args.design)
    _validate_design(design)
    if file_sha256(args.phase1) != FROZEN_PHASE1_SHA256:
        raise ValueError("Frozen phase-one checksum mismatch")

    configs = {config.arm_id: config for config in load_config_family(args.phase1)}
    base = configs[SOURCE_ARM_ID]
    results: dict[str, dict[str, object]] = {}
    source_audits: list[dict[str, object]] = []
    one_minute_by_partition: dict[str, pd.DataFrame] = {}

    for index, partition in enumerate(PARTITIONS):
        one_minute, audits = index_proxy_source.load_partition(
            args.sources,
            design,
            partition,
            filename_prefix=SOURCE_PREFIX,
        )
        one_minute_by_partition[partition] = one_minute
        source_audits.extend(audits)
        results[partition] = usa500_rth_study.run_partition(
            partition=partition,
            one_minute=one_minute,
            base=base,
            iterations=args.iterations,
            seed_base=20260730 + index * 100_000,
            out=args.out,
        )

    frames_by_partition = {
        partition: _candidate_trades(args.out, partition) for partition in PARTITIONS
    }
    combined_summary, combined_inference, combined_review, combined_trades = (
        _combined_candidate_summary(args.out, frames_by_partition)
    )

    summary_rows: list[dict[str, object]] = []
    inference_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    exit_rows: list[dict[str, object]] = []
    matched_rows: list[dict[str, object]] = []
    for partition in PARTITIONS:
        result = results[partition]
        summary_rows.extend(result["summary_rows"])
        inference_rows.extend(result["inference_rows"])
        review_rows.extend(result["review_rows"])
        annual_rows.extend(result["annual_rows"])
        exit_rows.extend(result["exit_rows"])
        matched_rows.extend(result["matched_rows"])

    summary_rows.append(combined_summary)
    inference_rows.append(combined_inference)
    review_rows.append(combined_review)

    summary_frame = pd.DataFrame(summary_rows)
    inference_frame = pd.DataFrame(inference_rows)
    review_frame = pd.DataFrame(review_rows)
    annual_frame = pd.DataFrame(annual_rows)
    exit_frame = pd.DataFrame(exit_rows)
    matched_frame = pd.DataFrame(matched_rows)
    gates_frame = pd.DataFrame(
        usa500_forward_gates.promotion_gates(
            results["primary_forward"],
            results["crisis_regime"],
            results["recent_holdout"],
            combined_summary,
        )
    )

    summary_frame.to_csv(args.out / "scenario_summary.csv", index=False)
    inference_frame.to_csv(args.out / "inference.csv", index=False)
    review_frame.to_csv(args.out / "independent_review.csv", index=False)
    annual_frame.to_csv(args.out / "annual_attribution.csv", index=False)
    exit_frame.to_csv(args.out / "exit_attribution.csv", index=False)
    matched_frame.to_csv(args.out / "matched_time_rth_long_control.csv", index=False)
    gates_frame.to_csv(args.out / "promotion_gates.csv", index=False)
    pd.DataFrame(source_audits).to_csv(args.out / "source_audit.csv", index=False)

    if not bool((review_frame["status"] == "PASS").all()):
        raise RuntimeError("Independent scenario review failed")
    for partition in PARTITIONS:
        if results[partition]["management_direction_count"] != 2:
            raise RuntimeError(
                f"Management detector did not retain both directions in {partition}"
            )

    primary_rows = gates_frame.loc[gates_frame["gate_group"].eq("primary")]
    cross_rows = gates_frame.loc[gates_frame["gate_group"].eq("cross_block")]
    primary_pass = bool(primary_rows["passed"].all())
    cross_pass = bool(cross_rows["passed"].all())

    primary_expectancy = float(
        results["primary_forward"]["summaries"][CANDIDATE_SCENARIO]["expectancy_r"]
    )
    crisis_expectancy = float(
        results["crisis_regime"]["summaries"][CANDIDATE_SCENARIO]["expectancy_r"]
    )
    recent_expectancy = float(
        results["recent_holdout"]["summaries"][CANDIDATE_SCENARIO]["expectancy_r"]
    )
    if primary_pass and cross_pass:
        status = "RETAIN_USA500_RTH_FULL_123_FOR_ACTUAL_ES_VALIDATION"
    elif min(
        primary_expectancy,
        crisis_expectancy,
        recent_expectancy,
        float(combined_summary["expectancy_r"]),
    ) > 0:
        status = "HOLD_USA500_RTH_FULL_123_INDETERMINATE"
    else:
        status = "REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE"

    monitoring_summary = results["monitoring_2026_ytd"]["summaries"][CANDIDATE_SCENARIO]
    decision = {
        "study_id": str(design["study_id"]),
        "status": status,
        "primary_all_gates_passed": primary_pass,
        "cross_block_all_gates_passed": cross_pass,
        "passed_gate_count": int(gates_frame["passed"].sum()),
        "total_gate_count": int(len(gates_frame)),
        "source_classification": (
            usa500_rth_study.USA500_RTH_SPEC.source_classification
        ),
        "candidate": dict(design["candidate"]),
        "phase1_sha256": file_sha256(args.phase1),
        "design_sha256": file_sha256(args.design),
        "combined_2015_2025_trades": int(len(combined_trades)),
        "combined_2015_2025_expectancy_r": float(combined_summary["expectancy_r"]),
        "combined_2015_2025_net_r": float(combined_summary["net_r"]),
        "monitoring_2026_ytd_excluded_from_gates": True,
        "monitoring_2026_ytd_trades": int(monitoring_summary["trades"]),
        "monitoring_2026_ytd_net_r": float(monitoring_summary["net_r"]),
        "monitoring_2026_ytd_expectancy_r": float(
            monitoring_summary["expectancy_r"]
        ),
        "management_direction_retained": True,
        "rth_entry_window": "09:30:00-16:00:00 America/New_York",
        "entry_filter_only": True,
        "ema200_filter": False,
        "raw_source_published": False,
        "restrictions": list(design["restrictions"]),
    }
    (args.out / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "decision": decision,
        "config": asdict(base),
        "instrument_spec": asdict(usa500_rth_study.USA500_RTH_SPEC),
        "source_audit": source_audits,
        "partition_rows": {
            partition: int(len(one_minute_by_partition[partition]))
            for partition in PARTITIONS
        },
        "management": {
            partition: {
                "events": results[partition]["management_event_count"],
                "long": results[partition]["management_long_count"],
                "short": results[partition]["management_short_count"],
            }
            for partition in PARTITIONS
        },
    }
    (args.out / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(summary_frame.to_string(index=False))
    print(gates_frame.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
