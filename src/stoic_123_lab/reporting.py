from __future__ import annotations

import numpy as np
import pandas as pd


def summarize(trades: pd.DataFrame, *, instrument: str, arm_id: str) -> dict[str, object]:
    if trades.empty:
        return {
            "instrument": instrument,
            "arm_id": arm_id,
            "trades": 0,
            "net_r": 0.0,
            "expectancy_r": np.nan,
            "win_rate": np.nan,
            "profit_factor": np.nan,
            "max_drawdown_r": 0.0,
            "median_hold_minutes": np.nan,
        }
    pnl = trades["pnl_r"].to_numpy(float)
    equity = np.cumsum(pnl)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    drawdown = peaks - equity
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = -pnl[pnl < 0].sum()
    hold = (
        pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])
    ).dt.total_seconds() / 60
    result = {
        "instrument": instrument,
        "arm_id": arm_id,
        "trades": int(len(trades)),
        "net_r": float(pnl.sum()),
        "expectancy_r": float(pnl.mean()),
        "win_rate": float(np.mean(pnl > 0)),
        "profit_factor": float(gross_profit / gross_loss) if gross_loss > 0 else np.inf,
        "max_drawdown_r": float(drawdown.max(initial=0.0)),
        "median_hold_minutes": float(hold.median()),
    }
    years = pd.to_datetime(trades["entry_time"]).dt.year
    for year in sorted(years.unique()):
        result[f"net_{int(year)}"] = float(trades.loc[years == year, "pnl_r"].sum())
    return result


def date_block_bootstrap(
    trades: pd.DataFrame,
    *,
    iterations: int = 10_000,
    seed: int = 20260723,
) -> dict[str, float | int]:
    if trades.empty:
        return {
            "blocks": 0,
            "observed_expectancy_r": np.nan,
            "lo95_expectancy_r": np.nan,
            "hi95_expectancy_r": np.nan,
            "prob_expectancy_positive": np.nan,
        }
    work = trades.copy()
    work["block"] = pd.to_datetime(work["entry_time"]).dt.normalize()
    blocks = [group["pnl_r"].to_numpy(float) for _, group in work.groupby("block", sort=True)]
    rng = np.random.default_rng(seed)
    means = np.empty(iterations)
    for iteration in range(iterations):
        selected = rng.integers(0, len(blocks), size=len(blocks))
        means[iteration] = np.concatenate([blocks[index] for index in selected]).mean()
    return {
        "blocks": len(blocks),
        "observed_expectancy_r": float(work["pnl_r"].mean()),
        "lo95_expectancy_r": float(np.quantile(means, 0.025)),
        "hi95_expectancy_r": float(np.quantile(means, 0.975)),
        "prob_expectancy_positive": float(np.mean(means > 0)),
    }


def classify(summary: dict[str, object], inference: dict[str, object]) -> str:
    trades = int(summary["trades"])
    expectancy = float(summary["expectancy_r"])
    lo95 = float(inference["lo95_expectancy_r"])
    if trades < 100:
        return "INSUFFICIENT_SAMPLE"
    if expectancy <= 0:
        return "NO_EDGE"
    if lo95 > 0:
        return "ROBUST_RESEARCH_CANDIDATE"
    return "POSITIVE_BUT_UNCERTAIN"


def validate_no_pooling(summary: pd.DataFrame) -> None:
    if "instrument" not in summary.columns:
        raise ValueError("Summary must retain instrument labels")
    allowed = {"NQ", "ES_PROXY"}
    observed = set(summary["instrument"].dropna().astype(str))
    if not observed.issubset(allowed):
        raise ValueError(f"Unexpected instrument labels: {sorted(observed - allowed)}")
    if any(summary["instrument"].astype(str).str.contains("POOL", case=False, na=False)):
        raise ValueError("Pooled performance is prohibited")
