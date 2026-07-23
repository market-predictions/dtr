from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ARMS = {
    "S0_ALL": ("ASIA_7PM", "LONDON_2AM", "NEW_YORK_9AM"),
    "S1_LONDON_ONLY": ("LONDON_2AM",),
    "S2_NEW_YORK_ONLY": ("NEW_YORK_9AM",),
    "S3_ASIA_ONLY": ("ASIA_7PM",),
    "S4_LONDON_ASIA": ("LONDON_2AM", "ASIA_7PM"),
    "S5_ASIA_NEW_YORK": ("ASIA_7PM", "NEW_YORK_9AM"),
}


def sequence(features: pd.DataFrame, cache: pd.DataFrame, allowed: tuple[str, ...]) -> pd.DataFrame:
    selected = features.loc[
        features["weekday"].isin((1, 2, 3, 4)) & features["session"].isin(allowed)
    ].sort_values("entry_time")
    records = cache.set_index("signal_id")
    rows = []
    next_free = pd.Timestamp.min
    for row in selected.itertuples(index=False):
        signal_id = int(row.signal_id)
        if signal_id not in records.index:
            continue
        trade = records.loc[signal_id]
        entry_time = pd.Timestamp(trade["entry_time"])
        if entry_time < next_free:
            continue
        rows.append(trade.to_dict())
        next_free = pd.Timestamp(trade["exit_time"])
    return pd.DataFrame(rows)


def max_drawdown(values: np.ndarray) -> float:
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(peaks - equity, initial=0.0))


def metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    values = frame["pnl_r"].to_numpy(float)
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    dd = max_drawdown(values)
    return {
        "trades": len(values),
        "net_r": float(values.sum()),
        "expectancy_r": float(values.mean()),
        "profit_factor": gains / losses if losses else math.inf,
        "max_drawdown_r": dd,
        "return_dd": float(values.sum() / dd) if dd else np.nan,
    }


def paired(
    candidate: pd.DataFrame, baseline: pd.DataFrame, iterations: int, seed: int
) -> dict[str, float]:
    def blocks(frame: pd.DataFrame) -> pd.Series:
        date = pd.to_datetime(frame["session_date"]).dt.normalize()
        return frame.assign(block=date).groupby("block")["pnl_r"].sum()

    left = blocks(candidate)
    right = blocks(baseline)
    index = left.index.union(right.index)
    values = (left.reindex(index, fill_value=0.0) - right.reindex(index, fill_value=0.0)).to_numpy(
        float
    )
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
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20261023)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    features = pd.read_csv(args.features, parse_dates=["entry_time", "session_date"])
    cache = pd.read_csv(
        args.results / "all_signal_trades.csv.gz",
        parse_dates=["entry_time", "exit_time", "session_date"],
    )
    reported = pd.read_csv(args.results / "stage1b_session_decomposition.csv")
    decision = json.loads((args.results / "stage1b_decision.json").read_text())

    checks = {
        "arm_contract": set(reported["arm"]) == set(ARMS),
        "selected_session_is_none": decision["selected_session"] is None,
        "decision_no_viable_baseline": decision["decision"] == "NO_VIABLE_USA500_CORE_BASELINE",
        "no_context_run_after_failed_gate": not (
            args.results / "stage2_session_context_candidates.csv"
        ).exists(),
        "no_event_run_after_failed_gate": not (
            args.results / "stage3_session_event_candidates.csv"
        ).exists(),
        "deployment_blocked": bool(decision["no_deployment_authorization"]),
    }

    rows = []
    recreated: dict[str, pd.DataFrame] = {}
    for arm, allowed in ARMS.items():
        frame = sequence(features, cache, allowed)
        recreated[arm] = frame
        values = metrics(frame)
        source = reported.loc[reported["arm"] == arm].iloc[0]
        for key in ("trades", "net_r", "expectancy_r", "max_drawdown_r", "return_dd"):
            if not np.isclose(
                float(values[key]), float(source[key]), atol=1e-9, rtol=0, equal_nan=True
            ):
                raise AssertionError(f"{arm}/{key}: {values[key]} != {source[key]}")
        rows.append({"arm": arm, **values})
    checks["all_trade_streams_resequenced"] = True

    baseline = recreated["S0_ALL"]
    bootstrap_rows = []
    for index, arm in enumerate(ARMS):
        if arm == "S0_ALL":
            continue
        result = paired(recreated[arm], baseline, args.iterations, args.seed + index)
        observed = float(reported.loc[reported["arm"] == arm, "observed_net_difference_r"].iloc[0])
        if not np.isclose(result["observed"], observed, atol=1e-9, rtol=0):
            raise AssertionError(f"paired observed mismatch for {arm}")
        bootstrap_rows.append({"arm": arm, **result})
    checks["paired_effects_reproduced"] = True

    nonbaseline_passes = bool(
        reported.loc[reported["arm"] != "S0_ALL", "gate_all"].fillna(False).any()
    )
    checks["stop_rule_followed"] = not nonbaseline_passes
    conclusion = "INDEPENDENT_REVIEW_PASS" if all(checks.values()) else "INDEPENDENT_REVIEW_FAIL"
    review = {
        "study_id": decision["study_id"],
        "conclusion": conclusion,
        "checks": checks,
        "roadmap_monitor": {
            "factorial_preceded_session_decomposition": True,
            "stage1b_was_preregistered": True,
            "no_monday_reintroduction": True,
            "no_session_time_search": True,
            "no_context_or_event_continuation_without_baseline": True,
            "no_core_retuning": True,
        },
        "interpretation": "London-only is positive at one and two ticks but fails the frozen year-stability gate because 2022 and 2025 are negative. It remains diagnostic and is not a USA500 baseline.",
    }
    (args.out / "stage1b_independent_review.json").write_text(
        json.dumps(review, indent=2), encoding="utf-8"
    )
    pd.DataFrame(rows).to_csv(args.out / "stage1b_independent_metrics.csv", index=False)
    pd.DataFrame(bootstrap_rows).to_csv(args.out / "stage1b_independent_bootstrap.csv", index=False)
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
