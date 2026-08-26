from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction import PRIMARY_PAIRS

MIN_H4_CONFIRMATIONS = 300
MIN_PAIR_H4_CONFIRMATIONS = 40
MIN_H4_PAIR_BREADTH = 4
MIN_ALIGNED_MONTHS = 80
MIN_PAIR_ALIGNED_MONTHS = 10
MIN_ALIGNED_PAIR_BREADTH = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the frozen Wayne H4 structural sensitivity."
    )
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--structures", type=Path, nargs="+", required=True)
    parser.add_argument("--attributions", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _load_summaries(paths: list[Path]) -> list[dict[str, Any]]:
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    symbols = tuple(sorted(item["instrument"] for item in summaries))
    if symbols != PRIMARY_PAIRS:
        raise ValueError(f"expected {PRIMARY_PAIRS}, found {symbols}")
    return summaries


def _read_csvs(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        try:
            frame = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue
        if not frame.empty:
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _coerce_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(bool)
    mapped = series.astype(str).str.strip().str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    )
    if mapped.isna().any():
        raise ValueError("attribution contains invalid Boolean values")
    return mapped.astype(bool)


def _event_counts(structure: pd.DataFrame) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for value in structure["events"].fillna(""):
        counter.update(item for item in str(value).split(";") if item)
    return dict(sorted(counter.items()))


def _markdown(
    decision: dict[str, Any],
    pair_summary: pd.DataFrame,
    health: pd.DataFrame,
    category: pd.DataFrame,
    reach: pd.DataFrame,
) -> str:
    payload = decision["decision"]
    lines = [
        "# Wayne Direction-First H4 Structural Sensitivity",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"H4 trend confirmations: `{payload['h4_trend_confirmations']}`  ",
        f"H4 pair breadth: `{payload['h4_pair_breadth']}`  ",
        f"Aligned healthy zone months: `{payload['aligned_healthy_months']}`  ",
        f"Aligned-month pair breadth: `{payload['aligned_pair_breadth']}`",
        "",
        "## Pair census",
        "",
        "| Pair | H4 bars | Swings | Bull | Bear | Total | Aligned months |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in pair_summary.itertuples(index=False):
        lines.append(
            f"| {row.instrument} | {row.h4_bars} | {row.h4_swing_points} | "
            f"{row.h4_bull_confirmations} | {row.h4_bear_confirmations} | "
            f"{row.h4_trend_confirmations} | {row.aligned_healthy_months} |"
        )

    lines.extend(
        [
            "",
            "## H4 health at confirmation",
            "",
            "| Side | Health | Confirmations |",
            "|---|---|---:|",
        ]
    )
    for row in health.itertuples(index=False):
        lines.append(f"| {row.side} | {row.health_state} | {row.confirmations} |")

    lines.extend(
        [
            "",
            "## Month-open categories",
            "",
            "| H4 relation | D1 relation | Side | Months |",
            "|---|---|---|---:|",
        ]
    )
    for row in category.itertuples(index=False):
        lines.append(
            f"| {row.h4_relation} | {row.d1_relation} | {row.side} | "
            f"{row.months} |"
        )

    lines.extend(
        [
            "",
            "## Descriptive month-end reach",
            "",
            "| H4 relation | D1 relation | Side | Target | N | Reached | Rate |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in reach.itertuples(index=False):
        lines.append(
            f"| {row.h4_relation} | {row.d1_relation} | {row.side} | "
            f"{row.target_name} | {row.observations} | {row.reached} | "
            f"{row.reach_rate:.2%} |"
        )

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This stage tests sample sufficiency and descriptive conditional reach. It does "
            "not establish incremental edge and does not authorize macro attribution, "
            "execution, sizing, Pine or deployment unless the frozen census gates pass.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summaries = _load_summaries(args.summaries)
    structure = _read_csvs(args.structures)
    attribution = _read_csvs(args.attributions)
    if structure.empty:
        raise ValueError("pooled H4 structure ledger is empty")
    if tuple(sorted(structure["instrument"].unique())) != PRIMARY_PAIRS:
        raise ValueError("pooled H4 structure ledger is missing primary pairs")
    if not attribution.empty:
        attribution["reached_by_month_end"] = _coerce_bool(
            attribution["reached_by_month_end"]
        )

    pair_summary = pd.DataFrame(
        [
            {
                "instrument": item["instrument"],
                "h4_bars": item["h4_bars"],
                "h4_swing_points": item["h4_swing_points"],
                "h4_bull_confirmations": item["h4_bull_confirmations"],
                "h4_bear_confirmations": item["h4_bear_confirmations"],
                "h4_trend_confirmations": item["h4_trend_confirmations"],
                "monthly_opportunities": item["monthly_opportunities"],
                "aligned_healthy_months": item["aligned_healthy_months"],
            }
            for item in summaries
        ]
    ).sort_values("instrument")

    confirmations = structure.loc[
        structure["events"].fillna("").str.contains("TREND_CONFIRMED")
    ].copy()
    confirmations["side"] = np.where(
        confirmations["events"].str.contains("BULL_TREND_CONFIRMED"),
        "BULL",
        "BEAR",
    )
    health = (
        confirmations.groupby(["side", "health_state"], dropna=False, sort=True)
        .size()
        .rename("confirmations")
        .reset_index()
    )

    if attribution.empty:
        unique = pd.DataFrame()
        category = pd.DataFrame(
            columns=["h4_relation", "d1_relation", "side", "months"]
        )
        reach = pd.DataFrame(
            columns=[
                "h4_relation",
                "d1_relation",
                "side",
                "target_name",
                "observations",
                "reached",
                "reach_rate",
            ]
        )
    else:
        unique = attribution.drop_duplicates(["instrument", "month_id", "side"])
        category = (
            unique.groupby(
                ["h4_relation", "d1_relation", "side"],
                dropna=False,
                sort=True,
            )
            .size()
            .rename("months")
            .reset_index()
        )
        reach = (
            attribution.groupby(
                ["h4_relation", "d1_relation", "side", "target_name"],
                dropna=False,
                sort=True,
            )
            .agg(
                observations=("reached_by_month_end", "size"),
                reached=("reached_by_month_end", "sum"),
                reach_rate=("reached_by_month_end", "mean"),
            )
            .reset_index()
        )

    total_confirmations = int(pair_summary["h4_trend_confirmations"].sum())
    h4_pair_breadth = int(
        pair_summary["h4_trend_confirmations"].ge(MIN_PAIR_H4_CONFIRMATIONS).sum()
    )
    aligned_months = int(pair_summary["aligned_healthy_months"].sum())
    aligned_pair_breadth = int(
        pair_summary["aligned_healthy_months"].ge(MIN_PAIR_ALIGNED_MONTHS).sum()
    )
    transitions_pass = (
        total_confirmations >= MIN_H4_CONFIRMATIONS
        and h4_pair_breadth >= MIN_H4_PAIR_BREADTH
    )
    months_pass = (
        aligned_months >= MIN_ALIGNED_MONTHS
        and aligned_pair_breadth >= MIN_ALIGNED_PAIR_BREADTH
    )
    if transitions_pass and months_pass:
        code = "PASS_H4_CENSUS_OPEN_CONTEXT_ATTRIBUTION"
    elif not transitions_pass:
        code = "FAIL_H4_TRANSITION_SAMPLE_REVIEW"
    else:
        code = "FAIL_H4_MONTHLY_ALIGNMENT_SAMPLE_REVIEW"

    decision = {
        "decision": {
            "decision": code,
            "instruments": list(PRIMARY_PAIRS),
            "years": list(range(2015, 2022)),
            "h4_trend_confirmations": total_confirmations,
            "h4_pair_breadth": h4_pair_breadth,
            "aligned_healthy_months": aligned_months,
            "aligned_pair_breadth": aligned_pair_breadth,
            "transition_gate_passed": transitions_pass,
            "monthly_alignment_gate_passed": months_pass,
            "minimum_h4_confirmations": MIN_H4_CONFIRMATIONS,
            "minimum_pair_h4_confirmations": MIN_PAIR_H4_CONFIRMATIONS,
            "minimum_h4_pair_breadth": MIN_H4_PAIR_BREADTH,
            "minimum_aligned_months": MIN_ALIGNED_MONTHS,
            "minimum_pair_aligned_months": MIN_PAIR_ALIGNED_MONTHS,
            "minimum_aligned_pair_breadth": MIN_ALIGNED_PAIR_BREADTH,
            "macro_stage_opened": False,
            "execution_stage_opened": False,
            "strategy_pnl_calculated": False,
        },
        "event_counts": _event_counts(structure),
        "pairs": pair_summary.to_dict(orient="records"),
        "confirmation_health": health.to_dict(orient="records"),
        "monthly_categories": category.to_dict(orient="records"),
        "monthly_reach": reach.to_dict(orient="records"),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    pair_summary.to_csv(args.out / "wayne_h4_pair_census.csv", index=False)
    health.to_csv(args.out / "wayne_h4_confirmation_health.csv", index=False)
    category.to_csv(args.out / "wayne_h4_monthly_categories.csv", index=False)
    reach.to_csv(args.out / "wayne_h4_monthly_reach.csv", index=False)
    structure.to_csv(args.out / "wayne_h4_pooled_structure_ledger.csv", index=False)
    attribution.to_csv(args.out / "wayne_h4_pooled_attribution.csv", index=False)
    safe = _json_safe(decision)
    (args.out / "wayne_h4_sensitivity_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_H4_SENSITIVITY_DECISION.md").write_text(
        _markdown(safe, pair_summary, health, category, reach),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
