from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.research import (
    build_session_table,
    load_manifest,
    load_zip,
    resample_5m,
    run_backtest,
    verify_dataset,
)
from dtr_lab.research.engine import metrics
from dtr_lab.research.manifest import file_sha256
from dtr_lab.research.uncertainty import (
    block_bootstrap_mean,
    sign_flip_p_value,
    trade_bootstrap_mean,
)
from dtr_lab.research.validity import (
    attach_roll_market_dates,
    compare_trade_sets,
    quarterly_roll_candidates,
    leave_one_group_out,
    rollover_discontinuity_diagnostics,
    rollover_stress,
    rollover_trade_attribution,
    session_weekday_attribution,
    timestamp_vwap_hypotheses,
)


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NQ baseline validity reset review")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260722)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    dataset_path = verify_dataset(manifest, manifest_path)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)

    one = load_zip(dataset_path)
    bars = resample_5m(one)
    sessions = build_session_table(one, bars)
    config = manifest.strategy_config()

    runs: dict[str, tuple[pd.DataFrame, object]] = {}
    rows: list[dict[str, object]] = []
    for policy in ("observe_only", "reject_unsafe", "liquidate_unsafe"):
        trades, funnel = run_backtest(one, bars, sessions, config, gap_policy=policy)
        runs[policy] = (trades, funnel)
        rows.append({"gap_policy": policy, **metrics(trades), **{f"funnel_{k}": v for k, v in funnel.as_dict().items()}})
    comparison = pd.DataFrame(rows)
    comparison.to_csv(output / "baseline_policy_comparison.csv", index=False)

    observe = runs["observe_only"][0]
    legacy = runs["reject_unsafe"][0]
    causal = runs["liquidate_unsafe"][0]
    gap_liquidations = causal[causal["exit_reason"] == "GAP_LIQUIDATION"].copy()
    gap_liquidations.to_csv(output / "gap_liquidations.csv", index=False)

    set_comparisons = {
        "legacy_to_causal": compare_trade_sets(legacy, causal),
        "observe_to_causal": compare_trade_sets(observe, causal),
    }
    with (output / "trade_set_comparison.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_value(set_comparisons), handle, indent=2, sort_keys=True)
        handle.write("\n")

    work = causal.copy()
    work["entry_time"] = pd.to_datetime(work["entry_time"])
    work["month"] = work["entry_time"].dt.to_period("M").astype(str)
    work["session_date_block"] = pd.to_datetime(work["session_date"]).dt.strftime("%Y-%m-%d")
    uncertainty = {
        "trade_bootstrap": trade_bootstrap_mean(
            work["pnl_r"], iterations=args.iterations, seed=args.seed
        ).as_dict(),
        "month_block_bootstrap": block_bootstrap_mean(
            work,
            value_column="pnl_r",
            block_column="month",
            iterations=args.iterations,
            seed=args.seed + 1,
        ).as_dict(),
        "session_date_block_bootstrap": block_bootstrap_mean(
            work,
            value_column="pnl_r",
            block_column="session_date_block",
            iterations=args.iterations,
            seed=args.seed + 2,
        ).as_dict(),
        "sign_flip_one_sided_p": sign_flip_p_value(
            work["pnl_r"], iterations=max(100_000, args.iterations), seed=args.seed + 3
        ),
        "multiple_testing_status": "UNRESOLVED_NO_ALIGNED_904_CANDIDATE_RETURN_MATRIX",
    }
    with (output / "baseline_uncertainty.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_value(uncertainty), handle, indent=2, sort_keys=True)
        handle.write("\n")

    session_weekday_attribution(causal).to_csv(
        output / "session_weekday_attribution.csv", index=False
    )
    leave_one_group_out(causal, ["session", "day_of_week"]).to_csv(
        output / "leave_one_cell_out.csv", index=False
    )
    leave_one_group_out(causal, ["session"]).to_csv(
        output / "leave_one_session_out.csv", index=False
    )
    leave_one_group_out(causal, ["day_of_week"]).to_csv(
        output / "leave_one_weekday_out.csv", index=False
    )

    vwap_hypotheses, timestamp_conclusion = timestamp_vwap_hypotheses(one)
    vwap_hypotheses.to_csv(output / "timestamp_vwap_hypotheses.csv", index=False)
    with (output / "timestamp_conclusion.json").open("w", encoding="utf-8") as handle:
        json.dump(timestamp_conclusion.as_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")

    raw_candidates = quarterly_roll_candidates(one["timestamp"].min(), one["timestamp"].max())
    market_dates = pd.to_datetime(one["timestamp"]).dt.normalize().unique()
    roll_candidates = attach_roll_market_dates(raw_candidates, market_dates)
    roll_candidates.to_csv(output / "rollover_candidates.csv", index=False)
    rollover_stress(causal, roll_candidates, market_dates).to_csv(
        output / "rollover_stress.csv", index=False
    )
    rollover_discontinuity_diagnostics(one, roll_candidates).to_csv(
        output / "rollover_discontinuity_diagnostics.csv", index=False
    )
    rollover_trade_attribution(causal, roll_candidates).to_csv(
        output / "rollover_trade_attribution.csv", index=False
    )

    walk_forward_path = Path("results/2026-07-21/rolling_walk_forward.csv")
    walk_forward = pd.read_csv(walk_forward_path)
    walk_forward_summary = {
        "folds": int(len(walk_forward)),
        "test_trades": int(walk_forward["test_trades"].sum()),
        "test_net_r": float(walk_forward["test_net_r"].sum()),
        "test_expectancy_r": float(
            walk_forward["test_net_r"].sum() / walk_forward["test_trades"].sum()
        ),
        "selected_config_count": int(walk_forward["selected"].nunique()),
        "weak_fold_count_below_0_06R": int((walk_forward["test_expectancy_r"] < 0.06).sum()),
        "status": "HISTORICAL_PROCEDURE_EVIDENCE_NOT_PRISTINE_HOLDOUT",
    }

    summary = {
        "schema_version": 1,
        "decision": "CONTINUE_RESEARCH_DO_NOT_DEPLOY",
        "dataset_sha256": file_sha256(dataset_path),
        "manifest_sha256": file_sha256(manifest_path),
        "corrected_baseline": metrics(causal),
        "historical_observe": metrics(observe),
        "historical_retrospective_reject": metrics(legacy),
        "gap_liquidations": int(len(gap_liquidations)),
        "trade_set_comparisons": set_comparisons,
        "timestamp": timestamp_conclusion.as_dict(),
        "uncertainty": uncertainty,
        "walk_forward": walk_forward_summary,
        "rollover_status": "SENSITIVITY_ONLY_CONTRACT_METADATA_UNRESOLVED",
        "restrictions": [
            "no deployment",
            "no Pine strategy port",
            "no fresh-data inspection before preregistration",
            "no module retuning during corrected-baseline reruns",
        ],
    }
    with (output / "baseline_validity_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_value(summary), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(_json_value(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
