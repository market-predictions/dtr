from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from stoic_123_lab import (
    NQ_SPEC,
    detect_sequences,
    load_config_family,
    load_nq,
    resample_ohlcv,
    summarize,
)
from stoic_123_lab.data import file_sha256
from stoic_123_lab.validation import (
    delay_events,
    detect_long_stage_events,
    entry_config,
    expanding_year_folds,
    full_sequence_events,
    management_config,
    matched_time_events,
    run_scenario,
    session_attribution,
)
from stoic_123_lab.validation_runner import (
    annual_rows,
    gate_rows,
    load_design,
    run_evaluated_scenario,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Preregistered NQ long-only mechanism validation")
    parser.add_argument("--nq", type=Path, required=True)
    parser.add_argument("--phase1", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    design = load_design(args.design)
    candidate_ids = list(design["candidate_arms"])
    matched_replicates = int(design["matched_control_replicates"])
    configs = {config.arm_id: config for config in load_config_family(args.phase1)}
    missing = set(candidate_ids).difference(configs)
    if missing:
        raise ValueError(f"Candidate arms missing from phase one: {sorted(missing)}")

    one_minute = load_nq(args.nq)
    source_start = pd.Timestamp(one_minute["timestamp"].min())
    source_end = pd.Timestamp(one_minute["timestamp"].max())
    required_minutes = sorted(
        {
            minutes
            for arm_id in candidate_ids
            for minutes in (
                configs[arm_id].execution_minutes,
                configs[arm_id].management_minutes,
                configs[arm_id].map_minutes,
            )
        }
    )
    bars = {minutes: resample_ohlcv(one_minute, minutes) for minutes in required_minutes}

    summary_rows: list[dict[str, object]] = []
    inference_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    yearly_rows: list[dict[str, object]] = []
    session_rows: list[dict[str, object]] = []
    fold_rows: list[dict[str, object]] = []
    mechanism_rows: list[dict[str, object]] = []
    matched_rows: list[dict[str, object]] = []
    scenario_summaries: dict[str, dict[str, object]] = {}
    scenario_inference: dict[str, dict[str, object]] = {}

    for arm_index, arm_id in enumerate(candidate_ids):
        base = configs[arm_id]
        execution_bars = bars[base.execution_minutes]
        management_bars = bars[base.management_minutes]
        map_bars = bars[base.map_minutes]
        management = detect_sequences(
            management_bars,
            map_bars,
            management_config(base),
        ).events
        management.to_csv(args.out / f"{arm_id}__management_events.csv", index=False)

        long_config = entry_config(base, "long_only")
        short_config = entry_config(base, "short_only")
        both_config = entry_config(base, "both")
        long_events = full_sequence_events(
            execution_bars,
            map_bars,
            base,
            direction_mode="long_only",
        )
        short_events = full_sequence_events(
            execution_bars,
            map_bars,
            base,
            direction_mode="short_only",
        )
        both_events = full_sequence_events(
            execution_bars,
            map_bars,
            base,
            direction_mode="both",
        )
        break_events = detect_long_stage_events(
            execution_bars,
            map_bars,
            long_config,
            model="ema_break",
        ).events
        retest_events = detect_long_stage_events(
            execution_bars,
            map_bars,
            long_config,
            model="ema_break_retest",
        ).events

        scenarios = [
            (f"{arm_id}__BOTH_FULL", both_events, both_config),
            (f"{arm_id}__LONG_FULL", long_events, long_config),
            (f"{arm_id}__SHORT_FULL", short_events, short_config),
            (f"{arm_id}__LONG_EMA_BREAK", break_events, long_config),
            (f"{arm_id}__LONG_EMA_BREAK_RETEST", retest_events, long_config),
            (
                f"{arm_id}__LONG_FULL_COST_2T",
                long_events,
                replace(long_config, slippage_ticks_each_side=2.0),
            ),
            (f"{arm_id}__LONG_FULL_DELAY_1M", delay_events(long_events, 1), long_config),
            (f"{arm_id}__LONG_FULL_DELAY_5M", delay_events(long_events, 5), long_config),
        ]

        arm_trades: dict[str, pd.DataFrame] = {}
        for scenario_index, (scenario_id, events, scenario_config) in enumerate(scenarios):
            summary, inference, review, trades = run_evaluated_scenario(
                scenario_id=scenario_id,
                one_minute=one_minute,
                events=events,
                management_events=management,
                config=scenario_config,
                source_start=source_start,
                source_end=source_end,
                iterations=args.iterations,
                seed=20260724 + arm_index * 100 + scenario_index,
                out=args.out,
            )
            summary_rows.append(summary)
            inference_rows.append(inference)
            review_rows.append(review)
            scenario_summaries[scenario_id] = summary
            scenario_inference[scenario_id] = inference
            arm_trades[scenario_id] = trades
            yearly_rows.extend(annual_rows(trades, scenario_id))
            sessions = session_attribution(trades)
            if not sessions.empty:
                sessions.insert(0, "scenario_id", scenario_id)
                session_rows.extend(sessions.to_dict("records"))
            folds = expanding_year_folds(trades)
            if not folds.empty:
                folds.insert(0, "scenario_id", scenario_id)
                fold_rows.extend(folds.to_dict("records"))

        full = scenario_summaries[f"{arm_id}__LONG_FULL"]
        for control_name in ("LONG_EMA_BREAK", "LONG_EMA_BREAK_RETEST"):
            control = scenario_summaries[f"{arm_id}__{control_name}"]
            mechanism_rows.append(
                {
                    "arm_id": arm_id,
                    "control": control_name,
                    "full_expectancy_r": full["expectancy_r"],
                    "control_expectancy_r": control["expectancy_r"],
                    "expectancy_delta_r": (
                        float(full["expectancy_r"]) - float(control["expectancy_r"])
                    ),
                    "full_return_to_drawdown": full["return_to_drawdown"],
                    "control_return_to_drawdown": control["return_to_drawdown"],
                    "full_trades": full["trades"],
                    "control_trades": control["trades"],
                }
            )

        full_trades = arm_trades[f"{arm_id}__LONG_FULL"]
        full_expectancy = float(full["expectancy_r"])
        full_hold = float(full["median_hold_minutes"])
        matched_metrics: list[dict[str, object]] = []
        for replicate in range(matched_replicates):
            matched_events = matched_time_events(
                long_events,
                execution_bars,
                map_bars,
                long_config,
                seed=20260724 + arm_index * 10_000 + replicate,
            )
            event_match_fraction = (
                len(matched_events) / len(long_events) if len(long_events) else np.nan
            )
            matched_config = replace(
                long_config,
                arm_id=f"{arm_id}__MATCHED_{replicate:03d}",
            )
            matched_trades = run_scenario(
                one_minute=one_minute,
                events=matched_events,
                management_events=management,
                spec=NQ_SPEC,
                config=matched_config,
            )
            metric = summarize(
                matched_trades,
                instrument="NQ",
                arm_id=matched_config.arm_id,
            )
            metric["event_match_fraction"] = float(event_match_fraction)
            matched_metrics.append(metric)
            if replicate == 0:
                matched_events.to_csv(
                    args.out / f"{arm_id}__MATCHED_TIME_EXAMPLE__events.csv",
                    index=False,
                )
                matched_trades.to_csv(
                    args.out / f"{arm_id}__MATCHED_TIME_EXAMPLE__trades.csv",
                    index=False,
                )
        matched_frame = pd.DataFrame(matched_metrics)
        matched_hold = float(matched_frame["median_hold_minutes"].median())
        hold_ratio = matched_hold / full_hold if full_hold > 0 else np.nan
        matched_rows.append(
            {
                "arm_id": arm_id,
                "replicates": matched_replicates,
                "full_expectancy_r": full_expectancy,
                "matched_median_expectancy_r": float(
                    matched_frame["expectancy_r"].median()
                ),
                "matched_p95_expectancy_r": float(
                    matched_frame["expectancy_r"].quantile(0.95)
                ),
                "empirical_prob_matched_ge_full": float(
                    (matched_frame["expectancy_r"] >= full_expectancy).mean()
                ),
                "full_median_hold_minutes": full_hold,
                "matched_median_hold_minutes": matched_hold,
                "matched_to_full_hold_ratio": hold_ratio,
                "hold_distribution_match_flag": bool(0.75 <= hold_ratio <= 1.25),
                "full_event_count": int(len(long_events)),
                "matched_min_event_match_fraction": float(
                    matched_frame["event_match_fraction"].min()
                ),
                "full_trade_count": int(len(full_trades)),
                "matched_median_trade_count": float(matched_frame["trades"].median()),
            }
        )

    all_gate_rows = []
    for arm_id in candidate_ids:
        all_gate_rows.extend(gate_rows(arm_id, scenario_summaries, scenario_inference))

    summary_frame = pd.DataFrame(summary_rows)
    inference_frame = pd.DataFrame(inference_rows)
    review_frame = pd.DataFrame(review_rows)
    gates_frame = pd.DataFrame(all_gate_rows)
    summary_frame.to_csv(args.out / "scenario_summary.csv", index=False)
    inference_frame.to_csv(args.out / "inference.csv", index=False)
    review_frame.to_csv(args.out / "independent_review.csv", index=False)
    pd.DataFrame(yearly_rows).to_csv(args.out / "annual_attribution.csv", index=False)
    pd.DataFrame(session_rows).to_csv(args.out / "session_attribution.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(args.out / "expanding_year_folds.csv", index=False)
    pd.DataFrame(mechanism_rows).to_csv(args.out / "mechanism_comparison.csv", index=False)
    pd.DataFrame(matched_rows).to_csv(args.out / "matched_time_control.csv", index=False)
    gates_frame.to_csv(args.out / "promotion_gates.csv", index=False)

    if not bool((review_frame["status"] == "PASS").all()):
        raise RuntimeError("Independent scenario review failed")

    arm_gate = gates_frame.groupby("arm_id")["passed"].all()
    promoted = [arm for arm, passed in arm_gate.items() if bool(passed)]
    decision = {
        "study_id": str(design["study_id"]),
        "status": "PROMOTION_GATE_PASSED" if promoted else "NO_PROMOTION",
        "promoted_arms": promoted,
        "candidate_arms": candidate_ids,
        "matched_control_replicates": matched_replicates,
        "source_sha256": file_sha256(args.nq),
        "phase1_sha256": file_sha256(args.phase1),
        "design_sha256": file_sha256(args.design),
        "management_contract": (
            "entry restrictions do not disable opposite-direction technical exits"
        ),
        "restrictions": list(design["restrictions"]),
    }
    (args.out / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "study_id": decision["study_id"],
        "source": {
            "path": str(args.nq.resolve()),
            "sha256": file_sha256(args.nq),
            "classification": NQ_SPEC.source_classification,
        },
        "phase1": {
            "path": str(args.phase1.resolve()),
            "sha256": file_sha256(args.phase1),
        },
        "design": {
            "path": str(args.design.resolve()),
            "sha256": file_sha256(args.design),
            "payload": design,
        },
        "configs": [asdict(configs[arm_id]) for arm_id in candidate_ids],
    }
    (args.out / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(summary_frame.to_string(index=False))
    print(gates_frame.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
