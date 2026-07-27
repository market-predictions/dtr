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

MIN_POOLED_CONFIRMATIONS = 300
MIN_PAIR_CONFIRMATIONS = 40
MIN_PAIR_BREADTH = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the frozen six-pair Wayne direction census."
    )
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--structures", type=Path, nargs="+", required=True)
    parser.add_argument("--reaches", type=Path, nargs="+", required=True)
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
    if len(set(symbols)) != len(PRIMARY_PAIRS):
        raise ValueError("pair summaries contain duplicate instruments")
    return summaries


def _read_nonempty_csv(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        if path.stat().st_size == 0:
            continue
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
        {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
        }
    )
    if mapped.isna().any():
        raise ValueError("reach ledger contains invalid Boolean values")
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
    reach: pd.DataFrame,
) -> str:
    payload = decision["decision"]
    lines = [
        "# Wayne Direction-First Structural Census",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Pairs: `{payload['instruments']}`  ",
        f"Development years: `{payload['years']}`  ",
        f"Trend confirmations: `{payload['trend_confirmations']}`  ",
        f"Pairs with at least {MIN_PAIR_CONFIRMATIONS} confirmations: "
        f"`{payload['pair_breadth']}`",
        "",
        "## Pair census",
        "",
        "| Pair | D1 bars | Swings | Bull confirmations | Bear confirmations | Total |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in pair_summary.itertuples(index=False):
        lines.append(
            f"| {row.instrument} | {row.daily_bars} | {row.swing_points} | "
            f"{row.bull_confirmations} | {row.bear_confirmations} | "
            f"{row.trend_confirmations} |"
        )

    lines.extend(
        [
            "",
            "## H4 health at structural confirmation",
            "",
            "| Side | H4 health | Confirmations |",
            "|---|---|---:|",
        ]
    )
    if health.empty:
        lines.append("| — | — | 0 |")
    else:
        for row in health.itertuples(index=False):
            lines.append(f"| {row.side} | {row.health_state} | {row.confirmations} |")

    lines.extend(
        [
            "",
            "## Conditional monthly reach — descriptive only",
            "",
            "| Side | Target | Opportunities | Reached | Reach rate |",
            "|---|---|---:|---:|---:|",
        ]
    )
    if reach.empty:
        lines.append("| — | — | 0 | 0 | — |")
    else:
        for row in reach.itertuples(index=False):
            lines.append(
                f"| {row.side} | {row.target_name} | {row.observations} | "
                f"{row.reached} | {row.reach_rate:.2%} |"
            )

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a structural sample-sufficiency census. Monthly reach is descriptive and "
            "does not authorize entries, stops, sizing or deployment. Macro, regime and "
            "seasonality attribution remains unopened until their causal data contracts "
            "are frozen.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summaries = _load_summaries(args.summaries)
    structure = _read_nonempty_csv(args.structures)
    reach_ledger = _read_nonempty_csv(args.reaches)
    if structure.empty:
        raise ValueError("pooled structure ledger is empty")
    if tuple(sorted(structure["instrument"].unique())) != PRIMARY_PAIRS:
        raise ValueError("pooled structure ledger does not contain all primary pairs")

    pair_summary = pd.DataFrame(
        [
            {
                "instrument": item["instrument"],
                "daily_bars": item["daily_bars"],
                "swing_points": item["swing_points"],
                "bull_confirmations": item["bull_confirmations"],
                "bear_confirmations": item["bear_confirmations"],
                "trend_confirmations": item["trend_confirmations"],
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

    if reach_ledger.empty:
        reach_summary = pd.DataFrame()
    else:
        reach_ledger["reached_before_invalidation"] = _coerce_bool(
            reach_ledger["reached_before_invalidation"]
        )
        reach_summary = (
            reach_ledger.groupby(["side", "target_name"], sort=True)
            .agg(
                observations=("reached_before_invalidation", "size"),
                reached=("reached_before_invalidation", "sum"),
                reach_rate=("reached_before_invalidation", "mean"),
            )
            .reset_index()
        )

    total_confirmations = int(pair_summary["trend_confirmations"].sum())
    pair_breadth = int(
        pair_summary["trend_confirmations"].ge(MIN_PAIR_CONFIRMATIONS).sum()
    )
    sufficient = (
        total_confirmations >= MIN_POOLED_CONFIRMATIONS
        and pair_breadth >= MIN_PAIR_BREADTH
    )
    decision_code = (
        "PASS_STRUCTURE_CENSUS_OPEN_H4_MONTHLY_ATTRIBUTION"
        if sufficient
        else "FAIL_STRUCTURE_CENSUS_REVIEW_DEFINITION"
    )
    decision = {
        "decision": {
            "decision": decision_code,
            "instruments": list(PRIMARY_PAIRS),
            "years": list(range(2015, 2022)),
            "trend_confirmations": total_confirmations,
            "bull_confirmations": int(pair_summary["bull_confirmations"].sum()),
            "bear_confirmations": int(pair_summary["bear_confirmations"].sum()),
            "pair_breadth": pair_breadth,
            "minimum_pooled_confirmations": MIN_POOLED_CONFIRMATIONS,
            "minimum_pair_confirmations": MIN_PAIR_CONFIRMATIONS,
            "minimum_pair_breadth": MIN_PAIR_BREADTH,
            "macro_stage_opened": False,
            "execution_stage_opened": False,
            "strategy_pnl_calculated": False,
        },
        "event_counts": _event_counts(structure),
        "pairs": pair_summary.to_dict(orient="records"),
        "confirmation_health": health.to_dict(orient="records"),
        "monthly_reach": (
            [] if reach_summary.empty else reach_summary.to_dict(orient="records")
        ),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    pair_summary.to_csv(args.out / "wayne_direction_pair_census.csv", index=False)
    health.to_csv(args.out / "wayne_direction_confirmation_health.csv", index=False)
    reach_summary.to_csv(
        args.out / "wayne_direction_monthly_reach_summary.csv",
        index=False,
    )
    structure.to_csv(
        args.out / "wayne_direction_pooled_structure_ledger.csv",
        index=False,
    )
    reach_ledger.to_csv(
        args.out / "wayne_direction_pooled_monthly_reach.csv",
        index=False,
    )
    safe = _json_safe(decision)
    (args.out / "wayne_direction_census_decision.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "WAYNE_DIRECTION_CENSUS_DECISION.md").write_text(
        _markdown(safe, pair_summary, health, reach_summary),
        encoding="utf-8",
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
