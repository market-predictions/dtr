from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from stoic_123_lab import load_config_family
from stoic_123_lab import index_proxy_source, usa500_rth_gates, usa500_rth_study
from stoic_123_lab.data import file_sha256

FROZEN_PHASE1_SHA256 = "5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805"
SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
MATCHED_REPLICATES = 50
SOURCE_PREFIX = "usa500idxusd_m1_bid"


def _validate_design(design: dict[str, object]) -> None:
    if str(design.get("status")) != "SOURCE_QUALIFIED_EXECUTION_AUTHORIZED":
        raise ValueError("USA500 RTH design is not execution authorized")
    hypotheses = design.get("hypotheses")
    if not isinstance(hypotheses, dict):
        raise ValueError("hypotheses must be a mapping")
    if hypotheses.get("source_arm_id") != SOURCE_ARM_ID:
        raise ValueError("Frozen source arm mismatch")
    primary = hypotheses.get("primary")
    secondary = hypotheses.get("secondary")
    if not isinstance(primary, dict) or not isinstance(secondary, dict):
        raise ValueError("Primary and secondary hypotheses must be mappings")
    if primary.get("id") != "RTH_LONG_EMA_BREAK":
        raise ValueError("Frozen primary hypothesis mismatch")
    if secondary.get("id") != "RTH_LONG_FULL_123":
        raise ValueError("Frozen secondary hypothesis mismatch")
    if primary.get("direction_mode") != "long_only":
        raise ValueError("Frozen primary direction mismatch")
    if secondary.get("direction_mode") != "long_only":
        raise ValueError("Frozen secondary direction mismatch")
    if int(design.get("matched_control_replicates", 0)) != MATCHED_REPLICATES:
        raise ValueError("Matched replicate count mismatch")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen USA500 RTH long cross-asset replication"
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
    history_frame, history_audits = index_proxy_source.load_partition(
        args.sources,
        design,
        "fresh_history",
        filename_prefix=SOURCE_PREFIX,
    )
    holdout_frame, holdout_audits = index_proxy_source.load_partition(
        args.sources,
        design,
        "fresh_holdout",
        filename_prefix=SOURCE_PREFIX,
    )

    history = usa500_rth_study.run_partition(
        partition="fresh_history",
        one_minute=history_frame,
        base=base,
        iterations=args.iterations,
        seed_base=20260725,
        out=args.out,
    )
    holdout = usa500_rth_study.run_partition(
        partition="fresh_holdout",
        one_minute=holdout_frame,
        base=base,
        iterations=args.iterations,
        seed_base=20261725,
        out=args.out,
    )

    summary_frame = pd.DataFrame(history["summary_rows"] + holdout["summary_rows"])
    inference_frame = pd.DataFrame(
        history["inference_rows"] + holdout["inference_rows"]
    )
    review_frame = pd.DataFrame(history["review_rows"] + holdout["review_rows"])
    annual_frame = pd.DataFrame(history["annual_rows"] + holdout["annual_rows"])
    exit_frame = pd.DataFrame(history["exit_rows"] + holdout["exit_rows"])
    matched_frame = pd.DataFrame(history["matched_rows"] + holdout["matched_rows"])
    gates_frame = pd.DataFrame(usa500_rth_gates.promotion_gates(history, holdout))

    summary_frame.to_csv(args.out / "scenario_summary.csv", index=False)
    inference_frame.to_csv(args.out / "inference.csv", index=False)
    review_frame.to_csv(args.out / "independent_review.csv", index=False)
    annual_frame.to_csv(args.out / "annual_attribution.csv", index=False)
    exit_frame.to_csv(args.out / "exit_attribution.csv", index=False)
    matched_frame.to_csv(args.out / "matched_time_rth_long_control.csv", index=False)
    gates_frame.to_csv(args.out / "promotion_gates.csv", index=False)
    pd.DataFrame(history_audits + holdout_audits).to_csv(
        args.out / "source_audit.csv",
        index=False,
    )

    if not bool((review_frame["status"] == "PASS").all()):
        raise RuntimeError("Independent scenario review failed")
    if (
        history["management_direction_count"] != 2
        or holdout["management_direction_count"] != 2
    ):
        raise RuntimeError("Management detector did not retain both directions")

    primary_rows = gates_frame.loc[gates_frame["gate_group"].eq("primary")]
    secondary_rows = gates_frame.loc[gates_frame["gate_group"].eq("secondary")]
    primary_pass = bool(primary_rows["passed"].all())
    secondary_pass = primary_pass and bool(secondary_rows["passed"].all())
    if secondary_pass:
        status = "POSITIVE_USA500_TRANSFER_PRIMARY_AND_SECONDARY"
    elif primary_pass:
        status = "POSITIVE_USA500_TRANSFER_EMA_BREAK_ONLY"
    else:
        status = "REJECT_OR_HOLD_USA500_TRANSFER"

    decision = {
        "study_id": str(design["study_id"]),
        "status": status,
        "primary_all_gates_passed": primary_pass,
        "secondary_all_gates_passed": secondary_pass,
        "passed_gate_count": int(gates_frame["passed"].sum()),
        "total_gate_count": int(len(gates_frame)),
        "source_classification": (
            usa500_rth_study.USA500_RTH_SPEC.source_classification
        ),
        "phase1_sha256": file_sha256(args.phase1),
        "design_sha256": file_sha256(args.design),
        "management_direction_retained": True,
        "rth_entry_window": "09:30:00-16:00:00 America/New_York",
        "entry_filter_only": True,
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
        "source_audit": history_audits + holdout_audits,
        "partition_rows": {
            "fresh_history": int(len(history_frame)),
            "fresh_holdout": int(len(holdout_frame)),
        },
        "management": {
            "fresh_history_events": history["management_event_count"],
            "fresh_history_long": history["management_long_count"],
            "fresh_history_short": history["management_short_count"],
            "fresh_holdout_events": holdout["management_event_count"],
            "fresh_holdout_long": holdout["management_long_count"],
            "fresh_holdout_short": holdout["management_short_count"],
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
