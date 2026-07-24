from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict, replace
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from . import (
    ES_PROXY_SPEC,
    date_block_bootstrap,
    detect_sequences,
    independent_trade_review,
    resample_ohlcv,
    summarize,
)
from .config import InstrumentSpec, SequenceConfig
from .cost_repricing import reprice_single_stream_costs
from .research_cache import FrameCache
from .research_runtime import ResearchPlan, StageTimer, plan_for_mode
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
USA500_RTH_SPEC = replace(
    ES_PROXY_SPEC,
    source_sha256="partitioned-checksum-gated-usa500-rth-source",
    source_classification=(
        "Dukascopy USA500 bid-CFD RTH cross-asset partitions with ES-equivalent "
        "research economics; not CME ES futures"
    ),
)


def _measure(timer: StageTimer | None, stage: str, **metadata: object):
    return timer.measure(stage, **metadata) if timer is not None else nullcontext()


def _cached_frame(
    cache: FrameCache | None,
    namespace: str,
    components: dict[str, object],
    builder: Callable[[], pd.DataFrame],
) -> pd.DataFrame:
    if cache is None:
        return builder()
    frame, _, _ = cache.get_or_build(namespace, components, builder)
    return frame


def _return_to_drawdown(summary: dict[str, object]) -> float:
    drawdown = float(summary["max_drawdown_r"])
    return float(summary["net_r"]) / drawdown if drawdown > 0 else np.nan


def _annual_rows(
    trades: pd.DataFrame,
    *,
    partition: str,
    scenario_id: str,
    instrument: str,
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
                **summarize(group, instrument=instrument, arm_id=scenario_id),
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


def _skipped_inference(trades: pd.DataFrame) -> dict[str, object]:
    blocks = (
        int(pd.to_datetime(trades["entry_time"]).dt.normalize().nunique())
        if not trades.empty
        else 0
    )
    return {
        "status": "SKIPPED",
        "iterations": 0,
        "blocks": blocks,
        "observed_expectancy_r": (
            float(trades["pnl_r"].mean()) if not trades.empty else np.nan
        ),
        "lo95_expectancy_r": np.nan,
        "hi95_expectancy_r": np.nan,
        "prob_expectancy_positive": np.nan,
    }


def _skipped_review(instrument: str, arm_id: str) -> dict[str, object]:
    return {
        "instrument": instrument,
        "arm_id": arm_id,
        "status": "SKIPPED",
        "observed_trades": np.nan,
        "observed_net_r": np.nan,
        "observed_expectancy_r": np.nan,
        "count_match": np.nan,
        "net_match": np.nan,
        "expectancy_match": np.nan,
        "overlap_count": np.nan,
        "invalid_risk_count": np.nan,
        "invalid_chronology_count": np.nan,
    }


def _evaluate_trade_ledger(
    *,
    partition: str,
    scenario_name: str,
    scenario_id: str,
    one_minute: pd.DataFrame,
    events: pd.DataFrame,
    trades: pd.DataFrame,
    instrument: str,
    bootstrap_iterations: int,
    seed: int,
    run_review: bool,
    write_ledgers: bool,
    out: Path,
    timer: StageTimer | None,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    pd.DataFrame,
]:
    source_start = pd.Timestamp(one_minute["timestamp"].min())
    source_end = pd.Timestamp(one_minute["timestamp"].max())
    summary = evaluate_trades(
        trades,
        instrument=instrument,
        arm_id=scenario_id,
        source_start=source_start,
        source_end=source_end,
    )
    summary["partition"] = partition
    summary["return_to_drawdown"] = _return_to_drawdown(summary)

    if bootstrap_iterations:
        with _measure(
            timer,
            "bootstrap",
            partition=partition,
            scenario=scenario_name,
            iterations=bootstrap_iterations,
        ):
            inference = {
                "status": "COMPLETED",
                "iterations": bootstrap_iterations,
                **date_block_bootstrap(
                    trades,
                    iterations=bootstrap_iterations,
                    seed=seed,
                ),
            }
    else:
        inference = _skipped_inference(trades)

    if run_review:
        with _measure(timer, "independent_review", partition=partition, scenario=scenario_name):
            review = independent_trade_review(
                trades,
                summary,
                instrument=instrument,
                arm_id=scenario_id,
            )
    else:
        review = _skipped_review(instrument, scenario_id)

    if write_ledgers:
        events.to_csv(out / f"{partition}__{scenario_id}__events.csv", index=False)
        trades.to_csv(out / f"{partition}__{scenario_id}__trades.csv", index=False)
    return (
        summary,
        {"partition": partition, "scenario_id": scenario_id, **inference},
        {"partition": partition, **review},
        trades,
    )


def _evaluate_scenario(
    *,
    partition: str,
    scenario_name: str,
    scenario_id: str,
    one_minute: pd.DataFrame,
    events: pd.DataFrame,
    management_events: pd.DataFrame,
    config: SequenceConfig,
    spec: InstrumentSpec,
    instrument: str,
    bootstrap_iterations: int,
    seed: int,
    run_review: bool,
    write_ledgers: bool,
    out: Path,
    timer: StageTimer | None,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    pd.DataFrame,
]:
    scenario_config = replace(config, arm_id=scenario_id, description=scenario_id)
    with _measure(timer, "simulate", partition=partition, scenario=scenario_name):
        trades = run_scenario(
            one_minute=one_minute,
            events=events,
            management_events=management_events,
            spec=spec,
            config=scenario_config,
        )
    return _evaluate_trade_ledger(
        partition=partition,
        scenario_name=scenario_name,
        scenario_id=scenario_id,
        one_minute=one_minute,
        events=events,
        trades=trades,
        instrument=instrument,
        bootstrap_iterations=bootstrap_iterations,
        seed=seed,
        run_review=run_review,
        write_ledgers=write_ledgers,
        out=out,
        timer=timer,
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
    candidate_config: SequenceConfig,
    candidate_summary: dict[str, object],
    spec: InstrumentSpec,
    instrument: str,
    seed_base: int,
    out: Path,
    replicates: int,
    write_ledgers: bool,
    timer: StageTimer | None,
) -> dict[str, object]:
    if replicates <= 0:
        raise ValueError("matched control replicates must be positive")
    metrics: list[dict[str, object]] = []
    coverages: list[float] = []
    with _measure(
        timer,
        "matched_controls",
        partition=partition,
        candidate=candidate_name,
        replicates=replicates,
    ):
        for replicate in range(replicates):
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
                spec=spec,
                config=config,
            )
            metrics.append(summarize(trades, instrument=instrument, arm_id=config.arm_id))
            if replicate == 0 and write_ledgers:
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
        "replicates": replicates,
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


def run_partition(
    *,
    partition: str,
    one_minute: pd.DataFrame,
    base: SequenceConfig,
    iterations: int,
    seed_base: int,
    out: Path,
    spec: InstrumentSpec = USA500_RTH_SPEC,
    instrument: str = "ES_PROXY",
    plan: ResearchPlan | None = None,
    cache: FrameCache | None = None,
    source_key: str | None = None,
    timer: StageTimer | None = None,
) -> dict[str, object]:
    active_plan = plan or plan_for_mode("legacy", certify_iterations=iterations)
    active_plan.validate()
    if cache is not None and not source_key:
        raise ValueError("source_key is required when a frame cache is supplied")
    cache_source = source_key or f"uncached:{partition}:{len(one_minute)}"

    def resampled(minutes: int) -> pd.DataFrame:
        with _measure(timer, "resample", partition=partition, minutes=minutes):
            return _cached_frame(
                cache,
                "resampled-bars",
                {
                    "source_key": cache_source,
                    "minutes": minutes,
                    "resample_version": 1,
                },
                lambda: resample_ohlcv(one_minute, minutes),
            )

    execution_bars = resampled(base.execution_minutes)
    management_bars = resampled(base.management_minutes)
    map_bars = resampled(base.map_minutes)

    management_cfg = management_config(base)
    with _measure(timer, "detect_management", partition=partition):
        management = _cached_frame(
            cache,
            "detected-events",
            {
                "source_key": cache_source,
                "role": "management",
                "config": asdict(management_cfg),
                "detector_version": 1,
            },
            lambda: detect_sequences(management_bars, map_bars, management_cfg).events,
        )
    if active_plan.write_ledgers:
        management.to_csv(out / f"{partition}__management_events.csv", index=False)

    long_config = entry_config(base, "long_only")
    with _measure(timer, "detect_full_sequence", partition=partition):
        full_events = _cached_frame(
            cache,
            "detected-events",
            {
                "source_key": cache_source,
                "role": "full_sequence_long_only",
                "config": asdict(base),
                "detector_version": 1,
            },
            lambda: full_sequence_events(
                execution_bars,
                map_bars,
                base,
                direction_mode="long_only",
            ),
        )
    with _measure(timer, "detect_ema_break", partition=partition):
        break_events = _cached_frame(
            cache,
            "detected-events",
            {
                "source_key": cache_source,
                "role": "ema_break_long_only",
                "config": asdict(long_config),
                "detector_version": 1,
            },
            lambda: detect_long_stage_events(
                execution_bars,
                map_bars,
                long_config,
                model="ema_break",
            ).events,
        )
    with _measure(timer, "detect_ema_break_retest", partition=partition):
        retest_events = _cached_frame(
            cache,
            "detected-events",
            {
                "source_key": cache_source,
                "role": "ema_break_retest_long_only",
                "config": asdict(long_config),
                "detector_version": 1,
            },
            lambda: detect_long_stage_events(
                execution_bars,
                map_bars,
                long_config,
                model="ema_break_retest",
            ).events,
        )

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
    scenarios = [row for row in scenarios if active_plan.includes_scenario(row[0])]

    summaries: dict[str, dict[str, object]] = {}
    inferences: dict[str, dict[str, object]] = {}
    trade_ledgers: dict[str, pd.DataFrame] = {}
    summary_rows: list[dict[str, object]] = []
    inference_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    exit_rows: list[dict[str, object]] = []
    exact_cost_sources = {
        "RTH_LONG_FULL_COST_2T": "RTH_LONG_FULL",
        "RTH_LONG_EMA_BREAK_COST_2T": "RTH_LONG_EMA_BREAK",
    }

    for index, (name, events, config) in enumerate(scenarios):
        scenario_id = f"{SOURCE_ARM_ID}__{name}"
        bootstrap_iterations = active_plan.bootstrap_iterations_for(name)
        if active_plan.exact_cost_repricing and name in exact_cost_sources:
            source_name = exact_cost_sources[name]
            if source_name not in trade_ledgers:
                raise RuntimeError(f"cost source scenario was not executed first: {source_name}")
            with _measure(timer, "cost_repricing", partition=partition, scenario=name):
                trades = reprice_single_stream_costs(
                    trade_ledgers[source_name],
                    spec=spec,
                    config=config,
                    arm_id=scenario_id,
                )
            summary, inference, review, trades = _evaluate_trade_ledger(
                partition=partition,
                scenario_name=name,
                scenario_id=scenario_id,
                one_minute=one_minute,
                events=events,
                trades=trades,
                instrument=instrument,
                bootstrap_iterations=bootstrap_iterations,
                seed=seed_base + index,
                run_review=active_plan.should_review(name),
                write_ledgers=active_plan.write_ledgers,
                out=out,
                timer=timer,
            )
        else:
            summary, inference, review, trades = _evaluate_scenario(
                partition=partition,
                scenario_name=name,
                scenario_id=scenario_id,
                one_minute=one_minute,
                events=events,
                management_events=management,
                config=config,
                spec=spec,
                instrument=instrument,
                bootstrap_iterations=bootstrap_iterations,
                seed=seed_base + index,
                run_review=active_plan.should_review(name),
                write_ledgers=active_plan.write_ledgers,
                out=out,
                timer=timer,
            )
        summaries[name] = summary
        inferences[name] = inference
        trade_ledgers[name] = trades
        summary_rows.append(summary)
        inference_rows.append(inference)
        review_rows.append(review)
        if active_plan.include_attribution:
            annual_rows.extend(
                _annual_rows(
                    trades,
                    partition=partition,
                    scenario_id=scenario_id,
                    instrument=instrument,
                )
            )
            exit_rows.extend(_exit_rows(trades, partition=partition, scenario_id=scenario_id))

    matched_inputs = {
        "RTH_LONG_EMA_BREAK": (rth_break, seed_base + 10_000),
        "RTH_LONG_FULL": (rth_full, seed_base + 20_000),
    }
    matched_rows: list[dict[str, object]] = []
    for candidate_name in active_plan.matched_control_candidates:
        if candidate_name not in summaries or candidate_name not in matched_inputs:
            raise RuntimeError(f"matched candidate is unavailable: {candidate_name}")
        candidate_events, matched_seed = matched_inputs[candidate_name]
        matched_rows.append(
            _matched_control(
                partition=partition,
                candidate_name=candidate_name,
                one_minute=one_minute,
                execution_bars=execution_bars,
                map_bars=map_bars,
                management=management,
                candidate_events=candidate_events,
                candidate_config=long_config,
                candidate_summary=summaries[candidate_name],
                spec=spec,
                instrument=instrument,
                seed_base=matched_seed,
                out=out,
                replicates=active_plan.matched_control_replicates,
                write_ledgers=active_plan.write_ledgers,
                timer=timer,
            )
        )

    return {
        "summaries": summaries,
        "inferences": inferences,
        "summary_rows": summary_rows,
        "inference_rows": inference_rows,
        "review_rows": review_rows,
        "annual_rows": annual_rows,
        "exit_rows": exit_rows,
        "matched_rows": matched_rows,
        "plan_mode": active_plan.mode,
        "cache_summary": cache.summary() if cache is not None else None,
        "management_direction_count": (
            int(management["direction"].nunique()) if not management.empty else 0
        ),
        "management_event_count": int(len(management)),
        "management_long_count": int((management["direction"] == 1).sum())
        if not management.empty
        else 0,
        "management_short_count": int((management["direction"] == -1).sum())
        if not management.empty
        else 0,
    }
