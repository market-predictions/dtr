from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

TARGET_ORDER = (
    "EXT_FIXED_3R_1200",
    "EXT_FIXED_4R_1400",
    "EXT_FIXED_2R_1100",
    "EXT_OPPOSING_LIQUIDITY_1400",
    "EXT_OPPOSITE_BOUNDARY_1100",
)
LANDMARKS = ("T0", "T1", "T2", "T3")
STRESS_PIPS = 0.10

TARGET_HOURS = {
    "EXT_FIXED_2R_1100": 11,
    "EXT_FIXED_3R_1200": 12,
    "EXT_FIXED_4R_1400": 14,
    "EXT_OPPOSITE_BOUNDARY_1100": 11,
    "EXT_OPPOSING_LIQUIDITY_1400": 14,
}


def _amsterdam_hour(trade_date: str, hour: int) -> pd.Timestamp:
    return pd.Timestamp(
        f"{trade_date} {hour:02d}:00:00",
        tz="Europe/Amsterdam",
    ).tz_convert("UTC")


def _opposing_liquidity_target(
    row: pd.Series,
    levels: pd.DataFrame,
    *,
    is_long: bool,
    entry_price: float,
) -> float | None:
    event_levels = levels.loc[
        levels["event_id"].eq(row["event_id"])
        & levels["available_at_0800"].astype(bool)
    ]
    if is_long:
        candidates = event_levels.loc[
            event_levels["level_side"].eq("HIGH")
            & event_levels["level_price"].gt(entry_price)
        ]
        return float(candidates["level_price"].min()) if len(candidates) else None
    candidates = event_levels.loc[
        event_levels["level_side"].eq("LOW")
        & event_levels["level_price"].lt(entry_price)
    ]
    return float(candidates["level_price"].max()) if len(candidates) else None


def _targets(
    row: pd.Series,
    levels: pd.DataFrame,
    *,
    entry_price: float,
    stop_price: float,
    is_long: bool,
) -> dict[str, float]:
    risk = entry_price - stop_price if is_long else stop_price - entry_price
    fixed = {
        "EXT_FIXED_2R_1100": (
            entry_price + 2.0 * risk if is_long else entry_price - 2.0 * risk
        ),
        "EXT_FIXED_3R_1200": (
            entry_price + 3.0 * risk if is_long else entry_price - 3.0 * risk
        ),
        "EXT_FIXED_4R_1400": (
            entry_price + 4.0 * risk if is_long else entry_price - 4.0 * risk
        ),
        "EXT_OPPOSITE_BOUNDARY_1100": (
            float(row["asian_high"]) if is_long else float(row["asian_low"])
        ),
    }
    liquidity = _opposing_liquidity_target(
        row,
        levels,
        is_long=is_long,
        entry_price=entry_price,
    )
    if liquidity is not None:
        fixed["EXT_OPPOSING_LIQUIDITY_1400"] = liquidity
    return fixed


def _label_target(
    row: pd.Series,
    bars: pd.DataFrame,
    *,
    target_name: str,
    target_price: float,
    entry_price: float,
    stop_price: float,
    is_long: bool,
) -> dict[str, Any] | None:
    risk = entry_price - stop_price if is_long else stop_price - entry_price
    reward = target_price - entry_price if is_long else entry_price - target_price
    if risk <= 0.0 or reward <= 0.0:
        return None
    start = pd.Timestamp(row["entry_timestamp_utc"])
    end = _amsterdam_hour(str(row["trade_date"]), TARGET_HOURS[target_name])
    path = bars.loc[
        (bars.index >= start)
        & (bars.index < end)
        & bars["active"].astype(bool)
    ]
    if path.empty:
        return None
    target_hit = False
    stop_first = False
    ambiguous_stop_first = False
    resolution = pd.NaT
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
            resolution = pd.Timestamp(timestamp)
            break
        if objective_hit:
            target_hit = True
            resolution = pd.Timestamp(timestamp)
            break
    pip = PIP_SIZE[str(row["instrument"])]
    slip = STRESS_PIPS * pip
    stressed_entry = entry_price + slip if is_long else entry_price - slip
    stressed_stop = stop_price - slip if is_long else stop_price + slip
    stressed_risk = (
        stressed_entry - stressed_stop if is_long else stressed_stop - stressed_entry
    )
    stressed_reward = (
        target_price - stressed_entry if is_long else stressed_entry - target_price
    )
    return {
        "extended_target": target_name,
        "extended_target_price": target_price,
        "extended_target_hit": int(target_hit),
        "extended_stop_first": int(stop_first),
        "extended_ambiguous_stop_first": int(ambiguous_stop_first),
        "extended_horizon_hour_amsterdam": TARGET_HOURS[target_name],
        "extended_reward_price": reward,
        "extended_reward_risk": reward / risk,
        "extended_reward_risk_stress_010": (
            stressed_reward / stressed_risk
            if stressed_risk > 0.0 and stressed_reward > 0.0
            else math.nan
        ),
        "extended_resolution_timestamp_utc": (
            pd.Timestamp(resolution).isoformat() if pd.notna(resolution) else None
        ),
    }


def build_pair_extended_target_ledger(
    landmark_ledger: pd.DataFrame,
    levels: pd.DataFrame,
    source_directory: Path,
    *,
    symbol: str,
) -> pd.DataFrame:
    symbol = symbol.upper()
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "side",
        "landmark",
        "entry_timestamp_utc",
        "entry_price",
        "stop_price",
        "asian_high",
        "asian_low",
    }
    missing = sorted(required - set(landmark_ledger.columns))
    if missing:
        raise ValueError(f"missing extended-target ledger columns: {missing}")
    source = landmark_ledger.loc[
        landmark_ledger["instrument"].eq(symbol)
        & landmark_ledger["landmark"].isin(LANDMARKS)
        & landmark_ledger["year"].between(2015, 2019)
    ].copy()
    source["entry_timestamp_utc"] = pd.to_datetime(
        source["entry_timestamp_utc"], utc=True, errors="raise"
    )
    if source.duplicated(["event_id", "landmark"]).any():
        raise ValueError(f"{symbol}: duplicate event-landmark source rows")
    rows: list[dict[str, Any]] = []
    for year, year_rows in source.groupby("year", sort=True):
        bars = load_bid_ask_minutes(source_directory, symbol, int(year))
        for _, row in year_rows.sort_values(
            ["entry_timestamp_utc", "event_id"], kind="mergesort"
        ).iterrows():
            entry_time = pd.Timestamp(row["entry_timestamp_utc"])
            if entry_time not in bars.index or not bool(bars.at[entry_time, "active"]):
                continue
            is_long = str(row["side"]) == "DOWN"
            entry_price = float(
                bars.at[entry_time, "open_ask" if is_long else "open_bid"]
            )
            stop_price = float(row["stop_price"])
            targets = _targets(
                row,
                levels,
                entry_price=entry_price,
                stop_price=stop_price,
                is_long=is_long,
            )
            for target_name in TARGET_ORDER:
                if target_name not in targets:
                    continue
                outcome = _label_target(
                    row,
                    bars,
                    target_name=target_name,
                    target_price=float(targets[target_name]),
                    entry_price=entry_price,
                    stop_price=stop_price,
                    is_long=is_long,
                )
                if outcome is None:
                    continue
                record = row.to_dict()
                record["entry_price"] = entry_price
                record.update(outcome)
                rows.append(record)
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError(f"{symbol}: extended-target ledger is empty")
    if result.duplicated(["event_id", "landmark", "extended_target"]).any():
        raise ValueError(f"{symbol}: duplicate extended target keys")
    return result.sort_values(
        ["extended_target", "landmark", "entry_timestamp_utc", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def target_census(ledger: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (target, landmark), group in ledger.groupby(
        ["extended_target", "landmark"], sort=True
    ):
        rows.append(
            {
                "extended_target": target,
                "landmark": landmark,
                "eligible_events": int(len(group)),
                "positive_cases": int(group["extended_target_hit"].sum()),
                "base_rate": float(group["extended_target_hit"].mean()),
                "median_reward_risk": float(group["extended_reward_risk"].median()),
                "median_reward_risk_stress_010": float(
                    group["extended_reward_risk_stress_010"].median()
                ),
                "pairs": int(group["instrument"].nunique()),
                "years": int(group["year"].nunique()),
            }
        )
    return pd.DataFrame(rows)
