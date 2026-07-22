# ruff: noqa
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit
from numba.typed import List


@njit(cache=True)
def simulate(returns_r, blocks, iterations, seed, risks):
    np.random.seed(seed)
    number_of_blocks = len(blocks)
    maximum_block = 0
    for block in blocks:
        maximum_block = max(maximum_block, len(block))
    sequence = np.empty(number_of_blocks * maximum_block)
    finals = np.empty((len(risks), iterations))
    drawdowns = np.empty((len(risks), iterations))
    for iteration in range(iterations):
        length = 0
        for _ in range(number_of_blocks):
            block = blocks[np.random.randint(0, number_of_blocks)]
            for position in block:
                sequence[length] = returns_r[position]
                length += 1
        for risk_index in range(len(risks)):
            equity = 100000.0
            peak = equity
            maximum_drawdown = 0.0
            for index in range(length):
                equity *= 1.0 + risks[risk_index] * sequence[index]
                peak = max(peak, equity)
                maximum_drawdown = max(maximum_drawdown, 1.0 - equity / peak)
            finals[risk_index, iteration] = equity
            drawdowns[risk_index, iteration] = maximum_drawdown
    return finals, drawdowns


def make_blocks(frame: pd.DataFrame, column: str):
    result = List()
    for _, group in frame.groupby(column, sort=True):
        result.append(group.index.to_numpy(dtype=np.int64))
    return result


def historical(returns_r: np.ndarray, risk: float) -> tuple[float, float]:
    equity = 100000.0 * np.cumprod(1.0 + risk * returns_r)
    full = np.r_[100000.0, equity]
    peak = np.maximum.accumulate(full)
    return float(full[-1]), float(np.max(1.0 - full / peak))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.trades).sort_values(["entry_time", "signal_id"]).reset_index(drop=True)
    frame["entry_time"] = pd.to_datetime(frame["entry_time"])
    frame["eth_market_date"] = pd.to_datetime(frame["eth_market_date"])
    frame["month"] = frame["entry_time"].dt.to_period("M").astype(str)
    base = frame["pnl_r"].to_numpy(float)
    risk_points = frame["risk_points"].to_numpy(float)
    if len(frame) != 304 or not np.isclose(base.sum(), 48.93754952687199, atol=1e-9, rtol=0.0):
        raise AssertionError("E6 baseline mismatch")
    scenarios = {
        "NORMAL_1_TICK_EACH_SIDE": base,
        "MODERATE_2_TICKS_EACH_SIDE": base - 0.5 / risk_points,
        "SEVERE_4_TICKS_EACH_SIDE": base - 1.5 / risk_points,
    }
    risks = np.asarray([0.005, 0.01, 0.015])
    published = pd.read_csv(args.published / "historical_summary.csv")
    for scenario, returns_r in scenarios.items():
        for risk in risks:
            final, drawdown = historical(returns_r, risk)
            row = published[(published.cost_scenario == scenario) & np.isclose(published.risk_fraction, risk)].iloc[0]
            if not np.isclose(final, row.final_equity_usd, atol=1e-6, rtol=0.0):
                raise AssertionError("Historical final equity mismatch")
            if not np.isclose(drawdown, row.maximum_drawdown_pct, atol=1e-10, rtol=0.0):
                raise AssertionError("Historical drawdown mismatch")
    date_blocks = make_blocks(frame, "eth_market_date")
    month_blocks = make_blocks(frame, "month")
    rows = []
    for scenario_index, (scenario, returns_r) in enumerate(scenarios.items()):
        for method, blocks, seed in (
            ("DATE_BLOCK", date_blocks, 20260922 + scenario_index * 1000),
            ("MONTH_BLOCK", month_blocks, 20261022 + scenario_index * 1000),
        ):
            finals, drawdowns = simulate(returns_r, blocks, 10000, seed, risks)
            for risk_index, risk in enumerate(risks):
                rows.append({
                    "method": method,
                    "cost_scenario": scenario,
                    "risk_fraction": risk,
                    "final_p05": float(np.quantile(finals[risk_index], 0.05)),
                    "final_p50": float(np.quantile(finals[risk_index], 0.50)),
                    "dd_p95": float(np.quantile(drawdowns[risk_index], 0.95)),
                    "p_loss": float(np.mean(finals[risk_index] < 100000.0)),
                    "p_dd20": float(np.mean(drawdowns[risk_index] >= 0.20)),
                    "p_dd30": float(np.mean(drawdowns[risk_index] >= 0.30)),
                })
    independent = pd.DataFrame(rows)
    normal_05 = independent[(independent.cost_scenario == "NORMAL_1_TICK_EACH_SIDE") & np.isclose(independent.risk_fraction, 0.005)]
    normal_10 = independent[(independent.cost_scenario == "NORMAL_1_TICK_EACH_SIDE") & np.isclose(independent.risk_fraction, 0.01)]
    severe_10 = independent[(independent.cost_scenario == "SEVERE_4_TICKS_EACH_SIDE") & np.isclose(independent.risk_fraction, 0.01)]
    severe_15 = independent[(independent.cost_scenario == "SEVERE_4_TICKS_EACH_SIDE") & np.isclose(independent.risk_fraction, 0.015)]
    if not ((normal_05.p_loss < 0.03).all() and (normal_05.p_dd20 < 0.01).all()):
        raise AssertionError("0.5% conclusion changed")
    if not ((normal_10.final_p05 > 100000).all() and (normal_10.dd_p95 > 0.15).all()):
        raise AssertionError("1.0% normal conclusion changed")
    if not ((severe_10.p_loss > 0.04).all() and (severe_10.dd_p95 > 0.20).all()):
        raise AssertionError("1.0% severe conclusion changed")
    if not ((severe_15.p_dd20 > 0.35).all() and (severe_15.p_dd30 > 0.05).all()):
        raise AssertionError("1.5% severe conclusion changed")
    independent.to_csv(args.output / "independent_bootstrap.csv", index=False)
    review = {
        "decision": "INDEPENDENT_REVIEW_PASS",
        "baseline_exact": True,
        "cost_adjustments_exact": True,
        "historical_paths_exact": True,
        "independent_iterations_per_method_scenario": 10000,
        "no_sizing_authorization": True,
    }
    (args.output / "independent_review.json").write_text(json.dumps(review, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
