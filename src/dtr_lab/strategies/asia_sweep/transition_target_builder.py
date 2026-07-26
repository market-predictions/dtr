from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes
from dtr_lab.strategies.asia_sweep.extended_reversal_targets import (
    LANDMARKS,
    TARGET_ORDER,
    _label_target,
    _targets,
)


def build_partition_extended_target_ledger(
    landmark_ledger: pd.DataFrame,
    levels: pd.DataFrame,
    source_directory: Path,
    *,
    symbol: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Rebuild the frozen extended targets for an explicit year partition.

    The original 2015-2019 builder remains untouched. This wrapper reuses its exact
    target and first-passage functions while making the validation partition explicit.
    """
    if start_year > end_year:
        raise ValueError("start_year must not exceed end_year")
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
        raise ValueError(f"missing transition-target ledger columns: {missing}")
    source = landmark_ledger.loc[
        landmark_ledger["instrument"].eq(symbol)
        & landmark_ledger["landmark"].isin(LANDMARKS)
        & landmark_ledger["year"].between(start_year, end_year)
    ].copy()
    if source.empty:
        raise ValueError(
            f"{symbol}: no landmarks in validation partition {start_year}-{end_year}"
        )
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
        raise ValueError(f"{symbol}: transition-target ledger is empty")
    years = tuple(sorted(pd.to_numeric(result["year"]).astype(int).unique()))
    expected = tuple(range(start_year, end_year + 1))
    if years != expected:
        raise ValueError(f"{symbol}: expected years {expected}, found {years}")
    if result.duplicated(["event_id", "landmark", "extended_target"]).any():
        raise ValueError(f"{symbol}: duplicate transition target keys")
    return result.sort_values(
        ["extended_target", "landmark", "entry_timestamp_utc", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)
