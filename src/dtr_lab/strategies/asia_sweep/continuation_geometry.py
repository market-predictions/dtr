from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

SELECTED_FAMILY = "elastic_net"
SELECTED_LANDMARK = "T2"
SELECTED_DECISION = "CONTINUATION"
STRESS_PIPS = 0.10

OBJECTIVE_ORDER = (
    "CONT_RANGE_025_1000",
    "CONT_RANGE_050_1100",
    "CONT_RANGE_100_1200",
    "CONT_NEXT_LIQUIDITY_1200",
    "CONT_FIXED_2R_1200",
)


def _amsterdam_hour(trade_date: str, hour: int) -> pd.Timestamp:
    return pd.Timestamp(
        f"{trade_date} {hour:02d}:00:00",
        tz="Europe/Amsterdam",
    ).tz_convert("UTC")


def prepare_continuation_events(
    predictions: pd.DataFrame,
    landmark_ledger: pd.DataFrame,
    *,
    symbol: str,
) -> pd.DataFrame:
    symbol = symbol.upper()
    required_predictions = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "side",
        "landmark",
        "family",
        "decision",
        "p_continuation",
        "entry_timestamp_utc",
    }
    missing_predictions = sorted(required_predictions - set(predictions.columns))
    if missing_predictions:
        raise ValueError(
            f"missing continuation prediction columns: {missing_predictions}"
        )
    required_ledger = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "side",
        "landmark",
        "entry_timestamp_utc",
        "asian_high",
        "asian_low",
        "asian_range_price",
        "sweep_extreme",
    }
    missing_ledger = sorted(required_ledger - set(landmark_ledger.columns))
    if missing_ledger:
        raise ValueError(f"missing continuation ledger columns: {missing_ledger}")

    selected_predictions = predictions.loc[
        predictions["instrument"].eq(symbol)
        & predictions["landmark"].eq(SELECTED_LANDMARK)
        & predictions["family"].eq(SELECTED_FAMILY)
        & predictions["year"].between(2015, 2019)
    ].copy()
    geometry = landmark_ledger.loc[
        landmark_ledger["instrument"].eq(symbol)
        & landmark_ledger["landmark"].eq(SELECTED_LANDMARK)
        & landmark_ledger["year"].between(2015, 2019),
        [
            "event_id",
            "asian_high",
            "asian_low",
            "asian_range_price",
            "sweep_extreme",
        ],
    ].copy()
    events = selected_predictions.merge(
        geometry,
        on="event_id",
        how="inner",
        validate="one_to_one",
    )
    if len(events) != len(selected_predictions):
        raise ValueError(f"{symbol}: incomplete continuation geometry merge")
    if events.duplicated("event_id").any():
        raise ValueError(f"{symbol}: duplicate continuation event ids")
    events["entry_timestamp_utc"] = pd.to_datetime(
        events["entry_timestamp_utc"], utc=True, errors="raise"
    )
    return events.sort_values(
        ["year", "entry_timestamp_utc", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def _nearest_liquidity_target(
    event: pd.Series,
    levels: pd.DataFrame,
    *,
    is_long: bool,
) -> float | None:
    event_levels = levels.loc[
        levels["event_id"].eq(event["event_id"])
        & levels["available_at_0800"].astype(bool)
    ].copy()
    extreme = float(event["sweep_extreme"])
    if is_long:
        candidates = event_levels.loc[
            event_levels["level_side"].eq("HIGH")
            & event_levels["level_price"].gt(extreme)
        ]
        return float(candidates["level_price"].min()) if len(candidates) else None
    candidates = event_levels.loc[
        event_levels["level_side"].eq("LOW")
        & event_levels["level_price"].lt(extreme)
    ]
    return float(candidates["level_price"].max()) if len(candidates) else None


def _objective_targets(
    event: pd.Series,
    levels: pd.DataFrame,
    *,
    entry_price: float,
    stop_price: float,
    is_long: bool,
) -> dict[str, tuple[float, int]]:
    asian_range = float(event["asian_range_price"])
    extreme = float(event["sweep_extreme"])
    risk = entry_price - stop_price if is_long else stop_price - entry_price
    targets = {
        "CONT_RANGE_025_1000": (
            extreme + 0.25 * asian_range
            if is_long
            else extreme - 0.25 * asian_range,
            10,
        ),
        "CONT_RANGE_050_1100": (
            extreme + 0.50 * asian_range
            if is_long
            else extreme - 0.50 * asian_range,
            11,
        ),
        "CONT_RANGE_100_1200": (
            extreme + asian_range if is_long else extreme - asian_range,
            12,
        ),
        "CONT_FIXED_2R_1200": (
            entry_price + 2.0 * risk if is_long else entry_price - 2.0 * risk,
            12,
        ),
    }
    liquidity_target = _nearest_liquidity_target(
        event,
        levels,
        is_long=is_long,
    )
    if liquidity_target is not None:
        targets["CONT_NEXT_LIQUIDITY_1200"] = (liquidity_target, 12)
    return targets


def _simulate_objective(
    event: pd.Series,
    bars: pd.DataFrame,
    *,
    objective: str,
    target_price: float,
    horizon_hour: int,
    entry_price: float,
    stop_price: float,
    is_long: bool,
) -> dict[str, Any] | None:
    entry_time = pd.Timestamp(event["entry_timestamp_utc"])
    risk = entry_price - stop_price if is_long else stop_price - entry_price
    reward = target_price - entry_price if is_long else entry_price - target_price
    if risk <= 0.0 or reward <= 0.0:
        return None
    end = _amsterdam_hour(str(event["trade_date"]), horizon_hour)
    path = bars.loc[
        (bars.index >= entry_time)
        & (bars.index < end)
        & bars["active"].astype(bool)
    ]
    if path.empty:
        return None

    target_hit = False
    stop_first = False
    ambiguous_stop_first = False
    resolution_time = pd.NaT
    for timestamp, bar in path.iterrows():
        stop_hit = (
            float(bar["low_bid"]) <= stop_price
            if is_long
            else float(bar["high_ask"]) >= stop_price
        )
        objective_hit = (
            float(bar["high_bid"]) >= target_price
            if is_long
            else float(bar["low_ask"]) <= target_price
        )
        if stop_hit:
            stop_first = True
            ambiguous_stop_first = bool(objective_hit)
            resolution_time = pd.Timestamp(timestamp)
            break
        if objective_hit:
            target_hit = True
            resolution_time = pd.Timestamp(timestamp)
            break

    pip = PIP_SIZE[str(event["instrument"])]
    slippage = STRESS_PIPS * pip
    stressed_entry = entry_price + slippage if is_long else entry_price - slippage
    stressed_stop = stop_price - slippage if is_long else stop_price + slippage
    stressed_risk = (
        stressed_entry - stressed_stop
        if is_long
        else stressed_stop - stressed_entry
    )
    stressed_reward = (
        target_price - stressed_entry
        if is_long
        else stressed_entry - target_price
    )
    stressed_reward_risk = (
        stressed_reward / stressed_risk
        if stressed_risk > 0.0 and stressed_reward > 0.0
        else math.nan
    )
    return {
        "event_id": str(event["event_id"]),
        "instrument": str(event["instrument"]),
        "trade_date": str(event["trade_date"]),
        "year": int(event["year"]),
        "weekday": int(event["weekday"]),
        "side": str(event["side"]),
        "decision": str(event["decision"]),
        "p_continuation": float(event["p_continuation"]),
        "objective": objective,
        "horizon_hour_amsterdam": horizon_hour,
        "entry_timestamp_utc": entry_time.isoformat(),
        "entry_price": entry_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "risk_price": risk,
        "reward_price": reward,
        "reward_risk": reward / risk,
        "reward_risk_stress_010": stressed_reward_risk,
        "target_hit": bool(target_hit),
        "stop_first": bool(stop_first),
        "ambiguous_stop_first": bool(ambiguous_stop_first),
        "resolution_timestamp_utc": (
            pd.Timestamp(resolution_time).isoformat()
            if pd.notna(resolution_time)
            else None
        ),
    }


def build_pair_continuation_geometry(
    events: pd.DataFrame,
    levels: pd.DataFrame,
    source_directory: Path,
    *,
    symbol: str,
) -> pd.DataFrame:
    symbol = symbol.upper()
    rows: list[dict[str, Any]] = []
    for year, year_events in events.groupby("year", sort=True):
        bars = load_bid_ask_minutes(source_directory, symbol, int(year))
        for _, event in year_events.iterrows():
            entry_time = pd.Timestamp(event["entry_timestamp_utc"])
            if entry_time not in bars.index or not bool(bars.at[entry_time, "active"]):
                continue
            is_long = str(event["side"]) == "UP"
            entry_price = float(
                bars.at[entry_time, "open_ask" if is_long else "open_bid"]
            )
            asian_range = float(event["asian_range_price"])
            stop_price = (
                float(event["asian_high"]) - 0.10 * asian_range
                if is_long
                else float(event["asian_low"]) + 0.10 * asian_range
            )
            targets = _objective_targets(
                event,
                levels,
                entry_price=entry_price,
                stop_price=stop_price,
                is_long=is_long,
            )
            for objective in OBJECTIVE_ORDER:
                if objective not in targets:
                    continue
                target_price, horizon_hour = targets[objective]
                result = _simulate_objective(
                    event,
                    bars,
                    objective=objective,
                    target_price=float(target_price),
                    horizon_hour=int(horizon_hour),
                    entry_price=entry_price,
                    stop_price=stop_price,
                    is_long=is_long,
                )
                if result is not None:
                    rows.append(result)
    geometry = pd.DataFrame(rows)
    if geometry.empty:
        raise ValueError(f"{symbol}: continuation geometry ledger is empty")
    if geometry.duplicated(["event_id", "objective"]).any():
        raise ValueError(f"{symbol}: duplicate continuation event-objective rows")
    return geometry.sort_values(
        ["objective", "entry_timestamp_utc", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def _breadth_table(group: pd.DataFrame, column: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for value, segment in group.groupby(column, sort=True):
        selected = segment.loc[segment["decision"].eq(SELECTED_DECISION)]
        rows.append(
            {
                column: value,
                "eligible_events": int(len(segment)),
                "base_target_rate": float(segment["target_hit"].mean()),
                "selected_events": int(len(selected)),
                "selected_target_rate": (
                    float(selected["target_hit"].mean())
                    if len(selected)
                    else math.nan
                ),
            }
        )
    table = pd.DataFrame(rows)
    table["positive_lift"] = (
        table["selected_events"].gt(0)
        & table["selected_target_rate"].gt(table["base_target_rate"])
    )
    return table


def summarize_objective(
    geometry: pd.DataFrame,
    objective: str,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    group = geometry.loc[geometry["objective"].eq(objective)].copy()
    selected = group.loc[group["decision"].eq(SELECTED_DECISION)].copy()
    if group.empty or selected.empty:
        raise ValueError(f"{objective}: missing eligible or selected events")
    base_rate = float(group["target_hit"].mean())
    selected_rate = float(selected["target_hit"].mean())
    expected_value = (
        selected["p_continuation"] * selected["reward_risk_stress_010"]
        - (1.0 - selected["p_continuation"])
    )
    tables = {
        column: _breadth_table(group, column)
        for column in ("instrument", "year", "weekday", "side")
    }
    concentration = max(
        float(selected[column].value_counts(normalize=True).max())
        for column in ("instrument", "year", "side")
    )
    summary: dict[str, Any] = {
        "objective": objective,
        "eligible_events": int(len(group)),
        "positive_cases": int(group["target_hit"].sum()),
        "base_target_rate": base_rate,
        "selected_events": int(len(selected)),
        "selected_target_rate": selected_rate,
        "selected_lift": selected_rate / base_rate,
        "median_selected_reward_risk": float(selected["reward_risk"].median()),
        "selected_rr_at_least_1_5": float(
            selected["reward_risk"].ge(1.5).mean()
        ),
        "median_selected_reward_risk_stress_010": float(
            selected["reward_risk_stress_010"].median()
        ),
        "median_stressed_expected_value_proxy": float(expected_value.median()),
        "pair_positive_lift_count": int(tables["instrument"]["positive_lift"].sum()),
        "year_positive_lift_count": int(tables["year"]["positive_lift"].sum()),
        "max_selected_concentration": concentration,
    }
    gates = {
        "sample_size": summary["eligible_events"] >= 400
        and summary["positive_cases"] >= 75,
        "selected_lift": summary["selected_lift"] >= 1.60,
        "pair_breadth": summary["pair_positive_lift_count"] == 2,
        "year_breadth": summary["year_positive_lift_count"] >= 4,
        "median_reward_risk": summary["median_selected_reward_risk"] >= 1.25,
        "reward_risk_breadth": summary["selected_rr_at_least_1_5"] >= 0.35,
        "expected_value_proxy": summary["median_stressed_expected_value_proxy"]
        > 0.0,
        "concentration": summary["max_selected_concentration"] <= 0.70,
    }
    summary["gates"] = gates
    summary["passes"] = bool(all(gates.values()))
    return summary, tables


def select_continuation_objective(summaries: pd.DataFrame) -> str | None:
    passing = summaries.loc[summaries["passes"].astype(bool)]
    if passing.empty:
        return None
    for objective in OBJECTIVE_ORDER:
        if objective in set(passing["objective"]):
            return objective
    raise RuntimeError("passing continuation objective is outside frozen order")
