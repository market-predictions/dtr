from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_nq_usa500_parallel as parallel
from dtr_lab.research import engine
from dtr_lab.research.cross_market import cost_stress_expectancy
from dtr_lab.research.proxy_validation import (
    classify_proxy_oos,
    clean_dukascopy_candles,
    paired_date_delta,
)

FOMC_2026 = {
    pd.Timestamp("2026-01-28"),
    pd.Timestamp("2026-03-18"),
    pd.Timestamp("2026-04-29"),
    pd.Timestamp("2026-06-17"),
}
ALL_FOMC = parallel.FOMC_DATES.union(FOMC_2026)
NQ_EXPECTED = {
    "UNFILTERED": (477, 42.57751500303384, 0.0892610377422093, 16.426492880443),
    "E6": (304, 48.93754952687199, 0.16097878133839472, 8.632571354238342),
    "E6_NO_FOMC_DAY": (
        291,
        53.48334196741127,
        0.18379155315261606,
        9.151060839915637,
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_proxy(path: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    frame, audit = clean_dukascopy_candles(pd.read_csv(path))
    audit["source_file_sha256"] = sha256(path)
    return frame, audit


def proxy_config(name: str) -> engine.StrategyConfig:
    # Preserve NQ decision geometry and synthetic NQ execution economics.
    return parallel.NQ_SPEC.strategy_config(name=name)


def assert_nq_regressions(summary: pd.DataFrame) -> None:
    for arm, expected in NQ_EXPECTED.items():
        row = summary.loc[summary["arm"] == arm].iloc[0]
        observed = (
            int(row["trades"]),
            float(row["net_r"]),
            float(row["expectancy_r"]),
            float(row["max_drawdown_r"]),
        )
        for actual, target in zip(observed, expected, strict=True):
            if not np.isclose(actual, target, atol=2e-6, rtol=0):
                raise RuntimeError(f"NQ {arm} mismatch: {actual!r} != {target!r}")


def log_return_series(frame: pd.DataFrame, frequency: str) -> pd.Series:
    closes = frame.set_index("timestamp")["close"].resample(frequency).last().dropna()
    return np.log(closes).diff().dropna()


def eth_daily_returns(frame: pd.DataFrame) -> pd.Series:
    work = frame[["timestamp", "close"]].copy()
    work["eth_day"] = (work["timestamp"] - pd.Timedelta(hours=18)).dt.normalize()
    return np.log(work.groupby("eth_day")["close"].last()).diff().dropna()


def price_concordance(nq: pd.DataFrame, proxy: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for frequency, name in (("1min", "one_minute"), ("5min", "five_minute")):
        joined = pd.concat(
            [
                log_return_series(nq, frequency).rename("nq"),
                log_return_series(proxy, frequency).rename("proxy"),
            ],
            axis=1,
            join="inner",
        ).dropna()
        rows.append(
            {
                "metric": name,
                "observations": len(joined),
                "pearson": float(joined["nq"].corr(joined["proxy"])),
                "spearman": float(
                    joined["nq"].corr(joined["proxy"], method="spearman")
                ),
            }
        )
    joined = pd.concat(
        [eth_daily_returns(nq).rename("nq"), eth_daily_returns(proxy).rename("proxy")],
        axis=1,
        join="inner",
    ).dropna()
    rows.append(
        {
            "metric": "eth_daily",
            "observations": len(joined),
            "pearson": float(joined["nq"].corr(joined["proxy"])),
            "spearman": float(
                joined["nq"].corr(joined["proxy"], method="spearman")
            ),
        }
    )
    return pd.DataFrame(rows)


def session_range_concordance(nq_result: dict, proxy_result: dict) -> pd.DataFrame:
    nq_sessions = nq_result["eligible_sessions"][
        ["session_date", "session", "range_size"]
    ]
    proxy_sessions = proxy_result["eligible_sessions"][
        ["session_date", "session", "range_size"]
    ]
    merged = nq_sessions.merge(
        proxy_sessions,
        on=["session_date", "session"],
        suffixes=("_nq", "_proxy"),
    )
    rows = []
    for session, group in list(merged.groupby("session")) + [("ALL", merged)]:
        rows.append(
            {
                "session": session,
                "observations": len(group),
                "pearson": float(group["range_size_nq"].corr(group["range_size_proxy"])),
                "spearman": float(
                    group["range_size_nq"].corr(
                        group["range_size_proxy"], method="spearman"
                    )
                ),
            }
        )
    return pd.DataFrame(rows)


def decision_concordance(nq_result: dict, proxy_result: dict, output: Path) -> dict:
    nq_signals = nq_result["signals"].copy()
    proxy_signals = proxy_result["signals"].copy()
    for frame in (nq_signals, proxy_signals):
        frame["session_date"] = pd.to_datetime(frame["session_date"]).dt.normalize()
        frame["entry_time"] = pd.to_datetime(frame["entry_time"])
        frame["e6_keep"] = parallel.e6_mask(frame)
    signals = nq_signals.merge(
        proxy_signals,
        on=["session_date", "session"],
        how="outer",
        suffixes=("_nq", "_proxy"),
        indicator=True,
    )
    shared = signals.loc[signals["_merge"] == "both"].copy()
    shared["entry_difference_minutes"] = (
        shared["entry_time_nq"] - shared["entry_time_proxy"]
    ).abs().dt.total_seconds() / 60

    nq_trades = nq_result["trades"]["UNFILTERED"].copy()
    proxy_trades = proxy_result["trades"]["UNFILTERED"].copy()
    for frame in (nq_trades, proxy_trades):
        frame["session_date"] = pd.to_datetime(frame["session_date"]).dt.normalize()
    trades = nq_trades.merge(
        proxy_trades,
        on=["session_date", "session"],
        suffixes=("_nq", "_proxy"),
    )
    shared.to_csv(output / "shared_signal_sessions.csv", index=False)
    trades.to_csv(output / "shared_trade_sessions.csv", index=False)
    return {
        "nq_signals": len(nq_signals),
        "proxy_signals": len(proxy_signals),
        "shared_signal_sessions": len(shared),
        "direction_agreement": float(
            (shared["direction_nq"] == shared["direction_proxy"]).mean()
        )
        if len(shared)
        else np.nan,
        "entry_within_5m": float((shared["entry_difference_minutes"] <= 5).mean())
        if len(shared)
        else np.nan,
        "entry_within_15m": float((shared["entry_difference_minutes"] <= 15).mean())
        if len(shared)
        else np.nan,
        "entry_within_30m": float((shared["entry_difference_minutes"] <= 30).mean())
        if len(shared)
        else np.nan,
        "median_entry_difference_minutes": float(
            shared["entry_difference_minutes"].median()
        )
        if len(shared)
        else np.nan,
        "e6_keep_agreement": float(
            (shared["e6_keep_nq"] == shared["e6_keep_proxy"]).mean()
        )
        if len(shared)
        else np.nan,
        "shared_unfiltered_trade_sessions": len(trades),
        "trade_direction_agreement": float(
            (trades["direction_nq"] == trades["direction_proxy"]).mean()
        )
        if len(trades)
        else np.nan,
        "trade_outcome_sign_agreement": float(
            (np.sign(trades["pnl_r_nq"]) == np.sign(trades["pnl_r_proxy"])).mean()
        )
        if len(trades)
        else np.nan,
        "trade_pnl_r_correlation": float(
            trades["pnl_r_nq"].corr(trades["pnl_r_proxy"])
        )
        if len(trades) > 1
        else np.nan,
    }


def summarize_oos(trades: pd.DataFrame, arm: str) -> dict[str, object]:
    result = {"arm": arm, **engine.metrics(trades)}
    result["one_tick_expectancy_r"] = result["expectancy_r"]
    result["two_tick_expectancy_r"] = cost_stress_expectancy(
        trades, total_ticks_each_side=2, tick_size=0.25
    )
    result["four_tick_expectancy_r"] = cost_stress_expectancy(
        trades, total_ticks_each_side=4, tick_size=0.25
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nq", type=Path, required=True)
    parser.add_argument("--proxy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    proxy_all, proxy_audit = load_proxy(args.proxy)
    nq_frame = parallel.load_nq(args.nq)
    proxy_overlap = proxy_all.loc[
        (proxy_all["timestamp"] >= nq_frame["timestamp"].min())
        & (proxy_all["timestamp"] <= nq_frame["timestamp"].max())
    ].copy()

    nq_result = parallel.run_instrument(
        instrument="NQ",
        one_minute=nq_frame,
        config=parallel.NQ_SPEC.strategy_config(name="NQ_SCIENTIFIC_REFERENCE"),
        minimum_range_coverage=parallel.NQ_SPEC.minimum_range_coverage,
        proxy_gap_policy=False,
        include_unfiltered=True,
        fomc_dates=ALL_FOMC,
    )
    assert_nq_regressions(nq_result["summary"])
    proxy_result = parallel.run_instrument(
        instrument="USATECH_PROXY",
        one_minute=proxy_overlap,
        config=proxy_config("USATECH_PROXY_OVERLAP"),
        minimum_range_coverage=0.95,
        proxy_gap_policy=True,
        include_unfiltered=True,
        fomc_dates=ALL_FOMC,
    )

    overlap_summary = pd.concat(
        [nq_result["summary"], proxy_result["summary"]], ignore_index=True
    )
    overlap_summary.to_csv(args.out / "overlap_arm_summary.csv", index=False)
    price = price_concordance(nq_frame, proxy_overlap)
    price.to_csv(args.out / "price_concordance.csv", index=False)
    ranges = session_range_concordance(nq_result, proxy_result)
    ranges.to_csv(args.out / "session_range_concordance.csv", index=False)
    decisions = decision_concordance(nq_result, proxy_result, args.out)
    (args.out / "decision_concordance.json").write_text(
        json.dumps(decisions, indent=2, default=float)
    )

    proxy_full = parallel.run_instrument(
        instrument="USATECH_PROXY",
        one_minute=proxy_all,
        config=proxy_config("USATECH_PROXY_FULL"),
        minimum_range_coverage=0.95,
        proxy_gap_policy=True,
        include_unfiltered=True,
        fomc_dates=ALL_FOMC,
    )
    oos_trades: dict[str, pd.DataFrame] = {}
    oos_rows = []
    for arm, all_trades in proxy_full["trades"].items():
        selected = all_trades.loc[
            pd.to_datetime(all_trades["entry_time"]) >= pd.Timestamp("2026-01-01")
        ].copy()
        oos_trades[arm] = selected
        oos_rows.append(summarize_oos(selected, arm))
        selected.to_csv(args.out / f"proxy_2026_{arm}_trades.csv", index=False)
    oos_summary = pd.DataFrame(oos_rows)
    oos_summary.to_csv(args.out / "proxy_2026_oos_summary.csv", index=False)

    inference = [
        {
            "comparison": "E6_MINUS_UNFILTERED",
            **paired_date_delta(
                oos_trades["UNFILTERED"],
                oos_trades["E6"],
                iterations=args.iterations,
                seed=20260725,
            ),
        },
        {
            "comparison": "NO_FOMC_MINUS_E6",
            **paired_date_delta(
                oos_trades["E6"],
                oos_trades["E6_NO_FOMC_DAY"],
                iterations=args.iterations,
                seed=20260726,
            ),
        },
    ]
    pd.DataFrame(inference).to_csv(
        args.out / "proxy_2026_incremental_inference.csv", index=False
    )

    proxy_audit["overlap_active_rows"] = len(proxy_overlap)
    proxy_audit["oos_active_rows"] = int(
        (proxy_all["timestamp"] >= pd.Timestamp("2026-01-01")).sum()
    )
    (args.out / "proxy_qualification.json").write_text(
        json.dumps(proxy_audit, indent=2)
    )

    five_minute_correlation = float(
        price.loc[price["metric"] == "five_minute", "pearson"].iloc[0]
    )
    direction_agreement = float(decisions["direction_agreement"])
    unfiltered_oos = oos_summary.loc[oos_summary["arm"] == "UNFILTERED"].iloc[0]
    decision = classify_proxy_oos(
        five_minute_correlation=five_minute_correlation,
        direction_agreement=direction_agreement,
        unfiltered_trades=int(unfiltered_oos["trades"]),
        unfiltered_net_r=float(unfiltered_oos["net_r"]),
        unfiltered_expectancy_r=float(unfiltered_oos["expectancy_r"]),
        unfiltered_two_tick_expectancy_r=float(
            unfiltered_oos["two_tick_expectancy_r"]
        ),
    )

    final = {
        "study_id": "DTR-NQ-WP-20260722-19",
        "decision": decision,
        "proxy_is_not_cme_nq_futures": True,
        "price_concordance": price.to_dict("records"),
        "decision_concordance": decisions,
        "overlap_arms": overlap_summary.to_dict("records"),
        "proxy_2026_oos": oos_summary.to_dict("records"),
        "incremental_inference": inference,
        "restrictions": [
            "no proxy retuning",
            "no pooled returns",
            "no live sizing",
            "no Pine or deployment authorization",
        ],
    }
    (args.out / "decision.json").write_text(
        json.dumps(final, indent=2, default=str)
    )
    hashes = {
        path.name: sha256(path)
        for path in sorted(args.out.iterdir())
        if path.is_file()
    }
    (args.out / "artifact_hashes.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True)
    )
    print(overlap_summary.to_string(index=False))
    print(oos_summary.to_string(index=False))
    print(json.dumps(final, indent=2, default=str))


if __name__ == "__main__":
    main()
