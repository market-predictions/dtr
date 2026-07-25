from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PRIMARY_LABEL = "midpoint_success_09_10"
KEY_FEATURES = [
    "asian_range_pips",
    "asian_range_atr20",
    "asian_range_adr20",
    "asian_range_percentile60",
    "sweep_depth_range_fraction",
    "pre_sweep_reversal_signed_return",
    "pre_sweep_trailing_15m_range_fraction",
    "t5_reclaim_depth_range_fraction",
    "t5_return_range_fraction",
    "t5_mfe_range_fraction",
    "t5_mae_range_fraction",
    "same_side_level_count",
    "same_side_source_diversity",
    "same_side_weighted_density",
    "stack_member_count",
    "stack_fraction_consumed_t0",
    "stack_fraction_consumed_t5",
    "remaining_levels_beyond_t0",
    "remaining_levels_beyond_t5",
    "nearest_remaining_distance_atr_t0",
    "residual_density_t0",
    "nearest_opposite_distance_atr",
]


def _wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    half = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return center - half, center + half


def _rate_table(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=[*columns, "events", "successes", "success_rate"])
    grouped = frame.groupby(columns, dropna=False, sort=True)[PRIMARY_LABEL]
    return grouped.agg(events="size", successes="sum", success_rate="mean").reset_index()


def _weekly_claim(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame()
    event_weeks = (
        frame.groupby(["instrument", "week_key"], sort=True)[PRIMARY_LABEL]
        .agg(candidates="size", successes="sum")
        .reset_index()
    )
    pair_rows: list[dict[str, Any]] = []
    for instrument, group in event_weeks.groupby("instrument", sort=True):
        weeks = len(group)
        successful_weeks = int((group["successes"] > 0).sum())
        lo, hi = _wilson(successful_weeks, weeks)
        pair_rows.append(
            {
                "instrument": instrument,
                "pair_weeks_with_candidates": weeks,
                "pair_weeks_with_success": successful_weeks,
                "successful_week_rate": successful_weeks / weeks if weeks else math.nan,
                "wilson_lo95": lo,
                "wilson_hi95": hi,
                "weeks_zero_success": int((group["successes"] == 0).sum()),
                "weeks_one_success": int((group["successes"] == 1).sum()),
                "weeks_two_successes": int((group["successes"] == 2).sum()),
                "weeks_three_or_more_successes": int((group["successes"] >= 3).sum()),
            }
        )
    return pd.DataFrame(pair_rows), event_weeks


def _feature_contrasts(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    success = frame.loc[frame[PRIMARY_LABEL].astype(bool)]
    failure = frame.loc[~frame[PRIMARY_LABEL].astype(bool)]
    for feature in KEY_FEATURES:
        if feature not in frame.columns:
            continue
        success_values = pd.to_numeric(success[feature], errors="coerce").dropna()
        failure_values = pd.to_numeric(failure[feature], errors="coerce").dropna()
        if success_values.empty or failure_values.empty:
            continue
        pooled = pd.concat([success_values, failure_values], ignore_index=True)
        scale = float(pooled.std(ddof=0))
        mean_difference = float(success_values.mean() - failure_values.mean())
        rows.append(
            {
                "feature": feature,
                "success_n": len(success_values),
                "failure_n": len(failure_values),
                "success_median": float(success_values.median()),
                "failure_median": float(failure_values.median()),
                "success_mean": float(success_values.mean()),
                "failure_mean": float(failure_values.mean()),
                "mean_difference": mean_difference,
                "standardized_mean_difference": mean_difference / scale
                if np.isfinite(scale) and scale > 0
                else math.nan,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        "standardized_mean_difference",
        key=lambda values: values.abs(),
        ascending=False,
    )


def _quintile_lifts(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    base = float(frame[PRIMARY_LABEL].mean()) if not frame.empty else math.nan
    for feature in KEY_FEATURES:
        if feature not in frame.columns:
            continue
        working = frame.loc[:, [feature, PRIMARY_LABEL, "instrument", "trade_date"]].copy()
        working[feature] = pd.to_numeric(working[feature], errors="coerce")
        working = working.dropna(subset=[feature])
        if len(working) < 100 or working[feature].nunique() < 5:
            continue
        try:
            working["quintile"] = pd.qcut(
                working[feature],
                q=5,
                labels=False,
                duplicates="drop",
            )
        except ValueError:
            continue
        grouped = (
            working.groupby("quintile", sort=True)[PRIMARY_LABEL]
            .agg(events="size", successes="sum", success_rate="mean")
            .reset_index()
        )
        for row in grouped.itertuples(index=False):
            rows.append(
                {
                    "feature": feature,
                    "quintile": int(row.quintile),
                    "events": int(row.events),
                    "successes": int(row.successes),
                    "success_rate": float(row.success_rate),
                    "lift_vs_base": float(row.success_rate / base)
                    if np.isfinite(base) and base > 0
                    else math.nan,
                }
            )
    return pd.DataFrame(rows)


def build_development_report(inputs: Path) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    files = sorted(inputs.rglob("fingerprint_events.csv"))
    if not files:
        raise RuntimeError("no fingerprint event ledgers found")
    frames = [pd.read_csv(path) for path in files]
    events = pd.concat(frames, ignore_index=True)
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "weekday",
        "side",
        "primary_outcome",
        PRIMARY_LABEL,
    }
    missing = required.difference(events.columns)
    if missing:
        raise RuntimeError(f"event ledger missing columns: {sorted(missing)}")
    if events["event_id"].duplicated().any():
        duplicates = events.loc[
            events["event_id"].duplicated(), "event_id"
        ].head().tolist()
        raise RuntimeError(f"duplicate event IDs: {duplicates}")
    events[PRIMARY_LABEL] = events[PRIMARY_LABEL].astype(bool)
    events["year"] = pd.to_datetime(events["trade_date"]).dt.year
    events["weekday_name"] = pd.to_datetime(events["trade_date"]).dt.day_name()
    weekly_summary, pair_weeks = _weekly_claim(events)
    tables = {
        "events": events,
        "outcome_distribution": _rate_table(events, ["primary_outcome"]),
        "pair_summary": _rate_table(events, ["instrument"]),
        "year_summary": _rate_table(events, ["year"]),
        "weekday_summary": _rate_table(
            events, ["instrument", "weekday", "weekday_name"]
        ),
        "side_summary": _rate_table(events, ["instrument", "side"]),
        "sweep_time_summary": _rate_table(
            events, ["instrument", "sweep_half_hour"]
        ),
        "compression_summary": _rate_table(
            events, ["instrument", "asian_compression_bucket"]
        ),
        "stack_summary": _rate_table(
            events, ["instrument", "stack_present", "full_stack_exhausted_t0"]
        ),
        "residual_summary": _rate_table(
            events.assign(
                residual_bucket=pd.cut(
                    pd.to_numeric(events["remaining_levels_beyond_t0"], errors="coerce"),
                    bins=[-0.5, 0.5, 1.5, 3.5, np.inf],
                    labels=["NONE", "ONE", "TWO_THREE", "FOUR_PLUS"],
                )
            ),
            ["instrument", "residual_bucket"],
        ),
        "weekly_summary": weekly_summary,
        "pair_weeks": pair_weeks,
        "feature_contrasts": _feature_contrasts(events),
        "quintile_lifts": _quintile_lifts(events),
    }
    total_weeks = int(weekly_summary["pair_weeks_with_candidates"].sum())
    success_weeks = int(weekly_summary["pair_weeks_with_success"].sum())
    report = {
        "programme": "ASIAN_SWEEP_FINGERPRINT_V1",
        "stage": "DEVELOPMENT_ANATOMY_2015_2021",
        "candidate_events": int(len(events)),
        "midpoint_successes": int(events[PRIMARY_LABEL].sum()),
        "base_success_rate": float(events[PRIMARY_LABEL].mean()),
        "pairs": sorted(events["instrument"].unique().tolist()),
        "years": sorted(events["year"].unique().astype(int).tolist()),
        "pair_weeks_with_candidates": total_weeks,
        "pair_weeks_with_success": success_weeks,
        "pooled_successful_week_rate": success_weeks / total_weeks if total_weeks else None,
        "strategy_pnl_calculated": False,
        "validation_2022_2023_opened": False,
        "holdout_2024_2025_opened": False,
    }
    return report, tables


def write_development_report(
    output: Path,
    report: dict[str, Any],
    tables: dict[str, pd.DataFrame],
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "development_anatomy_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for name, table in tables.items():
        table.to_csv(output / f"{name}.csv", index=False)
