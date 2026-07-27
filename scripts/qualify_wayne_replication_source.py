from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = tuple(range(2015, 2022))
COLUMNS = (
    "timestamp_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "is_active_quote",
)
DTYPES = {
    "timestamp_utc": "string",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "float64",
    "is_active_quote": "int8",
}
OUTPUT_COLUMNS = (
    "instrument",
    "year",
    "coverage",
    "expected_open_minutes",
    "active_synchronized_minutes",
    "active_trading_days",
    "median_active_minutes_per_day",
    "p10_active_minutes_per_day",
    "max_gap_trading_minutes",
    "gaps_gt_1day",
    "gaps_gt_5days",
    "timestamp_alignment_share",
    "bid_duplicate_share",
    "ask_duplicate_share",
    "invalid_ohlc_share",
    "negative_spread_count",
    "ask_ge_bid_share",
    "median_spread",
    "p99_spread",
    "median_relative_spread",
    "bid_sha256",
    "ask_sha256",
    "q1_pass",
    "q2_pass",
    "q3_pass",
    "q4_pass",
    "q5_pass",
    "q6_pass",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Qualify one frozen independent FX source artifact."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _calendar(year: int) -> dict[str, np.ndarray | int]:
    index = pd.date_range(
        f"{year}-01-01",
        f"{year + 1}-01-01",
        inclusive="left",
        freq="min",
        tz="UTC",
    )
    new_york = index.tz_convert("America/New_York")
    day = new_york.dayofweek.to_numpy()
    minute = (new_york.hour * 60 + new_york.minute).to_numpy()
    expected = (
        (day <= 3)
        | ((day == 4) & (minute < 17 * 60))
        | ((day == 6) & (minute >= 17 * 60))
    )
    trading_date = (new_york + pd.Timedelta(hours=7)).date
    trading_code = pd.factorize(trading_date, sort=True)[0]
    month = np.asarray(
        [f"{value.year:04d}-{value.month:02d}" for value in trading_date],
        dtype="U7",
    )
    iso = np.asarray(index.strftime("%Y-%m-%dT%H:%M:%SZ"), dtype="U20")
    return {
        "expected": expected,
        "trading_code": trading_code,
        "month": month,
        "iso": iso,
        "rows": len(index),
    }


def _gap_runs(inactive: np.ndarray) -> np.ndarray:
    values = inactive.astype(np.int8)
    edges = np.diff(np.r_[0, values, 0])
    return np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, usecols=COLUMNS, dtype=DTYPES)


def _year_record(
    directory: Path,
    symbol: str,
    year: int,
    audit: dict,
    previous_last: str | None,
) -> tuple[dict, str, list[dict]]:
    lower = symbol.lower()
    calendar = _calendar(year)
    paths = {
        side: directory / f"{lower}_m1_{side}_{year}.csv.gz"
        for side in ("bid", "ask")
    }
    hashes = {side: _sha256(path) for side, path in paths.items()}
    bid = _read(paths["bid"])
    ask = _read(paths["ask"])
    bid_time = bid["timestamp_utc"].to_numpy(dtype="U20", na_value="")
    ask_time = ask["timestamp_utc"].to_numpy(dtype="U20", na_value="")
    exact_bid = len(bid_time) == calendar["rows"] and np.all(
        bid_time == calendar["iso"]
    )
    exact_ask = len(ask_time) == calendar["rows"] and np.all(
        ask_time == calendar["iso"]
    )
    alignment = float(np.mean(bid_time == ask_time)) if len(bid) == len(ask) else 0.0
    first = min(bid_time[0], ask_time[0])
    last = max(bid_time[-1], ask_time[-1])
    annual_overlap = previous_last is not None and first <= previous_last

    bid_ohlc = bid[["open", "high", "low", "close"]].to_numpy()
    ask_ohlc = ask[["open", "high", "low", "close"]].to_numpy()
    bid_invalid = (
        (~np.isfinite(bid_ohlc).all(axis=1))
        | (bid_ohlc <= 0).any(axis=1)
        | (bid_ohlc[:, 1] < np.maximum(bid_ohlc[:, 0], bid_ohlc[:, 3]))
        | (bid_ohlc[:, 2] > np.minimum(bid_ohlc[:, 0], bid_ohlc[:, 3]))
    )
    ask_invalid = (
        (~np.isfinite(ask_ohlc).all(axis=1))
        | (ask_ohlc <= 0).any(axis=1)
        | (ask_ohlc[:, 1] < np.maximum(ask_ohlc[:, 0], ask_ohlc[:, 3]))
        | (ask_ohlc[:, 2] > np.minimum(ask_ohlc[:, 0], ask_ohlc[:, 3]))
    )
    invalid = bid_invalid | ask_invalid
    active = bid["is_active_quote"].to_numpy() == 1
    active &= ask["is_active_quote"].to_numpy() == 1
    active &= ~invalid
    spread = ask_ohlc[:, 3] - bid_ohlc[:, 3]
    valid_active = active & (spread >= 0)
    midpoint = 0.5 * (ask_ohlc[:, 3] + bid_ohlc[:, 3])
    relative_spread = spread[valid_active] / midpoint[valid_active]

    expected = calendar["expected"]
    expected_active = active[expected]
    gap_runs = _gap_runs(~expected_active)
    trading_code = calendar["trading_code"][expected]
    counts = np.bincount(
        trading_code[expected_active],
        minlength=int(trading_code.max()) + 1,
    )
    counts = counts[counts > 0]
    monthly = []
    months = calendar["month"][expected]
    for month in np.unique(months):
        mask = months == month
        monthly.append(
            {
                "month": month,
                "coverage": float(np.mean(expected_active[mask])),
            }
        )

    bid_duplicate_share = float(
        2 * np.sum(bid_time[1:] == bid_time[:-1]) / max(len(bid_time), 1)
    )
    ask_duplicate_share = float(
        2 * np.sum(ask_time[1:] == ask_time[:-1]) / max(len(ask_time), 1)
    )
    record = {
        "instrument": symbol,
        "year": year,
        "coverage": float(np.mean(expected_active)),
        "expected_open_minutes": int(np.sum(expected)),
        "active_synchronized_minutes": int(np.sum(expected_active)),
        "active_trading_days": int(len(counts)),
        "median_active_minutes_per_day": float(np.median(counts)),
        "p10_active_minutes_per_day": float(np.quantile(counts, 0.10)),
        "max_gap_trading_minutes": int(gap_runs.max(initial=0)),
        "gaps_gt_1day": int(np.sum(gap_runs > 1440)),
        "gaps_gt_5days": int(np.sum(gap_runs > 7200)),
        "timestamp_alignment_share": alignment,
        "bid_duplicate_share": bid_duplicate_share,
        "ask_duplicate_share": ask_duplicate_share,
        "invalid_ohlc_share": float(np.mean(invalid)),
        "negative_spread_count": int(np.sum(spread < 0)),
        "ask_ge_bid_share": float(np.mean(spread >= 0)),
        "median_spread": float(np.median(spread[valid_active])),
        "p99_spread": float(np.quantile(spread[valid_active], 0.99)),
        "median_relative_spread": float(np.median(relative_spread)),
        "bid_sha256": hashes["bid"],
        "ask_sha256": hashes["ask"],
    }
    record["q1_pass"] = bool(
        paths["bid"].stat().st_size
        and paths["ask"].stat().st_size
        and hashes["bid"] == audit["sides"]["bid"]["sha256"]
        and hashes["ask"] == audit["sides"]["ask"]["sha256"]
        and exact_bid
        and exact_ask
    )
    record["q2_pass"] = bool(
        exact_bid
        and exact_ask
        and not annual_overlap
        and bid_duplicate_share <= 0.0005
        and ask_duplicate_share <= 0.0005
        and alignment >= 0.99
    )
    record["q3_pass"] = bool(
        record["invalid_ohlc_share"] <= 0.0001
        and record["ask_ge_bid_share"] >= 0.9999
    )
    record["q4_pass"] = bool(
        record["coverage"] >= 0.95
        and record["gaps_gt_5days"] == 0
        and record["gaps_gt_1day"] <= 3
    )
    record["q5_pass"] = bool(
        record["median_spread"] > 0
        and math.isfinite(record["p99_spread"])
        and record["median_relative_spread"] <= 0.0015
    )
    record["q6_pass"] = bool(
        record["active_trading_days"] >= 250
        and record["median_active_minutes_per_day"] >= 1200
        and record["p10_active_minutes_per_day"] >= 900
    )
    return record, last, monthly


def main() -> None:
    args = parse_args()
    symbol = args.symbol.upper()
    lower = symbol.lower()
    manifest = json.loads(
        (args.data / f"{lower}_source_manifest.json").read_text(encoding="utf-8")
    )
    audits = {
        int(item["partition"]["label"]): item
        for item in manifest["annual_audits"]
        if item["partition"]["label"].isdigit()
    }
    records = []
    monthly = []
    previous_last = None
    for year in YEARS:
        record, previous_last, months = _year_record(
            args.data,
            symbol,
            year,
            audits[year],
            previous_last,
        )
        records.append(record)
        monthly.extend(months)
    seven_year_spread = float(np.median([r["median_relative_spread"] for r in records]))
    for record in records:
        record["q5_pass"] = bool(
            record["q5_pass"]
            and record["median_relative_spread"] <= 3 * seven_year_spread
        )
    median_monthly = float(np.median([item["coverage"] for item in monthly]))
    collapsed = [item["coverage"] < 0.8 * median_monthly for item in monthly]
    persistent_collapse = any(
        collapsed[index] and collapsed[index + 1]
        for index in range(len(collapsed) - 1)
    )
    if persistent_collapse:
        for record in records:
            record["q6_pass"] = False
    frame = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    passed = bool(frame[[f"q{i}_pass" for i in range(1, 7)]].all().all())
    args.out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out / "wayne_replication_source_quality.csv", index=False)
    summary = {
        "instrument": symbol,
        "years": list(YEARS),
        "included": passed,
        "seven_year_median_relative_spread": seven_year_spread,
        "seven_year_median_monthly_coverage": median_monthly,
        "persistent_two_month_collapse": persistent_collapse,
        "gates": {
            f"q{i}_pass": bool(frame[f"q{i}_pass"].all()) for i in range(1, 7)
        },
    }
    (args.out / "wayne_replication_source_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
