from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from stoic_123_lab import index_proxy_source, load_config_family, usa500_rth_study
from stoic_123_lab.data import file_sha256
from stoic_123_lab.research_cache import FrameCache
from stoic_123_lab.research_runtime import StageTimer, plan_for_mode

FROZEN_PHASE1_SHA256 = "5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805"
SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
SOURCE_PREFIX = "usa500idxusd_m1_bid"
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


def _source_key(audits: list[dict[str, object]]) -> str:
    rows = sorted((str(row["label"]), str(row["sha256"])) for row in audits)
    payload = json.dumps(rows, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _write_frame(rows: list[dict[str, object]], path: Path) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one checksum-gated USA500 research partition"
    )
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--phase1", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--partition", choices=PARTITIONS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".research-cache/stoic-usa500"),
    )
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    plan = plan_for_mode("certify", certify_iterations=args.iterations)
    timer = StageTimer()
    cache = FrameCache(args.cache_dir, enabled=not args.no_cache)

    with timer.measure("load_design"):
        design = index_proxy_source.load_design(args.design)
        _validate_design(design)
        if file_sha256(args.phase1) != FROZEN_PHASE1_SHA256:
            raise ValueError("Frozen phase-one checksum mismatch")
        configs = {config.arm_id: config for config in load_config_family(args.phase1)}
        base = configs[SOURCE_ARM_ID]

    with timer.measure("load_partition", partition=args.partition):
        one_minute, audits = index_proxy_source.load_partition(
            args.sources,
            design,
            args.partition,
            filename_prefix=SOURCE_PREFIX,
        )

    result = usa500_rth_study.run_partition(
        partition=args.partition,
        one_minute=one_minute,
        base=base,
        iterations=args.iterations,
        seed_base=20260730 + PARTITIONS.index(args.partition) * 100_000,
        out=args.out,
        plan=plan,
        cache=cache,
        source_key=_source_key(audits),
        timer=timer,
    )

    _write_frame(result["summary_rows"], args.out / "scenario_summary.csv")
    _write_frame(result["inference_rows"], args.out / "inference.csv")
    _write_frame(result["review_rows"], args.out / "independent_review.csv")
    _write_frame(result["annual_rows"], args.out / "annual_attribution.csv")
    _write_frame(result["exit_rows"], args.out / "exit_attribution.csv")
    _write_frame(result["matched_rows"], args.out / "matched_time_rth_long_control.csv")
    _write_frame(audits, args.out / "source_audit.csv")

    review = pd.DataFrame(result["review_rows"])
    if not bool(review["status"].eq("PASS").all()):
        raise RuntimeError("Independent partition review failed")
    if result["management_direction_count"] != 2:
        raise RuntimeError("Management detector did not retain both directions")

    decision = {
        "study_id": str(design["study_id"]),
        "status": "CERTIFICATION_PARTITION_COMPLETE",
        "mode": "certify",
        "partition": args.partition,
        "source_classification": usa500_rth_study.USA500_RTH_SPEC.source_classification,
        "phase1_sha256": file_sha256(args.phase1),
        "design_sha256": file_sha256(args.design),
        "candidate": dict(design["candidate"]),
        "cache": cache.summary(),
        "promotion_authorized": False,
        "raw_source_published": False,
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
        "source_audit": audits,
        "partition_rows": int(len(one_minute)),
        "management": {
            "events": result["management_event_count"],
            "long": result["management_long_count"],
            "short": result["management_short_count"],
        },
    }
    (args.out / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    timer.write(args.out)
    print(pd.DataFrame(result["summary_rows"]).to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
