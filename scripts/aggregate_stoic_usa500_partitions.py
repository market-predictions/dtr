from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from stoic_123_lab import date_block_bootstrap, independent_trade_review, usa500_forward_gates
from stoic_123_lab.validation import evaluate_trades

SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
CANDIDATE_SCENARIO = "RTH_LONG_FULL"
CANDIDATE_SCENARIO_ID = f"{SOURCE_ARM_ID}__{CANDIDATE_SCENARIO}"
PARTITIONS = (
    "primary_forward",
    "crisis_regime",
    "recent_holdout",
    "monitoring_2026_ytd",
)
DECISION_PARTITIONS = PARTITIONS[:3]


def _discover(inputs: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in inputs.rglob("decision.json"):
        decision = json.loads(path.read_text(encoding="utf-8"))
        partition = str(decision.get("partition", ""))
        if partition not in PARTITIONS:
            continue
        if decision.get("status") != "CERTIFICATION_PARTITION_COMPLETE":
            raise ValueError(f"partition did not complete certification: {path}")
        if partition in found:
            raise ValueError(f"duplicate partition result: {partition}")
        found[partition] = path.parent
    missing = set(PARTITIONS).difference(found)
    if missing:
        raise ValueError(f"missing partition results: {sorted(missing)}")
    return found


def _read(directory: Path, name: str) -> pd.DataFrame:
    path = directory / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _scenario_name(arm_id: str) -> str:
    prefix = f"{SOURCE_ARM_ID}__"
    if not arm_id.startswith(prefix):
        raise ValueError(f"unexpected scenario arm_id: {arm_id}")
    return arm_id[len(prefix) :]


def _partition_result(directory: Path) -> dict[str, object]:
    summaries = _read(directory, "scenario_summary.csv")
    inferences = _read(directory, "inference.csv")
    matched = _read(directory, "matched_time_rth_long_control.csv")
    return {
        "summaries": {
            _scenario_name(str(row.arm_id)): row._asdict()
            for row in summaries.itertuples(index=False)
        },
        "inferences": {
            _scenario_name(str(row.scenario_id)): row._asdict()
            for row in inferences.itertuples(index=False)
        },
        "matched_rows": matched.to_dict("records"),
    }


def _candidate_trades(directory: Path, partition: str) -> pd.DataFrame:
    path = directory / f"{partition}__{CANDIDATE_SCENARIO_ID}__trades.csv"
    frame = pd.read_csv(path)
    for column in ("entry_time", "exit_time", "signal_time", "base_lock_time"):
        if not frame.empty:
            frame[column] = pd.to_datetime(frame[column], errors="raise")
    return frame


def _return_to_drawdown(summary: dict[str, object]) -> float:
    drawdown = float(summary["max_drawdown_r"])
    return float(summary["net_r"]) / drawdown if drawdown > 0 else np.nan


def _combined_candidate(
    directories: dict[str, Path],
    *,
    out: Path,
    iterations: int,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], pd.DataFrame]:
    combined = pd.concat(
        [_candidate_trades(directories[partition], partition) for partition in DECISION_PARTITIONS],
        ignore_index=True,
    ).sort_values("entry_time").reset_index(drop=True)
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
        "status": "COMPLETED",
        "iterations": iterations,
        **date_block_bootstrap(combined, iterations=iterations, seed=20265724),
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


def _concat(directories: dict[str, Path], filename: str) -> pd.DataFrame:
    return pd.concat(
        [_read(directories[partition], filename) for partition in PARTITIONS],
        ignore_index=True,
    )


def _partition_wall_seconds(directory: Path) -> float | None:
    path = directory / "wall_seconds.txt"
    return float(path.read_text().strip()) if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate parallel USA500 certification partitions"
    )
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    directories = _discover(args.inputs)
    results = {
        partition: _partition_result(directories[partition]) for partition in PARTITIONS
    }
    combined_summary, combined_inference, combined_review, combined_trades = (
        _combined_candidate(directories, out=args.out, iterations=args.iterations)
    )

    summary = _concat(directories, "scenario_summary.csv")
    inference = _concat(directories, "inference.csv")
    review = _concat(directories, "independent_review.csv")
    annual = _concat(directories, "annual_attribution.csv")
    exits = _concat(directories, "exit_attribution.csv")
    matched = _concat(directories, "matched_time_rth_long_control.csv")
    source_audit = _concat(directories, "source_audit.csv")
    summary = pd.concat([summary, pd.DataFrame([combined_summary])], ignore_index=True)
    inference = pd.concat([inference, pd.DataFrame([combined_inference])], ignore_index=True)
    review = pd.concat([review, pd.DataFrame([combined_review])], ignore_index=True)

    gates = pd.DataFrame(
        usa500_forward_gates.promotion_gates(
            results["primary_forward"],
            results["crisis_regime"],
            results["recent_holdout"],
            combined_summary,
        )
    )
    if not bool(review["status"].eq("PASS").all()):
        raise RuntimeError("parallel independent review failed")

    primary_pass = bool(gates.loc[gates["gate_group"].eq("primary"), "passed"].all())
    cross_pass = bool(gates.loc[gates["gate_group"].eq("cross_block"), "passed"].all())
    partition_expectancies = [
        float(results[partition]["summaries"][CANDIDATE_SCENARIO]["expectancy_r"])
        for partition in DECISION_PARTITIONS
    ]
    if primary_pass and cross_pass:
        status = "RETAIN_USA500_RTH_FULL_123_FOR_ACTUAL_ES_VALIDATION"
    elif min(*partition_expectancies, float(combined_summary["expectancy_r"])) > 0:
        status = "HOLD_USA500_RTH_FULL_123_INDETERMINATE"
    else:
        status = "REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE"

    summary.to_csv(args.out / "scenario_summary.csv", index=False)
    inference.to_csv(args.out / "inference.csv", index=False)
    review.to_csv(args.out / "independent_review.csv", index=False)
    annual.to_csv(args.out / "annual_attribution.csv", index=False)
    exits.to_csv(args.out / "exit_attribution.csv", index=False)
    matched.to_csv(args.out / "matched_time_rth_long_control.csv", index=False)
    source_audit.to_csv(args.out / "source_audit.csv", index=False)
    gates.to_csv(args.out / "promotion_gates.csv", index=False)

    walls = {
        partition: _partition_wall_seconds(directories[partition]) for partition in PARTITIONS
    }
    observed_walls = [value for value in walls.values() if value is not None]
    decisions = {
        partition: json.loads(
            (directories[partition] / "decision.json").read_text(encoding="utf-8")
        )
        for partition in PARTITIONS
    }
    decision = {
        "study_id": decisions["primary_forward"]["study_id"],
        "mode": "certify_parallel",
        "status": status,
        "source_classification": decisions["primary_forward"]["source_classification"],
        "candidate": decisions["primary_forward"]["candidate"],
        "passed_gate_count": int(gates["passed"].sum()),
        "total_gate_count": int(len(gates)),
        "combined_2015_2025_trades": int(len(combined_trades)),
        "combined_2015_2025_expectancy_r": float(combined_summary["expectancy_r"]),
        "combined_2015_2025_net_r": float(combined_summary["net_r"]),
        "partition_wall_seconds": walls,
        "parallel_compute_lower_bound_seconds": max(observed_walls) if observed_walls else None,
        "serial_partition_compute_seconds": sum(observed_walls) if observed_walls else None,
        "promotion_authorized": status.startswith("RETAIN_"),
        "raw_source_published": False,
    }
    (args.out / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "run_manifest.json").write_text(
        json.dumps(
            {
                "decision": decision,
                "partition_decisions": decisions,
                "source_rows": int(source_audit["rows"].sum()),
                "partition_directories": {
                    partition: str(directory) for partition, directory in directories.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(summary.to_string(index=False))
    print(gates.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
