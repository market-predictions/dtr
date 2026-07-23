from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from stoic_123_lab import load_config_family
from stoic_123_lab.data import file_sha256
from stoic_123_lab.short_proxy_gates import _promotion_gates as promotion_gates
from stoic_123_lab.short_proxy_source import (
    _load_design as load_design,
    _load_partition as load_partition,
)
from stoic_123_lab.short_proxy_study import (
    SHORT_PROXY_SPEC,
    _run_partition as run_partition,
)

FROZEN_PHASE1_SHA256 = "5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805"
SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
MATCHED_REPLICATES = 50


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen unseen short-side USATECH proxy falsification"
    )
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--phase1", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    design = load_design(args.design)
    if file_sha256(args.phase1) != FROZEN_PHASE1_SHA256:
        raise ValueError("Frozen phase-one checksum mismatch")
    hypothesis = design.get("hypothesis")
    if not isinstance(hypothesis, dict):
        raise ValueError("hypothesis must be a mapping")
    if hypothesis.get("source_arm_id") != SOURCE_ARM_ID:
        raise ValueError("Frozen source arm mismatch")
    if hypothesis.get("direction_mode") != "short_only":
        raise ValueError("Frozen direction mismatch")
    matched_replicates = int(
        design.get("matched_control_replicates", MATCHED_REPLICATES)
    )
    if matched_replicates != MATCHED_REPLICATES:
        raise ValueError("Matched replicate count mismatch")

    configs = {config.arm_id: config for config in load_config_family(args.phase1)}
    base = configs[SOURCE_ARM_ID]
    older_frame, older_audits = load_partition(args.sources, design, "older_history")
    forward_frame, forward_audits = load_partition(args.sources, design, "forward_2026")

    older = run_partition(
        partition="older_history",
        one_minute=older_frame,
        base=base,
        iterations=args.iterations,
        seed_base=20260723,
        out=args.out,
    )
    forward = run_partition(
        partition="forward_2026",
        one_minute=forward_frame,
        base=base,
        iterations=args.iterations,
        seed_base=20261723,
        out=args.out,
    )

    summary_rows = older["summary_rows"] + forward["summary_rows"]
    inference_rows = older["inference_rows"] + forward["inference_rows"]
    review_rows = older["review_rows"] + forward["review_rows"]
    annual_rows = older["annual_rows"] + forward["annual_rows"]
    matched_rows = [older["matched"], forward["matched"]]
    gates = promotion_gates(older, forward)

    summary_frame = pd.DataFrame(summary_rows)
    inference_frame = pd.DataFrame(inference_rows)
    review_frame = pd.DataFrame(review_rows)
    annual_frame = pd.DataFrame(annual_rows)
    matched_frame = pd.DataFrame(matched_rows)
    gates_frame = pd.DataFrame(gates)
    summary_frame.to_csv(args.out / "scenario_summary.csv", index=False)
    inference_frame.to_csv(args.out / "inference.csv", index=False)
    review_frame.to_csv(args.out / "independent_review.csv", index=False)
    annual_frame.to_csv(args.out / "annual_attribution.csv", index=False)
    matched_frame.to_csv(args.out / "matched_time_short_control.csv", index=False)
    gates_frame.to_csv(args.out / "promotion_gates.csv", index=False)
    pd.DataFrame(older_audits + forward_audits).to_csv(
        args.out / "source_audit.csv",
        index=False,
    )

    if not bool((review_frame["status"] == "PASS").all()):
        raise RuntimeError("Independent scenario review failed")
    if (
        older["management_direction_count"] != 2
        or forward["management_direction_count"] != 2
    ):
        raise RuntimeError("Management detector did not retain both directions")

    all_pass = bool(gates_frame["passed"].all())
    status = (
        "RETAIN_FOR_PAID_NQ_FUTURES_VALIDATION"
        if all_pass
        else "REJECT_OR_HOLD_NO_PROMOTION"
    )
    decision = {
        "study_id": str(design["study_id"]),
        "status": status,
        "all_promotion_gates_passed": all_pass,
        "passed_gate_count": int(gates_frame["passed"].sum()),
        "total_gate_count": int(len(gates_frame)),
        "source_classification": SHORT_PROXY_SPEC.source_classification,
        "phase1_sha256": file_sha256(args.phase1),
        "design_sha256": file_sha256(args.design),
        "management_direction_retained": True,
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
        "source_audit": older_audits + forward_audits,
        "partition_rows": {
            "older_history": int(len(older_frame)),
            "forward_2026": int(len(forward_frame)),
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
