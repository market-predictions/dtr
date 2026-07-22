from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.data.gaps import classify_gaps
from dtr_lab.research import engine
from dtr_lab.research.cross_market import (
    NQ_SPEC,
    PRIMARY_END_ET,
    PRIMARY_START_ET,
    USA500_PROXY_SPEC,
    build_covered_session_table,
    classify_proxy_gaps,
    classify_proxy_replication,
    cost_stress_expectancy,
    date_block_bootstrap,
    e6_mask,
    load_usa500_proxy,
    no_fomc_mask,
    summarize_arm,
)

FOMC_DATES = set(
    pd.to_datetime(
        [
            "2023-02-01",
            "2023-03-22",
            "2023-05-03",
            "2023-06-14",
            "2023-07-26",
            "2023-09-20",
            "2023-11-01",
            "2023-12-13",
            "2024-01-31",
            "2024-03-20",
            "2024-05-01",
            "2024-06-12",
            "2024-07-31",
            "2024-09-18",
            "2024-11-07",
            "2024-12-18",
            "2025-01-29",
            "2025-03-19",
            "2025-05-07",
            "2025-06-18",
            "2025-07-30",
            "2025-09-17",
            "2025-10-29",
            "2025-12-10",
        ]
    ).normalize()
)

NQ_REGRESSION = {
    "E6": (304, 48.93754952687199, 0.16097878133839472, 8.632571354238342),
    "E6_NO_FOMC_DAY": (291, 53.48334196741127, 0.18379155315261606, 9.151060839915637),
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_nq(path: Path) -> pd.DataFrame:
    if file_sha256(path) != NQ_SPEC.source_sha256:
        raise ValueError("NQ source checksum mismatch")
    frame = engine.load_zip(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]) - pd.Timedelta(minutes=1)
    return (
        frame.loc[
            (frame["timestamp"] >= PRIMARY_START_ET)
            & (frame["timestamp"] <= PRIMARY_END_ET)
        ]
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def attach_gap_metadata(bars: pd.DataFrame, gaps: pd.DataFrame) -> pd.DataFrame:
    reset = (
        pd.to_datetime(gaps.loc[gaps["reset_strategy_state"], "current_timestamp"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    unsafe = (
        pd.to_datetime(gaps.loc[gaps["reject_trade_bridge"], "current_timestamp"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    starts = bars["timestamp"].to_numpy(dtype="datetime64[ns]").astype(np.int64)
    ends = bars["bar_end"].to_numpy(dtype="datetime64[ns]").astype(np.int64)
    work = bars.copy()
    work["state_epoch_start"] = np.searchsorted(reset, starts, side="left")
    work["state_epoch_end"] = np.searchsorted(reset, ends, side="left")
    work["unsafe_epoch_start"] = np.searchsorted(unsafe, starts, side="left")
    work["unsafe_epoch_end"] = np.searchsorted(unsafe, ends, side="left")
    work["contains_reset_gap"] = work["state_epoch_end"] > work["state_epoch_start"]
    work["contains_unsafe_gap"] = work["unsafe_epoch_end"] > work["unsafe_epoch_start"]
    return work


def sanitize_sessions(
    sessions: pd.DataFrame,
    bars: pd.DataFrame,
    gaps: pd.DataFrame,
) -> pd.DataFrame:
    reset = gaps.loc[
        gaps["reset_strategy_state"],
        ["previous_timestamp", "current_timestamp"],
    ].copy()
    reset["previous_timestamp"] = pd.to_datetime(reset["previous_timestamp"])
    reset["current_timestamp"] = pd.to_datetime(reset["current_timestamp"])
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    original: list[int] = []
    rejected: list[bool] = []
    truncated: list[bool] = []
    adjusted: list[int] = []
    for row in sessions.itertuples(index=False):
        original_end = int(row.post_end_index)
        original.append(original_end)
        range_overlap = (reset["previous_timestamp"] < row.range_end) & (
            reset["current_timestamp"] > row.range_start
        )
        rejected.append(bool(range_overlap.any()))
        path_overlap = (reset["previous_timestamp"] < row.break_end) & (
            reset["current_timestamp"] > row.range_end
        )
        new_end = original_end
        was_truncated = False
        if path_overlap.any():
            first = reset.loc[path_overlap].iloc[0]
            first_missing = max(
                pd.Timestamp(first["previous_timestamp"]) + pd.Timedelta(minutes=1),
                pd.Timestamp(row.range_end),
            )
            gap_bar = max(
                0,
                int(
                    np.searchsorted(
                        bar_times,
                        np.datetime64(first_missing),
                        side="right",
                    )
                    - 1
                ),
            )
            if gap_bar < new_end:
                new_end = gap_bar
                was_truncated = True
        adjusted.append(new_end)
        truncated.append(was_truncated)
    work = sessions.copy()
    work["integrity_original_post_end_index"] = original
    work["post_end_index"] = adjusted
    work["integrity_range_gap_rejected"] = rejected
    work["integrity_signal_path_truncated"] = truncated
    return work


def simulate_all_signals(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    signals: list[engine.CandidateSignal],
    config: engine.StrategyConfig,
    gaps: pd.DataFrame,
) -> dict[int, engine.Trade]:
    times, open_, high, low, close = engine.prepare_market_arrays(one_minute)
    unsafe = gaps.loc[
        gaps["reject_trade_bridge"],
        ["previous_timestamp", "current_timestamp"],
    ]
    unsafe_previous = (
        pd.to_datetime(unsafe["previous_timestamp"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    unsafe_current = (
        pd.to_datetime(unsafe["current_timestamp"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    result: dict[int, engine.Trade] = {}
    for signal_id, signal in enumerate(signals):
        trade = engine._simulate_trade_np(
            times,
            open_,
            high,
            low,
            close,
            bars,
            signal,
            config,
            unsafe_previous_ns=unsafe_previous,
            unsafe_current_ns=unsafe_current,
            gap_policy="liquidate",
        )
        if trade is not None:
            result[signal_id] = trade
    return result


def sequence_portfolio(
    signal_features: pd.DataFrame,
    trades_by_signal: dict[int, engine.Trade],
    mask: pd.Series,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    next_free = pd.Timestamp.min
    selected = signal_features.loc[mask.fillna(False)].sort_values("entry_time")
    for row in selected.itertuples(index=False):
        trade = trades_by_signal.get(int(row.signal_id))
        if trade is None or pd.Timestamp(row.entry_time) < next_free:
            continue
        rows.append(asdict(trade))
        next_free = pd.Timestamp(trade.exit_time)
    return pd.DataFrame(rows)


def add_e6_features(
    one_minute: pd.DataFrame,
    sessions: pd.DataFrame,
    signal_features: pd.DataFrame,
) -> pd.DataFrame:
    one = one_minute.copy()
    one["eth_day"] = (one["timestamp"] - pd.Timedelta(hours=18)).dt.normalize()
    daily = (
        one.groupby("eth_day", as_index=False)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .sort_values("eth_day")
    )
    previous_close = daily["close"].shift(1)
    true_range = pd.concat(
        [
            daily["high"] - daily["low"],
            (daily["high"] - previous_close).abs(),
            (daily["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    daily["atr20"] = true_range.ewm(
        alpha=1 / 20,
        adjust=False,
        min_periods=20,
    ).mean()
    daily["complete_time"] = daily["eth_day"] + pd.Timedelta(days=1, hours=17)
    session_features = pd.merge_asof(
        sessions.sort_values("range_start"),
        daily[["complete_time", "high", "low", "atr20"]].sort_values("complete_time"),
        left_on="range_start",
        right_on="complete_time",
        direction="backward",
        allow_exact_matches=True,
    ).rename(
        columns={
            "high": "prev_d1_high",
            "low": "prev_d1_low",
            "atr20": "d1_atr20",
        }
    )
    return signal_features.merge(
        session_features[
            [
                "session_date",
                "session",
                "prev_d1_high",
                "prev_d1_low",
                "d1_atr20",
            ]
        ],
        on=["session_date", "session"],
        how="left",
        validate="many_to_one",
    )


def run_instrument(
    *,
    instrument: str,
    one_minute: pd.DataFrame,
    config: engine.StrategyConfig,
    minimum_range_coverage: float,
    proxy_gap_policy: bool,
) -> dict[str, object]:
    gaps = (
        classify_proxy_gaps(one_minute)
        if proxy_gap_policy
        else classify_gaps(one_minute, timestamp_column="timestamp")
    )
    bars = attach_gap_metadata(engine.resample_5m(one_minute), gaps)
    raw_sessions = build_covered_session_table(
        one_minute,
        bars,
        minimum_coverage=minimum_range_coverage,
    )
    sessions = sanitize_sessions(raw_sessions, bars, gaps)
    eligible = sessions.loc[~sessions["integrity_range_gap_rejected"]].copy()
    signals, funnel = engine.generate_signals(bars, eligible, config)
    cached = simulate_all_signals(one_minute, bars, signals, config, gaps)
    signal_rows = [
        {
            "signal_id": signal_id,
            "session": signal.session,
            "session_date": pd.Timestamp(signal.session_date).normalize(),
            "weekday": signal.day_of_week,
            "direction": signal.direction,
            "entry_time": signal.entry_time,
            "range_high": signal.range_high,
            "range_low": signal.range_low,
        }
        for signal_id, signal in enumerate(signals)
    ]
    signal_features = add_e6_features(
        one_minute,
        eligible,
        pd.DataFrame(signal_rows),
    )
    masks = {
        "E6": e6_mask(signal_features),
        "E6_NO_FOMC_DAY": e6_mask(signal_features)
        & no_fomc_mask(signal_features, FOMC_DATES),
    }
    eligible_count = int(
        eligible.loc[
            eligible["weekday"].isin(config.weekdays)
            & eligible["session"].isin(config.sessions)
        ].shape[0]
    )
    arm_trades: dict[str, pd.DataFrame] = {}
    summaries: list[dict[str, object]] = []
    for arm, mask in masks.items():
        trades = sequence_portfolio(signal_features, cached, mask)
        arm_trades[arm] = trades
        summaries.append(
            summarize_arm(
                trades,
                instrument=instrument,
                arm=arm,
                eligible_sessions=eligible_count,
                candidate_signals=int(mask.sum()),
                tick_size=config.tick_size,
            )
        )
    return {
        "summary": pd.DataFrame(summaries),
        "trades": arm_trades,
        "signals": signal_features,
        "funnel": funnel.as_dict(),
        "gaps": gaps,
        "bars": bars,
        "sessions": sessions,
        "eligible_sessions": eligible,
    }


def validate_nq_regression(summary: pd.DataFrame) -> None:
    for arm, expected in NQ_REGRESSION.items():
        row = summary.loc[summary["arm"] == arm].iloc[0]
        observed = (
            int(row["trades"]),
            float(row["net_r"]),
            float(row["expectancy_r"]),
            float(row["max_drawdown_r"]),
        )
        for actual, target in zip(observed, expected, strict=True):
            if not np.isclose(actual, target, atol=1e-9, rtol=0):
                raise RuntimeError(
                    f"NQ {arm} regression mismatch: {actual!r} != {target!r}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen NQ versus Dukascopy USA500 proxy replication"
    )
    parser.add_argument("--nq", type=Path, required=True)
    parser.add_argument("--usa500", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    nq = run_instrument(
        instrument="NQ",
        one_minute=load_nq(args.nq),
        config=NQ_SPEC.strategy_config(name="NQ_E6_PARALLEL"),
        minimum_range_coverage=NQ_SPEC.minimum_range_coverage,
        proxy_gap_policy=False,
    )
    validate_nq_regression(nq["summary"])

    proxy_path = args.usa500.resolve()
    if file_sha256(proxy_path) != USA500_PROXY_SPEC.source_sha256:
        raise ValueError("USA500 proxy source checksum mismatch")
    proxy = run_instrument(
        instrument="USA500_PROXY",
        one_minute=load_usa500_proxy(proxy_path),
        config=USA500_PROXY_SPEC.strategy_config(name="USA500_PROXY_E6_PARALLEL"),
        minimum_range_coverage=USA500_PROXY_SPEC.minimum_range_coverage,
        proxy_gap_policy=True,
    )

    summary = pd.concat([nq["summary"], proxy["summary"]], ignore_index=True)
    proxy_e6 = summary.loc[
        (summary["instrument"] == "USA500_PROXY") & (summary["arm"] == "E6")
    ].iloc[0]
    classification = classify_proxy_replication(proxy_e6)
    summary["replication_classification"] = "NQ_REFERENCE"
    summary.loc[
        summary["instrument"] == "USA500_PROXY",
        "replication_classification",
    ] = classification
    summary.to_csv(args.out / "parallel_summary.csv", index=False)

    inference: list[dict[str, object]] = []
    for instrument_name, result, offset in (
        ("NQ", nq, 0),
        ("USA500_PROXY", proxy, 100),
    ):
        for arm_index, arm in enumerate(("E6", "E6_NO_FOMC_DAY")):
            trades = result["trades"][arm]
            trades.to_csv(
                args.out / f"{instrument_name}__{arm}__trades.csv",
                index=False,
            )
            inference.append(
                {
                    "instrument": instrument_name,
                    "arm": arm,
                    **date_block_bootstrap(
                        trades,
                        iterations=args.iterations,
                        seed=20260722 + offset + arm_index,
                    ),
                }
            )
    pd.DataFrame(inference).to_csv(args.out / "parallel_inference.csv", index=False)

    decision = {
        "study_id": "DTR-CROSSMARKET-WP-20260722-18",
        "decision": classification,
        "nq_regression": "PASS",
        "proxy_is_not_es_futures": True,
        "restrictions": [
            "no pooled portfolio",
            "no proxy-specific tuning",
            "no CME ES execution claim",
            "no live sizing, Pine or deployment authorization",
        ],
    }
    (args.out / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(summary.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
