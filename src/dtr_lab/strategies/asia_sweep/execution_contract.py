from __future__ import annotations

from typing import Literal

import pandas as pd

AMSTERDAM_TZ = "Europe/Amsterdam"
PAIRS = ("EURUSD", "GBPUSD")
PIP_SIZE = {"EURUSD": 0.0001, "GBPUSD": 0.0001}
ENTRY_VARIANTS = (
    "MKT_NEXT_OPEN",
    "LIMIT_ASIAN_BOUNDARY",
    "LIMIT_HALF_RETRACE",
)
EntryVariant = Literal[
    "MKT_NEXT_OPEN",
    "LIMIT_ASIAN_BOUNDARY",
    "LIMIT_HALF_RETRACE",
]
FROZEN_THRESHOLD = 0.18252984704127595
DISCOVERY_YEARS = tuple(range(2015, 2020))
BOOTSTRAP_SEED = 20260726
BOOTSTRAP_ITERATIONS = 10_000


def amsterdam_1000(trade_date: str) -> pd.Timestamp:
    return pd.Timestamp(f"{trade_date} 10:00:00", tz=AMSTERDAM_TZ).tz_convert("UTC")


def _parse_utc(frame: pd.DataFrame, column: str) -> pd.Series:
    values = frame[column] if column in frame else pd.Series(pd.NaT, index=frame.index)
    return pd.to_datetime(values, utc=True, errors="coerce")


def validate_predictions(predictions: pd.DataFrame, *, symbol: str) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "side",
        "prediction",
        "target",
    }
    missing = sorted(required - set(predictions.columns))
    if missing:
        raise ValueError(f"prediction ledger missing columns: {missing}")
    if predictions["event_id"].duplicated().any():
        raise ValueError("prediction event IDs must be unique")
    instruments = set(predictions["instrument"].astype(str).unique())
    if not instruments.issubset(set(PAIRS)) or symbol not in instruments:
        raise ValueError(f"unexpected prediction instruments: {sorted(instruments)}")
    if "landmark" in predictions and not predictions["landmark"].eq("T5").all():
        raise ValueError("execution discovery requires T5 predictions")
    if "family" in predictions and not predictions["family"].eq("hgb").all():
        raise ValueError("execution discovery requires the frozen HGB candidate")


def validate_event_ledger(events: pd.DataFrame, *, symbol: str) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "weekday",
        "side",
        "t5_timestamp_utc",
        "t5_available",
        "asian_high",
        "asian_low",
        "asian_midpoint",
        "asian_range_price",
        "sweep_extreme",
        "midpoint_success_09_10",
    }
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"event ledger missing columns: {missing}")
    if events["event_id"].duplicated().any():
        raise ValueError("event IDs must be unique within a pair ledger")
    if set(events["instrument"].astype(str).unique()) != {symbol}:
        raise ValueError("event ledger instrument mismatch")
    if not set(events["side"].astype(str).unique()).issubset({"UP", "DOWN"}):
        raise ValueError("unsupported sweep side")


def prepare_execution_events(
    events: pd.DataFrame,
    predictions: pd.DataFrame,
    *,
    symbol: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    symbol = symbol.upper()
    if symbol not in PAIRS:
        raise ValueError(f"unsupported symbol: {symbol}")
    if end_year < start_year:
        raise ValueError("end_year must be >= start_year")
    validate_event_ledger(events, symbol=symbol)
    validate_predictions(predictions, symbol=symbol)

    event_frame = events.copy()
    event_frame["t5_timestamp_utc"] = _parse_utc(event_frame, "t5_timestamp_utc")
    for column in (
        "midpoint_first_passage_utc",
        "barrier_first_passage_utc",
        "opposite_first_passage_utc",
    ):
        event_frame[column] = _parse_utc(event_frame, column)
    event_frame["year"] = pd.to_datetime(event_frame["trade_date"]).dt.year.astype(int)

    prediction_frame = predictions.loc[
        predictions["instrument"].astype(str).eq(symbol),
        ["event_id", "prediction", "target", "year"],
    ].copy()
    prediction_frame = prediction_frame.rename(
        columns={"target": "prediction_target", "year": "prediction_year"}
    )
    joined = event_frame.merge(
        prediction_frame,
        on="event_id",
        how="inner",
        validate="one_to_one",
    )
    if joined.empty:
        raise ValueError(f"no joined execution events for {symbol}")
    if not joined["prediction_year"].eq(joined["year"]).all():
        raise ValueError("prediction year does not match event trade date")
    target = joined["midpoint_success_09_10"].astype(int)
    if not joined["prediction_target"].astype(int).eq(target).all():
        raise ValueError("prediction targets do not match the event ledger")

    decision = joined["t5_timestamp_utc"]
    resolved = pd.Series(False, index=joined.index)
    for column in (
        "midpoint_first_passage_utc",
        "barrier_first_passage_utc",
        "opposite_first_passage_utc",
    ):
        passage = joined[column]
        resolved |= passage.notna() & decision.notna() & passage.le(decision)
    if resolved.any():
        raise ValueError("prediction ledger contains events already resolved by T5")

    eligible = joined.loc[
        joined["year"].between(start_year, end_year)
        & joined["t5_available"].astype(bool)
        & joined["t5_timestamp_utc"].notna()
        & joined["prediction"].ge(FROZEN_THRESHOLD)
    ].copy()
    eligible["first_actionable_timestamp_utc"] = eligible["t5_timestamp_utc"] + pd.Timedelta(
        minutes=1
    )
    eligible = eligible.loc[
        eligible.apply(
            lambda row: row["first_actionable_timestamp_utc"]
            < amsterdam_1000(str(row["trade_date"])),
            axis=1,
        )
    ]
    return eligible.sort_values(
        ["instrument", "trade_date", "t5_timestamp_utc", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)
