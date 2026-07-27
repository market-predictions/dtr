from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PRIMARY_PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "USDCAD", "USDCHF", "USDJPY")
REPLICATION_PAIRS = ("EURGBP", "EURJPY", "GBPJPY", "NZDUSD")
SUPPORTED_PAIRS = tuple(sorted((*PRIMARY_PAIRS, *REPLICATION_PAIRS)))
_REQUIRED_COLUMNS = {
    "timestamp_utc",
    "open",
    "high",
    "low",
    "close",
    "is_active_quote",
}


def _source_file(directory: Path, symbol: str, side: str, year: int) -> Path:
    return directory / f"{symbol.lower()}_m1_{side}_{year}.csv.gz"


def _load_side(path: Path, side: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(
        path,
        compression="gzip",
        usecols=sorted(_REQUIRED_COLUMNS),
    )
    missing = sorted(_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"],
        utc=True,
        errors="raise",
    )
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError(f"{path.name}: duplicate timestamps")
    if not frame["timestamp_utc"].is_monotonic_increasing:
        raise ValueError(f"{path.name}: timestamps are not sorted")
    for column in _REQUIRED_COLUMNS - {"timestamp_utc"}:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    renamed = {
        column: f"{column}_{side}"
        for column in _REQUIRED_COLUMNS
        if column != "timestamp_utc"
    }
    return frame.rename(columns=renamed)


def load_bid_ask_minutes(
    directory: Path,
    symbol: str,
    *,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    symbol = symbol.upper()
    if symbol not in SUPPORTED_PAIRS:
        raise ValueError(f"unsupported Wayne pair: {symbol}")
    if end_year < start_year:
        raise ValueError("end_year must not precede start_year")

    frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        bid = _load_side(_source_file(directory, symbol, "bid", year), "bid")
        ask = _load_side(_source_file(directory, symbol, "ask", year), "ask")
        merged = bid.merge(
            ask,
            on="timestamp_utc",
            how="inner",
            validate="one_to_one",
        )
        if len(merged) != len(bid) or len(merged) != len(ask):
            raise ValueError(f"{symbol} {year}: BID/ASK timestamp mismatch")
        frames.append(merged)

    result = pd.concat(frames, ignore_index=True).sort_values("timestamp_utc")
    if result["timestamp_utc"].duplicated().any():
        raise ValueError(f"{symbol}: duplicate timestamps across annual partitions")
    return result.set_index("timestamp_utc")


def midpoint_minutes(quotes: pd.DataFrame) -> pd.DataFrame:
    required = {
        "open_bid",
        "high_bid",
        "low_bid",
        "close_bid",
        "open_ask",
        "high_ask",
        "low_ask",
        "close_ask",
        "is_active_quote_bid",
        "is_active_quote_ask",
    }
    missing = sorted(required - set(quotes.columns))
    if missing:
        raise ValueError(f"quote frame missing columns: {missing}")
    if not isinstance(quotes.index, pd.DatetimeIndex) or quotes.index.tz is None:
        raise ValueError("quote frame must use a timezone-aware DatetimeIndex")

    out = pd.DataFrame(index=quotes.index)
    for column in ("open", "high", "low", "close"):
        out[column] = 0.5 * (
            quotes[f"{column}_bid"].astype(float)
            + quotes[f"{column}_ask"].astype(float)
        )
    out["active"] = (
        quotes["is_active_quote_bid"].eq(1)
        & quotes["is_active_quote_ask"].eq(1)
    )
    out["spread_close"] = quotes["close_ask"] - quotes["close_bid"]
    active_spread = out.loc[out["active"], "spread_close"]
    if not np.isfinite(active_spread).all() or active_spread.lt(0.0).any():
        raise ValueError("active quotes contain invalid close spreads")
    return out.sort_index()
