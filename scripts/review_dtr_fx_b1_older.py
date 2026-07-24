from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260723
ARM = "FX_B1_PREVDAY_LONDON_BOS_MID"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def profit_factor(values: np.ndarray) -> float:
    gain = float(values[values > 0].sum())
    loss = float(-values[values < 0].sum())
    if loss > 0:
        return gain / loss
    if gain > 0:
        return math.inf
    return math.nan


def max_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(peak - equity))


def block_ci(trades: pd.DataFrame, iterations: int) -> dict[str, float]:
    blocks = [
        group["pnl_r"].to_numpy(float)
        for _, group in trades.groupby(pd.to_datetime(trades["day"]).dt.normalize())
    ]
    if not blocks:
        return {"ci_lo": math.nan, "ci_hi": math.nan, "p_positive": math.nan}
    rng = np.random.default_rng(SEED)
    means = np.empty(iterations)
    for index in range(iterations):
        selected = rng.integers(0, len(blocks), len(blocks))
        means[index] = np.concatenate([blocks[item] for item in selected]).mean()
    return {
        "ci_lo": float(np.quantile(means, 0.025)),
        "ci_hi": float(np.quantile(means, 0.975)),
        "p_positive": float(np.mean(means > 0)),
    }


def recompute(
    trades: pd.DataFrame, years: tuple[int, ...], iterations: int
) -> dict[str, object]:
    values = trades["pnl_r"].to_numpy(float)
    result: dict[str, object] = {
        "arm": ARM,
        "trades": int(len(trades)),
        "net_r": float(values.sum()),
        "expectancy_r": float(values.mean()) if len(values) else math.nan,
        "gross_expectancy_r": (
            float(trades["gross_r"].mean()) if len(trades) else math.nan
        ),
        "profit_factor": profit_factor(values),
        "win_rate": float(np.mean(values > 0)) if len(values) else math.nan,
        "max_drawdown_r": max_drawdown(values),
        "stress_1p5x_cost_expectancy_r": float(
            (
                trades["pnl_r"]
                - 0.5 * trades["estimated_cost_pips"] / trades["risk_pips"]
            ).mean()
        )
        if len(trades)
        else math.nan,
    }
    entry_year = pd.to_datetime(trades["entry_time"], utc=True).dt.year
    year_nets: list[float] = []
    for year in years:
        subset = trades.loc[entry_year == year]
        net = float(subset["pnl_r"].sum())
        result[f"trades_{year}"] = int(len(subset))
        result[f"net_{year}"] = net
        result[f"exp_{year}"] = (
            float(subset["pnl_r"].mean()) if len(subset) else math.nan
        )
        year_nets.append(net)
    positive_years = sum(value > 0 for value in year_nets)
    positive_total = sum(value for value in year_nets if value > 0)
    result["positive_years"] = positive_years
    result["single_year_positive_share"] = (
        max(year_nets) / positive_total if positive_total > 0 else math.inf
    )
    result.update(block_ci(trades, iterations))

    if years == tuple(range(2015, 2022)):
        primary = trades.loc[entry_year.isin(range(2015, 2020))]
        crisis = trades.loc[entry_year.isin([2020, 2021])]
        result["primary_2015_2019_expectancy_r"] = (
            float(primary["pnl_r"].mean()) if len(primary) else math.nan
        )
        result["crisis_2020_2021_expectancy_r"] = (
            float(crisis["pnl_r"].mean()) if len(crisis) else math.nan
        )
        gates = {
            "gate_combined_expectancy": result["expectancy_r"] > 0,
            "gate_cost_stress": result["stress_1p5x_cost_expectancy_r"] > 0,
            "gate_primary": result["primary_2015_2019_expectancy_r"] > 0,
            "gate_crisis": result["crisis_2020_2021_expectancy_r"] > 0,
            "gate_positive_years": positive_years >= 4,
            "gate_concentration": result["single_year_positive_share"] <= 0.60,
        }
        result.update(gates)
        result["hard_stop_passed"] = all(gates.values())
        result["gate_ci"] = result["ci_lo"] > 0
    return result


def equal_value(left: object, right: object, tolerance: float = 1e-12) -> bool:
    if isinstance(left, (bool, np.bool_)) or isinstance(right, (bool, np.bool_)):
        return bool(left) == bool(right)
    try:
        left_float = float(left)
        right_float = float(right)
    except (TypeError, ValueError):
        return str(left) == str(right)
    if math.isnan(left_float) and math.isnan(right_float):
        return True
    if math.isinf(left_float) or math.isinf(right_float):
        return left_float == right_float
    return math.isclose(left_float, right_float, rel_tol=tolerance, abs_tol=tolerance)


def expected_decision(metrics: dict[str, object], years: tuple[int, ...]) -> str:
    if years != tuple(range(2015, 2022)):
        return "REGRESSION_ONLY"
    if not bool(metrics["hard_stop_passed"]):
        return "REJECT_B1_ON_OLDER_HISTORY"
    if bool(metrics["gate_ci"]):
        return "OLDER_HISTORY_SUPPORTS_PROSPECTIVE_2026_MONITORING"
    return "OLDER_HISTORY_POSITIVE_BUT_UNCERTAIN_NO_PROMOTION"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--expected-runner-sha256", required=True)
    parser.add_argument("--source-qualification", type=Path, required=True)
    args = parser.parse_args()

    years = tuple(range(args.start_year, args.end_year + 1))
    trades_path = args.results / f"{ARM}__trades.csv"
    summary_path = args.results / "dtr_fx_b1_summary.csv"
    decision_path = args.results / "decision.json"
    trades = pd.read_csv(trades_path)
    reported = pd.read_csv(summary_path).iloc[0].to_dict()
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    qualification = json.loads(args.source_qualification.read_text(encoding="utf-8"))

    reconstructed = recompute(trades, years, args.iterations)
    mismatches = {
        key: {"reported": reported.get(key), "reconstructed": value}
        for key, value in reconstructed.items()
        if key not in reported or not equal_value(reported[key], value)
    }
    runner_sha = sha256(args.runner)
    expected = expected_decision(reconstructed, years)
    checks = {
        "runner_hash_matches": runner_sha == args.expected_runner_sha256,
        "source_qualified": bool(qualification.get("qualified")),
        "summary_parity": not mismatches,
        "decision_parity": decision.get("decision") == expected,
        "years_match": decision.get("years") == list(years),
        "deployment_block_retained": bool(
            decision.get("no_pine_sizing_or_deployment_authorization")
        ),
    }
    review = {
        "study_id": "DTR-FX-WP-20260724-23",
        "review_type": "independent_trade_ledger_reconstruction",
        "runner_sha256": runner_sha,
        "trade_ledger_sha256": sha256(trades_path),
        "source_qualification_sha256": sha256(args.source_qualification),
        "reconstructed_metrics": reconstructed,
        "reported_decision": decision.get("decision"),
        "reconstructed_decision": expected,
        "mismatches": mismatches,
        "checks": checks,
        "conclusion": "PASS" if all(checks.values()) else "FAIL",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(review, indent=2), encoding="utf-8")
    if review["conclusion"] != "PASS":
        raise SystemExit("independent B1 older-history review failed")


if __name__ == "__main__":
    main()
