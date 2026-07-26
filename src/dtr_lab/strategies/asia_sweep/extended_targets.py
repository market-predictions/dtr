from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import AMSTERDAM_TZ, PIP_SIZE
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

TARGETS = (
    "EXTENDED_1_5R_1300",
    "EXTENDED_2R_1300",
    "EXTENDED_3R_1600",
    "OPPOSITE_ASIAN_BOUNDARY_1300",
    "LATE_TREND_HOLD_1600",
)
LANDMARKS = ("T0", "T1")
SLIPPAGE_PIPS = 0.10


def _horizon(trade_date: str, hour: int) -> pd.Timestamp:
    return pd.Timestamp(
        f"{trade_date} {hour:02d}:00:00", tz=AMSTERDAM_TZ
    ).tz_convert("UTC")


def _active_path(
    bars: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    return bars.loc[
        (bars.index >= start)
        & (bars.index < end)
        & bars["active"].astype(bool)
    ]


def _target_price(
    *,
    entry: float,
    risk: float,
    is_long: bool,
    reward_multiple: float,
) -> float:
    return (
        entry + reward_multiple * risk
        if is_long
        else entry - reward_multiple * risk
    )


def _first_passage_label(
    path: pd.DataFrame,
    *,
    is_long: bool,
    stop: float,
    target: float,
    horizon: pd.Timestamp,
) -> tuple[float, bool, str]:
    if path.empty:
        return math.nan, False, "NO_ACTIVE_PATH"
    for _, bar in path.iterrows():
        stop_hit = (
            float(bar["low_bid"]) <= stop
            if is_long
            else float(bar["high_ask"]) >= stop
        )
        target_hit = (
            float(bar["high_bid"]) >= target
            if is_long
            else float(bar["low_ask"]) <= target
        )
        if stop_hit and target_hit:
            return math.nan, True, "AMBIGUOUS_STOP_FIRST"
        if stop_hit:
            return 0.0, False, "STOP"
        if target_hit:
            return 1.0, False, "TARGET"
    coverage_ok = pd.Timestamp(path.index[-1]) >= horizon - pd.Timedelta(minutes=2)
    return (
        (0.0, False, "HORIZON")
        if coverage_ok
        else (math.nan, False, "INCOMPLETE_PATH")
    )


def _late_hold_label(
    path: pd.DataFrame,
    *,
    is_long: bool,
    entry: float,
    stop: float,
    risk: float,
    horizon: pd.Timestamp,
) -> tuple[float, str, float, float]:
    if path.empty:
        return math.nan, "NO_ACTIVE_PATH", math.nan, math.nan
    stopped = False
    for _, bar in path.iterrows():
        stop_hit = (
            float(bar["low_bid"]) <= stop
            if is_long
            else float(bar["high_ask"]) >= stop
        )
        if stop_hit:
            stopped = True
            break
    coverage_ok = pd.Timestamp(path.index[-1]) >= horizon - pd.Timedelta(minutes=2)
    if not coverage_ok and not stopped:
        return math.nan, "INCOMPLETE_PATH", math.nan, math.nan
    if is_long:
        mfe = (float(path["high_bid"].max()) - entry) / risk
        close_r = (float(path.iloc[-1]["close_bid"]) - entry) / risk
    else:
        mfe = (entry - float(path["low_ask"].min())) / risk
        close_r = (entry - float(path.iloc[-1]["close_ask"])) / risk
    label = float((not stopped) and mfe >= 2.0 and close_r >= 1.0)
    return label, "STOP" if stopped else "HORIZON", float(mfe), float(close_r)


def _label_row(row: pd.Series, bars: pd.DataFrame) -> dict[str, Any]:
    entry_time = pd.Timestamp(row["entry_timestamp_utc"])
    entry = float(row["entry_price"])
    stop = float(row["stop_price"])
    is_long = str(row["side"]) == "DOWN"
    risk = entry - stop if is_long else stop - entry
    base = {
        "event_id": str(row["event_id"]),
        "instrument": str(row["instrument"]),
        "trade_date": str(row["trade_date"]),
        "week_key": str(row["week_key"]),
        "year": int(row["year"]),
        "weekday": int(row["weekday"]),
        "side": str(row["side"]),
        "landmark": str(row["landmark"]),
        "entry_timestamp_utc": entry_time.isoformat(),
        "entry_price": entry,
        "stop_price": stop,
        "initial_risk_price": risk,
        "spread_risk_fraction": float(row["spread_risk_fraction"]),
    }
    if not np.isfinite(risk) or risk <= 0:
        return {**base, "status": "INVALID_GEOMETRY"}
    horizon_1300 = _horizon(str(row["trade_date"]), 13)
    horizon_1600 = _horizon(str(row["trade_date"]), 16)
    path_1300 = _active_path(bars, entry_time, horizon_1300)
    path_1600 = _active_path(bars, entry_time, horizon_1600)
    result: dict[str, Any] = {**base, "status": "LABELED"}
    for name, multiple, path, horizon in (
        ("EXTENDED_1_5R_1300", 1.5, path_1300, horizon_1300),
        ("EXTENDED_2R_1300", 2.0, path_1300, horizon_1300),
        ("EXTENDED_3R_1600", 3.0, path_1600, horizon_1600),
    ):
        target = _target_price(
            entry=entry,
            risk=risk,
            is_long=is_long,
            reward_multiple=multiple,
        )
        label, ambiguous, reason = _first_passage_label(
            path,
            is_long=is_long,
            stop=stop,
            target=target,
            horizon=horizon,
        )
        result[name] = label
        result[f"{name}_ambiguous"] = ambiguous
        result[f"{name}_resolution"] = reason
        result[f"{name}_reward_risk"] = multiple
    opposite = float(row["asian_high"] if is_long else row["asian_low"])
    opposite_reward = (
        (opposite - entry) / risk if is_long else (entry - opposite) / risk
    )
    if opposite_reward <= 0:
        result["OPPOSITE_ASIAN_BOUNDARY_1300"] = math.nan
        result["OPPOSITE_ASIAN_BOUNDARY_1300_ambiguous"] = False
        result["OPPOSITE_ASIAN_BOUNDARY_1300_resolution"] = "INVALID_TARGET"
    else:
        label, ambiguous, reason = _first_passage_label(
            path_1300,
            is_long=is_long,
            stop=stop,
            target=opposite,
            horizon=horizon_1300,
        )
        result["OPPOSITE_ASIAN_BOUNDARY_1300"] = label
        result["OPPOSITE_ASIAN_BOUNDARY_1300_ambiguous"] = ambiguous
        result["OPPOSITE_ASIAN_BOUNDARY_1300_resolution"] = reason
    result["OPPOSITE_ASIAN_BOUNDARY_1300_reward_risk"] = float(opposite_reward)
    late, reason, mfe_r, close_r = _late_hold_label(
        path_1600,
        is_long=is_long,
        entry=entry,
        stop=stop,
        risk=risk,
        horizon=horizon_1600,
    )
    result["LATE_TREND_HOLD_1600"] = late
    result["LATE_TREND_HOLD_1600_ambiguous"] = False
    result["LATE_TREND_HOLD_1600_resolution"] = reason
    result["LATE_TREND_HOLD_1600_reward_risk"] = 2.0
    result["late_mfe_r"] = mfe_r
    result["late_close_r"] = close_r
    pip = PIP_SIZE[str(row["instrument"])]
    result["entry_slippage_r"] = SLIPPAGE_PIPS * pip / risk
    return result


def build_extended_target_ledger(
    landmark_ledger: pd.DataFrame,
    source_root: Path,
    *,
    start_year: int = 2015,
    end_year: int = 2019,
) -> pd.DataFrame:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "weekday",
        "side",
        "landmark",
        "entry_timestamp_utc",
        "entry_price",
        "stop_price",
        "asian_high",
        "asian_low",
        "spread_risk_fraction",
    }
    missing = sorted(required - set(landmark_ledger.columns))
    if missing:
        raise ValueError(f"missing extended-target columns: {missing}")
    population = landmark_ledger.loc[
        landmark_ledger["landmark"].isin(LANDMARKS)
        & landmark_ledger["year"].between(start_year, end_year)
    ].copy()
    population["entry_timestamp_utc"] = pd.to_datetime(
        population["entry_timestamp_utc"], utc=True, errors="coerce"
    )
    rows: list[dict[str, Any]] = []
    for (symbol, year), group in population.groupby(
        ["instrument", "year"], sort=True
    ):
        bars = load_bid_ask_minutes(source_root / str(symbol), str(symbol), int(year))
        for _, row in group.sort_values(
            ["entry_timestamp_utc", "event_id"], kind="mergesort"
        ).iterrows():
            rows.append(_label_row(row, bars))
    labels = pd.DataFrame(rows)
    joined = landmark_ledger.merge(
        labels,
        on=["event_id", "landmark"],
        how="inner",
        validate="one_to_one",
        suffixes=("", "_label"),
    )
    if joined.duplicated(["event_id", "landmark"]).any():
        raise ValueError("duplicate extended-target keys")
    return joined
