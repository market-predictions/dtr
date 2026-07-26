from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE, amsterdam_1000
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

LANDMARKS = ("T0", "T1", "T2", "T3")
POLICIES = (
    "T0_QUARTERS",
    "T1_QUARTERS",
    "T0_CONCENTRATED",
    "T0_LATE_WEIGHTED",
    "T0_STATIC_025",
    "T0_STATIC_100",
)
SLIPPAGE_PIPS = 0.10
ADD_THRESHOLDS = {"T1": 0.19, "T2": 0.21, "T3": 0.23}


@dataclass(frozen=True)
class Tranche:
    allocation_r: float
    entry_price: float
    entry_timestamp: pd.Timestamp
    risk_price: float


@dataclass(frozen=True)
class Resolution:
    reason: str
    timestamp: pd.Timestamp
    price: float
    ambiguous: bool = False


def _parse_utc(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column], utc=True, errors="coerce")


def load_hgb_triage_predictions(directory: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for landmark in LANDMARKS:
        path = directory / f"triage_predictions_{landmark}_hgb.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        if not frame["landmark"].eq(landmark).all():
            raise ValueError(f"{path.name}: landmark mismatch")
        if not frame["family"].eq("hgb").all():
            raise ValueError(f"{path.name}: family mismatch")
        frames.append(frame)
    predictions = pd.concat(frames, ignore_index=True)
    if predictions.duplicated(["event_id", "landmark"]).any():
        raise ValueError("duplicate triage prediction keys")
    return predictions


def prepare_staged_population(
    ledger: pd.DataFrame,
    predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "weekday",
        "side",
        "sweep_timestamp_utc",
        "asian_midpoint",
        "stop_price",
        "landmark",
        "entry_price",
        "entry_timestamp_utc",
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing staged ledger columns: {missing}")
    frame = ledger.loc[ledger["landmark"].isin(LANDMARKS)].copy()
    frame["sweep_timestamp_utc"] = _parse_utc(frame, "sweep_timestamp_utc")
    frame["entry_timestamp_utc"] = _parse_utc(frame, "entry_timestamp_utc")
    joined = frame.merge(
        predictions[
            [
                "event_id",
                "landmark",
                "p_reversal",
                "p_continuation",
                "p_unresolved",
                "outer_year",
            ]
        ],
        on=["event_id", "landmark"],
        how="inner",
        validate="one_to_one",
    )
    t0 = joined.loc[joined["landmark"].eq("T0")].sort_values(
        ["instrument", "trade_date", "sweep_timestamp_utc", "event_id"],
        kind="mergesort",
    )
    selected_ids: list[str] = []
    same_minute_ambiguous = 0
    ignored_later = 0
    for _, day in t0.groupby(["instrument", "trade_date"], sort=True):
        first_time = day["sweep_timestamp_utc"].min()
        first = day.loc[day["sweep_timestamp_utc"].eq(first_time)]
        if len(first) > 1 and first["side"].nunique() > 1:
            same_minute_ambiguous += 1
            ignored_later += len(day)
            continue
        selected_ids.append(str(first.iloc[0]["event_id"]))
        ignored_later += max(0, len(day) - 1)
    selected = joined.loc[joined["event_id"].isin(selected_ids)].copy()
    selected = selected.sort_values(
        ["instrument", "trade_date", "landmark"], kind="mergesort"
    ).reset_index(drop=True)
    counts = {
        "candidate_t0_events": int(len(t0)),
        "selected_pair_days": int(len(selected_ids)),
        "same_minute_side_ambiguous_days": int(same_minute_ambiguous),
        "ignored_later_events": int(ignored_later),
    }
    return selected, counts


def _t0_eligible(row: pd.Series) -> bool:
    return bool(row["p_continuation"] < 0.72 and row["p_unresolved"] < 0.30)


def _add_eligible(row: pd.Series) -> bool:
    landmark = str(row["landmark"])
    return bool(
        landmark in ADD_THRESHOLDS
        and row["p_reversal"] >= ADD_THRESHOLDS[landmark]
        and row["p_continuation"] < 0.72
        and row["p_unresolved"] < 0.35
    )


def _cancel_active(row: pd.Series) -> bool:
    landmark = str(row["landmark"])
    threshold = 0.80 if landmark == "T3" else 0.75
    return bool(
        landmark in ("T1", "T2", "T3")
        and row["p_continuation"] >= threshold
        and row["p_continuation"] - row["p_reversal"] >= 0.40
    )


def _entry_allocation(
    policy: str,
    landmark: str,
    rows: dict[str, pd.Series],
    current_allocation: float,
    first_concentrated_add_done: bool,
) -> float:
    row = rows.get(landmark)
    if row is None:
        return 0.0
    if landmark == "T0":
        if policy.startswith("T0_") and _t0_eligible(row):
            return 1.0 if policy == "T0_STATIC_100" else 0.25
        return 0.0
    if policy in ("T0_STATIC_025", "T0_STATIC_100"):
        return 0.0
    if policy == "T1_QUARTERS" and landmark == "T1" and current_allocation == 0:
        return 0.25 if _add_eligible(row) else 0.0
    if current_allocation <= 0 or not _add_eligible(row):
        return 0.0
    if policy == "T0_QUARTERS" and landmark in ("T1", "T2", "T3"):
        return min(0.25, 1.0 - current_allocation)
    if policy == "T1_QUARTERS" and landmark in ("T2", "T3"):
        return min(0.25, 0.75 - current_allocation)
    if policy == "T0_LATE_WEIGHTED" and landmark in ("T2", "T3"):
        return min(0.375, 1.0 - current_allocation)
    if policy == "T0_CONCENTRATED" and landmark in ("T2", "T3"):
        if first_concentrated_add_done:
            return min(0.25, 1.0 - current_allocation) if landmark == "T3" else 0.0
        return min(0.75 if landmark == "T3" else 0.50, 1.0 - current_allocation)
    return 0.0


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


def _resolution_in_path(
    path: pd.DataFrame,
    *,
    is_long: bool,
    stop: float,
    target: float,
) -> Resolution | None:
    for timestamp, bar in path.iterrows():
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
        if stop_hit:
            return Resolution(
                "AMBIGUOUS_STOP_FIRST" if target_hit else "STOP",
                pd.Timestamp(timestamp),
                stop,
                bool(target_hit),
            )
        if target_hit:
            return Resolution("TARGET", pd.Timestamp(timestamp), target)
    return None


def _market_exit_price(
    bars: pd.DataFrame,
    timestamp: pd.Timestamp,
    *,
    is_long: bool,
    use_close: bool,
) -> float:
    if timestamp not in bars.index or not bool(bars.at[timestamp, "active"]):
        raise ValueError(f"inactive market exit timestamp: {timestamp}")
    field = "close" if use_close else "open"
    side = "bid" if is_long else "ask"
    return float(bars.at[timestamp, f"{field}_{side}"])


def _trade_pnl(
    tranches: list[Tranche],
    *,
    exit_price: float,
    exit_reason: str,
    is_long: bool,
    pip: float,
) -> float:
    direction = 1.0 if is_long else -1.0
    slippage = SLIPPAGE_PIPS * pip
    total = 0.0
    for tranche in tranches:
        stressed_entry = (
            tranche.entry_price + slippage
            if is_long
            else tranche.entry_price - slippage
        )
        stressed_exit = exit_price
        if exit_reason != "TARGET":
            stressed_exit = exit_price - slippage if is_long else exit_price + slippage
        units = tranche.allocation_r / tranche.risk_price
        total += units * direction * (stressed_exit - stressed_entry)
    return float(total)


def simulate_staged_event(
    event_rows: pd.DataFrame,
    bars: pd.DataFrame,
    *,
    policy: str,
) -> dict[str, Any]:
    if policy not in POLICIES:
        raise ValueError(policy)
    rows = {str(row["landmark"]): row for _, row in event_rows.iterrows()}
    t0 = rows.get("T0")
    if t0 is None:
        raise ValueError("staged event has no T0 row")
    is_long = str(t0["side"]) == "DOWN"
    symbol = str(t0["instrument"])
    stop = float(t0["stop_price"])
    target = float(t0["asian_midpoint"])
    pip = PIP_SIZE[symbol]
    end = amsterdam_1000(str(t0["trade_date"]))
    tranches: list[Tranche] = []
    allocation = 0.0
    first_concentrated_add_done = False
    action_rows: list[str] = []
    previous_time: pd.Timestamp | None = None

    for landmark in LANDMARKS:
        row = rows.get(landmark)
        if row is None:
            continue
        decision_time = pd.Timestamp(row["entry_timestamp_utc"])
        if previous_time is not None and tranches:
            resolution = _resolution_in_path(
                _active_path(bars, previous_time, decision_time),
                is_long=is_long,
                stop=stop,
                target=target,
            )
            if resolution is not None:
                return {
                    **_base_result(t0, policy),
                    "status": "FILLED",
                    "exit_reason": resolution.reason,
                    "exit_timestamp_utc": resolution.timestamp.isoformat(),
                    "net_r": _trade_pnl(
                        tranches,
                        exit_price=resolution.price,
                        exit_reason=resolution.reason,
                        is_long=is_long,
                        pip=pip,
                    ),
                    "allocated_r": allocation,
                    "tranche_count": len(tranches),
                    "actions": ";".join(action_rows),
                    "ambiguous_stop_first": resolution.ambiguous,
                }
        if tranches and _cancel_active(row):
            exit_price = _market_exit_price(
                bars, decision_time, is_long=is_long, use_close=False
            )
            action_rows.append(f"{landmark}:CANCEL")
            return {
                **_base_result(t0, policy),
                "status": "FILLED",
                "exit_reason": "CONTINUATION_CANCEL",
                "exit_timestamp_utc": decision_time.isoformat(),
                "net_r": _trade_pnl(
                    tranches,
                    exit_price=exit_price,
                    exit_reason="CONTINUATION_CANCEL",
                    is_long=is_long,
                    pip=pip,
                ),
                "allocated_r": allocation,
                "tranche_count": len(tranches),
                "actions": ";".join(action_rows),
                "ambiguous_stop_first": False,
            }
        add = _entry_allocation(
            policy,
            landmark,
            rows,
            allocation,
            first_concentrated_add_done,
        )
        if add > 0:
            entry = float(row["entry_price"])
            risk = entry - stop if is_long else stop - entry
            if risk > 0 and allocation + add <= 1.0 + 1e-12:
                tranches.append(
                    Tranche(add, entry, decision_time, float(risk))
                )
                allocation += add
                action_rows.append(f"{landmark}:ADD_{add:.3f}")
                if policy == "T0_CONCENTRATED" and landmark in ("T2", "T3"):
                    first_concentrated_add_done = True
        previous_time = decision_time

    if not tranches:
        return {
            **_base_result(t0, policy),
            "status": "NO_TRADE",
            "exit_reason": None,
            "net_r": 0.0,
            "allocated_r": 0.0,
            "tranche_count": 0,
            "actions": ";".join(action_rows),
            "ambiguous_stop_first": False,
        }
    if previous_time is None:
        raise RuntimeError("filled staged trade has no decision timestamp")
    resolution = _resolution_in_path(
        _active_path(bars, previous_time, end),
        is_long=is_long,
        stop=stop,
        target=target,
    )
    if resolution is not None:
        exit_price = resolution.price
        exit_reason = resolution.reason
        exit_time = resolution.timestamp
        ambiguous = resolution.ambiguous
    else:
        path = _active_path(bars, previous_time, end)
        if path.empty:
            return {
                **_base_result(t0, policy),
                "status": "NO_ACTIVE_EXIT_PATH",
                "exit_reason": None,
                "net_r": math.nan,
                "allocated_r": allocation,
                "tranche_count": len(tranches),
                "actions": ";".join(action_rows),
                "ambiguous_stop_first": False,
            }
        exit_time = pd.Timestamp(path.index[-1])
        exit_price = _market_exit_price(
            bars, exit_time, is_long=is_long, use_close=True
        )
        exit_reason = "TIME_1000"
        ambiguous = False
    return {
        **_base_result(t0, policy),
        "status": "FILLED",
        "exit_reason": exit_reason,
        "exit_timestamp_utc": exit_time.isoformat(),
        "net_r": _trade_pnl(
            tranches,
            exit_price=exit_price,
            exit_reason=exit_reason,
            is_long=is_long,
            pip=pip,
        ),
        "allocated_r": allocation,
        "tranche_count": len(tranches),
        "actions": ";".join(action_rows),
        "ambiguous_stop_first": ambiguous,
    }


def _base_result(row: pd.Series, policy: str) -> dict[str, Any]:
    return {
        "event_id": str(row["event_id"]),
        "instrument": str(row["instrument"]),
        "trade_date": str(row["trade_date"]),
        "week_key": str(row["week_key"]),
        "year": int(row["year"]),
        "weekday": int(row["weekday"]),
        "side": str(row["side"]),
        "policy": policy,
    }


def simulate_staged_development(
    population: pd.DataFrame,
    source_root: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (symbol, year), group in population.groupby(
        ["instrument", "year"], sort=True
    ):
        bars = load_bid_ask_minutes(source_root / str(symbol), str(symbol), int(year))
        for _, event_rows in group.groupby("event_id", sort=True):
            event_rows = event_rows.sort_values("landmark", kind="mergesort")
            for policy in POLICIES:
                rows.append(
                    simulate_staged_event(event_rows, bars, policy=policy)
                )
    return pd.DataFrame(rows)


def _max_drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    peak = equity.cummax()
    return float((peak - equity).max()) if len(equity) else 0.0


def summarize_staged(results: pd.DataFrame) -> pd.DataFrame:
    filled = results.loc[results["status"].eq("FILLED")].copy()
    summaries: list[dict[str, Any]] = []
    for policy, group in filled.groupby("policy", sort=True):
        ordered = group.sort_values(
            ["trade_date", "instrument", "event_id"], kind="mergesort"
        )
        pair_expectancy = ordered.groupby("instrument")["net_r"].mean()
        year_expectancy = ordered.groupby("year")["net_r"].mean()
        net = float(ordered["net_r"].sum())
        drawdown = _max_drawdown(ordered["net_r"])
        summaries.append(
            {
                "policy": policy,
                "trades": int(len(ordered)),
                "net_r": net,
                "expectancy_r": float(ordered["net_r"].mean()),
                "median_r": float(ordered["net_r"].median()),
                "win_rate": float(ordered["net_r"].gt(0).mean()),
                "max_drawdown_r": drawdown,
                "return_drawdown": net / drawdown if drawdown > 0 else math.nan,
                "positive_pair_count": int(pair_expectancy.gt(0).sum()),
                "positive_year_count": int(year_expectancy.gt(0).sum()),
                "mean_allocated_r": float(ordered["allocated_r"].mean()),
                "mean_tranche_count": float(ordered["tranche_count"].mean()),
                "cancel_rate": float(
                    ordered["exit_reason"].eq("CONTINUATION_CANCEL").mean()
                ),
                "ambiguous_rate": float(
                    ordered["ambiguous_stop_first"].astype(bool).mean()
                ),
            }
        )
    return pd.DataFrame(summaries)
