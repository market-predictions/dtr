from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

CANONICAL_COLUMNS = (
    "timestamp_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "is_active_quote",
)


@dataclass(frozen=True)
class FXInstrument:
    symbol: str
    factor_block: str
    divisor: float
    pip_size: float


INSTRUMENTS = (
    FXInstrument("EURUSD", "usd_europe", 100_000.0, 0.0001),
    FXInstrument("GBPUSD", "usd_europe", 100_000.0, 0.0001),
    FXInstrument("USDCHF", "usd_europe", 100_000.0, 0.0001),
    FXInstrument("AUDUSD", "usd_commodity", 100_000.0, 0.0001),
    FXInstrument("NZDUSD", "usd_commodity", 100_000.0, 0.0001),
    FXInstrument("USDCAD", "usd_commodity", 100_000.0, 0.0001),
    FXInstrument("USDJPY", "jpy", 1_000.0, 0.01),
    FXInstrument("EURJPY", "jpy", 1_000.0, 0.01),
    FXInstrument("GBPJPY", "jpy", 1_000.0, 0.01),
    FXInstrument("EURGBP", "europe_cross", 100_000.0, 0.0001),
)
_INSTRUMENT_BY_SYMBOL = {item.symbol: item for item in INSTRUMENTS}


@dataclass(frozen=True)
class SourcePartition:
    label: str
    start_inclusive: dt.date
    end_exclusive: dt.date
    monitoring_only: bool = False


def instrument(symbol: str) -> FXInstrument:
    normalized = symbol.upper().strip()
    try:
        return _INSTRUMENT_BY_SYMBOL[normalized]
    except KeyError as error:
        raise ValueError(f"unsupported Stacey Burke FX symbol: {symbol}") from error


def price_divisor(symbol: str) -> float:
    return instrument(symbol).divisor


def pip_size(symbol: str) -> float:
    return instrument(symbol).pip_size


def annual_partitions(
    *,
    start_year: int,
    end_year: int,
    ytd_end_exclusive: dt.date | None = None,
) -> tuple[SourcePartition, ...]:
    if end_year < start_year:
        raise ValueError("end_year must be greater than or equal to start_year")
    partitions = [
        SourcePartition(
            label=str(year),
            start_inclusive=dt.date(year, 1, 1),
            end_exclusive=dt.date(year + 1, 1, 1),
        )
        for year in range(start_year, end_year + 1)
    ]
    if ytd_end_exclusive is not None:
        if ytd_end_exclusive <= dt.date(end_year + 1, 1, 1):
            raise ValueError("ytd_end_exclusive must fall after the final complete year")
        partitions.append(
            SourcePartition(
                label=f"{ytd_end_exclusive.year}_ytd",
                start_inclusive=dt.date(ytd_end_exclusive.year, 1, 1),
                end_exclusive=ytd_end_exclusive,
                monitoring_only=True,
            )
        )
    return tuple(partitions)


def source_filename(symbol: str, side: str, label: str) -> str:
    normalized_side = side.lower()
    if normalized_side not in {"bid", "ask"}:
        raise ValueError(f"unsupported side: {side}")
    return f"{symbol.lower()}_m1_{normalized_side}_{label}.csv.gz"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_side(path: Path, partition: SourcePartition) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(
        path,
        compression="gzip",
        dtype={"is_active_quote": "int8"},
    )
    missing = sorted(set(CANONICAL_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    frame = frame.loc[:, CANONICAL_COLUMNS].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if frame.empty:
        raise ValueError(f"{path.name}: empty source partition")
    duplicate_rows = int(frame["timestamp_utc"].duplicated().sum())
    monotonic = bool(frame["timestamp_utc"].is_monotonic_increasing)
    finite = bool(frame[["open", "high", "low", "close", "volume"]].notna().all().all())
    valid_ohlc = (
        (frame["high"] >= frame[["open", "close", "low"]].max(axis=1))
        & (frame["low"] <= frame[["open", "close", "high"]].min(axis=1))
        & (frame["low"] <= frame["high"])
        & (frame[["open", "high", "low", "close"]] > 0).all(axis=1)
        & (frame["volume"] >= 0)
    )
    active_expected = (frame["volume"] > 0).astype("int8")
    active_flag_mismatches = int((frame["is_active_quote"] != active_expected).sum())
    lower = pd.Timestamp(partition.start_inclusive, tz="UTC")
    upper = pd.Timestamp(partition.end_exclusive, tz="UTC")
    out_of_bounds = int(((frame["timestamp_utc"] < lower) | (frame["timestamp_utc"] >= upper)).sum())
    active = frame.loc[frame["is_active_quote"] == 1, "timestamp_utc"]
    audit: dict[str, Any] = {
        "file": path.name,
        "sha256": sha256_file(path),
        "rows": int(len(frame)),
        "active_rows": int((frame["is_active_quote"] == 1).sum()),
        "zero_volume_rows": int((frame["volume"] == 0).sum()),
        "duplicate_rows": duplicate_rows,
        "strictly_increasing": monotonic and duplicate_rows == 0,
        "finite_numeric_rows": finite,
        "invalid_ohlc_rows": int((~valid_ohlc).sum()),
        "active_flag_mismatches": active_flag_mismatches,
        "out_of_bounds_rows": out_of_bounds,
        "first_timestamp_utc": frame["timestamp_utc"].iloc[0].isoformat(),
        "last_timestamp_utc": frame["timestamp_utc"].iloc[-1].isoformat(),
        "active_months": int(active.dt.strftime("%Y-%m").nunique()) if not active.empty else 0,
    }
    audit["qualified"] = all(
        (
            audit["duplicate_rows"] == 0,
            audit["strictly_increasing"],
            audit["finite_numeric_rows"],
            audit["invalid_ohlc_rows"] == 0,
            audit["active_flag_mismatches"] == 0,
            audit["out_of_bounds_rows"] == 0,
            audit["active_rows"] > 0,
        )
    )
    return frame, audit


def _expected_active_months(partition: SourcePartition) -> int:
    final_observed_day = partition.end_exclusive - dt.timedelta(days=1)
    month_count = (final_observed_day.year - partition.start_inclusive.year) * 12
    month_count += final_observed_day.month - partition.start_inclusive.month + 1
    return max(1, month_count - 1)


def qualify_partition(
    *,
    directory: Path,
    item: FXInstrument,
    partition: SourcePartition,
) -> dict[str, Any]:
    bid_path = directory / source_filename(item.symbol, "bid", partition.label)
    ask_path = directory / source_filename(item.symbol, "ask", partition.label)
    bid, bid_audit = _load_side(bid_path, partition)
    ask, ask_audit = _load_side(ask_path, partition)

    merged = bid.merge(
        ask,
        on="timestamp_utc",
        how="inner",
        suffixes=("_bid", "_ask"),
        validate="one_to_one",
    )
    synchronized_rows = int(len(merged))
    synchronization_fraction = synchronized_rows / max(len(bid), len(ask))
    synchronized_active = merged.loc[
        (merged["is_active_quote_bid"] == 1) & (merged["is_active_quote_ask"] == 1)
    ].copy()
    synchronized_active_rows = int(len(synchronized_active))
    open_spread = synchronized_active["open_ask"] - synchronized_active["open_bid"]
    close_spread = synchronized_active["close_ask"] - synchronized_active["close_bid"]
    negative_open_spread_rows = int((open_spread < 0).sum())
    negative_close_spread_rows = int((close_spread < 0).sum())
    spread_pips = close_spread / item.pip_size

    minimum_active_rows = 25_000 if partition.monitoring_only else 100_000
    required_active_months = _expected_active_months(partition)
    gates = {
        "bid_side_qualified": bool(bid_audit["qualified"]),
        "ask_side_qualified": bool(ask_audit["qualified"]),
        "bid_ask_synchronization": synchronization_fraction >= 0.999,
        "active_coverage": synchronized_active_rows >= minimum_active_rows,
        "month_breadth": min(bid_audit["active_months"], ask_audit["active_months"])
        >= required_active_months,
        "non_negative_executable_spreads": negative_open_spread_rows == 0
        and negative_close_spread_rows == 0,
    }
    return {
        "symbol": item.symbol,
        "factor_block": item.factor_block,
        "partition": asdict(partition),
        "bid": bid_audit,
        "ask": ask_audit,
        "synchronized_rows": synchronized_rows,
        "bid_ask_synchronization_fraction": synchronization_fraction,
        "synchronized_active_rows": synchronized_active_rows,
        "minimum_required_active_rows": minimum_active_rows,
        "required_active_months": required_active_months,
        "negative_open_spread_rows": negative_open_spread_rows,
        "negative_close_spread_rows": negative_close_spread_rows,
        "median_close_spread_pips": float(spread_pips.median())
        if synchronized_active_rows
        else None,
        "q75_close_spread_pips": float(spread_pips.quantile(0.75))
        if synchronized_active_rows
        else None,
        "q95_close_spread_pips": float(spread_pips.quantile(0.95))
        if synchronized_active_rows
        else None,
        "gates": gates,
        "qualified": all(gates.values()),
        "performance_execution": False,
    }


def qualify_symbol_directory(
    *,
    directory: Path,
    symbol: str,
    start_year: int,
    end_year: int,
    ytd_end_exclusive: dt.date | None,
) -> dict[str, Any]:
    item = instrument(symbol)
    partitions = annual_partitions(
        start_year=start_year,
        end_year=end_year,
        ytd_end_exclusive=ytd_end_exclusive,
    )
    results = [
        qualify_partition(directory=directory, item=item, partition=partition)
        for partition in partitions
    ]
    return {
        "programme": "stacey_burke_fx_source_universe_v1",
        "symbol": item.symbol,
        "factor_block": item.factor_block,
        "partitions": results,
        "qualified": all(result["qualified"] for result in results),
        "performance_execution": False,
    }
