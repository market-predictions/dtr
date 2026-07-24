from __future__ import annotations

import argparse
import calendar
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_side(path: Path, year: int) -> tuple[pd.DataFrame, dict[str, object]]:
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"{path.name} missing columns: {sorted(missing)}")
    timestamps = pd.to_datetime(frame["timestamp"], unit="ms", utc=True, errors="raise")
    expected_rows = (366 if calendar.isleap(year) else 365) * 24 * 60
    expected_start = pd.Timestamp(f"{year}-01-01T00:00:00Z")
    expected_end = pd.Timestamp(f"{year}-12-31T23:59:00Z")
    valid_ohlc = (
        frame["high"] >= frame[["open", "close", "low"]].max(axis=1)
    ) & (frame["low"] <= frame[["open", "close", "high"]].min(axis=1))
    deltas = timestamps.diff().dropna().dt.total_seconds().to_numpy()
    audit = {
        "file": path.name,
        "sha256": sha256(path),
        "rows": int(len(frame)),
        "expected_rows": expected_rows,
        "start_utc": str(timestamps.min()),
        "end_utc": str(timestamps.max()),
        "duplicate_timestamps": int(timestamps.duplicated().sum()),
        "strictly_increasing": bool(timestamps.is_monotonic_increasing),
        "off_grid_intervals": int(np.sum(deltas != 60.0)),
        "ohlc_invalid_rows": int((~valid_ohlc).sum()),
        "positive_volume_rows": int((frame["volume"] > 0).sum()),
        "qualified": bool(
            len(frame) == expected_rows
            and timestamps.min() == expected_start
            and timestamps.max() == expected_end
            and not timestamps.duplicated().any()
            and timestamps.is_monotonic_increasing
            and np.all(deltas == 60.0)
            and valid_ohlc.all()
        ),
    }
    frame = frame.assign(timestamp=timestamps)
    return frame, audit


def inspect_year(data: Path, year: int) -> dict[str, object]:
    bid, bid_audit = inspect_side(data / f"gbpusd_m1_bid_{year}.csv.gz", year)
    ask, ask_audit = inspect_side(data / f"gbpusd_m1_ask_{year}.csv.gz", year)
    same_timestamps = bool(bid["timestamp"].equals(ask["timestamp"]))
    active = (bid["volume"] > 0) & (ask["volume"] > 0)
    open_spread = ask["open"] - bid["open"]
    close_spread = ask["close"] - bid["close"]
    nonnegative_spread = bool((open_spread >= 0).all() and (close_spread >= 0).all())
    qualified = bool(
        bid_audit["qualified"]
        and ask_audit["qualified"]
        and same_timestamps
        and nonnegative_spread
        and active.any()
    )
    return {
        "year": year,
        "bid": bid_audit,
        "ask": ask_audit,
        "bid_ask_timestamps_identical": same_timestamps,
        "active_bid_ask_rows": int(active.sum()),
        "negative_open_spread_rows": int((open_spread < 0).sum()),
        "negative_close_spread_rows": int((close_spread < 0).sum()),
        "median_active_open_spread_pips": float((open_spread.loc[active] / 0.0001).median()),
        "qualified": qualified,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    years = [inspect_year(args.data, year) for year in range(args.start_year, args.end_year + 1)]
    result = {
        "study_id": "DTR-FX-WP-20260724-23",
        "instrument": "GBPUSD",
        "provider": "Dukascopy",
        "price_sides": ["BID", "ASK"],
        "resolution": "M1",
        "period": [args.start_year, args.end_year],
        "purpose": "source qualification only; no strategy returns inspected",
        "canonical_bi5_mapping": ["seconds", "open", "close", "low", "high", "volume"],
        "years": years,
        "qualified": all(bool(item["qualified"]) for item in years),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not result["qualified"]:
        raise SystemExit("GBPUSD older-history source qualification failed")


if __name__ == "__main__":
    main()
