from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from stoic_123_lab import (
    date_block_bootstrap,
    independent_trade_review,
    index_proxy_source,
    load_config_family,
    usa500_forward_gates,
    usa500_rth_study,
)
from stoic_123_lab.data import file_sha256
from stoic_123_lab.research_cache import FrameCache
from stoic_123_lab.research_runtime import (
    ResearchMode,
    StageTimer,
    plan_for_mode,
    primary_futility_reason,
)
from stoic_123_lab.validation import evaluate_trades

FROZEN_PHASE1_SHA256 = "5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805"
SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
SOURCE_PREFIX = "usa500idxusd_m1_bid"
CANDIDATE_SCENARIO = "RTH_LONG_FULL"
CANDIDATE_SCENARIO_ID = f"{SOURCE_ARM_ID}__{CANDIDATE_SCENARIO}"
DECISION_PARTITIONS = ("primary_forward", "crisis_regime", "recent_holdout")
ALL_PARTITIONS = (*DECISION_PARTITIONS, "monitoring_2026_ytd")


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


def _partitions_for_mode(mode: ResearchMode) -> tuple[str, ...]:
    if mode == "screen":
        return ("primary_forward",)
    if mode == "validate":
        return DECISION_PARTITIONS
    return ALL_PARTITIONS


def _source_key(audits: list[dict[str, object]]) -> str:
    rows = sorted((str(row["label"]), str(row["sha256"])) for row in audits)
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def _return_to_drawdown(summary: dict[str, object]) -> float:
    drawdown = float(summary["max_drawdown_r"])
    return float(summary["net_r"]) / drawdown if drawdown > 0 else np.nan


def _candidate_trades(out: Path, partition: str) -> pd.DataFrame:
    path = out / f"{partition}__{CANDIDATE_SCENARIO_ID}__trades.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing candidate ledger: {path}")
    frame = pd.read_csv(path)
    for column in ("entry_time", "exit_time", "signal_time", "base_lock_time"):
        if not frame.empty:
            frame[column] = pd.to_datetime(frame[column], errors="raise")
    return frame


def _combined_candidate(
    out: Path,
    *,
    iterations: int,
    run_review: bool,
    timer: StageTimer,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], pd.DataFrame]:
    with timer.measure("combine_candidate_ledgers"):
        combined = pd.concat(
            [_candidate_trades(out, partition) for partition in DECISION_PARTITIONS],
            ignore_index=True,
        ).sort_values("entry_time").reset_index(drop=True)
    if combined.empty:
        raise RuntimeError("Combined candidate ledger is empty")
    summary = evaluate_trades(
        combined,
        instrument="ES_PROXY",
        arm_id="USA500_RTH_FULL_123_COMBINED_2015_2025",
        source_start=pd.Timestamp("2015-01-01"),
        source_end=pd.Timestamp("2026-01-01"),
    )
    summary["partition"] = "combined_2015_2025"
    summary["return_to_drawdown"] = _return_to_drawdown(summary)
    if iterations:
        with timer.measure("bootstrap", partition="combined_2015_2025", iterations=iterations):
            inference = {
                "partition": "combined_2015_2025",
                "scenario_id": "USA500_RTH_FULL_123_COMBINED_2015_2025",
                "status": "COMPLETED",
                "iterations": iterations,
                **date_block_bootstrap(combined, iterations=iterations, seed=20265724),
            }
    else:
        inference = {
            "partition": "combined_2015_2025",
            "scenario_id": "USA500_RTH_FULL_123_COMBINED_2015_2025",
            "status": "SKIPPED",
            "iterations": 0,
            "blocks": int(pd.to_datetime(combined["entry_time"]).dt.normalize().nunique()),
            "observed_expectancy_r": float(combined["pnl_r"].mean()),
            "lo95_expectancy_r": np.nan,
            "hi95_expectancy_r": np.nan,
            "prob_expectancy_positive": np.nan,
        }
    if run_review:
        with timer.measure("independent_review", partition="combined_2015_2025"):
            review = {
                "partition": "combined_2015_2025",
                **independent_trade_review(
                    combined,
                    summary,
                    instrument="ES_PROXY",
                    arm_id="USA500_RTH_FULL_123_COMBINED_2015_2025",
                ),
            }
    else:
        review = {
            "partition": "combined_2015_2025",
            "instrument": "ES_PROXY",
            "arm_id": "USA500_RTH_FULL_123_COMBINED_2015_2025",
            "status": "SKIPPED",
        }
    combined.to_csv(out / "combined_2015_2025__RTH_LONG_FULL__trades.csv", index=False)
    return summary, inference, review, combined


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run accelerated staged USA500 strategy research"
    )
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--phase1", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("screen", "validate", "certify", "legacy"),
        default="screen",
    )
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".research-cache/stoic-usa500"),
    )
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    mode: ResearchMode = args.mode
    plan = plan_for_mode(mode, certify_iterations=args.iterations)
    timer = StageTimer()
    cache = FrameCache(args.cache_dir, enabled=not args.no_cache)

    with timer.measure("load_design"):
        design = index_proxy_source.load_design(args.design)
        _validate_design(design)
        if file_sha256(args.phase1) != FROZEN_PHASE1_SHA256:
            raise ValueError("Frozen phase-one checksum mismatch")
        configs = {config.arm_id: config for config in load_config_family(args.phase1)}
        base = configs[SOURCE_ARM_ID]

    results: dict[str, dict[str, object]] = {}
    source_audits: list[dict[str, object]] = []
    partition_rows: dict[str, int] = {}
    futility_reason: str | None = None
    executed_partitions: list[str] = []

    for index, partition in enumerate(_partitions_for_mode(mode)):
        with timer.measure("load_partition", partition=partition):
            one_minute, audits = index_proxy_source.load_partition(
                args.sources,
                design,
                partition,
                filename_prefix=SOURCE_PREFIX,
            )
        source_audits.extend(audits)
        partition_rows[partition] = int(len(one_minute))
        results[partition] = usa500_rth_study.run_partition(
            partition=partition,
            one_minute=one_minute,
            base=base,
            iterations=args.iterations,
            seed_base=20260730 + index * 100_000,
            out=args.out,
            plan=plan,
            cache=cache,
            source_key=_source_key(audits),
            timer=timer,
        )
        executed_partitions.append(partition)
        if partition == "primary_forward" and plan.early_stop:
            primary = results[partition]["summaries"][CANDIDATE_SCENARIO]
            futility_reason = primary_futility_reason(primary)
            if futility_reason is not None:
                break

    summary_rows: list[dict[str, object]] = []
    inference_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    exit_rows: list[dict[str, object]] = []
    matched_rows: list[dict[str, object]] = []
    for partition in executed_partitions:
        result = results[partition]
        summary_rows.extend(result["summary_rows"])
        inference_rows.extend(result["inference_rows"])
        review_rows.extend(result["review_rows"])
        annual_rows.extend(result["annual_rows"])
        exit_rows.extend(result["exit_rows"])
        matched_rows.extend(result["matched_rows"])

    combined_summary: dict[str, object] | None = None
    combined_trades = pd.DataFrame()
    if all(partition in results for partition in DECISION_PARTITIONS):
        combined_summary, combined_inference, combined_review, combined_trades = (
            _combined_candidate(
                args.out,
                iterations=plan.candidate_bootstrap_iterations,
                run_review=plan.review_scope != "none",
                timer=timer,
            )
        )
        summary_rows.append(combined_summary)
        inference_rows.append(combined_inference)
        review_rows.append(combined_review)

    summary_frame = pd.DataFrame(summary_rows)
    inference_frame = pd.DataFrame(inference_rows)
    review_frame = pd.DataFrame(review_rows)
    annual_frame = pd.DataFrame(annual_rows)
    exit_frame = pd.DataFrame(exit_rows)
    matched_frame = pd.DataFrame(matched_rows)

    gates_frame = pd.DataFrame()
    if mode in {"certify", "legacy"} and combined_summary is not None:
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

    completed_reviews = review_frame.loc[
        review_frame.get("status", pd.Series(dtype=str)).eq("PASS")
    ]
    failed_reviews = review_frame.loc[
        review_frame.get("status", pd.Series(dtype=str)).eq("FAIL")
    ]
    if not failed_reviews.empty:
        raise RuntimeError("Independent scenario review failed")
    for partition in executed_partitions:
        if results[partition]["management_direction_count"] != 2:
            raise RuntimeError(
                f"Management detector did not retain both directions in {partition}"
            )

    if mode == "screen":
        status = (
            "SCREEN_REJECTED_PRIMARY_FUTILITY"
            if futility_reason
            else "SCREEN_SURVIVOR_REQUIRES_VALIDATION"
        )
    elif mode == "validate":
        status = (
            "VALIDATION_REJECTED_PRIMARY_FUTILITY"
            if futility_reason
            else "VALIDATION_SURVIVOR_REQUIRES_CERTIFICATION"
        )
    else:
        if gates_frame.empty:
            status = "CERTIFICATION_INCOMPLETE"
        else:
            primary_pass = bool(
                gates_frame.loc[gates_frame["gate_group"].eq("primary"), "passed"].all()
            )
            cross_pass = bool(
                gates_frame.loc[
                    gates_frame["gate_group"].eq("cross_block"), "passed"
                ].all()
            )
            primary_expectancy = float(
                results["primary_forward"]["summaries"][CANDIDATE_SCENARIO][
                    "expectancy_r"
                ]
            )
            crisis_expectancy = float(
                results["crisis_regime"]["summaries"][CANDIDATE_SCENARIO][
                    "expectancy_r"
                ]
            )
            recent_expectancy = float(
                results["recent_holdout"]["summaries"][CANDIDATE_SCENARIO][
                    "expectancy_r"
                ]
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

    decision = {
        "study_id": str(design["study_id"]),
        "mode": mode,
        "status": status,
        "futility_reason": futility_reason,
        "executed_partitions": executed_partitions,
        "candidate": dict(design["candidate"]),
        "source_classification": usa500_rth_study.USA500_RTH_SPEC.source_classification,
        "phase1_sha256": file_sha256(args.phase1),
        "design_sha256": file_sha256(args.design),
        "cache": cache.summary(),
        "completed_independent_reviews": int(len(completed_reviews)),
        "passed_gate_count": int(gates_frame["passed"].sum())
        if not gates_frame.empty
        else 0,
        "total_gate_count": int(len(gates_frame)),
        "combined_2015_2025_trades": int(len(combined_trades)),
        "combined_2015_2025_expectancy_r": (
            float(combined_summary["expectancy_r"])
            if combined_summary is not None
            else None
        ),
        "promotion_authorized": mode in {"certify", "legacy"}
        and status.startswith("RETAIN_"),
    }
    (args.out / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "execution_plan.json").write_text(
        json.dumps(asdict(plan), indent=2, sort_keys=True, default=list) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "decision": decision,
        "config": asdict(base),
        "instrument_spec": asdict(usa500_rth_study.USA500_RTH_SPEC),
        "source_audit": source_audits,
        "partition_rows": partition_rows,
        "management": {
            partition: {
                "events": results[partition]["management_event_count"],
                "long": results[partition]["management_long_count"],
                "short": results[partition]["management_short_count"],
            }
            for partition in executed_partitions
        },
    }
    (args.out / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    timer.write(args.out)
    print(summary_frame.to_string(index=False))
    if not gates_frame.empty:
        print(gates_frame.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
