from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

StagedVariant = Literal[
    "MIDPOINT_50_RUNNER_ORIGINAL_STOP",
    "MIDPOINT_50_RUNNER_BE",
]

STAGED_VARIANTS: tuple[StagedVariant, ...] = (
    "MIDPOINT_50_RUNNER_ORIGINAL_STOP",
    "MIDPOINT_50_RUNNER_BE",
)
SLIPPAGE_STRESSES = (0.0, 0.10, 0.25)
TP1_FRACTION = 0.50
RUNNER_FRACTION = 0.50


def _amsterdam_clock(trade_date: str, hour: int) -> pd.Timestamp:
    return pd.Timestamp(f"{trade_date} {hour:02d}:00:00", tz="Europe/Amsterdam").tz_convert(
        "UTC"
    )


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _base_row(order: pd.Series, variant: StagedVariant) -> dict[str, Any]:
    return {
        "event_id": str(order["event_id"]),
        "instrument": str(order["instrument"]),
        "trade_date": str(order["trade_date"]),
        "week_key": str(order["week_key"]),
        "year": int(order["year"]),
        "weekday": int(order["weekday"]),
        "side": str(order["side"]),
        "prediction": float(order["prediction"]),
        "entry_variant": "MKT_NEXT_OPEN",
        "staged_variant": variant,
        "t5_timestamp_utc": pd.Timestamp(order["t5_timestamp_utc"]).isoformat(),
        "entry_timestamp_utc": pd.Timestamp(order["entry_timestamp_utc"]).isoformat(),
        "entry_price": float(order["entry_price"]),
    }


def _exit_quote_price(bar: pd.Series, *, is_long: bool, field: str) -> float:
    side = "bid" if is_long else "ask"
    return float(bar[f"{field}_{side}"])


def _stop_hit(bar: pd.Series, *, is_long: bool, stop: float) -> bool:
    return bool(float(bar["low_bid"]) <= stop) if is_long else bool(
        float(bar["high_ask"]) >= stop
    )


def _target_hit(bar: pd.Series, *, is_long: bool, target: float) -> bool:
    return bool(float(bar["high_bid"]) >= target) if is_long else bool(
        float(bar["low_ask"]) <= target
    )


def _stressed_leg_r(
    *,
    entry: float,
    exit_price: float,
    risk: float,
    is_long: bool,
    entry_is_market: bool,
    exit_is_market_or_stop: bool,
    stress_pips: float,
    pip: float,
) -> float:
    slippage = stress_pips * pip
    stressed_entry = entry
    stressed_exit = exit_price
    if entry_is_market:
        stressed_entry = entry + slippage if is_long else entry - slippage
    if exit_is_market_or_stop:
        stressed_exit = exit_price - slippage if is_long else exit_price + slippage
    direction = 1.0 if is_long else -1.0
    return direction * (stressed_exit - stressed_entry) / risk


def _finalize_result(
    base: dict[str, Any],
    *,
    instrument: str,
    is_long: bool,
    entry: float,
    risk: float,
    original_stop: float,
    tp1: float,
    tp2: float,
    tp1_hit: bool,
    tp2_hit: bool,
    tp1_time: pd.Timestamp | None,
    runner_exit_time: pd.Timestamp,
    tp1_exit_price: float,
    runner_exit_price: float,
    tp1_exit_reason: str,
    runner_exit_reason: str,
    break_even_activated: bool,
) -> dict[str, Any]:
    pip = PIP_SIZE[instrument]
    result: dict[str, Any] = {
        **base,
        "status": "FILLED",
        "filled": True,
        "initial_risk_price": risk,
        "original_stop_price": original_stop,
        "tp1_price": tp1,
        "tp2_price": tp2,
        "tp1_fraction": TP1_FRACTION,
        "runner_fraction": RUNNER_FRACTION,
        "tp1_hit": tp1_hit,
        "tp2_hit": tp2_hit,
        "tp1_timestamp_utc": tp1_time.isoformat() if tp1_time is not None else None,
        "runner_exit_timestamp_utc": runner_exit_time.isoformat(),
        "tp1_exit_price": tp1_exit_price,
        "runner_exit_price": runner_exit_price,
        "tp1_exit_reason": tp1_exit_reason,
        "runner_exit_reason": runner_exit_reason,
        "break_even_activated": break_even_activated,
    }
    tp1_is_market_or_stop = tp1_exit_reason in {
        "STOP_FULL",
        "TIME_1000_FULL",
    }
    runner_is_market_or_stop = runner_exit_reason in {
        "STOP_FULL",
        "TIME_1000_FULL",
        "ORIGINAL_STOP_AFTER_TP1",
        "BE_STOP",
        "TIME_1100",
    }
    for stress in SLIPPAGE_STRESSES:
        leg1 = _stressed_leg_r(
            entry=entry,
            exit_price=tp1_exit_price,
            risk=risk,
            is_long=is_long,
            entry_is_market=True,
            exit_is_market_or_stop=tp1_is_market_or_stop,
            stress_pips=stress,
            pip=pip,
        )
        leg2 = _stressed_leg_r(
            entry=entry,
            exit_price=runner_exit_price,
            risk=risk,
            is_long=is_long,
            entry_is_market=True,
            exit_is_market_or_stop=runner_is_market_or_stop,
            stress_pips=stress,
            pip=pip,
        )
        suffix = str(stress).replace(".", "_")
        result[f"tp1_leg_r_{suffix}"] = leg1
        result[f"runner_leg_r_{suffix}"] = leg2
        result[f"net_r_{suffix}"] = TP1_FRACTION * leg1 + RUNNER_FRACTION * leg2
    return result


def simulate_staged_trade(
    order: pd.Series,
    event: pd.Series,
    bars: pd.DataFrame,
    *,
    variant: StagedVariant,
) -> dict[str, Any]:
    if variant not in STAGED_VARIANTS:
        raise ValueError(f"unsupported staged variant: {variant}")
    base = _base_row(order, variant)
    is_long = str(order["side"]) == "DOWN"
    entry_time = pd.Timestamp(order["entry_timestamp_utc"])
    entry = float(order["entry_price"])
    original_stop = float(order["stop_price"])
    tp1 = float(event["asian_midpoint"])
    tp2 = float(event["asian_high"] if is_long else event["asian_low"])
    risk = entry - original_stop if is_long else original_stop - entry
    tp1_distance = tp1 - entry if is_long else entry - tp1
    tp2_distance = tp2 - entry if is_long else entry - tp2
    if risk <= 0 or tp1_distance <= 0 or tp2_distance <= 0:
        return {
            **base,
            "status": "INVALID_GEOMETRY",
            "filled": False,
            "initial_risk_price": risk,
            "original_stop_price": original_stop,
            "tp1_price": tp1,
            "tp2_price": tp2,
        }

    tp1_deadline = _amsterdam_clock(str(order["trade_date"]), 10)
    runner_deadline = _amsterdam_clock(str(order["trade_date"]), 11)
    path = bars.loc[
        (bars.index >= entry_time)
        & (bars.index < runner_deadline)
        & bars["active"].astype(bool)
    ]
    if path.empty:
        return {**base, "status": "NO_ACTIVE_PATH", "filled": False}

    pre_tp1 = path.loc[path.index < tp1_deadline]
    if pre_tp1.empty:
        return {**base, "status": "NO_ACTIVE_PATH_BEFORE_1000", "filled": False}

    tp1_time: pd.Timestamp | None = None
    tp2_same_bar = False
    for timestamp, bar in pre_tp1.iterrows():
        if _stop_hit(bar, is_long=is_long, stop=original_stop):
            return _finalize_result(
                base,
                instrument=str(order["instrument"]),
                is_long=is_long,
                entry=entry,
                risk=risk,
                original_stop=original_stop,
                tp1=tp1,
                tp2=tp2,
                tp1_hit=False,
                tp2_hit=False,
                tp1_time=None,
                runner_exit_time=pd.Timestamp(timestamp),
                tp1_exit_price=original_stop,
                runner_exit_price=original_stop,
                tp1_exit_reason="STOP_FULL",
                runner_exit_reason="STOP_FULL",
                break_even_activated=False,
            )
        if _target_hit(bar, is_long=is_long, target=tp1):
            tp1_time = pd.Timestamp(timestamp)
            tp2_same_bar = _target_hit(bar, is_long=is_long, target=tp2)
            break

    if tp1_time is None:
        last_time = pd.Timestamp(pre_tp1.index[-1])
        last_bar = pre_tp1.iloc[-1]
        time_price = _exit_quote_price(last_bar, is_long=is_long, field="close")
        return _finalize_result(
            base,
            instrument=str(order["instrument"]),
            is_long=is_long,
            entry=entry,
            risk=risk,
            original_stop=original_stop,
            tp1=tp1,
            tp2=tp2,
            tp1_hit=False,
            tp2_hit=False,
            tp1_time=None,
            runner_exit_time=last_time,
            tp1_exit_price=time_price,
            runner_exit_price=time_price,
            tp1_exit_reason="TIME_1000_FULL",
            runner_exit_reason="TIME_1000_FULL",
            break_even_activated=False,
        )

    if tp2_same_bar:
        return _finalize_result(
            base,
            instrument=str(order["instrument"]),
            is_long=is_long,
            entry=entry,
            risk=risk,
            original_stop=original_stop,
            tp1=tp1,
            tp2=tp2,
            tp1_hit=True,
            tp2_hit=True,
            tp1_time=tp1_time,
            runner_exit_time=tp1_time,
            tp1_exit_price=tp1,
            runner_exit_price=tp2,
            tp1_exit_reason="TP1",
            runner_exit_reason="TP2_SAME_BAR",
            break_even_activated=False,
        )

    runner_path = path.loc[path.index > tp1_time]
    active_stop = entry if variant == "MIDPOINT_50_RUNNER_BE" else original_stop
    break_even = variant == "MIDPOINT_50_RUNNER_BE" and not runner_path.empty
    for timestamp, bar in runner_path.iterrows():
        stop_hit = _stop_hit(bar, is_long=is_long, stop=active_stop)
        tp2_hit = _target_hit(bar, is_long=is_long, target=tp2)
        if stop_hit:
            return _finalize_result(
                base,
                instrument=str(order["instrument"]),
                is_long=is_long,
                entry=entry,
                risk=risk,
                original_stop=original_stop,
                tp1=tp1,
                tp2=tp2,
                tp1_hit=True,
                tp2_hit=False,
                tp1_time=tp1_time,
                runner_exit_time=pd.Timestamp(timestamp),
                tp1_exit_price=tp1,
                runner_exit_price=active_stop,
                tp1_exit_reason="TP1",
                runner_exit_reason=(
                    "BE_STOP"
                    if variant == "MIDPOINT_50_RUNNER_BE"
                    else "ORIGINAL_STOP_AFTER_TP1"
                ),
                break_even_activated=break_even,
            )
        if tp2_hit:
            return _finalize_result(
                base,
                instrument=str(order["instrument"]),
                is_long=is_long,
                entry=entry,
                risk=risk,
                original_stop=original_stop,
                tp1=tp1,
                tp2=tp2,
                tp1_hit=True,
                tp2_hit=True,
                tp1_time=tp1_time,
                runner_exit_time=pd.Timestamp(timestamp),
                tp1_exit_price=tp1,
                runner_exit_price=tp2,
                tp1_exit_reason="TP1",
                runner_exit_reason="TP2",
                break_even_activated=break_even,
            )

    if runner_path.empty:
        final_time = tp1_time
        final_bar = path.loc[tp1_time]
    else:
        final_time = pd.Timestamp(runner_path.index[-1])
        final_bar = runner_path.iloc[-1]
    final_price = _exit_quote_price(final_bar, is_long=is_long, field="close")
    return _finalize_result(
        base,
        instrument=str(order["instrument"]),
        is_long=is_long,
        entry=entry,
        risk=risk,
        original_stop=original_stop,
        tp1=tp1,
        tp2=tp2,
        tp1_hit=True,
        tp2_hit=False,
        tp1_time=tp1_time,
        runner_exit_time=final_time,
        tp1_exit_price=tp1,
        runner_exit_price=final_price,
        tp1_exit_reason="TP1",
        runner_exit_reason="TIME_1100",
        break_even_activated=break_even,
    )


def simulate_pair_staged_exits(
    execution_orders: pd.DataFrame,
    events: pd.DataFrame,
    source_directory: Path,
    *,
    symbol: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    orders = execution_orders.copy()
    orders = orders.loc[
        orders["variant"].eq("MKT_NEXT_OPEN")
        & orders["filled"].map(_as_bool)
        & orders["instrument"].eq(symbol)
        & orders["year"].between(start_year, end_year)
    ].copy()
    if orders.empty:
        raise ValueError(f"{symbol}: no filled market-entry orders in requested partition")
    if orders.duplicated(["instrument", "trade_date"]).any():
        raise ValueError(f"{symbol}: more than one market fill per pair/date")

    event_columns = [
        "event_id",
        "asian_high",
        "asian_low",
        "asian_midpoint",
        "asian_range_price",
        "sweep_extreme",
    ]
    event_map = events.loc[:, event_columns].drop_duplicates("event_id")
    merged = orders.merge(event_map, on="event_id", how="left", validate="one_to_one")
    if merged[event_columns[1:]].isna().any().any():
        raise ValueError(f"{symbol}: missing staged-exit event geometry")

    rows: list[dict[str, Any]] = []
    for year, year_orders in merged.groupby("year", sort=True):
        bars = load_bid_ask_minutes(source_directory, symbol, int(year))
        for _, order in year_orders.sort_values(
            ["entry_timestamp_utc", "event_id"], kind="mergesort"
        ).iterrows():
            for variant in STAGED_VARIANTS:
                rows.append(simulate_staged_trade(order, order, bars, variant=variant))
    return pd.DataFrame(rows)
