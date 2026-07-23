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
    entry_config,
    evaluate_trades,
    full_sequence_events,
    management_config,
    run_scenario,
)
from .validation_short_direction import detect_short_stage_events
from .validation_short_matching import matched_time_short_events

SOURCE_ARM_ID = "S123_M0_NO_MAP_CONTROL"
MATCHED_REPLICATES = 50
SHORT_PROXY_SPEC = replace(
    NQ_PROXY_SPEC,
    source_sha256="partitioned-checksum-gated-source",
    source_classification=(
        "Dukascopy USATECH bid-CFD disjoint proxy partitions; not CME NQ futures"
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
) -> tuple[dict[str, object], dict[str, object], dict[str, object], pd.DataFrame]:
    scenario_config = replace(config, arm_id=scenario_id, description=scenario_id)
    trades = run_scenario(
        one_minute=one_minute,
        events=events,
        management_events=management_events,
        spec=SHORT_PROXY_SPEC,
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
    one_minute: pd.DataFrame,
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    management: pd.DataFrame,
    short_events: pd.DataFrame,
    short_config: object,
    short_summary: dict[str, object],
    seed_base: int,
    out: Path,
) -> dict[str, object]:
    metrics: list[dict[str, object]] = []
    coverages: list[float] = []
    for replicate in range(MATCHED_REPLICATES):
        events = matched_time_short_events(
            short_events,
            execution_bars,
            map_bars,
            short_config,
            seed=seed_base + replicate,
        )
        coverages.append(float(events.attrs.get("match_fraction", 0.0)))
        config = replace(
            short_config,
            arm_id=f"{SOURCE_ARM_ID}__{partition}__MATCHED_SHORT_{replicate:03d}",
        )
        trades = run_scenario(
            one_minute=one_minute,
            events=events,
            management_events=management,
            spec=SHORT_PROXY_SPEC,
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
                out / f"{partition}__MATCHED_SHORT_EXAMPLE__events.csv",
                index=False,
            )
            trades.to_csv(
                out / f"{partition}__MATCHED_SHORT_EXAMPLE__trades.csv",
                index=False,
            )

    frame = pd.DataFrame(metrics)
    full_hold = float(short_summary["median_hold_minutes"])
    matched_hold = float(frame["median_hold_minutes"].median())
    hold_ratio = matched_hold / full_hold if full_hold > 0 else np.nan
    full_expectancy = float(short_summary["expectancy_r"])
    matched_p95 = float(frame["expectancy_r"].quantile(0.95))
    minimum_coverage = float(min(coverages)) if coverages else 0.0
    comparable = bool(
        minimum_coverage >= 0.90
        and np.isfinite(hold_ratio)
        and 0.75 <= hold_ratio <= 1.25
    )
    return {
        "partition": partition,
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


def _run_partition(
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

    both_config = entry_config(base, "both")
    long_config = entry_config(base, "long_only")
    short_config = entry_config(base, "short_only")
    both_events = full_sequence_events(
        execution_bars,
        map_bars,
        base,
        direction_mode="both",
    )
    long_events = full_sequence_events(
        execution_bars,
        map_bars,
        base,
        direction_mode="long_only",
    )
    short_events = full_sequence_events(
        execution_bars,
        map_bars,
        base,
        direction_mode="short_only",
    )
    break_events = detect_short_stage_events(
        execution_bars,
        map_bars,
        short_config,
        model="ema_break",
    ).events
    retest_events = detect_short_stage_events(
        execution_bars,
        map_bars,
        short_config,
        model="ema_break_retest",
    ).events

    scenarios = [
        ("BOTH_FULL", both_events, both_config),
        ("LONG_FULL", long_events, long_config),
        ("SHORT_FULL", short_events, short_config),
        ("SHORT_EMA_BREAK", break_events, short_config),
        ("SHORT_EMA_BREAK_RETEST", retest_events, short_config),
        (
            "SHORT_FULL_COST_2T",
            short_events,
            replace(short_config, slippage_ticks_each_side=2.0),
        ),
        ("SHORT_FULL_DELAY_1M", delay_events(short_events, 1), short_config),
        ("SHORT_FULL_DELAY_5M", delay_events(short_events, 5), short_config),
    ]

    summaries: dict[str, dict[str, object]] = {}
    inferences: dict[str, dict[str, object]] = {}
    summary_rows: list[dict[str, object]] = []
    inference_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    annual: list[dict[str, object]] = []
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
        annual.extend(_annual_rows(trades, partition=partition, scenario_id=scenario_id))

    matched = _matched_control(
        partition=partition,
        one_minute=one_minute,
        execution_bars=execution_bars,
        map_bars=map_bars,
        management=management,
        short_events=short_events,
        short_config=short_config,
        short_summary=summaries["SHORT_FULL"],
        seed_base=seed_base + 10_000,
        out=out,
    )
    return {
        "summaries": summaries,
        "inferences": inferences,
        "summary_rows": summary_rows,
        "inference_rows": inference_rows,
        "review_rows": review_rows,
        "annual_rows": annual,
        "matched": matched,
        "management_direction_count": int(management["direction"].nunique())
        if not management.empty
        else 0,
    }
