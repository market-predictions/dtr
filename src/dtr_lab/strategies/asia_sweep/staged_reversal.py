from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

PolicyTier = Literal["conservative", "balanced", "aggressive"]

POLICY_ORDER = (
    "CONSERVATIVE_NO_T0",
    "CONSERVATIVE_T0_025",
    "BALANCED_NO_T0",
    "BALANCED_T0_025",
    "AGGRESSIVE_NO_T0",
    "AGGRESSIVE_T0_050",
)

POLICY_CONFIG = {
    "CONSERVATIVE_NO_T0": {"tier": "conservative", "t0_risk": 0.0},
    "CONSERVATIVE_T0_025": {"tier": "conservative", "t0_risk": 0.25},
    "BALANCED_NO_T0": {"tier": "balanced", "t0_risk": 0.0},
    "BALANCED_T0_025": {"tier": "balanced", "t0_risk": 0.25},
    "AGGRESSIVE_NO_T0": {"tier": "aggressive", "t0_risk": 0.0},
    "AGGRESSIVE_T0_050": {"tier": "aggressive", "t0_risk": 0.50},
}

STRESS_LEVELS = (0.0, 0.10, 0.25)


@dataclass
class OpenLot:
    units: float
    entry_price: float
    assigned_risk: float


def _amsterdam_1000(trade_date: str) -> pd.Timestamp:
    return pd.Timestamp(
        f"{trade_date} 10:00:00",
        tz="Europe/Amsterdam",
    ).tz_convert("UTC")


def _action_for_state(
    policy: str,
    stage: Literal["T2", "T3"],
    decision: str,
    *,
    has_position: bool,
    assigned_risk: float,
) -> tuple[str, float]:
    config = POLICY_CONFIG[policy]
    tier = str(config["tier"])
    has_t0 = float(config["t0_risk"]) > 0.0
    if not has_position:
        return "NONE", 0.0
    if decision == "CONTINUATION":
        return "EXIT", 1.0
    if stage == "T2":
        if decision == "REVERSAL":
            add = {"conservative": 0.25, "balanced": 0.50, "aggressive": 0.50}[
                tier
            ]
            return "ADD", add
        if tier == "balanced":
            return "REDUCE", 0.50
        return "HOLD", 0.0
    if decision == "REVERSAL":
        if tier == "conservative":
            return "ADD", 0.25
        if tier == "balanced":
            return "ADD_TO", 1.0
        return "HOLD", 0.0
    if tier == "conservative":
        return "EXIT", 1.0
    if tier == "balanced":
        return ("HOLD", 0.0) if has_t0 else ("REDUCE", 0.50)
    return "REDUCE", 0.50


def prepare_policy_candidates(
    t0_predictions: pd.DataFrame,
    t2_predictions: pd.DataFrame,
    landmark_ledger: pd.DataFrame,
    *,
    symbol: str,
    policy: str,
) -> pd.DataFrame:
    if policy not in POLICY_CONFIG:
        raise ValueError(f"unsupported staged reversal policy: {policy}")
    symbol = symbol.upper()
    geometry = landmark_ledger.sort_values(
        ["event_id", "landmark_bar_count"], kind="mergesort"
    ).drop_duplicates("event_id")
    geometry = geometry.loc[
        geometry["instrument"].eq(symbol)
        & geometry["year"].between(2015, 2019),
        [
            "event_id",
            "asian_midpoint",
            "asian_range_price",
            "sweep_extreme",
        ],
    ]
    has_t0 = float(POLICY_CONFIG[policy]["t0_risk"]) > 0.0
    if has_t0:
        candidates = t0_predictions.loc[
            t0_predictions["instrument"].eq(symbol)
            & t0_predictions["year"].between(2015, 2019)
        ].copy()
    else:
        candidates = t2_predictions.loc[
            t2_predictions["instrument"].eq(symbol)
            & t2_predictions["year"].between(2015, 2019)
            & t2_predictions["decision"].eq("REVERSAL")
        ].copy()
    candidates["entry_timestamp_utc"] = pd.to_datetime(
        candidates["entry_timestamp_utc"], utc=True, errors="raise"
    )
    candidates = candidates.sort_values(
        ["trade_date", "entry_timestamp_utc", "event_id"], kind="mergesort"
    ).groupby(["instrument", "trade_date"], as_index=False).first()
    candidates = candidates.merge(
        geometry,
        on="event_id",
        how="inner",
        validate="one_to_one",
    )
    if candidates.duplicated(["instrument", "trade_date"]).any():
        raise ValueError(f"{symbol}/{policy}: daily lockout selection failed")
    return candidates.sort_values(
        ["year", "entry_timestamp_utc", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def _prediction_map(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    result = frame.copy()
    result["entry_timestamp_utc"] = pd.to_datetime(
        result["entry_timestamp_utc"], utc=True, errors="raise"
    )
    if result.duplicated("event_id").any():
        raise ValueError("staged prediction event ids must be unique")
    return result.set_index("event_id")[["decision", "entry_timestamp_utc"]].to_dict(
        orient="index"
    )


def _market_price(bar: pd.Series, *, is_long: bool, is_entry: bool) -> float:
    if is_entry:
        return float(bar["open_ask" if is_long else "open_bid"])
    return float(bar["open_bid" if is_long else "open_ask"])


def _close_fill(
    raw_price: float,
    *,
    is_long: bool,
    stress_pips: float,
    pip: float,
    target_limit: bool,
) -> float:
    if target_limit:
        return raw_price
    slippage = stress_pips * pip
    return raw_price - slippage if is_long else raw_price + slippage


def _entry_fill(
    raw_price: float,
    *,
    is_long: bool,
    stress_pips: float,
    pip: float,
) -> float:
    slippage = stress_pips * pip
    return raw_price + slippage if is_long else raw_price - slippage


def simulate_staged_attempt(
    event: pd.Series,
    policy: str,
    bars: pd.DataFrame,
    t0_map: dict[str, dict[str, Any]],
    t2_map: dict[str, dict[str, Any]],
    t3_map: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    config = POLICY_CONFIG[policy]
    event_id = str(event["event_id"])
    side = str(event["side"])
    is_long = side == "DOWN"
    direction = 1.0 if is_long else -1.0
    asian_range = float(event["asian_range_price"])
    sweep_extreme = float(event["sweep_extreme"])
    stop_price = (
        sweep_extreme - 0.20 * asian_range
        if is_long
        else sweep_extreme + 0.20 * asian_range
    )
    target_price = float(event["asian_midpoint"])
    actions: dict[pd.Timestamp, tuple[str, float, str, str]] = {}
    t0_risk = float(config["t0_risk"])
    if t0_risk > 0.0:
        t0 = t0_map.get(event_id)
        if t0 is None:
            return None
        actions[pd.Timestamp(t0["entry_timestamp_utc"])] = (
            "INITIAL",
            t0_risk,
            "T0",
            "ABSTAIN",
        )
    else:
        t2 = t2_map.get(event_id)
        if t2 is None or str(t2["decision"]) != "REVERSAL":
            return None
        initial_risk = {
            "conservative": 0.50,
            "balanced": 0.75,
            "aggressive": 1.00,
        }[str(config["tier"])]
        actions[pd.Timestamp(t2["entry_timestamp_utc"])] = (
            "INITIAL",
            initial_risk,
            "T2",
            "REVERSAL",
        )
    for stage, stage_map in (("T2", t2_map), ("T3", t3_map)):
        state = stage_map.get(event_id)
        if state is None:
            continue
        timestamp = pd.Timestamp(state["entry_timestamp_utc"])
        if timestamp not in actions:
            actions[timestamp] = ("STATE", 0.0, stage, str(state["decision"]))

    start = min(actions)
    end = _amsterdam_1000(str(event["trade_date"]))
    path = bars.loc[
        (bars.index >= start)
        & (bars.index < end)
        & bars["active"].astype(bool)
    ]
    if path.empty:
        return None

    lots: list[OpenLot] = []
    pnl = {stress: 0.0 for stress in STRESS_LEVELS}
    assigned_risk = 0.0
    blocked = False
    action_log: list[dict[str, Any]] = []
    exit_reason: str | None = None
    exit_time = pd.NaT
    pip = PIP_SIZE[str(event["instrument"])]
    last_active: tuple[pd.Timestamp, pd.Series] | None = None

    def add_lot(risk_allocation: float, raw_entry: float) -> bool:
        nonlocal assigned_risk
        allocation = min(max(risk_allocation, 0.0), 1.0 - assigned_risk)
        risk_price = (
            raw_entry - stop_price if is_long else stop_price - raw_entry
        )
        reward_price = (
            target_price - raw_entry if is_long else raw_entry - target_price
        )
        if allocation <= 0.0 or risk_price <= 0.0 or reward_price <= 0.0:
            return False
        lots.append(
            OpenLot(
                units=allocation / risk_price,
                entry_price=raw_entry,
                assigned_risk=allocation,
            )
        )
        assigned_risk += allocation
        return True

    def close_fraction(
        fraction: float,
        raw_exit: float,
        *,
        target_limit: bool,
    ) -> None:
        nonlocal assigned_risk
        close_fraction_value = min(max(fraction, 0.0), 1.0)
        for lot in lots:
            closed_units = lot.units * close_fraction_value
            for stress in STRESS_LEVELS:
                entry_fill = _entry_fill(
                    lot.entry_price,
                    is_long=is_long,
                    stress_pips=stress,
                    pip=pip,
                )
                exit_fill = _close_fill(
                    raw_exit,
                    is_long=is_long,
                    stress_pips=stress,
                    pip=pip,
                    target_limit=target_limit,
                )
                pnl[stress] += closed_units * direction * (exit_fill - entry_fill)
            lot.units *= 1.0 - close_fraction_value
            lot.assigned_risk *= 1.0 - close_fraction_value
        assigned_risk = sum(lot.assigned_risk for lot in lots)
        lots[:] = [lot for lot in lots if lot.units > 1e-12]

    for timestamp, bar in path.iterrows():
        last_active = (pd.Timestamp(timestamp), bar)
        if timestamp in actions:
            kind, value, stage, decision = actions[pd.Timestamp(timestamp)]
            if kind == "INITIAL":
                raw_entry = _market_price(bar, is_long=is_long, is_entry=True)
                executed = add_lot(value, raw_entry)
                action_log.append(
                    {
                        "timestamp": pd.Timestamp(timestamp).isoformat(),
                        "stage": stage,
                        "decision": decision,
                        "action": "ENTER",
                        "value": value,
                        "executed": executed,
                    }
                )
            elif lots and not blocked:
                action, action_value = _action_for_state(
                    policy,
                    stage,
                    decision,
                    has_position=True,
                    assigned_risk=assigned_risk,
                )
                executed = True
                if action == "EXIT":
                    raw_exit = _market_price(bar, is_long=is_long, is_entry=False)
                    close_fraction(1.0, raw_exit, target_limit=False)
                    blocked = True
                    exit_reason = f"{stage}_{decision}_EXIT"
                    exit_time = pd.Timestamp(timestamp)
                elif action == "REDUCE":
                    raw_exit = _market_price(bar, is_long=is_long, is_entry=False)
                    close_fraction(action_value, raw_exit, target_limit=False)
                elif action == "ADD":
                    raw_entry = _market_price(bar, is_long=is_long, is_entry=True)
                    executed = add_lot(action_value, raw_entry)
                elif action == "ADD_TO":
                    raw_entry = _market_price(bar, is_long=is_long, is_entry=True)
                    executed = add_lot(
                        max(0.0, action_value - assigned_risk),
                        raw_entry,
                    )
                action_log.append(
                    {
                        "timestamp": pd.Timestamp(timestamp).isoformat(),
                        "stage": stage,
                        "decision": decision,
                        "action": action,
                        "value": action_value,
                        "executed": executed,
                    }
                )
        if not lots:
            if blocked:
                break
            continue
        stop_hit = (
            float(bar["low_bid"]) <= stop_price
            if is_long
            else float(bar["high_ask"]) >= stop_price
        )
        target_hit = (
            float(bar["high_bid"]) >= target_price
            if is_long
            else float(bar["low_ask"]) <= target_price
        )
        if stop_hit:
            close_fraction(1.0, stop_price, target_limit=False)
            exit_reason = "AMBIGUOUS_STOP_FIRST" if target_hit else "STOP"
            exit_time = pd.Timestamp(timestamp)
            break
        if target_hit:
            close_fraction(1.0, target_price, target_limit=True)
            exit_reason = "TARGET"
            exit_time = pd.Timestamp(timestamp)
            break

    if lots and last_active is not None:
        timestamp, bar = last_active
        raw_exit = float(bar["close_bid" if is_long else "close_ask"])
        close_fraction(1.0, raw_exit, target_limit=False)
        exit_reason = "TIME"
        exit_time = timestamp
    if not any(action["action"] == "ENTER" and action["executed"] for action in action_log):
        return None
    return {
        "policy": policy,
        "event_id": event_id,
        "instrument": str(event["instrument"]),
        "trade_date": str(event["trade_date"]),
        "week_key": str(event["week_key"]),
        "year": int(event["year"]),
        "weekday": int(event["weekday"]),
        "side": side,
        "exit_reason": exit_reason,
        "exit_timestamp_utc": (
            pd.Timestamp(exit_time).isoformat() if pd.notna(exit_time) else None
        ),
        "net_r_0_0": pnl[0.0],
        "net_r_0_1": pnl[0.10],
        "net_r_0_25": pnl[0.25],
        "action_count": int(len(action_log)),
        "action_log": json.dumps(action_log, sort_keys=True),
    }


def build_pair_staged_policy_ledger(
    candidates: pd.DataFrame,
    policy: str,
    source_directory: Path,
    *,
    symbol: str,
    t0_predictions: pd.DataFrame,
    t2_predictions: pd.DataFrame,
    t3_predictions: pd.DataFrame,
) -> pd.DataFrame:
    t0_map = _prediction_map(t0_predictions.loc[t0_predictions["instrument"].eq(symbol)])
    t2_map = _prediction_map(t2_predictions.loc[t2_predictions["instrument"].eq(symbol)])
    t3_map = _prediction_map(t3_predictions.loc[t3_predictions["instrument"].eq(symbol)])
    rows: list[dict[str, Any]] = []
    for year, year_events in candidates.groupby("year", sort=True):
        bars = load_bid_ask_minutes(source_directory, symbol, int(year))
        for _, event in year_events.iterrows():
            result = simulate_staged_attempt(
                event,
                policy,
                bars,
                t0_map,
                t2_map,
                t3_map,
            )
            if result is not None:
                rows.append(result)
    ledger = pd.DataFrame(rows)
    if ledger.empty:
        raise ValueError(f"{symbol}/{policy}: staged ledger is empty")
    if ledger.duplicated(["policy", "instrument", "trade_date"]).any():
        raise ValueError(f"{symbol}/{policy}: daily lockout violated")
    return ledger.sort_values(
        ["trade_date", "instrument", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def maximum_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(np.concatenate(([0.0], equity)))
    return float(np.max(peak[1:] - equity))


def summarize_policy(trades: pd.DataFrame) -> dict[str, Any]:
    ordered = trades.sort_values(
        ["trade_date", "instrument", "event_id"], kind="mergesort"
    )
    net_r = float(ordered["net_r_0_0"].sum())
    drawdown = maximum_drawdown(ordered["net_r_0_0"].to_numpy(dtype=float))
    pair = ordered.groupby("instrument")["net_r_0_0"].sum()
    year = ordered.groupby("year")["net_r_0_0"].sum()
    return {
        "policy": str(ordered["policy"].iloc[0]),
        "trades": int(len(ordered)),
        "net_r": net_r,
        "expectancy": float(ordered["net_r_0_0"].mean()),
        "expectancy_stress_010": float(ordered["net_r_0_1"].mean()),
        "expectancy_stress_025": float(ordered["net_r_0_25"].mean()),
        "maximum_drawdown_r": drawdown,
        "return_drawdown": net_r / drawdown if drawdown > 0.0 else math.nan,
        "win_rate": float(ordered["net_r_0_0"].gt(0.0).mean()),
        "positive_pairs": int(pair.gt(0.0).sum()),
        "positive_years": int(year.gt(0.0).sum()),
        "mean_action_count": float(ordered["action_count"].mean()),
    }


def select_inner_policy(training: pd.DataFrame) -> str | None:
    candidates: list[tuple[float, float, float, int, str]] = []
    order = {policy: index for index, policy in enumerate(POLICY_ORDER)}
    for policy, group in training.groupby("policy", sort=False):
        summary = summarize_policy(group)
        pair_net = group.groupby("instrument")["net_r_0_1"].sum()
        year_net = group.groupby("year")["net_r_0_1"].sum()
        stressed_drawdown = maximum_drawdown(
            group.sort_values(
                ["trade_date", "instrument", "event_id"], kind="mergesort"
            )["net_r_0_1"].to_numpy(dtype=float)
        )
        if not (
            summary["trades"] >= 200
            and summary["expectancy_stress_010"] > 0.0
            and pair_net.gt(0.0).sum() == 2
            and year_net.gt(0.0).sum() >= 3
            and stressed_drawdown <= 12.0
        ):
            continue
        stressed_net = float(group["net_r_0_1"].sum())
        return_drawdown = (
            stressed_net / stressed_drawdown if stressed_drawdown > 0.0 else math.inf
        )
        candidates.append(
            (
                -float(summary["expectancy_stress_010"]),
                -return_drawdown,
                float(summary["mean_action_count"]),
                order[str(policy)],
                str(policy),
            )
        )
    return min(candidates)[-1] if candidates else None
