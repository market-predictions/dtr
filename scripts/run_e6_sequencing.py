# ruff: noqa
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ARCHIVE_SHA = "8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc"
SIGNAL_SHA = "39b48d9e6219357907eac1bf65d81d2dff392d1d172916008ad20365665693ad"
EXPECTED_E6 = (304, 48.93754952687199, 0.16097878133839472, 8.632571354238342)
SEED = 20260722
ITERATIONS = 20000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def eth_date(ts: pd.Timestamp) -> pd.Timestamp:
    ts = pd.Timestamp(ts)
    return ts.normalize() + (pd.Timedelta(days=1) if ts.hour >= 18 else pd.Timedelta(0))


def load_signals(path: Path) -> pd.DataFrame:
    if sha256(path) != SIGNAL_SHA:
        raise RuntimeError("Unexpected E6 signal-diagnostics checksum")
    frame = pd.read_csv(path)
    for column in ("entry_time", "exit_time", "session_date"):
        frame[column] = pd.to_datetime(frame[column], errors="raise")
    frame = frame.loc[frame["e6_keep"].astype(bool)].copy()
    frame["eth_market_date"] = frame["entry_time"].map(eth_date)
    return frame.sort_values(["entry_time", "signal_id"]).reset_index(drop=True)


def sequence(signals: pd.DataFrame, arm: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    accepted, rejected = [], []
    global_free = pd.Timestamp.min
    used_dates: set[pd.Timestamp] = set()
    sleeve_free = {name: pd.Timestamp.min for name in signals["session"].unique()}
    for row in signals.itertuples(index=False):
        reason = None
        if arm == "S0_GLOBAL":
            reason = "POSITION_OPEN" if row.entry_time < global_free else None
        elif arm == "S1_FIRST_PER_ETH_DATE":
            if row.eth_market_date in used_dates:
                reason = "DATE_ALREADY_TRADED"
            elif row.entry_time < global_free:
                reason = "POSITION_OPEN"
        elif arm == "S2_COOLDOWN_60":
            reason = "POSITION_OR_COOLDOWN" if row.entry_time < global_free else None
        elif arm == "S3_SESSION_SLEEVES":
            reason = "SLEEVE_POSITION_OPEN" if row.entry_time < sleeve_free[row.session] else None
        else:
            raise ValueError(arm)
        if reason:
            rejected.append({"arm": arm, "signal_id": row.signal_id, "reason": reason})
            continue
        accepted.append(row._asdict())
        if arm == "S1_FIRST_PER_ETH_DATE":
            used_dates.add(row.eth_market_date)
        if arm == "S2_COOLDOWN_60":
            global_free = row.exit_time + pd.Timedelta(minutes=60)
        elif arm == "S3_SESSION_SLEEVES":
            sleeve_free[row.session] = row.exit_time
        else:
            global_free = row.exit_time
    return pd.DataFrame(accepted), pd.DataFrame(rejected)


def scale(arm: str) -> float:
    return 1.0 / 3.0 if arm == "S3_SESSION_SLEEVES" else 1.0


def max_dd(values: np.ndarray) -> float:
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    return float((peaks[1:] - equity).max(initial=0.0))


def stressed(frame: pd.DataFrame, ticks_each_side: float) -> np.ndarray:
    return frame["pnl_r"].to_numpy(float) - (2.0 * (ticks_each_side - 1.0) * 0.25) / frame["risk_points"].to_numpy(float)


def metrics(arm: str, frame: pd.DataFrame) -> dict[str, float | int | str]:
    risk_scale = scale(arm)
    ordered = frame.sort_values(["exit_time", "signal_id"])
    raw = ordered["pnl_r"].to_numpy(float)
    portfolio = raw * risk_scale
    dd = max_dd(portfolio)
    wins = portfolio[portfolio > 0].sum()
    losses = -portfolio[portfolio < 0].sum()
    result = {
        "arm": arm,
        "trades": len(frame),
        "risk_scale_per_trade": risk_scale,
        "raw_net_r": float(raw.sum()),
        "portfolio_net_r": float(portfolio.sum()),
        "raw_expectancy_r": float(raw.mean()),
        "win_rate": float(np.mean(raw > 0)),
        "profit_factor": float(wins / losses),
        "portfolio_max_drawdown_r": dd,
        "portfolio_return_dd": float(portfolio.sum() / dd),
    }
    for ticks in (1.0, 2.0, 4.0):
        cost = stressed(frame, ticks)
        result[f"raw_expectancy_{int(ticks)}tick_side_r"] = float(cost.mean())
        result[f"portfolio_net_{int(ticks)}tick_side_r"] = float((cost * risk_scale).sum())
    return result


def date_returns(arm: str, frame: pd.DataFrame) -> pd.Series:
    work = frame.assign(portfolio_r=frame["pnl_r"] * scale(arm))
    return work.groupby("eth_market_date")["portfolio_r"].sum()


def inference(returns: dict[str, pd.Series], seed: int) -> pd.DataFrame:
    dates = sorted(set().union(*[set(series.index) for series in returns.values()]))
    table = pd.DataFrame({name: series.reindex(dates, fill_value=0.0) for name, series in returns.items()})
    names = ["S1_FIRST_PER_ETH_DATE", "S2_COOLDOWN_60", "S3_SESSION_SLEEVES"]
    diff = table[names].sub(table["S0_GLOBAL"], axis=0).to_numpy(float)
    n = len(table)
    rng = np.random.default_rng(seed)
    indexes = rng.integers(0, n, size=(ITERATIONS, n))
    samples = diff[indexes].sum(axis=1)
    means = samples / n
    observed_mean = diff.mean(axis=0)
    standard_error = means.std(axis=0, ddof=1)
    centered = diff - observed_mean
    null_t = (centered[indexes].sum(axis=1) / n) / standard_error
    maximum_t = null_t.max(axis=1)
    rows = []
    for position, name in enumerate(names):
        observed_t = observed_mean[position] / standard_error[position]
        rows.append({
            "arm": name,
            "incremental_net_r": float(diff[:, position].sum()),
            "ci95_low_net_r": float(np.quantile(samples[:, position], 0.025)),
            "ci95_high_net_r": float(np.quantile(samples[:, position], 0.975)),
            "probability_improvement": float(np.mean(samples[:, position] > 0)),
            "familywise_p": float(np.mean(maximum_t >= observed_t)) if observed_t > 0 else 1.0,
            "seed": seed,
            "iterations": ITERATIONS,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signals", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sha256(args.archive) != ARCHIVE_SHA:
        raise RuntimeError("Unexpected raw archive checksum")
    args.output.mkdir(parents=True, exist_ok=True)
    signals = load_signals(args.signals)
    arms, rejects = {}, []
    for arm in ("S0_GLOBAL", "S1_FIRST_PER_ETH_DATE", "S2_COOLDOWN_60", "S3_SESSION_SLEEVES"):
        arms[arm], rejected = sequence(signals, arm)
        rejects.append(rejected)
        arms[arm].to_csv(args.output / f"{arm}__trades.csv", index=False, float_format="%.12f")
    results = pd.DataFrame([metrics(name, frame) for name, frame in arms.items()])
    base = results.set_index("arm").loc["S0_GLOBAL"]
    actual = (int(base.trades), float(base.portfolio_net_r), float(base.raw_expectancy_r), float(base.portfolio_max_drawdown_r))
    if any(not np.isclose(a, b, atol=1e-9, rtol=0.0) for a, b in zip(actual, EXPECTED_E6, strict=True)):
        raise RuntimeError(f"E6 regression mismatch: {actual}")
    paired = inference({name: date_returns(name, frame) for name, frame in arms.items()}, SEED)
    results.to_csv(args.output / "sequencing_results.csv", index=False, float_format="%.12f")
    paired.to_csv(args.output / "sequencing_inference.csv", index=False, float_format="%.12f")
    pd.concat(rejects, ignore_index=True).to_csv(args.output / "sequencing_rejections.csv", index=False)
    summary = {"decision": "RETAIN_S0_GLOBAL_SEQUENCING", "results": results.to_dict(orient="records"), "inference": paired.to_dict(orient="records")}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
