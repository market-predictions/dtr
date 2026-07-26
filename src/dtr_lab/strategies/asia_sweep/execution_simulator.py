from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import (
    ENTRY_VARIANTS,
    PIP_SIZE,
    EntryVariant,
    amsterdam_1000,
    prepare_execution_events,
)

SIDE_COLUMNS = ("open", "high", "low", "close", "is_active_quote")
SLIPPAGE_STRESSES = (0.0, 0.10, 0.25)


def _source_file(directory: Path, symbol: str, side: str, year: int) -> Path:
    return directory / f"{symbol.lower()}_m1_{side}_{year}.csv.gz"


def _load_side(path: Path, side: str) -> pd.DataFrame:
    required = {"timestamp_utc", *SIDE_COLUMNS}
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path, compression="gzip")
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    frame = frame.loc[:, ["timestamp_utc", *SIDE_COLUMNS]].copy()
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"], utc=True, errors="raise"
    )
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError(f"{path.name}: duplicate timestamps")
    for column in SIDE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame.rename(
        columns={column: f"{column}_{side}" for column in SIDE_COLUMNS}
    )


def load_bid_ask_minutes(directory: Path, symbol: str, year: int) -> pd.DataFrame:
    bid = _load_side(_source_file(directory, symbol, "bid", year), "bid")
    ask = _load_side(_source_file(directory, symbol, "ask", year), "ask")
    merged = bid.merge(ask, on="timestamp_utc", how="inner", validate="one_to_one")
    merged["active"] = (
        merged["is_active_quote_bid"].eq(1)
        & merged["is_active_quote_ask"].eq(1)
    )
    return merged.set_index("timestamp_utc").sort_index()


def _limit_price(event: pd.Series, variant: EntryVariant, t5_mid_close: float) -> float:
    boundary = float(
        event["asian_low"] if event["side"] == "DOWN" else event["asian_high"]
    )
    if variant == "LIMIT_ASIAN_BOUNDARY":
        return boundary
    if variant == "LIMIT_HALF_RETRACE":
        return 0.5 * (boundary + t5_mid_close)
    raise ValueError(f"variant has no limit price: {variant}")


def _base_row(event: pd.Series, variant: EntryVariant) -> dict[str, Any]:
    return {
        "event_id": str(event["event_id"]),
        "instrument": str(event["instrument"]),
        "trade_date": str(event["trade_date"]),
        "week_key": str(event["week_key"]),
        "year": int(event["year"]),
        "weekday": int(event["weekday"]),
        "side": str(event["side"]),
        "prediction": float(event["prediction"]),
        "variant": variant,
        "t5_timestamp_utc": pd.Timestamp(event["t5_timestamp_utc"]).isoformat(),
    }


def _first_active_post_t5(
    bars: pd.DataFrame,
    t5_timestamp: pd.Timestamp,
    expiry: pd.Timestamp,
) -> pd.DataFrame:
    return bars.loc[
        (bars.index > t5_timestamp)
        & (bars.index < expiry)
        & bars["active"].astype(bool)
    ]


def _entry_for_variant(
    event: pd.Series,
    bars: pd.DataFrame,
    variant: EntryVariant,
    expiry: pd.Timestamp,
) -> tuple[pd.Timestamp, float, bool, float | None] | None:
    side = str(event["side"])
    is_long = side == "DOWN"
    t5_timestamp = pd.Timestamp(event["t5_timestamp_utc"])
    post = _first_active_post_t5(bars, t5_timestamp, expiry)
    if post.empty:
        return None
    if variant == "MKT_NEXT_OPEN":
        entry_time = pd.Timestamp(post.index[0])
        entry = float(post.iloc[0]["open_ask" if is_long else "open_bid"])
        return entry_time, entry, True, None

    if t5_timestamp not in bars.index or not bool(bars.at[t5_timestamp, "active"]):
        return None
    t5_mid_close = 0.5 * (
        float(bars.at[t5_timestamp, "close_bid"])
        + float(bars.at[t5_timestamp, "close_ask"])
    )
    limit = _limit_price(event, variant, t5_mid_close)
    if is_long:
        fills = post.loc[post["low_ask"] <= limit]
    else:
        fills = post.loc[post["high_bid"] >= limit]
    if fills.empty:
        return pd.NaT, math.nan, False, limit
    return pd.Timestamp(fills.index[0]), float(limit), False, limit


def _exit_trade(
    event: pd.Series,
    bars: pd.DataFrame,
    *,
    entry_time: pd.Timestamp,
    entry_price: float,
    entry_is_market: bool,
) -> dict[str, Any]:
    is_long = str(event["side"]) == "DOWN"
    target = float(event["asian_midpoint"])
    asian_range = float(event["asian_range_price"])
    sweep_extreme = float(event["sweep_extreme"])
    stop = (
        sweep_extreme - 0.20 * asian_range
        if is_long
        else sweep_extreme + 0.20 * asian_range
    )
    risk = entry_price - stop if is_long else stop - entry_price
    target_distance = target - entry_price if is_long else entry_price - target
    if risk <= 0 or target_distance <= 0:
        return {
            "status": "INVALID_GEOMETRY",
            "filled": False,
            "entry_timestamp_utc": entry_time.isoformat(),
            "entry_price": entry_price,
            "stop_price": stop,
            "target_price": target,
            "initial_risk_price": risk,
            "target_distance_price": target_distance,
        }

    end = amsterdam_1000(str(event["trade_date"]))
    path = bars.loc[
        (bars.index >= entry_time)
        & (bars.index < end)
        & bars["active"].astype(bool)
    ]
    if path.empty:
        return {
            "status": "NO_ACTIVE_PATH",
            "filled": False,
            "entry_timestamp_utc": entry_time.isoformat(),
        }

    exit_reason = "TIME"
    exit_time = pd.Timestamp(path.index[-1])
    exit_price = float(path.iloc[-1]["close_bid" if is_long else "close_ask"])
    ambiguous = False
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
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_STOP_FIRST" if ambiguous else "STOP"
            exit_time = pd.Timestamp(timestamp)
            exit_price = stop
            break
        if target_hit:
            exit_reason = "TARGET"
            exit_time = pd.Timestamp(timestamp)
            exit_price = target
            break

    direction = 1.0 if is_long else -1.0
    result: dict[str, Any] = {
        "status": "FILLED",
        "filled": True,
        "entry_timestamp_utc": entry_time.isoformat(),
        "entry_price": entry_price,
        "entry_is_market": entry_is_market,
        "stop_price": stop,
        "target_price": target,
        "initial_risk_price": risk,
        "target_distance_price": target_distance,
        "reward_risk": target_distance / risk,
        "exit_timestamp_utc": exit_time.isoformat(),
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "ambiguous_stop_first": ambiguous,
    }
    pip = PIP_SIZE[str(event["instrument"])]
    for stress_pips in SLIPPAGE_STRESSES:
        slippage = stress_pips * pip
        stressed_entry = entry_price
        stressed_exit = exit_price
        if entry_is_market:
            stressed_entry = entry_price + slippage if is_long else entry_price - slippage
        if exit_reason in {"STOP", "AMBIGUOUS_STOP_FIRST", "TIME"}:
            stressed_exit = exit_price - slippage if is_long else exit_price + slippage
        pnl = direction * (stressed_exit - stressed_entry)
        suffix = str(stress_pips).replace(".", "_")
        result[f"net_r_{suffix}"] = pnl / risk
    return result


def simulate_event(
    event: pd.Series,
    bars: pd.DataFrame,
    *,
    variant: EntryVariant,
    expiry: pd.Timestamp,
) -> dict[str, Any]:
    base = _base_row(event, variant)
    entry = _entry_for_variant(event, bars, variant, expiry)
    if entry is None:
        return {**base, "status": "NO_ACTIVE_ENTRY", "filled": False}
    entry_time, entry_price, entry_is_market, order_price = entry
    if pd.isna(entry_time):
        return {
            **base,
            "status": "UNFILLED",
            "filled": False,
            "order_price": order_price,
            "order_expiry_utc": expiry.isoformat(),
        }
    outcome = _exit_trade(
        event,
        bars,
        entry_time=pd.Timestamp(entry_time),
        entry_price=float(entry_price),
        entry_is_market=entry_is_market,
    )
    return {
        **base,
        "order_price": order_price,
        "order_expiry_utc": expiry.isoformat(),
        **outcome,
    }


def simulate_pair_execution(
    events: pd.DataFrame,
    predictions: pd.DataFrame,
    source_directory: Path,
    *,
    symbol: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    eligible = prepare_execution_events(
        events,
        predictions,
        symbol=symbol,
        start_year=start_year,
        end_year=end_year,
    )
    rows: list[dict[str, Any]] = []
    for year, year_events in eligible.groupby("year", sort=True):
        bars = load_bid_ask_minutes(source_directory, symbol, int(year))
        for trade_date, day in year_events.groupby("trade_date", sort=True):
            day = day.sort_values(
                ["t5_timestamp_utc", "event_id"], kind="mergesort"
            ).reset_index(drop=True)
            for variant in ENTRY_VARIANTS:
                filled = False
                for index, event in day.iterrows():
                    if filled:
                        break
                    final_expiry = amsterdam_1000(str(trade_date))
                    if variant == "MKT_NEXT_OPEN" or index + 1 == len(day):
                        expiry = final_expiry
                    else:
                        next_event = day.iloc[index + 1]
                        replacement = pd.Timestamp(
                            next_event["first_actionable_timestamp_utc"]
                        )
                        expiry = min(final_expiry, replacement)
                    result = simulate_event(
                        event,
                        bars,
                        variant=variant,
                        expiry=expiry,
                    )
                    rows.append(result)
                    filled = bool(result.get("filled", False))
    return pd.DataFrame(rows)
