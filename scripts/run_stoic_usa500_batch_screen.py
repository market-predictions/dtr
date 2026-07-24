from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from stoic_123_lab import index_proxy_source, load_config_family, usa500_rth_study
from stoic_123_lab.data import file_sha256
from stoic_123_lab.research_batch import (
    apply_variation,
    detection_signature,
    full_config_signature,
    group_variations_by_detection,
    load_batch_design,
)
from stoic_123_lab.research_cache import FrameCache
from stoic_123_lab.research_runtime import StageTimer, plan_for_mode, primary_futility_reason

FROZEN_PHASE1_SHA256 = "5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805"
SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
SOURCE_PREFIX = "usa500idxusd_m1_bid"
ALLOWED_DISCOVERY_PARTITIONS = {"primary_forward"}


def _source_key(audits: list[dict[str, object]]) -> str:
    rows = sorted((str(row["label"]), str(row["sha256"])) for row in audits)
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a discovery-only batch screen with shared source and feature caches"
    )
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--phase1", type=Path, required=True)
    parser.add_argument("--source-design", type=Path, required=True)
    parser.add_argument("--batch-design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".research-cache/stoic-usa500"),
    )
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    timer = StageTimer()
    cache = FrameCache(args.cache_dir, enabled=not args.no_cache)
    plan = plan_for_mode("screen")

    with timer.measure("load_designs"):
        source_design = index_proxy_source.load_design(args.source_design)
        batch_design = load_batch_design(
            args.batch_design,
            allowed_partitions=ALLOWED_DISCOVERY_PARTITIONS,
        )
        if file_sha256(args.phase1) != FROZEN_PHASE1_SHA256:
            raise ValueError("Frozen phase-one checksum mismatch")
        configs = {config.arm_id: config for config in load_config_family(args.phase1)}
        base = configs[SOURCE_ARM_ID]

    with timer.measure("load_partition", partition=batch_design.source_partition):
        one_minute, audits = index_proxy_source.load_partition(
            args.sources,
            source_design,
            batch_design.source_partition,
            filename_prefix=SOURCE_PREFIX,
        )
    source_key = _source_key(audits)

    groups = group_variations_by_detection(base, batch_design.variations)
    group_by_variation = {
        variation.variation_id: signature
        for signature, variations in groups.items()
        for variation in variations
    }
    rows: list[dict[str, object]] = []
    seen_full_signatures: set[str] = set()
    for index, variation in enumerate(batch_design.variations):
        config = apply_variation(base, variation)
        signature = full_config_signature(config)
        if signature in seen_full_signatures:
            raise ValueError(f"duplicate effective batch configuration: {variation.variation_id}")
        seen_full_signatures.add(signature)
        with timer.measure("batch_variation", variation=variation.variation_id):
            result = usa500_rth_study.run_partition(
                partition=batch_design.source_partition,
                one_minute=one_minute,
                base=config,
                iterations=1,
                seed_base=20260800 + index * 10_000,
                out=args.out,
                plan=plan,
                cache=cache,
                source_key=source_key,
                timer=timer,
            )
        candidate = result["summaries"]["RTH_LONG_FULL"]
        diagnostic = result["summaries"]["RTH_LONG_EMA_BREAK"]
        futility = primary_futility_reason(candidate)
        rows.append(
            {
                "study_id": batch_design.study_id,
                "variation_id": variation.variation_id,
                "description": variation.description,
                "status": "REJECTED_FAST_SCREEN" if futility else "SURVIVOR_REQUIRES_VALIDATION",
                "futility_reason": futility,
                "full_config_signature": signature,
                "detection_signature": detection_signature(config),
                "detection_group": group_by_variation[variation.variation_id],
                "candidate_trades": int(candidate["trades"]),
                "candidate_net_r": float(candidate["net_r"]),
                "candidate_expectancy_r": float(candidate["expectancy_r"]),
                "candidate_max_drawdown_r": float(candidate["max_drawdown_r"]),
                "diagnostic_trades": int(diagnostic["trades"]),
                "diagnostic_net_r": float(diagnostic["net_r"]),
                "diagnostic_expectancy_r": float(diagnostic["expectancy_r"]),
                "overrides": json.dumps(variation.overrides, sort_keys=True),
            }
        )

    results = pd.DataFrame(rows)
    results.to_csv(args.out / "batch_screen_results.csv", index=False)
    group_rows = [
        {
            "detection_signature": signature,
            "variation_count": len(variations),
            "variation_ids": ",".join(variation.variation_id for variation in variations),
        }
        for signature, variations in groups.items()
    ]
    pd.DataFrame(group_rows).to_csv(args.out / "detection_groups.csv", index=False)
    pd.DataFrame(audits).to_csv(args.out / "source_audit.csv", index=False)
    decision = {
        "study_id": batch_design.study_id,
        "status": "DISCOVERY_BATCH_COMPLETE",
        "source_partition": batch_design.source_partition,
        "variation_count": int(len(results)),
        "survivor_count": int(results["status"].eq("SURVIVOR_REQUIRES_VALIDATION").sum()),
        "promotion_authorized": False,
        "holdout_accessed": False,
        "cache": cache.summary(),
        "source_design_sha256": file_sha256(args.source_design),
        "batch_design_sha256": file_sha256(args.batch_design),
        "phase1_sha256": file_sha256(args.phase1),
    }
    (args.out / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "run_manifest.json").write_text(
        json.dumps(
            {
                "decision": decision,
                "base_config": asdict(base),
                "batch_design": asdict(batch_design),
                "source_audit": audits,
                "detection_group_count": len(groups),
            },
            indent=2,
            sort_keys=True,
            default=list,
        )
        + "\n",
        encoding="utf-8",
    )
    timer.write(args.out)
    print(results.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
