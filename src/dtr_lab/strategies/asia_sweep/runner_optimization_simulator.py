from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

TargetKind = Literal["2R", "3R", "4R", "5R", "OPPOSITE_BOUNDARY"]
StopPolicy = Literal["ORIGINAL_STOP", "BREAK_EVEN_AFTER_TP1"]

TARGET_KINDS: tuple[TargetKind, ...] = (
    "2R",
    "3R",
    "4R",
    "5R",
    "OPPOSITE_BOUNDARY",
)
EXIT_HOURS: tuple[int, ...] = (12, 14, 16, 18)
STOP_POLICIES: tuple[StopPolicy, ...] = (
    "ORIGINAL_STOP",
    "BREAK_EVEN_AFTER_TP1",
)
SLIPPAGE_STRESSES = (0.0, 0.10, 0.25)
TP1_FRACTION = 0.50
RUNNER_FRACTION = 0.50


def policy_id(target_kind: TargetKind, exit_hour: int, stop_policy: StopPolicy) -> str:
    return f"{target_kind}_H{exit_hour:02d}_{stop_policy}"


def runner_policy_manifest() -> list[dict[str, object]]:
    return [
        {
            "policy_id": policy_id(target_kind, exit_hour, stop_policy),
            "target_kind": target_kind,
            "exit_hour": exit_hour,
            "stop_policy": stop_policy,
        }
        for target_kind, exit_hour, stop_policy in product(
            TARGET_KINDS, EXIT_HOURS, STOP_POLICIES
        )
    ]


def _amsterdam_clock(trade_date: str, hour: int) -> pd.Timestamp:
    return pd.Timestamp(
        f"{trade_date} {hour:02d}:00:00", tz="Europe/Amsterdam"
    ).tz_convert("UTC")


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _exit_quote_price(bar: pd.Series, *, is_long: bool, field: str) -> float:
    side = "bid" if is_long else "ask"
    return float(bar[f"{field}_{side}"])


def _stop_hit(bar: pd.Series, *, is_long: bool, stop: float) -> bool:
    if is_long:
        return bool(float(bar["low_bid"]) <= stop)
    return bool(float(bar["high_ask"]) >= stop)


def _target_hit(bar: pd.Series, *, is_long: bool, target: float) -> bool:
    if is_long:
        return bool(float(bar["high_bid"]) >= target)
    return bool(float(bar["low_ask"]) <= target)


def _stressed_leg_r(
    *,
    entry: float,
    exit_price: float,
    risk: float,
    is_long: bool,
    exit_is_market_or_stop: bool,
    stress_pips: float,
    pip: float,
) -> float:
    slippage = stress_pips * pip
    stressed_entry = entry + slippage if is_long else entry - slippage
    stressed_exit = exit_price
    if exit_is_market_or_stop:
        stressed_exit = exit_price - slippage if is_long else exit_price + slippage
    direction = 1.0 if is_long else -1.0
    return direction * (stressed_exit - stressed_entry) / risk


def _runner_target(
    event: pd.Series,
    *,
    target_kind: TargetKind,
    entry: float,
    risk: float,
    is_long: bool,
) -> float:
    if target_kind == "OPPOSITE_BOUNDARY":
        return float(event["asian_high"] if is_long else event["asian_low"])
    multiple = float(target_kind.removesuffix("R"))
    return entry + multiple * risk if is_long else entry - multiple * risk


def _base_row(
    order: pd.Series,
    *,
    target_kind: TargetKind,
    exit_hour: int,
    stop_policy: StopPolicy,
) -> dict[str, Any]:
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
        "entry_timestamp_utc": pd.Timestamp(order["entry_timestamp_utc"]).isoformat(),
        "entry_price": float(order["entry_price"]),
        "target_kind": target_kind,
        "exit_hour": int(exit_hour),
        "stop_policy": stop_policy,
        "policy_id": policy_id(target_kind, exit_hour, stop_policy),
    }


def _finalize_result(
    base: dict[str, Any],
    *,
    instrument: str,
    is_long: bool,
    entry: float,
    risk: float,
    original_stop: float,
    tp1: float,
    runner_target: float,
    tp1_hit: bool,
    runner_target_hit: bool,
    tp1_time: pd.Timestamp | None,
    runner_exit_time: pd.Timestamp,
    tp1_exit_price: float,
    runner_exit_price: float,
    tp1_exit_reason: str,
    runner_exit_reason: str,
    break_even_activated: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        **base,
        "status": "FILLED",
        "filled": True,
        "initial_risk_price": risk,
        "original_stop_price": original_stop,
        "tp1_price": tp1,
        "runner_target_price": runner_target,
        "tp1_fraction": TP1_FRACTION,
        "runner_fraction": RUNNER_FRACTION,
        "tp1_hit": tp1_hit,
        "runner_target_hit": runner_target_hit,
        "tp1_timestamp_utc": tp1_time.isoformat() if tp1_time is not None else None,
        "runner_exit_timestamp_utc": runner_exit_time.isoformat(),
        "tp1_exit_price": tp1_exit_price,
        "runner_exit_price": runner_exit_price,
        "tp1_exit_reason": tp1_exit_reason,
        "runner_exit_reason": runner_exit_reason,
        "break_even_activated": break_even_activated,
    }
    tp1_market_or_stop = tp1_exit_reason in {"STOP_FULL", "TIME_FULL"}
    runner_market_or_stop = runner_exit_reason in {
        "STOP_FULL",
        "TIME_FULL",
        "ORIGINAL_STOP_AFTER_TP1",
        "BE_STOP",
        "TIME_RUNNER",
    }
    pip = PIP_SIZE[instrument]
    for stress in SLIPPAGE_STRESSES:
        leg1 = _stressed_leg_r(
            entry=entry,
            exit_price=tp1_exit_price,
            risk=risk,
            is_long=is_long,
            exit_is_market_or_stop=tp1_market_or_stop,
            stress_pips=stress,
            pip=pip,
        )
        leg2 = _stressed_leg_r(
            entry=entry,
            exit_price=runner_exit_price,
            risk=risk,
            is_long=is_long,
            exit_is_market_or_stop=runner_market_or_stop,
            stress_pips=stress,
            pip=pip,
        )
        suffix = str(stress).replace(".", "_")
        result[f"tp1_leg_r_{suffix}"] = leg1
        result[f"runner_leg_r_{suffix}"] = leg2
        result[f"net_r_{suffix}"] = TP1_FRACTION * leg1 + RUNNER_FRACTION * leg2
    return result


def simulate_runner_trade(
    order: pd.Series,
    event: pd.Series,
    bars: pd.DataFrame,
    *,
    target_kind: TargetKind,
    exit_hour: int,
    stop_policy: StopPolicy,
) -> dict[str, Any]:
    base = _base_row(
        order,
        target_kind=target_kind,
        exit_hour=exit_hour,
        stop_policy=stop_policy,
    )
    is_long = str(order["side"]) == "DOWN"
    entry_time = pd.Timestamp(order["entry_timestamp_utc"])
    entry = float(order["entry_price"])
    original_stop = float(order["stop_price"])
    risk = entry - original_stop if is_long else original_stop - entry
    tp1 = float(event["asian_midpoint"])
    target = _runner_target(
        event,
        target_kind=target_kind,
        entry=entry,
        risk=risk,
        is_long=is_long,
    )
    tp1_distance = tp1 - entry if is_long else entry - tp1
    target_distance = target - entry if is_long else entry - target
    target_beyond_tp1 = target > tp1 if is_long else target < tp1
    if risk <= 0 or tp1_distance <= 0 or target_distance <= 0 or not target_beyond_tp1:
        return {
            **base,
            "status": "INVALID_GEOMETRY",
            "filled": False,
            "initial_risk_price": risk,
            "original_stop_price": original_stop,
            "tp1_price": tp1,
            "runner_target_price": target,
        }

    deadline = _amsterdam_clock(str(order["trade_date"]), exit_hour)
    path = bars.loc[
        (bars.index >= entry_time)
        & (bars.index < deadline)
        & bars["active"].astype(bool)
    ]
    if path.empty:
        return {**base, "status": "NO_ACTIVE_PATH", "filled": False}

    tp1_time: pd.Timestamp | None = None
    target_same_bar = False
    for timestamp, bar in path.iterrows():
        if _stop_hit(bar, is_long=is_long, stop=original_stop):
            return _finalize_result(
                base,
                instrument=str(order["instrument"]),
                is_long=is_long,
                entry=entry,
                risk=risk,
                original_stop=original_stop,
                tp1=tp1,
                runner_target=target,
                tp1_hit=False,
                runner_target_hit=False,
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
            target_same_bar = _target_hit(bar, is_long=is_long, target=target)
            break

    if tp1_time is None:
        final_time = pd.Timestamp(path.index[-1])
        final_price = _exit_quote_price(path.iloc[-1], is_long=is_long, field="close")
        return _finalize_result(
            base,
            instrument=str(order["instrument"]),
            is_long=is_long,
            entry=entry,
            risk=risk,
            original_stop=original_stop,
            tp1=tp1,
            runner_target=target,
            tp1_hit=False,
            runner_target_hit=False,
            tp1_time=None,
            runner_exit_time=final_time,
            tp1_exit_price=final_price,
            runner_exit_price=final_price,
            tp1_exit_reason="TIME_FULL",
            runner_exit_reason="TIME_FULL",
            break_even_activated=False,
        )

    if target_same_bar:
        return _finalize_result(
            base,
            instrument=str(order["instrument"]),
            is_long=is_long,
            entry=entry,
            risk=risk,
            original_stop=original_stop,
            tp1=tp1,
            runner_target=target,
            tp1_hit=True,
            runner_target_hit=True,
            tp1_time=tp1_time,
            runner_exit_time=tp1_time,
            tp1_exit_price=tp1,
            runner_exit_price=target,
            tp1_exit_reason="TP1",
            runner_exit_reason="RUNNER_TARGET_SAME_BAR",
            break_even_activated=False,
        )

    runner_path = path.loc[path.index > tp1_time]
    active_stop = entry if stop_policy == "BREAK_EVEN_AFTER_TP1" else original_stop
    break_even = stop_policy == "BREAK_EVEN_AFTER_TP1" and not runner_path.empty
    for timestamp, bar in runner_path.iterrows():
        stop_hit = _stop_hit(bar, is_long=is_long, stop=active_stop)
        target_hit = _target_hit(bar, is_long=is_long, target=target)
        if stop_hit:
            return _finalize_result(
                base,
                instrument=str(order["instrument"]),
                is_long=is_long,
                entry=entry,
                risk=risk,
                original_stop=original_stop,
                tp1=tp1,
                runner_target=target,
                tp1_hit=True,
                runner_target_hit=False,
                tp1_time=tp1_time,
                runner_exit_time=pd.Timestamp(timestamp),
                tp1_exit_price=tp1,
                runner_exit_price=active_stop,
                tp1_exit_reason="TP1",
                runner_exit_reason=(
                    "BE_STOP"
                    if stop_policy == "BREAK_EVEN_AFTER_TP1"
                    else "ORIGINAL_STOP_AFTER_TP1"
                ),
                break_even_activated=break_even,
            )
        if target_hit:
            return _finalize_result(
                base,
                instrument=str(order["instrument"]),
                is_long=is_long,
                entry=entry,
                risk=risk,
                original_stop=original_stop,
                tp1=tp1,
                runner_target=target,
                tp1_hit=True,
                runner_target_hit=True,
                tp1_time=tp1_time,
                runner_exit_time=pd.Timestamp(timestamp),
                tp1_exit_price=tp1,
                runner_exit_price=target,
                tp1_exit_reason="TP1",
                runner_exit_reason="RUNNER_TARGET",
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
        runner_target=target,
        tp1_hit=True,
        runner_target_hit=False,
        tp1_time=tp1_time,
        runner_exit_time=final_time,
        tp1_exit_price=tp1,
        runner_exit_price=final_price,
        tp1_exit_reason="TP1",
        runner_exit_reason="TIME_RUNNER",
        break_even_activated=break_even,
    )


def simulate_pair_runner_grid(
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
        raise ValueError(f"{symbol}: missing runner event geometry")

    manifest = runner_policy_manifest()
    rows: list[dict[str, Any]] = []
    for year, year_orders in merged.groupby("year", sort=True):
        bars = load_bid_ask_minutes(source_directory, symbol, int(year))
        ordered = year_orders.sort_values(
            ["entry_timestamp_utc", "event_id"], kind="mergesort"
        )
        for _, order in ordered.iterrows():
            for policy in manifest:
                rows.append(
                    simulate_runner_trade(
                        order,
                        order,
                        bars,
                        target_kind=policy["target_kind"],
                        exit_hour=int(policy["exit_hour"]),
                        stop_policy=policy["stop_policy"],
                    )
                )
    return pd.DataFrame(rows)
