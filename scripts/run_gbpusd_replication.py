from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dtr_lab.research import engine
from dtr_lab.research.cross_market import (
    USA500_PROXY_SPEC,
    build_covered_session_table,
    classify_proxy_gaps,
)
from run_usa500_baseline_discovery import (
    attach_gap_metadata,
    block_bootstrap,
    eligible_count,
    max_drawdown,
    paired_date_bootstrap,
    sanitize_sessions,
    sequence,
    simulate_all,
)

STUDY_ID = "DTR-FX-WP-20260723-22"
YEARS = (2022, 2023, 2024, 2025)
PIP = 0.0001
POINT_VALUE = 100_000.0
COMMISSION_PER_SIDE = 3.50
SEED = 20260723

PRIMARY_ARMS: dict[str, tuple[tuple[int, ...], tuple[str, ...]]] = {
    "P0_TUE_FRI_ALL": (
        (1, 2, 3, 4),
        ("ASIA_7PM", "LONDON_2AM", "NEW_YORK_9AM"),
    ),
    "P1_MON_FRI_ALL": (
        (0, 1, 2, 3, 4),
        ("ASIA_7PM", "LONDON_2AM", "NEW_YORK_9AM"),
    ),
    "P2_TUE_FRI_NO_ASIA": (
        (1, 2, 3, 4),
        ("LONDON_2AM", "NEW_YORK_9AM"),
    ),
    "P3_MON_FRI_NO_ASIA": (
        (0, 1, 2, 3, 4),
        ("LONDON_2AM", "NEW_YORK_9AM"),
    ),
}

SESSION_ARMS: dict[str, tuple[str, ...]] = {
    "S1_LONDON_ONLY": ("LONDON_2AM",),
    "S2_NEW_YORK_ONLY": ("NEW_YORK_9AM",),
    "S3_ASIA_ONLY": ("ASIA_7PM",),
    "S4_LONDON_NEW_YORK": ("LONDON_2AM", "NEW_YORK_9AM"),
    "S5_LONDON_ASIA": ("LONDON_2AM", "ASIA_7PM"),
    "S6_ASIA_NEW_YORK": ("ASIA_7PM", "NEW_YORK_9AM"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_annual_files(input_dir: Path, side: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    frames: list[pd.DataFrame] = []
    audits: list[dict[str, object]] = []
    for year in YEARS:
        path = input_dir / f"gbpusd_m1_{side}_{year}.csv.gz"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path.name} missing columns: {sorted(missing)}")
        flat_zero = (
            (frame["volume"] <= 0)
            & (frame["open"] == frame["high"])
            & (frame["high"] == frame["low"])
            & (frame["low"] == frame["close"])
        )
        audit = {
            "side": side,
            "year": year,
            "source_file": path.name,
            "source_sha256": sha256(path),
            "raw_rows": int(len(frame)),
            "flat_zero_rows_removed": int(flat_zero.sum()),
        }
        frame = frame.loc[~flat_zero].copy()
        frame["timestamp"] = pd.to_numeric(frame["timestamp"], errors="raise").astype("int64")
        frame = frame.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
        audit["active_rows"] = int(len(frame))
        audit["duplicate_rows_after_cleaning"] = 0
        frames.append(frame)
        audits.append(audit)
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    return combined, audits


def build_midpoint(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    bid, bid_audit = read_annual_files(input_dir, "bid")
    ask, ask_audit = read_annual_files(input_dir, "ask")
    merged = bid.merge(ask, on="timestamp", how="inner", suffixes=("_bid", "_ask"), validate="one_to_one")
    merged["spread_close"] = merged["close_ask"] - merged["close_bid"]
    invalid_spread = merged["spread_close"] < 0
    invalid_count = int(invalid_spread.sum())
    if invalid_count:
        merged = merged.loc[~invalid_spread].copy()

    midpoint = pd.DataFrame({"timestamp": merged["timestamp"]})
    for column in ("open", "high", "low", "close"):
        midpoint[column] = (merged[f"{column}_bid"] + merged[f"{column}_ask"]) / 2.0
    midpoint["volume"] = (merged["volume_bid"] + merged["volume_ask"]) / 2.0
    midpoint["timestamp"] = (
        pd.to_datetime(midpoint["timestamp"], unit="ms", utc=True, errors="raise")
        .dt.tz_convert("America/New_York")
        .dt.tz_localize(None)
    )
    midpoint = midpoint.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)

    valid_ohlc = (
        (midpoint["high"] >= midpoint[["open", "close", "low"]].max(axis=1))
        & (midpoint["low"] <= midpoint[["open", "close", "high"]].min(axis=1))
    )
    if not valid_ohlc.all():
        raise ValueError("GBPUSD midpoint OHLC integrity failed")

    spread = pd.DataFrame(
        {
            "timestamp": midpoint["timestamp"],
            "spread_pips": merged.loc[~invalid_spread, "spread_close"].to_numpy(float) / PIP,
        }
    )
    spread = spread.loc[np.isfinite(spread["spread_pips"]) & (spread["spread_pips"] >= 0)].copy()
    if spread.empty:
        raise ValueError("No valid GBPUSD spread observations")

    spread_quantiles = spread["spread_pips"].quantile([0.5, 0.75, 0.9, 0.95, 0.99])
    base_slippage_pips_each_side = max(float(spread_quantiles.loc[0.75]) / 2.0 + 0.10, 0.10)
    audit = {
        "study_id": STUDY_ID,
        "bid_files": bid_audit,
        "ask_files": ask_audit,
        "bid_active_rows": int(len(bid)),
        "ask_active_rows": int(len(ask)),
        "synchronized_rows": int(len(midpoint)),
        "invalid_negative_spread_rows_removed": invalid_count,
        "active_start_et": str(midpoint["timestamp"].min()),
        "active_end_et": str(midpoint["timestamp"].max()),
        "duplicate_timestamps": int(midpoint["timestamp"].duplicated().sum()),
        "strictly_increasing": bool(midpoint["timestamp"].is_monotonic_increasing),
        "median_spread_pips": float(spread_quantiles.loc[0.5]),
        "q75_spread_pips": float(spread_quantiles.loc[0.75]),
        "q90_spread_pips": float(spread_quantiles.loc[0.9]),
        "q95_spread_pips": float(spread_quantiles.loc[0.95]),
        "q99_spread_pips": float(spread_quantiles.loc[0.99]),
        "base_slippage_pips_each_side": base_slippage_pips_each_side,
        "commission_per_side_usd_per_standard_lot": COMMISSION_PER_SIDE,
        "strategy_tick_size": PIP,
        "point_value_per_standard_lot": POINT_VALUE,
    }
    return midpoint, spread, audit


def signal_frame(signals: list[engine.CandidateSignal]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "signal_id": index,
                "session": signal.session,
                "session_date": pd.Timestamp(signal.session_date).normalize(),
                "direction": signal.direction,
                "entry_time": signal.entry_time,
                "weekday": int(signal.day_of_week),
            }
            for index, signal in enumerate(signals)
        ]
    )


def adjusted_expectancy(
    trades: pd.DataFrame,
    *,
    base_slippage_pips_each_side: float,
    target_slippage_pips_each_side: float,
) -> float:
    if trades.empty:
        return math.nan
    target = max(target_slippage_pips_each_side, base_slippage_pips_each_side)
    additional = (target - base_slippage_pips_each_side) * PIP
    risk_points = (trades["entry_price"] - trades["stop_price"]).abs().to_numpy(float)
    adjusted = trades["pnl_r"].to_numpy(float) - 2.0 * additional / risk_points
    return float(np.mean(adjusted))


def profit_factor(values: np.ndarray) -> float:
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    if losses == 0:
        return math.inf if gains > 0 else math.nan
    return gains / losses


def summarize(
    trades: pd.DataFrame,
    *,
    arm: str,
    eligible_sessions: int,
    qualifying_signals: int,
    base_slippage_pips_each_side: float,
) -> dict[str, object]:
    values = trades["pnl_r"].to_numpy(float) if not trades.empty else np.array([], dtype=float)
    net = float(values.sum()) if len(values) else 0.0
    drawdown = max_drawdown(values) if len(values) else 0.0
    result: dict[str, object] = {
        "arm": arm,
        "eligible_sessions": eligible_sessions,
        "qualifying_signals": qualifying_signals,
        "trades": int(len(trades)),
        "net_r": net,
        "expectancy_r": float(values.mean()) if len(values) else math.nan,
        "median_r": float(np.median(values)) if len(values) else math.nan,
        "profit_factor": profit_factor(values),
        "win_rate": float(np.mean(values > 0)) if len(values) else math.nan,
        "max_drawdown_r": drawdown,
        "return_dd": net / drawdown if drawdown > 0 else math.nan,
        "base_slippage_pips_each_side": base_slippage_pips_each_side,
        "one_pip_each_side_expectancy_r": adjusted_expectancy(
            trades,
            base_slippage_pips_each_side=base_slippage_pips_each_side,
            target_slippage_pips_each_side=1.0,
        ),
        "two_pips_each_side_expectancy_r": adjusted_expectancy(
            trades,
            base_slippage_pips_each_side=base_slippage_pips_each_side,
            target_slippage_pips_each_side=2.0,
        ),
    }
    entry_times = (
        pd.to_datetime(trades["entry_time"]) if not trades.empty else pd.Series(dtype="datetime64[ns]")
    )
    year_nets: list[float] = []
    for year in YEARS:
        year_net = (
            float(trades.loc[entry_times.dt.year == year, "pnl_r"].sum())
            if not trades.empty
            else 0.0
        )
        result[f"net_{year}"] = year_net
        year_nets.append(year_net)
    positive_total = max(net, 0.0)
    result["positive_years"] = int(sum(value > 0 for value in year_nets))
    result["minimum_year_net_r"] = float(min(year_nets))
    result["single_year_positive_net_share"] = (
        float(max(year_nets) / positive_total) if positive_total > 0 else math.inf
    )
    return result


def broad_viable(row: pd.Series, paired_required: bool) -> dict[str, bool]:
    checks = {
        "gate_positive_net": bool(row["net_r"] > 0),
        "gate_cost": bool(row["one_pip_each_side_expectancy_r"] > 0),
        "gate_years": bool(row["positive_years"] >= 3),
        "gate_latest_year": bool(row["net_2025"] >= 0),
        "gate_concentration": bool(row["single_year_positive_net_share"] <= 0.70),
        "gate_sample": bool(row["trades"] >= 200),
    }
    if paired_required:
        checks["gate_paired_interval"] = bool(row["lo95_net_difference_r"] > 0)
    return checks


def session_viable(row: pd.Series) -> dict[str, bool]:
    return {
        "gate_positive_net": bool(row["net_r"] > 0),
        "gate_cost": bool(row["one_pip_each_side_expectancy_r"] > 0),
        "gate_years": bool(row["positive_years"] >= 3),
        "gate_latest_year": bool(row["net_2025"] >= 0),
        "gate_concentration": bool(row["single_year_positive_net_share"] <= 0.70),
        "gate_sample": bool(row["trades"] >= 120),
        "gate_paired_interval": bool(row["lo95_net_difference_r"] > 0),
    }


def write_report(
    out: Path,
    audit: dict[str, object],
    stage1: pd.DataFrame,
    stage1b: pd.DataFrame,
    decision: dict[str, object],
) -> None:
    def table(frame: pd.DataFrame, columns: list[str]) -> str:
        return frame[columns].to_markdown(index=False, floatfmt=".4f")

    lines = [
        "# GBPUSD DTR Replication — 2026-07-23",
        "",
        "## Decision",
        "",
        f"`{decision['decision']}`",
        "",
        "This study applies the frozen Day Trader Rauf core to temporary Dukascopy GBPUSD one-minute bid/ask data from 2022 through 2025. Signals use synchronized midpoint OHLC; the base execution model uses the observed 75th-percentile spread plus 0.1 pip slippage and a $3.50 commission per side for one standard lot.",
        "",
        "## Data and execution audit",
        "",
        f"- Synchronized active candles: {audit['synchronized_rows']:,}",
        f"- Active period: {audit['active_start_et']} through {audit['active_end_et']}",
        f"- Median quoted spread: {audit['median_spread_pips']:.3f} pips",
        f"- 75th-percentile spread: {audit['q75_spread_pips']:.3f} pips",
        f"- Base modeled slippage: {audit['base_slippage_pips_each_side']:.3f} pips per side",
        f"- Eligible covered sessions: {decision['eligible_sessions']:,}",
        "",
        "## Monday × Asia factorial",
        "",
        table(
            stage1,
            [
                "arm",
                "trades",
                "net_r",
                "expectancy_r",
                "one_pip_each_side_expectancy_r",
                "max_drawdown_r",
                "positive_years",
                "gate_all",
            ],
        ),
        "",
    ]
    if not stage1b.empty:
        lines.extend(
            [
                "## Session decomposition",
                "",
                table(
                    stage1b,
                    [
                        "arm",
                        "trades",
                        "net_r",
                        "expectancy_r",
                        "one_pip_each_side_expectancy_r",
                        "max_drawdown_r",
                        "positive_years",
                        "gate_all",
                    ],
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            str(decision["interpretation"]),
            "",
            "This is exploratory cross-asset evidence. It does not authorize Pine conversion, position sizing, or live deployment.",
        ]
    )
    (out / "GBPUSD_DTR_REPLICATION_RESEARCH_2026-07-23.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def create_charts(out: Path, arm_trades: dict[str, pd.DataFrame], stage1: pd.DataFrame, stage1b: pd.DataFrame) -> None:
    chart_dir = out / "charts"
    chart_dir.mkdir(exist_ok=True)
    selected = list(PRIMARY_ARMS)
    if not stage1b.empty:
        selected.extend(stage1b.sort_values("net_r", ascending=False)["arm"].head(3).tolist())

    fig, ax = plt.subplots(figsize=(11, 6))
    for arm in selected:
        trades = arm_trades.get(arm)
        if trades is None or trades.empty:
            continue
        work = trades.sort_values("entry_time")
        ax.plot(pd.to_datetime(work["entry_time"]), work["pnl_r"].cumsum(), label=arm)
    ax.axhline(0, linewidth=1)
    ax.set_title("GBPUSD DTR cumulative R")
    ax.set_xlabel("Entry date")
    ax.set_ylabel("Cumulative R")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(chart_dir / "gbpusd_dtr_cumulative_r.png", dpi=180)
    plt.close(fig)

    frames = [stage1.assign(stage="calendar")]
    if not stage1b.empty:
        frames.append(stage1b.assign(stage="session"))
    annual = pd.concat(frames, ignore_index=True)
    rows = []
    for row in annual.itertuples(index=False):
        for year in YEARS:
            rows.append({"arm": row.arm, "year": year, "net_r": getattr(row, f"net_{year}")})
    annual_long = pd.DataFrame(rows)
    pivot = annual_long.pivot(index="arm", columns="year", values="net_r")
    fig, ax = plt.subplots(figsize=(11, 6))
    pivot.plot(kind="bar", ax=ax)
    ax.axhline(0, linewidth=1)
    ax.set_title("GBPUSD DTR annual net R")
    ax.set_xlabel("Arm")
    ax.set_ylabel("Net R")
    fig.tight_layout()
    fig.savefig(chart_dir / "gbpusd_dtr_annual_net_r.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    one, spread, audit = build_midpoint(args.input_dir)
    gaps = classify_proxy_gaps(one)
    bars = attach_gap_metadata(engine.resample_5m(one), gaps)
    raw_sessions = build_covered_session_table(one, bars, minimum_coverage=0.95)
    sessions = sanitize_sessions(raw_sessions, bars, gaps)
    eligible = sessions.loc[~sessions["integrity_range_gap_rejected"]].copy()
    eligible = eligible.sort_values(["range_start", "session"]).reset_index(drop=True)

    config = replace(
        USA500_PROXY_SPEC.strategy_config(name="GBPUSD_DTR_BROAD"),
        weekdays=(0, 1, 2, 3, 4),
        sessions=("LONDON_2AM", "NEW_YORK_9AM", "ASIA_7PM"),
        tick_size=PIP,
        point_value=POINT_VALUE,
        commission_per_side=COMMISSION_PER_SIDE,
        slippage_ticks_each_side=float(audit["base_slippage_pips_each_side"]),
    )
    signals, funnel = engine.generate_signals(bars, eligible, config)
    cached = simulate_all(one, bars, signals, config, gaps)
    features = signal_frame(signals)

    arm_trades: dict[str, pd.DataFrame] = {}
    stage1_rows: list[dict[str, object]] = []
    for index, (arm, (weekdays, allowed_sessions)) in enumerate(PRIMARY_ARMS.items()):
        mask = features["weekday"].isin(weekdays) & features["session"].isin(allowed_sessions)
        trades = sequence(features, cached, mask)
        arm_trades[arm] = trades
        row = summarize(
            trades,
            arm=arm,
            eligible_sessions=eligible_count(eligible, weekdays, allowed_sessions),
            qualifying_signals=int(mask.sum()),
            base_slippage_pips_each_side=float(audit["base_slippage_pips_each_side"]),
        )
        row.update(block_bootstrap(trades, "date", args.iterations, args.seed + index))
        stage1_rows.append(row)
    stage1 = pd.DataFrame(stage1_rows)

    paired_rows: list[dict[str, object]] = []
    p0_trades = arm_trades["P0_TUE_FRI_ALL"]
    for index, arm in enumerate(PRIMARY_ARMS):
        if arm == "P0_TUE_FRI_ALL":
            paired = {
                "observed_net_difference_r": 0.0,
                "lo95_net_difference_r": 0.0,
                "hi95_net_difference_r": 0.0,
                "prob_net_difference_positive": math.nan,
            }
        else:
            paired = paired_date_bootstrap(
                arm_trades[arm], p0_trades, args.iterations, args.seed + 100 + index
            )
        paired_rows.append({"arm": arm, **paired})
    paired_frame = pd.DataFrame(paired_rows)
    stage1 = stage1.merge(paired_frame, on="arm", how="left")

    for index, row in stage1.iterrows():
        checks = broad_viable(row, paired_required=row["arm"] != "P0_TUE_FRI_ALL")
        for key, value in checks.items():
            stage1.loc[index, key] = value
        stage1.loc[index, "gate_all"] = all(checks.values())

    passing_stage1 = stage1.loc[stage1["gate_all"].fillna(False)]
    stage1b = pd.DataFrame()
    if passing_stage1.empty:
        session_rows: list[dict[str, object]] = []
        for index, (arm, allowed_sessions) in enumerate(SESSION_ARMS.items()):
            weekdays = (1, 2, 3, 4)
            mask = features["weekday"].isin(weekdays) & features["session"].isin(allowed_sessions)
            trades = sequence(features, cached, mask)
            arm_trades[arm] = trades
            row = summarize(
                trades,
                arm=arm,
                eligible_sessions=eligible_count(eligible, weekdays, allowed_sessions),
                qualifying_signals=int(mask.sum()),
                base_slippage_pips_each_side=float(audit["base_slippage_pips_each_side"]),
            )
            row.update(
                paired_date_bootstrap(
                    trades, p0_trades, args.iterations, args.seed + 200 + index
                )
            )
            row.update(block_bootstrap(trades, "date", args.iterations, args.seed + 300 + index))
            session_rows.append(row)
        stage1b = pd.DataFrame(session_rows)
        for index, row in stage1b.iterrows():
            checks = session_viable(row)
            for key, value in checks.items():
                stage1b.loc[index, key] = value
            stage1b.loc[index, "gate_all"] = all(checks.values())

    passing_session = (
        stage1b.loc[stage1b["gate_all"].fillna(False)] if not stage1b.empty else pd.DataFrame()
    )
    if not passing_stage1.empty:
        selected = passing_stage1.sort_values(
            ["return_dd", "one_pip_each_side_expectancy_r", "net_r"], ascending=False
        ).iloc[0]
        selected_arm = str(selected["arm"])
        decision_code = "VIABLE_GBPUSD_DTR_BASELINE"
        interpretation = (
            "At least one broad calendar/session arm passed all frozen profitability, "
            "cost, year-stability, concentration, sample-size and paired-effect gates."
        )
    elif not passing_session.empty:
        selected = passing_session.sort_values(
            ["return_dd", "one_pip_each_side_expectancy_r", "net_r"], ascending=False
        ).iloc[0]
        selected_arm = str(selected["arm"])
        decision_code = "VIABLE_GBPUSD_SESSION_BASELINE"
        interpretation = (
            "No broad arm passed, but one bounded session arm passed every frozen gate. "
            "It remains exploratory cross-asset evidence pending fresh validation."
        )
    else:
        selected_arm = None
        decision_code = "NO_VIABLE_GBPUSD_DTR_BASELINE"
        interpretation = (
            "Neither the frozen broad arms nor the bounded session decomposition produced "
            "a cost-robust and year-stable GBPUSD baseline. No neighboring parameter search "
            "is authorized on this sample."
        )

    spread_summary = pd.DataFrame(
        {
            "metric": ["p50", "p75", "p90", "p95", "p99"],
            "spread_pips": [
                spread["spread_pips"].quantile(0.50),
                spread["spread_pips"].quantile(0.75),
                spread["spread_pips"].quantile(0.90),
                spread["spread_pips"].quantile(0.95),
                spread["spread_pips"].quantile(0.99),
            ],
        }
    )
    decision = {
        "study_id": STUDY_ID,
        "decision": decision_code,
        "classification": "EXPLORATORY_CROSS_ASSET_REPLICATION",
        "selected_arm": selected_arm,
        "eligible_sessions": int(len(eligible)),
        "signals": int(len(features)),
        "simulated_signals": int(len(cached)),
        "funnel": funnel.as_dict(),
        "base_slippage_pips_each_side": float(audit["base_slippage_pips_each_side"]),
        "commission_per_side_usd_per_standard_lot": COMMISSION_PER_SIDE,
        "session_decomposition_run": bool(passing_stage1.empty),
        "interpretation": interpretation,
        "independent_review_required": True,
        "no_deployment_authorization": True,
    }

    stage1.to_csv(args.out / "stage1_calendar_factorial.csv", index=False)
    paired_frame.to_csv(args.out / "stage1_paired_bootstrap.csv", index=False)
    stage1b.to_csv(args.out / "stage1b_session_decomposition.csv", index=False)
    spread_summary.to_csv(args.out / "spread_summary.csv", index=False)
    (args.out / "data_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    (args.out / "decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    pd.DataFrame([asdict(trade) | {"signal_id": signal_id} for signal_id, trade in cached.items()]).to_csv(
        args.out / "signal_trade_cache.csv.gz", index=False, compression="gzip"
    )
    features.to_csv(args.out / "signal_features.csv.gz", index=False, compression="gzip")
    for arm, trades in arm_trades.items():
        trades.to_csv(args.out / f"{arm}__trades.csv", index=False)

    write_report(args.out, audit, stage1, stage1b, decision)
    create_charts(args.out, arm_trades, stage1, stage1b)

    hashes = {
        path.relative_to(args.out).as_posix(): sha256(path)
        for path in sorted(args.out.rglob("*"))
        if path.is_file() and path.name != "artifact_hashes.json"
    }
    (args.out / "artifact_hashes.json").write_text(
        json.dumps(hashes, indent=2), encoding="utf-8"
    )
    print(json.dumps(decision, indent=2))
    print(stage1.to_string(index=False))
    if not stage1b.empty:
        print(stage1b.to_string(index=False))


if __name__ == "__main__":
    main()
