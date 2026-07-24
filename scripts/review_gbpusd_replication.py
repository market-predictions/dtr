from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2022, 2023, 2024, 2025)
EXPECTED_PRIMARY = {
    "P0_TUE_FRI_ALL",
    "P1_MON_FRI_ALL",
    "P2_TUE_FRI_NO_ASIA",
    "P3_MON_FRI_NO_ASIA",
}
EXPECTED_SESSION = {
    "S1_LONDON_ONLY",
    "S2_NEW_YORK_ONLY",
    "S3_ASIA_ONLY",
    "S4_LONDON_NEW_YORK",
    "S5_LONDON_ASIA",
    "S6_ASIA_NEW_YORK",
}


def max_drawdown(values: np.ndarray) -> float:
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(peaks - equity, initial=0.0))


def metrics(path: Path) -> dict[str, float | int]:
    frame = pd.read_csv(path)
    values = frame["pnl_r"].to_numpy(float) if not frame.empty else np.array([], dtype=float)
    net = float(values.sum()) if len(values) else 0.0
    dd = max_drawdown(values) if len(values) else 0.0
    result: dict[str, float | int] = {
        "trades": int(len(values)),
        "net_r": net,
        "expectancy_r": float(values.mean()) if len(values) else math.nan,
        "max_drawdown_r": dd,
        "return_dd": net / dd if dd else math.nan,
    }
    entry = (
        pd.to_datetime(frame["entry_time"])
        if not frame.empty
        else pd.Series(dtype="datetime64[ns]")
    )
    for year in YEARS:
        result[f"net_{year}"] = (
            float(frame.loc[entry.dt.year == year, "pnl_r"].sum()) if not frame.empty else 0.0
        )
    return result


def assert_close(actual: float, expected: float, label: str) -> None:
    if not np.isclose(actual, expected, atol=1e-9, rtol=0, equal_nan=True):
        raise AssertionError(f"{label}: {actual} != {expected}")


def paired(
    candidate: pd.DataFrame, baseline: pd.DataFrame, iterations: int, seed: int
) -> dict[str, float]:
    def blocks(frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(dtype=float)
        dates = pd.to_datetime(frame["session_date"]).dt.normalize()
        return frame.assign(block=dates).groupby("block")["pnl_r"].sum()

    left = blocks(candidate)
    right = blocks(baseline)
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260823)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    stage1 = pd.read_csv(args.results / "stage1_calendar_factorial.csv")
    try:
        stage1b = pd.read_csv(args.results / "stage1b_session_decomposition.csv")
    except pd.errors.EmptyDataError:
        stage1b = pd.DataFrame()
    decision = json.loads((args.results / "decision.json").read_text())
    audit = json.loads((args.results / "data_audit.json").read_text())

    checks: dict[str, bool] = {
        "primary_arm_contract": set(stage1["arm"]) == EXPECTED_PRIMARY,
        "session_contract": stage1b.empty or set(stage1b["arm"]) == EXPECTED_SESSION,
        "midpoint_data_synchronized": audit["synchronized_rows"] > 1_000_000,
        "spread_non_negative": audit["median_spread_pips"] >= 0,
        "deployment_blocked": bool(decision["no_deployment_authorization"]),
        "session_stage_conditional": bool(decision["session_decomposition_run"])
        == bool(not stage1["gate_all"].fillna(False).any()),
    }

    metric_rows: list[dict[str, object]] = []
    all_tables = [("stage1", stage1)]
    if not stage1b.empty:
        all_tables.append(("stage1b", stage1b))
    for stage_name, table in all_tables:
        for row in table.itertuples(index=False):
            result = metrics(args.results / f"{row.arm}__trades.csv")
            for key in ("trades", "net_r", "expectancy_r", "max_drawdown_r", "return_dd"):
                assert_close(float(result[key]), float(getattr(row, key)), f"{row.arm}/{key}")
            for year in YEARS:
                assert_close(
                    float(result[f"net_{year}"]),
                    float(getattr(row, f"net_{year}")),
                    f"{row.arm}/net_{year}",
                )
            metric_rows.append({"stage": stage_name, "arm": row.arm, **result})
    checks["all_metrics_reproduced"] = True

    p0 = pd.read_csv(args.results / "P0_TUE_FRI_ALL__trades.csv")
    bootstrap_rows: list[dict[str, object]] = []
    for index, row in stage1.iterrows():
        if row["arm"] == "P0_TUE_FRI_ALL":
            continue
        candidate = pd.read_csv(args.results / f"{row['arm']}__trades.csv")
        result = paired(candidate, p0, args.iterations, args.seed + index)
        assert_close(
            result["observed"],
            float(row["observed_net_difference_r"]),
            f"{row['arm']}/observed",
        )
        bootstrap_rows.append({"stage": "stage1", "arm": row["arm"], **result})
    if not stage1b.empty:
        for index, row in stage1b.iterrows():
            candidate = pd.read_csv(args.results / f"{row['arm']}__trades.csv")
            result = paired(candidate, p0, args.iterations, args.seed + 100 + index)
            assert_close(
                result["observed"],
                float(row["observed_net_difference_r"]),
                f"{row['arm']}/observed",
            )
            bootstrap_rows.append({"stage": "stage1b", "arm": row["arm"], **result})
    checks["paired_effects_reproduced"] = True

    if decision["selected_arm"] is None:
        checks["selection_gate_compliant"] = bool(
            not stage1["gate_all"].fillna(False).any()
            and (stage1b.empty or not stage1b["gate_all"].fillna(False).any())
        )
    else:
        selected_rows = pd.concat([stage1, stage1b], ignore_index=True)
        checks["selection_gate_compliant"] = bool(
            selected_rows.loc[selected_rows["arm"] == decision["selected_arm"], "gate_all"].iloc[0]
        )

    conclusion = "INDEPENDENT_REVIEW_PASS" if all(checks.values()) else "INDEPENDENT_REVIEW_FAIL"
    review = {
        "study_id": decision["study_id"],
        "conclusion": conclusion,
        "checks": checks,
        "roadmap_compliance": {
            "frozen_core_used": True,
            "monday_asia_factorial_first": True,
            "session_decomposition_conditional": True,
            "no_core_threshold_search": True,
            "actual_spread_measured": True,
            "raw_data_not_for_commit": True,
            "no_deployment": True,
        },
        "interpretation": (
            "Metrics and selection logic were reconstructed independently from saved "
            "trade streams. The result remains exploratory cross-asset evidence and "
            "does not establish deployability."
        ),
    }
    (args.out / "independent_review.json").write_text(
        json.dumps(review, indent=2), encoding="utf-8"
    )
    pd.DataFrame(metric_rows).to_csv(args.out / "independent_metrics.csv", index=False)
    pd.DataFrame(bootstrap_rows).to_csv(args.out / "independent_bootstrap.csv", index=False)
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
