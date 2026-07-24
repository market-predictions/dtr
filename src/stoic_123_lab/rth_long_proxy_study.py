from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from . import (
    NQ_PROXY_SPEC,
    date_block_bootstrap,
    detect_sequences,
    independent_trade_review,
    resample_ohlcv,
    summarize,
)
from .validation import (
    delay_events,
    detect_long_stage_events,
    entry_config,
    evaluate_trades,
    full_sequence_events,
    management_config,
    run_scenario,
)
from .validation_rth_long import (
    filter_entry_events_by_session,
    matched_time_rth_long_events,
    session_label,
)

SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
MATCHED_REPLICATES = 50
RTH_PROXY_SPEC = replace(
    NQ_PROXY_SPEC,
    source_sha256="partitioned-checksum-gated-rth-source",
    source_classification=(
        "Dukascopy USATECH bid-CFD RTH validation partitions; not CME NQ futures"
    ),
)


def _return_to_drawdown(summary: dict[str, object]) -> float:
    drawdown = float(summary["max_drawdown_r"])
    return float(summary["net_r"]) / drawdown if drawdown > 0 else np.nan


def _annual_rows(
    trades: pd.DataFrame,
    *,
    partition: str,
    scenario_id: str,
) -> list[dict[str, object]]:
    if trades.empty:
        return []
    years = pd.to_datetime(trades["entry_time"]).dt.year
    rows: list[dict[str, object]] = []
    for year in sorted(years.unique()):
        group = trades.loc[years == year]
        rows.append(
            {
                "partition": partition,
                "scenario_id": scenario_id,
                "year": int(year),
                **summarize(group, instrument="NQ_PROXY", arm_id=scenario_id),
            }
        )
    return rows


def _exit_rows(
    trades: pd.DataFrame,
    *,
    partition: str,
    scenario_id: str,
) -> list[dict[str, object]]:
    if trades.empty:
        return []
    rows: list[dict[str, object]] = []
    for reason, group in trades.groupby("exit_reason", sort=True):
        rows.append(
            {
                "partition": partition,
                "scenario_id": scenario_id,
                "exit_reason": str(reason),
                "trades": int(len(group)),
                "net_r": float(group["pnl_r"].sum()),
                "expectancy_r": float(group["pnl_r"].mean()),
            }
        )
    return rows


def _evaluate_scenario(
    *,
    partition: str,
    scenario_id: str,
    one_minute: pd.DataFrame,
    events: pd.DataFrame,
    management_events: pd.DataFrame,
    config: object,
    iterations: int,
    seed: int,
    out: Path,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    pd.DataFrame,
]:
    scenario_config = replace(config, arm_id=scenario_id, description=scenario_id)
    trades = run_scenario(
        one_minute=one_minute,
        events=events,
        management_events=management_events,
        spec=RTH_PROXY_SPEC,
        config=scenario_config,
    )
    source_start = pd.Timestamp(one_minute["timestamp"].min())
    source_end = pd.Timestamp(one_minute["timestamp"].max())
    summary = evaluate_trades(
        trades,
        instrument="NQ_PROXY",
        arm_id=scenario_id,
        source_start=source_start,
        source_end=source_end,
    )
    summary["partition"] = partition
    summary["return_to_drawdown"] = _return_to_drawdown(summary)
    inference = date_block_bootstrap(trades, iterations=iterations, seed=seed)
    review = independent_trade_review(
        trades,
        summary,
        instrument="NQ_PROXY",
        arm_id=scenario_id,
    )
    events.to_csv(out / f"{partition}__{scenario_id}__events.csv", index=False)
    trades.to_csv(out / f"{partition}__{scenario_id}__trades.csv", index=False)
    return (
        summary,
        {"partition": partition, "scenario_id": scenario_id, **inference},
        {"partition": partition, **review},
        trades,
    )


def _matched_control(
    *,
    partition: str,
    candidate_name: str,
    one_minute: pd.DataFrame,
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    management: pd.DataFrame,
    candidate_events: pd.DataFrame,
    candidate_config: object,
    candidate_summary: dict[str, object],
    seed_base: int,
    out: Path,
) -> dict[str, object]:
    metrics: list[dict[str, object]] = []
    coverages: list[float] = []
    for replicate in range(MATCHED_REPLICATES):
        events = matched_time_rth_long_events(
            candidate_events,
            execution_bars,
            map_bars,
            candidate_config,
            seed=seed_base + replicate,
        )
        coverages.append(float(events.attrs.get("match_fraction", 0.0)))
        config = replace(
            candidate_config,
            arm_id=(
                f"{SOURCE_ARM_ID}__{partition}__{candidate_name}__"
                f"MATCHED_RTH_LONG_{replicate:03d}"
            ),
        )
        trades = run_scenario(
            one_minute=one_minute,
            events=events,
            management_events=management,
            spec=RTH_PROXY_SPEC,
            config=config,
        )
        metrics.append(
            summarize(
                trades,
                instrument="NQ_PROXY",
                arm_id=config.arm_id,
            )
        )
        if replicate == 0:
            events.to_csv(
                out / f"{partition}__{candidate_name}__MATCHED_RTH_EXAMPLE__events.csv",
                index=False,
            )
            trades.to_csv(
                out / f"{partition}__{candidate_name}__MATCHED_RTH_EXAMPLE__trades.csv",
                index=False,
            )

    frame = pd.DataFrame(metrics)
    full_hold = float(candidate_summary["median_hold_minutes"])
    matched_hold = float(frame["median_hold_minutes"].median())
    hold_ratio = matched_hold / full_hold if full_hold > 0 else np.nan
    full_expectancy = float(candidate_summary["expectancy_r"])
    matched_p95 = float(frame["expectancy_r"].quantile(0.95))
    minimum_coverage = float(min(coverages)) if coverages else 0.0
    comparable = bool(
        minimum_coverage >= 0.90
        and np.isfinite(hold_ratio)
        and 0.75 <= hold_ratio <= 1.25
    )
    return {
        "partition": partition,
        "candidate": candidate_name,
        "replicates": MATCHED_REPLICATES,
        "full_expectancy_r": full_expectancy,
        "matched_median_expectancy_r": float(frame["expectancy_r"].median()),
        "matched_p95_expectancy_r": matched_p95,
        "full_expectancy_exceeds_matched_p95": full_expectancy > matched_p95,
        "minimum_event_match_fraction": minimum_coverage,
        "full_median_hold_minutes": full_hold,
        "matched_median_hold_minutes": matched_hold,
        "matched_to_full_hold_ratio": hold_ratio,
        "matched_control_comparable": comparable,
        "matched_control_passed": comparable and full_expectancy > matched_p95,
    }


def _assert_rth_events(events: pd.DataFrame, scenario: str) -> None:
    if events.empty:
        return
    invalid = [
        value
        for value in pd.to_datetime(events["signal_time"])
        if session_label(value) != "RTH"
    ]
    if invalid:
        raise RuntimeError(f"{scenario} contains non-RTH entry signals")


def run_rth_partition(
    *,
    partition: str,
    one_minute: pd.DataFrame,
    base: object,
    iterations: int,
    seed_base: int,
    out: Path,
) -> dict[str, object]:
    execution_bars = resample_ohlcv(one_minute, base.execution_minutes)
    management_bars = resample_ohlcv(one_minute, base.management_minutes)
    map_bars = resample_ohlcv(one_minute, base.map_minutes)
    management = detect_sequences(
        management_bars,
        map_bars,
        management_config(base),
    ).events
    management.to_csv(out / f"{partition}__management_events.csv", index=False)

    long_config = entry_config(base, "long_only")
    full_events = full_sequence_events(
        execution_bars,
        map_bars,
        base,
        direction_mode="long_only",
    )
    break_events = detect_long_stage_events(
        execution_bars,
        map_bars,
        long_config,
        model="ema_break",
    ).events
    retest_events = detect_long_stage_events(
        execution_bars,
        map_bars,
        long_config,
        model="ema_break_retest",
    ).events

    rth_full = filter_entry_events_by_session(full_events, session="RTH")
    overnight_full = filter_entry_events_by_session(full_events, session="OVERNIGHT")
    rth_break = filter_entry_events_by_session(break_events, session="RTH")
    rth_retest = filter_entry_events_by_session(retest_events, session="RTH")
    _assert_rth_events(rth_full, "RTH_LONG_FULL")
    _assert_rth_events(rth_break, "RTH_LONG_EMA_BREAK")
    _assert_rth_events(rth_retest, "RTH_LONG_EMA_BREAK_RETEST")

    scenarios = [
        ("FULL_SESSION_LONG_FULL", full_events, long_config),
        ("OVERNIGHT_ENTRY_LONG_FULL", overnight_full, long_config),
        ("RTH_LONG_FULL", rth_full, long_config),
        ("RTH_LONG_EMA_BREAK", rth_break, long_config),
        ("RTH_LONG_EMA_BREAK_RETEST", rth_retest, long_config),
        (
            "RTH_LONG_FULL_COST_2T",
            rth_full,
            replace(long_config, slippage_ticks_each_side=2.0),
        ),
        ("RTH_LONG_FULL_DELAY_1M", delay_events(rth_full, 1), long_config),
        ("RTH_LONG_FULL_DELAY_5M", delay_events(rth_full, 5), long_config),
        (
            "RTH_LONG_EMA_BREAK_COST_2T",
            rth_break,
            replace(long_config, slippage_ticks_each_side=2.0),
        ),
        ("RTH_LONG_EMA_BREAK_DELAY_1M", delay_events(rth_break, 1), long_config),
        ("RTH_LONG_EMA_BREAK_DELAY_5M", delay_events(rth_break, 5), long_config),
    ]

    summaries: dict[str, dict[str, object]] = {}
    inferences: dict[str, dict[str, object]] = {}
    summary_rows: list[dict[str, object]] = []
    inference_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    exit_rows: list[dict[str, object]] = []
    for index, (name, events, config) in enumerate(scenarios):
        scenario_id = f"{SOURCE_ARM_ID}__{name}"
        summary, inference, review, trades = _evaluate_scenario(
            partition=partition,
            scenario_id=scenario_id,
            one_minute=one_minute,
            events=events,
            management_events=management,
            config=config,
            iterations=iterations,
            seed=seed_base + index,
            out=out,
        )
        summaries[name] = summary
        inferences[name] = inference
        summary_rows.append(summary)
        inference_rows.append(inference)
        review_rows.append(review)
        annual_rows.extend(_annual_rows(trades, partition=partition, scenario_id=scenario_id))
        exit_rows.extend(_exit_rows(trades, partition=partition, scenario_id=scenario_id))

    matched = [
        _matched_control(
            partition=partition,
            candidate_name="RTH_LONG_EMA_BREAK",
            one_minute=one_minute,
            execution_bars=execution_bars,
            map_bars=map_bars,
            management=management,
            candidate_events=rth_break,
            candidate_config=long_config,
            candidate_summary=summaries["RTH_LONG_EMA_BREAK"],
            seed_base=seed_base + 10_000,
            out=out,
        ),
        _matched_control(
            partition=partition,
            candidate_name="RTH_LONG_FULL",
            one_minute=one_minute,
            execution_bars=execution_bars,
            map_bars=map_bars,
            management=management,
            candidate_events=rth_full,
            candidate_config=long_config,
            candidate_summary=summaries["RTH_LONG_FULL"],
            seed_base=seed_base + 20_000,
            out=out,
        ),
    ]
    return {
        "summaries": summaries,
        "inferences": inferences,
        "summary_rows": summary_rows,
        "inference_rows": inference_rows,
        "review_rows": review_rows,
        "annual_rows": annual_rows,
        "exit_rows": exit_rows,
        "matched_rows": matched,
        "management_direction_count": int(management["direction"].nunique())
        if not management.empty
        else 0,
    }
