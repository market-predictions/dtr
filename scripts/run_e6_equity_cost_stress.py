# ruff: noqa
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit
from numba.typed import List as NumbaList

EXPECTED = (304, 48.93754952687199, 0.16097878133839472, 8.632571354238342)


def max_drawdown_r(values: np.ndarray) -> float:
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(peak - equity, initial=0.0))


def longest_run(mask: np.ndarray) -> int:
    best = current = 0
    for item in mask:
        if bool(item):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def historical_metrics(returns_r: np.ndarray, times: pd.Series, start: float, risk: float) -> dict[str, float | int]:
    equity_after = start * np.cumprod(1.0 + risk * returns_r)
    equity = np.r_[start, equity_after]
    peaks = np.maximum.accumulate(equity)
    drawdowns = 1.0 - equity / peaks
    max_index = int(np.argmax(drawdowns))
    dates = pd.to_datetime(times).reset_index(drop=True)
    peak_equity = start
    peak_date = dates.iloc[0]
    in_drawdown = False
    drawdown_start = peak_date
    maximum_days = 0
    for index, value in enumerate(equity_after):
        date = dates.iloc[index]
        if value >= peak_equity - 1e-9:
            if in_drawdown:
                maximum_days = max(maximum_days, int((date - drawdown_start).days))
                in_drawdown = False
            if value > peak_equity:
                peak_equity = float(value)
                peak_date = date
        elif not in_drawdown:
            in_drawdown = True
            drawdown_start = peak_date
    if in_drawdown:
        maximum_days = max(maximum_days, int((dates.iloc[-1] - drawdown_start).days))
    underwater = equity_after < peaks[1:] - 1e-9
    pnl_usd = np.diff(equity)
    return {
        "final_equity_usd": float(equity[-1]),
        "total_return_pct": float(equity[-1] / start - 1.0),
        "maximum_drawdown_pct": float(drawdowns[max_index]),
        "maximum_drawdown_usd": float(peaks[max_index] - equity[max_index]),
        "longest_losing_streak": longest_run(returns_r < 0),
        "maximum_time_under_water_trades": longest_run(underwater),
        "maximum_time_under_water_calendar_days": maximum_days,
        "minimum_equity_usd": float(np.min(equity)),
        "largest_trade_loss_usd": float(np.min(pnl_usd)),
        "largest_trade_gain_usd": float(np.max(pnl_usd)),
    }


@njit(cache=True)
def bootstrap_kernel(returns_r, blocks, iterations, seed, start, risks):
    np.random.seed(seed)
    number_of_blocks = len(blocks)
    maximum_block = 0
    for block in blocks:
        maximum_block = max(maximum_block, len(block))
    sequence = np.empty(number_of_blocks * maximum_block)
    finals = np.empty((len(risks), iterations))
    maximum_drawdowns = np.empty((len(risks), iterations))
    losing_streaks = np.empty(iterations)
    underwater_streaks = np.empty((len(risks), iterations))
    for iteration in range(iterations):
        length = 0
        for _ in range(number_of_blocks):
            block = blocks[np.random.randint(0, number_of_blocks)]
            for position in block:
                sequence[length] = returns_r[position]
                length += 1
        current_loss = 0
        maximum_loss = 0
        for index in range(length):
            if sequence[index] < 0.0:
                current_loss += 1
                maximum_loss = max(maximum_loss, current_loss)
            else:
                current_loss = 0
        losing_streaks[iteration] = maximum_loss
        for risk_index in range(len(risks)):
            equity = start
            peak = start
            maximum_drawdown = 0.0
            current_underwater = 0
            maximum_underwater = 0
            for index in range(length):
                equity *= 1.0 + risks[risk_index] * sequence[index]
                if equity >= peak - 1e-9:
                    peak = max(peak, equity)
                    current_underwater = 0
                else:
                    current_underwater += 1
                    maximum_underwater = max(maximum_underwater, current_underwater)
                    maximum_drawdown = max(maximum_drawdown, 1.0 - equity / peak)
            finals[risk_index, iteration] = equity
            maximum_drawdowns[risk_index, iteration] = maximum_drawdown
            underwater_streaks[risk_index, iteration] = maximum_underwater
    return finals, maximum_drawdowns, losing_streaks, underwater_streaks


def blocks(frame: pd.DataFrame, column: str):
    result = NumbaList()
    for _, group in frame.groupby(column, sort=True):
        result.append(group.index.to_numpy(dtype=np.int64))
    return result


def quantiles(values: np.ndarray, probabilities: list[float]) -> list[float]:
    return [float(value) for value in np.quantile(values, probabilities)]


def warning_labels(final_equity: np.ndarray, maximum_drawdown: np.ndarray, start: float) -> str:
    labels = []
    if float(np.mean(final_equity < start)) >= 0.10:
        labels.append("LOSS_RISK_WATCH")
    if float(np.mean(maximum_drawdown >= 0.10)) >= 0.10:
        labels.append("DD10_WATCH")
    if float(np.mean(maximum_drawdown >= 0.20)) >= 0.05:
        labels.append("DD20_WATCH")
    if float(np.mean(maximum_drawdown >= 0.30)) >= 0.01:
        labels.append("DD30_WATCH")
    return "|".join(labels) if labels else "NO_FROZEN_WARNING"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--prereg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    prereg = json.loads(args.prereg.read_text())
    frame = pd.read_csv(args.trades).sort_values(["entry_time", "signal_id"]).reset_index(drop=True)
    frame["entry_time"] = pd.to_datetime(frame["entry_time"])
    frame["eth_market_date"] = pd.to_datetime(frame["eth_market_date"])
    frame["entry_month"] = frame["entry_time"].dt.to_period("M").astype(str)
    published = frame["pnl_r"].to_numpy(float)
    risk_points = frame["risk_points"].to_numpy(float)
    observed = (len(frame), float(published.sum()), float(published.mean()), max_drawdown_r(published))
    for value, expected in zip(observed, EXPECTED, strict=True):
        if not np.isclose(value, expected, atol=1e-9, rtol=0.0):
            raise AssertionError((value, expected))
    start = float(prereg["starting_capital_usd"])
    risks = [float(value) for value in prereg["risk_fractions"]]
    scenarios = {
        name: published - float(spec["additional_round_trip_points_vs_published_pnl_r"]) / risk_points
        for name, spec in prereg["cost_scenarios"].items()
    }
    historical_rows = []
    for scenario, returns_r in scenarios.items():
        for risk in risks:
            historical_rows.append({
                "cost_scenario": scenario,
                "risk_fraction": risk,
                "risk_pct": risk * 100,
                "adjusted_net_r": float(returns_r.sum()),
                "adjusted_expectancy_r": float(returns_r.mean()),
                **historical_metrics(returns_r, frame["entry_time"], start, risk),
            })
    pd.DataFrame(historical_rows).to_csv(args.output / "historical_summary.csv", index=False)
    date_blocks = blocks(frame, "eth_market_date")
    month_blocks = blocks(frame, "entry_month")
    bootstrap_rows = []
    for scenario_index, (scenario, returns_r) in enumerate(scenarios.items()):
        for method, block_set, specification in (
            ("DATE_BLOCK", date_blocks, prereg["resampling"]["date_block"]),
            ("MONTH_BLOCK", month_blocks, prereg["resampling"]["month_block"]),
        ):
            finals, drawdowns, losing, underwater = bootstrap_kernel(
                returns_r,
                block_set,
                int(specification["iterations"]),
                int(specification["seed"]) + scenario_index * 1000,
                start,
                np.asarray(risks),
            )
            for risk_index, risk in enumerate(risks):
                final_q = quantiles(finals[risk_index], [0.05, 0.25, 0.50, 0.75, 0.95])
                drawdown_q = quantiles(drawdowns[risk_index], [0.50, 0.75, 0.90, 0.95, 0.99])
                losing_q = quantiles(losing, [0.50, 0.90, 0.95, 0.99])
                underwater_q = quantiles(underwater[risk_index], [0.50, 0.90, 0.95, 0.99])
                bootstrap_rows.append({
                    "resampling_method": method,
                    "cost_scenario": scenario,
                    "risk_fraction": risk,
                    "iterations": len(finals[risk_index]),
                    "final_equity_p05": final_q[0],
                    "final_equity_p25": final_q[1],
                    "final_equity_p50": final_q[2],
                    "final_equity_p75": final_q[3],
                    "final_equity_p95": final_q[4],
                    "maximum_drawdown_pct_p50": drawdown_q[0],
                    "maximum_drawdown_pct_p75": drawdown_q[1],
                    "maximum_drawdown_pct_p90": drawdown_q[2],
                    "maximum_drawdown_pct_p95": drawdown_q[3],
                    "maximum_drawdown_pct_p99": drawdown_q[4],
                    "probability_final_below_start": float(np.mean(finals[risk_index] < start)),
                    "probability_drawdown_ge_10pct": float(np.mean(drawdowns[risk_index] >= 0.10)),
                    "probability_drawdown_ge_20pct": float(np.mean(drawdowns[risk_index] >= 0.20)),
                    "probability_drawdown_ge_30pct": float(np.mean(drawdowns[risk_index] >= 0.30)),
                    "longest_losing_streak_p50": losing_q[0],
                    "longest_losing_streak_p90": losing_q[1],
                    "longest_losing_streak_p95": losing_q[2],
                    "longest_losing_streak_p99": losing_q[3],
                    "time_under_water_trades_p50": underwater_q[0],
                    "time_under_water_trades_p90": underwater_q[1],
                    "time_under_water_trades_p95": underwater_q[2],
                    "time_under_water_trades_p99": underwater_q[3],
                    "warning_labels": warning_labels(finals[risk_index], drawdowns[risk_index], start),
                })
    pd.DataFrame(bootstrap_rows).to_csv(args.output / "bootstrap_summary.csv", index=False)


if __name__ == "__main__":
    main()
