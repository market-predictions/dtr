from __future__ import annotations

import math

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.auction_state import build_auction_state_ledger
from dtr_lab.strategies.asia_sweep.fx_ten_pair import (
    CONTROL_COUNT,
    MATCH_BUCKET_MINUTES,
    PRIMARY_SESSION,
    PRIMARY_STATE,
    _standardized_distance,
    factor_block,
)


def _reversal_return_60m(
    indexed: pd.DataFrame,
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


def prepare_boundary_rows_fast(
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
    indexed = minutes.copy()
    indexed["timestamp"] = pd.to_datetime(indexed["timestamp"], utc=True)
    indexed = indexed.set_index("timestamp").sort_index()
    ledger["reversal_return_60m_range_fraction"] = [
        _reversal_return_60m(
            indexed,
            detection_time=pd.Timestamp(row.state_detection_timestamp),
            window_end=pd.Timestamp(row.window_end),
            first_side=str(row.first_side),
            reference_range=float(row.reference_range),
        )
        for row in ledger.itertuples(index=False)
    ]
    detection = pd.to_datetime(ledger["state_detection_timestamp"])
    ledger["year"] = detection.dt.year
    ledger["weekday"] = detection.dt.weekday
    minute_of_day = detection.dt.hour * 60 + detection.dt.minute
    ledger["time_bucket"] = (minute_of_day // MATCH_BUCKET_MINUTES).astype(int)
    ledger["factor_block"] = factor_block(symbol)
    ledger["is_primary_event"] = ledger["state"].eq(PRIMARY_STATE)
    return ledger


def match_controls_safe(
    rows: pd.DataFrame,
    *,
    controls_per_event: int = CONTROL_COUNT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_columns = [
        "event_id",
        "instrument",
        "factor_block",
        "trade_date",
        "year",
        "weekday",
        "time_bucket",
        "event_return",
        "control_mean_return",
        "effect",
        "reference_range",
        "range_percentile_60",
        "breach_depth_range_fraction",
        "external_confluence",
    ]
    control_columns = [
        "event_id",
        "control_rank",
        "control_event_id",
        "instrument",
        "trade_date",
        "control_return",
        "match_distance",
    ]
    if rows.empty:
        return pd.DataFrame(columns=event_columns), pd.DataFrame(columns=control_columns)
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
    return (
        pd.DataFrame(matched_events, columns=event_columns),
        pd.DataFrame(matched_controls, columns=control_columns),
    )
