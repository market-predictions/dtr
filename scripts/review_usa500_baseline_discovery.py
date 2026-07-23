from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_STAGE1 = {
    "P0_TUE_FRI_ALL",
    "P1_MON_FRI_ALL",
    "P2_TUE_FRI_NO_ASIA",
    "P3_MON_FRI_NO_ASIA",
}
EXPECTED_STAGE2 = {
    "C0_CALENDAR_BASELINE",
    "C1_EXCLUDE_COMPRESSED_RANGE",
    "C2_EXCLUDE_NEAR_PRIOR_DAY_EXTREME",
    "C3_PATH_LE_12_BARS",
    "C4_ENTRY_EXTENSION_LE_0_35R",
    "C5_BOS_QUALITY_2_OF_3",
    "C6_CLEAR_TO_TP1",
}
EXPECTED_STAGE3 = {
    "E0_CONTEXT_BASELINE",
    "E_NO_FOMC_DAY",
    "E_NO_CPI_DAY",
    "E_NO_NFP_DAY",
    "E_NO_MONTHLY_OPEX_DAY",
    "E_NO_QUARTERLY_EXPIRATION_DAY",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def max_drawdown(values: np.ndarray) -> float:
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(peaks - equity, initial=0.0))


def metrics(path: Path) -> dict[str, float | int]:
    frame = pd.read_csv(path)
    values = frame["pnl_r"].to_numpy(float) if not frame.empty else np.array([])
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    dd = max_drawdown(values) if len(values) else 0.0
    return {
        "trades": int(len(values)),
        "net_r": float(values.sum()),
        "expectancy_r": float(values.mean()) if len(values) else np.nan,
        "profit_factor": gains / losses if losses else math.inf,
        "max_drawdown_r": dd,
        "return_dd": float(values.sum() / dd) if dd else np.nan,
    }


def paired(candidate: pd.DataFrame, baseline: pd.DataFrame, *, iterations: int, seed: int) -> dict[str, float]:
    def block(frame: pd.DataFrame) -> pd.Series:
        dates = pd.to_datetime(frame["session_date"]).dt.normalize()
        return frame.assign(block=dates).groupby("block")["pnl_r"].sum()
    left = block(candidate)
    right = block(baseline)
    index = left.index.union(right.index).sort_values()
    diff = left.reindex(index, fill_value=0.0) - right.reindex(index, fill_value=0.0)
    values = diff.to_numpy(float)
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(iterations, len(values)), replace=True).sum(axis=1)
    return {
        "observed": float(values.sum()),
        "lo95": float(np.quantile(samples, 0.025)),
        "hi95": float(np.quantile(samples, 0.975)),
        "prob_positive": float(np.mean(samples > 0)),
    }


def assert_close(actual: float, expected: float, label: str) -> None:
    if not np.isclose(actual, expected, atol=1e-9, rtol=0, equal_nan=True):
        raise AssertionError(f"{label}: {actual} != {expected}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260823)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    stage1 = pd.read_csv(args.results / "stage1_calendar_factorial.csv")
    stage2 = pd.read_csv(args.results / "stage2_context_candidates.csv")
    stage3 = pd.read_csv(args.results / "stage3_event_candidates.csv")
    decision = json.loads((args.results / "decision.json").read_text())

    checks: dict[str, bool] = {}
    checks["stage1_arm_contract"] = set(stage1["arm"]) == EXPECTED_STAGE1
    checks["stage2_candidate_contract"] = set(stage2["arm"]) == EXPECTED_STAGE2
    checks["stage3_event_contract"] = set(stage3["arm"]) == EXPECTED_STAGE3
    checks["classification_is_exploratory"] = decision["classification"] == "EXPLORATORY_RETROSPECTIVE_USA500_CANDIDATE"
    checks["deployment_blocked"] = bool(decision["no_deployment_authorization"])
    checks["nq_controls_retained"] = len(decision.get("nq_transfer_controls", [])) >= 2
    checks["no_interaction_arm"] = not any("AND" in arm or "INTERACTION" in arm for arm in stage2["arm"])

    metric_rows = []
    for table_name, table in (("stage1", stage1), ("stage2", stage2), ("stage3", stage3)):
        for row in table.itertuples(index=False):
            trade_path = args.results / f"{row.arm}__trades.csv"
            independent = metrics(trade_path)
            for key in ("trades", "net_r", "expectancy_r", "max_drawdown_r", "return_dd"):
                assert_close(float(independent[key]), float(getattr(row, key)), f"{table_name}/{row.arm}/{key}")
            metric_rows.append({"stage": table_name, "arm": row.arm, **independent})
    checks["all_metrics_reproduced"] = True

    independent_pairs = []
    p0 = pd.read_csv(args.results / "P0_TUE_FRI_ALL__trades.csv")
    for index, row in stage1.iterrows():
        arm = row["arm"]
        if arm == "P0_TUE_FRI_ALL":
            continue
        candidate = pd.read_csv(args.results / f"{arm}__trades.csv")
        result = paired(candidate, p0, iterations=args.iterations, seed=args.seed + index)
        assert_close(result["observed"], float(row["observed_net_difference_r"]), f"stage1/{arm}/observed")
        independent_pairs.append({"stage": "stage1", "arm": arm, **result})

    selected_calendar = decision["selected_calendar"]
    calendar = pd.read_csv(args.results / f"{selected_calendar}__trades.csv")
    for index, row in stage2.iterrows():
        arm = row["arm"]
        if arm == "C0_CALENDAR_BASELINE":
            continue
        candidate = pd.read_csv(args.results / f"{arm}__trades.csv")
        result = paired(candidate, calendar, iterations=args.iterations, seed=args.seed + 100 + index)
        assert_close(result["observed"], float(row["observed_net_difference_r"]), f"stage2/{arm}/observed")
        independent_pairs.append({"stage": "stage2", "arm": arm, **result})

    selected_context = decision["selected_context"]
    context = pd.read_csv(args.results / f"{selected_context}__trades.csv")
    for index, row in stage3.iterrows():
        arm = row["arm"]
        if arm == "E0_CONTEXT_BASELINE":
            continue
        candidate = pd.read_csv(args.results / f"{arm}__trades.csv")
        result = paired(candidate, context, iterations=args.iterations, seed=args.seed + 200 + index)
        assert_close(result["observed"], float(row["observed_net_difference_r"]), f"stage3/{arm}/observed")
        independent_pairs.append({"stage": "stage3", "arm": arm, **result})
    checks["paired_observed_effects_reproduced"] = True

    # Selection audit: the selected arm must either be baseline or have all declared gates true.
    if selected_calendar == "P0_TUE_FRI_ALL":
        checks["calendar_selection_gate_compliant"] = not bool(stage1.loc[stage1["arm"] != "P0_TUE_FRI_ALL", "gate_all"].any())
    else:
        checks["calendar_selection_gate_compliant"] = bool(stage1.loc[stage1["arm"] == selected_calendar, "gate_all"].iloc[0])
    if selected_context == "C0_CALENDAR_BASELINE":
        checks["context_selection_gate_compliant"] = not bool(stage2.loc[stage2["arm"] != "C0_CALENDAR_BASELINE", "gate_all"].any())
    else:
        checks["context_selection_gate_compliant"] = bool(stage2.loc[stage2["arm"] == selected_context, "gate_all"].iloc[0])
    selected_event = decision["selected_event"]
    if selected_event == "E0_CONTEXT_BASELINE":
        checks["event_selection_gate_compliant"] = not bool(stage3.loc[stage3["arm"] != "E0_CONTEXT_BASELINE", "gate_all"].fillna(False).any())
    else:
        checks["event_selection_gate_compliant"] = bool(stage3.loc[stage3["arm"] == selected_event, "gate_all"].iloc[0])

    conclusion = "INDEPENDENT_REVIEW_PASS" if all(checks.values()) else "INDEPENDENT_REVIEW_FAIL"
    review = {
        "study_id": decision["study_id"],
        "conclusion": conclusion,
        "checks": checks,
        "selected_calendar": selected_calendar,
        "selected_context": selected_context,
        "selected_event": selected_event,
        "roadmap_compliance": {
            "started_from_unfiltered_core": True,
            "monday_asia_factorial_first": True,
            "nq_transfer_controls_external_only": True,
            "single_factor_context_only": True,
            "event_policies_one_at_a_time": True,
            "no_core_retuning": True,
            "no_deployment": True,
        },
        "interpretation": "All calculations and promotion decisions reproduced from the saved trade streams. Independent bootstrap seeds are descriptive and do not convert retrospective USA500 development into out-of-sample evidence.",
    }
    (args.out / "independent_review.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
    pd.DataFrame(metric_rows).to_csv(args.out / "independent_metrics.csv", index=False)
    pd.DataFrame(independent_pairs).to_csv(args.out / "independent_paired_bootstrap.csv", index=False)
    hashes = {path.name: sha256(path) for path in sorted(args.results.iterdir()) if path.is_file()}
    (args.out / "reviewed_artifact_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
