from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from stoic_123_lab import NQ_SPEC, load_nq
from stoic_123_lab.data import file_sha256

FROZEN_PHASE1_SHA256 = "5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate frozen Stoic NQ study inputs")
    parser.add_argument("--nq", type=Path, required=True)
    parser.add_argument("--phase1", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    design = yaml.safe_load(args.design.read_text(encoding="utf-8"))
    if not isinstance(design, dict):
        raise ValueError("Validation design must be a mapping")
    source_contract = design.get("source_contract")
    execution = design.get("execution_tests")
    matched = design.get("matched_control_contract")
    if not isinstance(source_contract, dict):
        raise ValueError("source_contract must be a mapping")
    if not isinstance(execution, dict):
        raise ValueError("execution_tests must be a mapping")
    if not isinstance(matched, dict):
        raise ValueError("matched_control_contract must be a mapping")

    source_sha = file_sha256(args.nq)
    phase1_sha = file_sha256(args.phase1)
    expected_source = str(source_contract.get("expected_sha256", ""))
    expected_phase1 = str(design.get("phase1_expected_sha256", ""))
    if source_sha != expected_source or expected_source != NQ_SPEC.source_sha256:
        raise ValueError("Frozen NQ source checksum contract mismatch")
    if phase1_sha != expected_phase1 or expected_phase1 != FROZEN_PHASE1_SHA256:
        raise ValueError("Frozen phase-one checksum contract mismatch")

    candidates = design.get("candidate_arms")
    candidates_invalid = (
        not isinstance(candidates, list)
        or not candidates
        or len(candidates) != len(set(candidates))
    )
    if candidates_invalid:
        raise ValueError("candidate_arms must be a unique non-empty list")
    if int(design.get("matched_control_replicates", 0)) != 50:
        raise ValueError("Matched-control replicate count must remain 50")
    minimum_fraction = float(matched.get("minimum_event_match_fraction", np.nan))
    if not np.isfinite(minimum_fraction) or minimum_fraction != 0.90:
        raise ValueError("Matched-control minimum coverage must remain 90%")
    if float(execution.get("baseline_slippage_ticks_each_side", np.nan)) != 1.0:
        raise ValueError("Baseline slippage must remain one tick per side")
    if float(execution.get("stressed_slippage_ticks_each_side", np.nan)) != 2.0:
        raise ValueError("Stress slippage must remain two ticks per side")
    commission = float(execution.get("commission_per_side_usd", np.nan))
    if commission != NQ_SPEC.commission_per_side:
        raise ValueError("Commission contract mismatch")
    if list(execution.get("entry_delays_minutes", [])) != [1, 5]:
        raise ValueError("Delay family must remain one and five minutes")

    one_minute = load_nq(args.nq)
    observed_start = pd.Timestamp(one_minute["timestamp"].min())
    observed_end = pd.Timestamp(one_minute["timestamp"].max())
    expected_start = pd.Timestamp(source_contract["period_start_et"])
    expected_end = pd.Timestamp(source_contract["period_end_et"])
    if observed_start != expected_start or observed_end != expected_end:
        raise ValueError(
            "NQ source bounds mismatch: "
            f"observed {observed_start} to {observed_end}, "
            f"expected {expected_start} to {expected_end}"
        )

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "PASS",
        "study_id": design.get("study_id"),
        "source_sha256": source_sha,
        "phase1_sha256": phase1_sha,
        "design_sha256": file_sha256(args.design),
        "source_start": observed_start.isoformat(),
        "source_end": observed_end.isoformat(),
        "rows": int(len(one_minute)),
        "candidate_arms": candidates,
        "matched_control_replicates": 50,
        "minimum_event_match_fraction": minimum_fraction,
    }
    (args.out / "preflight.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
