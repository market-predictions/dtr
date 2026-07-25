from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.auction_state import build_auction_state_ledger

PAIR_SPECS = {
    "EURUSD": ("usd_europe", 0.0001),
    "GBPUSD": ("usd_europe", 0.0001),
    "USDCHF": ("usd_europe", 0.0001),
    "AUDUSD": ("usd_commodity", 0.0001),
    "NZDUSD": ("usd_commodity", 0.0001),
    "USDCAD": ("usd_commodity", 0.0001),
    "USDJPY": ("jpy", 0.01),
    "EURJPY": ("jpy", 0.01),
    "GBPJPY": ("jpy", 0.01),
    "EURGBP": ("europe_cross", 0.0001),
}
CONTROL_COUNT = 5
PRIMARY_SESSION = "LONDON"
PRIMARY_STATE = "REJECTION"
MATCH_BUCKET_MINUTES = 30


@dataclass(frozen=True)
class StudyPartition:
    label: str
    start_year: int
    end_year: int


DISCOVERY = StudyPartition("discovery_2015_2019", 2015, 2019)
MECHANISM_VALIDATION = StudyPartition("mechanism_validation_2020_2021", 2020, 2021)


def factor_block(symbol: str) -> str:
    try:
        return PAIR_SPECS[symbol.upper()][0]
    except KeyError as exc:
        raise ValueError(f"unsupported FX pair: {symbol}") from exc


def pip_size(symbol: str) -> float:
    try:
        return PAIR_SPECS[symbol.upper()][1]
    except KeyError as exc:
        raise ValueError(f"unsupported FX pair: {symbol}") from exc


def _source_file(directory: Path, symbol: str, side: str, year: int) -> Path:
    return directory / f"{symbol.lower()}_m1_{side}_{year}.csv.gz"


def _load_side(path: Path, side: str) -> pd.DataFrame:
    required = {
        "timestamp_utc",
        "open",
        "high",
        "low",
        "close",
        "is_active_quote",
    }
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path, compression="gzip")
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
    frame = frame.loc[:, sorted(required)].copy()
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"], utc=True, errors="raise"
    )
    for column in ("open", "high", "low", "close", "is_active_quote"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError(f"{path.name}: duplicate timestamps")
    suffix = f"_{side}"
    return frame.rename(
        columns={
            column: f"{column}{suffix}"
            for column in required
            if column != "timestamp_utc"
        }
    )


def load_midpoint_minutes(
    directory: Path,
    symbol: str,
    *,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    if end_year < start_year:
        raise ValueError("end_year must be >= start_year")
    frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        bid = _load_side(_source_file(directory, symbol, "bid", year), "bid")
        ask = _load_side(_source_file(directory, symbol, "ask", year), "ask")
        merged = bid.merge(ask, on="timestamp_utc", how="inner", validate="one_to_one")
        active = (
            (merged["is_active_quote_bid"] == 1)
            & (merged["is_active_quote_ask"] == 1)
        ).astype("int8")
        midpoint = pd.DataFrame(
            {
                "timestamp": merged["timestamp_utc"],
                "open": (merged["open_bid"] + merged["open_ask"]) / 2.0,
                "high": (merged["high_bid"] + merged["high_ask"]) / 2.0,
                "low": (merged["low_bid"] + merged["low_ask"]) / 2.0,
                "close": (merged["close_bid"] + merged["close_ask"]) / 2.0,
                "is_active_quote": active,
            }
        )
        frames.append(midpoint)
    out = pd.concat(frames, ignore_index=True)
    if out["timestamp"].duplicated().any():
        raise ValueError(f"{symbol}: duplicate timestamps across partitions")
    return out.sort_values("timestamp").reset_index(drop=True)


def _reversal_return_60m(
    minutes: pd.DataFrame,
    *,
    detection_time: pd.Timestamp,
    window_end: pd.Timestamp,
    first_side: str,
    reference_range: float,
) -> float:
    if (
        first_side not in {"UP", "DOWN"}
        or not np.isfinite(reference_range)
        or reference_range <= 0
    ):
        return math.nan
    indexed = minutes.set_index("timestamp")
    anchor_rows = indexed.loc[
        (indexed.index >= detection_time)
        & (indexed.index < window_end)
        & (indexed["is_active_quote"] > 0)
    ].head(1)
    if anchor_rows.empty:
        return math.nan
    anchor_time = pd.Timestamp(anchor_rows.index[0])
    endpoint_limit = min(anchor_time + pd.Timedelta(minutes=60), window_end)
    path = indexed.loc[
        (indexed.index >= anchor_time)
        & (indexed.index < endpoint_limit)
        & (indexed["is_active_quote"] > 0)
    ]
    if path.empty or pd.Timestamp(path.index[-1]) < endpoint_limit - pd.Timedelta(
        minutes=2
    ):
        return math.nan
    anchor = float(anchor_rows.iloc[0]["open"])
    endpoint = float(path.iloc[-1]["close"])
    direction = -1.0 if first_side == "UP" else 1.0
    return direction * (endpoint - anchor) / reference_range


def prepare_boundary_rows(
    symbol: str,
    minutes: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    start = pd.Timestamp(f"{start_year}-01-01", tz="America/New_York")
    end = pd.Timestamp(f"{end_year + 1}-01-01", tz="America/New_York")
    ledger = build_auction_state_ledger(
        symbol,
        minutes,
        development_start=start,
        development_end=end,
    )
    if ledger.empty:
        return ledger
    ledger = ledger.loc[
        (ledger["session"] == PRIMARY_SESSION)
        & ledger["first_side"].isin(["UP", "DOWN"])
    ].copy()
    minutes_indexed = minutes.copy()
    minutes_indexed["timestamp"] = pd.to_datetime(
        minutes_indexed["timestamp"], utc=True
    )
    values = []
    for row in ledger.itertuples(index=False):
        values.append(
            _reversal_return_60m(
                minutes_indexed,
                detection_time=pd.Timestamp(row.state_detection_timestamp),
                window_end=pd.Timestamp(row.window_end),
                first_side=str(row.first_side),
                reference_range=float(row.reference_range),
            )
        )
    ledger["reversal_return_60m_range_fraction"] = values
    detection = pd.to_datetime(ledger["state_detection_timestamp"])
    ledger["year"] = detection.dt.year
    ledger["weekday"] = detection.dt.weekday
    minute_of_day = detection.dt.hour * 60 + detection.dt.minute
    ledger["time_bucket"] = (minute_of_day // MATCH_BUCKET_MINUTES).astype(int)
    ledger["factor_block"] = factor_block(symbol)
    ledger["is_primary_event"] = ledger["state"].eq(PRIMARY_STATE)
    return ledger


def _standardized_distance(candidates: pd.DataFrame, event: pd.Series) -> pd.Series:
    columns = ("range_percentile_60", "breach_depth_range_fraction")
    total = pd.Series(0.0, index=candidates.index)
    for column in columns:
        sample = pd.to_numeric(candidates[column], errors="coerce")
        center = float(sample.median())
        scale = float((sample - center).abs().median())
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = 1.0
        event_value = float(event[column])
        total = total + (sample - event_value).abs() / scale
    return total


def match_controls(
    rows: pd.DataFrame,
    *,
    controls_per_event: int = CONTROL_COUNT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    eligible = rows.loc[
        rows["reversal_return_60m_range_fraction"].notna()
        & rows["state"].isin(["REJECTION", "ACCEPTANCE", "UNRESOLVED"])
    ].copy()
    events = eligible.loc[eligible["is_primary_event"]].copy()
    controls = eligible.loc[~eligible["is_primary_event"]].copy()
    matched_events: list[dict[str, object]] = []
    matched_controls: list[dict[str, object]] = []
    for _, event in events.sort_values("event_id").iterrows():
        candidates = controls.loc[
            (controls["instrument"] == event["instrument"])
            & (controls["year"] == event["year"])
            & (controls["weekday"] == event["weekday"])
            & (controls["time_bucket"] == event["time_bucket"])
            & (controls["trade_date"] != event["trade_date"])
        ].copy()
        candidates = candidates.dropna(
            subset=["range_percentile_60", "breach_depth_range_fraction"]
        )
        if candidates["trade_date"].nunique() < controls_per_event:
            continue
        candidates["match_distance"] = _standardized_distance(candidates, event)
        candidates = candidates.sort_values(
            ["match_distance", "trade_date", "event_id"]
        ).drop_duplicates("trade_date")
        selected = candidates.head(controls_per_event)
        if len(selected) != controls_per_event:
            continue
        control_mean = float(selected["reversal_return_60m_range_fraction"].mean())
        effect = float(event["reversal_return_60m_range_fraction"]) - control_mean
        matched_events.append(
            {
                "event_id": event["event_id"],
                "instrument": event["instrument"],
                "factor_block": event["factor_block"],
                "trade_date": event["trade_date"],
                "year": int(event["year"]),
                "weekday": int(event["weekday"]),
                "time_bucket": int(event["time_bucket"]),
                "event_return": float(
                    event["reversal_return_60m_range_fraction"]
                ),
                "control_mean_return": control_mean,
                "effect": effect,
                "reference_range": float(event["reference_range"]),
                "range_percentile_60": float(event["range_percentile_60"]),
                "breach_depth_range_fraction": float(
                    event["breach_depth_range_fraction"]
                ),
                "external_confluence": bool(event["external_confluence"]),
            }
        )
        for rank, (_, control) in enumerate(selected.iterrows(), start=1):
            matched_controls.append(
                {
                    "event_id": event["event_id"],
                    "control_rank": rank,
                    "control_event_id": control["event_id"],
                    "instrument": control["instrument"],
                    "trade_date": control["trade_date"],
                    "control_return": float(
                        control["reversal_return_60m_range_fraction"]
                    ),
                    "match_distance": float(control["match_distance"]),
                }
            )
    return pd.DataFrame(matched_events), pd.DataFrame(matched_controls)


def summarize_pair(
    symbol: str,
    boundary_rows: pd.DataFrame,
    matched_events: pd.DataFrame,
    matched_controls: pd.DataFrame,
) -> dict[str, object]:
    return {
        "programme": "ASIAN_SWEEP_FX_TEN_PAIR_V1",
        "symbol": symbol,
        "factor_block": factor_block(symbol),
        "boundary_rows": int(len(boundary_rows)),
        "rejection_events": int(boundary_rows["is_primary_event"].sum())
        if not boundary_rows.empty
        else 0,
        "matched_events": int(len(matched_events)),
        "matched_controls": int(len(matched_controls)),
        "mean_event_return": float(matched_events["event_return"].mean())
        if not matched_events.empty
        else None,
        "mean_control_return": float(matched_events["control_mean_return"].mean())
        if not matched_events.empty
        else None,
        "mean_effect": float(matched_events["effect"].mean())
        if not matched_events.empty
        else None,
        "positive_effect": bool(matched_events["effect"].mean() > 0)
        if not matched_events.empty
        else False,
        "controls_per_event": CONTROL_COUNT,
        "performance_execution": False,
    }


def write_pair_outputs(
    output: Path,
    *,
    symbol: str,
    boundary_rows: pd.DataFrame,
    matched_events: pd.DataFrame,
    matched_controls: pd.DataFrame,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    boundary_rows.to_csv(output / "boundary_rows.csv", index=False)
    matched_events.to_csv(output / "matched_events.csv", index=False)
    matched_controls.to_csv(output / "matched_controls.csv", index=False)
    summary = summarize_pair(symbol, boundary_rows, matched_events, matched_controls)
    (output / "pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary
