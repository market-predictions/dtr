from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

AMSTERDAM_TZ = "Europe/Amsterdam"
LANDMARKS = ("T0", "T1", "T2", "T3", "LEGACY_T5")
PRE_T5_LANDMARKS = ("T0", "T1", "T2", "T3")
POSITION_STRUCTURES = (
    "TP1_50_RUNNER_50",
    "TP1_25_RUNNER_75",
    "NO_TP1_FULL_RUNNER",
)
ADVERSE_BARRIER_FRACTION = 0.20
STRESS_PIPS = 0.10

DERIVED_COLUMNS = (
    "landmark",
    "landmark_timestamp_utc",
    "entry_timestamp_utc",
    "landmark_elapsed_minutes",
    "landmark_bar_count",
    "entry_delay_minutes",
    "target",
    "entry_price",
    "stop_price",
    "risk_price",
    "reward_price",
    "reward_risk",
    "reward_risk_stress_010",
    "spread_pips",
    "spread_risk_fraction",
    "closes_outside",
    "closes_inside",
    "reclaim",
    "reclaim_delay_bars",
    "reclaim_depth_range_fraction",
    "landmark_return_range_fraction",
    "landmark_mfe_range_fraction",
    "landmark_mae_range_fraction",
    "extreme_extension_range_fraction",
    "retest_touch",
    "retest_hold",
    "reversal_swing_break",
    "current_close_from_boundary_range",
    "levels_consumed_through_landmark",
    "remaining_levels_beyond_landmark",
    "residual_density_landmark",
    "other_pair_known",
    "other_pair_same_side",
    "other_pair_reclaim",
    "other_pair_return_range_fraction",
)


def _parse_events(events: pd.DataFrame) -> pd.DataFrame:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "side",
        "sweep_timestamp_utc",
        "t5_timestamp_utc",
        "midpoint_first_passage_utc",
        "barrier_first_passage_utc",
        "two_sided_ambiguous",
        "asian_high",
        "asian_low",
        "asian_midpoint",
        "asian_range_price",
        "sweep_extreme",
    }
    frame = events.copy()
    if "year" not in frame:
        frame["year"] = pd.to_datetime(frame["trade_date"], errors="raise").dt.year
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing early-entry event columns: {missing}")
    for column in (
        "sweep_timestamp_utc",
        "t5_timestamp_utc",
        "midpoint_first_passage_utc",
        "barrier_first_passage_utc",
    ):
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="raise").dt.date.astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    return frame


def _midpoint_bars(bars: pd.DataFrame) -> pd.DataFrame:
    active = bars.loc[bars["active"].astype(bool)].copy()
    for column in ("open", "high", "low", "close"):
        active[column] = 0.5 * (
            active[f"{column}_bid"].astype(float)
            + active[f"{column}_ask"].astype(float)
        )
    return active


def _landmark_times(event: pd.Series, bars: pd.DataFrame) -> dict[str, pd.Timestamp]:
    sweep = pd.Timestamp(event["sweep_timestamp_utc"])
    if sweep not in bars.index:
        return {}
    following = bars.loc[bars.index > sweep].head(5)
    result: dict[str, pd.Timestamp] = {"T0": sweep}
    for offset in (1, 2, 3):
        if len(following) >= offset:
            result[f"T{offset}"] = pd.Timestamp(following.index[offset - 1])
    legacy = event.get("t5_timestamp_utc")
    if pd.notna(legacy):
        legacy_time = pd.Timestamp(legacy)
        if legacy_time in bars.index:
            result["LEGACY_T5"] = legacy_time
    return result


def _next_active_bar(bars: pd.DataFrame, landmark: pd.Timestamp) -> pd.DataFrame:
    return bars.loc[bars.index > landmark].head(1)


def _before_1000(timestamp: pd.Timestamp) -> bool:
    local = timestamp.tz_convert(AMSTERDAM_TZ)
    return (local.hour, local.minute) < (10, 0)


def _path_features(
    path: pd.DataFrame,
    event: pd.Series,
    levels: pd.DataFrame,
) -> dict[str, Any]:
    side = str(event["side"])
    boundary = float(event["asian_high"] if side == "UP" else event["asian_low"])
    asian_range = float(event["asian_range_price"])
    sweep_extreme = float(event["sweep_extreme"])
    final_close = float(path.iloc[-1]["close"])
    anchor = float(path.iloc[0]["open"])
    outside = path["close"] > boundary if side == "UP" else path["close"] < boundary
    inside = ~outside
    reclaim_positions = np.flatnonzero(inside.to_numpy())
    reclaim = len(reclaim_positions) > 0

    if side == "UP":
        signed_return = (anchor - final_close) / asian_range
        mfe = (anchor - float(path["low"].min())) / asian_range
        mae = (float(path["high"].max()) - anchor) / asian_range
        extension = (float(path["high"].max()) - sweep_extreme) / asian_range
        retest_touch = bool((path["high"] >= boundary).any()) if reclaim else False
        retest_hold = bool(final_close < boundary) if retest_touch else False
        prior_swing = float(path.iloc[:-1]["low"].min()) if len(path) > 1 else math.nan
        swing_break = bool(final_close < prior_swing) if np.isfinite(prior_swing) else False
        reclaim_depth = (boundary - final_close) / asian_range
        same = levels.loc[levels["level_side"].eq("HIGH")]
        current_extreme = float(path["high"].max())
        consumed = int((same["level_price"] <= current_extreme).sum())
        remaining = same.loc[same["level_price"] > current_extreme]
        distances = (remaining["level_price"] - current_extreme) / asian_range
    else:
        signed_return = (final_close - anchor) / asian_range
        mfe = (float(path["high"].max()) - anchor) / asian_range
        mae = (anchor - float(path["low"].min())) / asian_range
        extension = (sweep_extreme - float(path["low"].min())) / asian_range
        retest_touch = bool((path["low"] <= boundary).any()) if reclaim else False
        retest_hold = bool(final_close > boundary) if retest_touch else False
        prior_swing = float(path.iloc[:-1]["high"].max()) if len(path) > 1 else math.nan
        swing_break = bool(final_close > prior_swing) if np.isfinite(prior_swing) else False
        reclaim_depth = (final_close - boundary) / asian_range
        same = levels.loc[levels["level_side"].eq("LOW")]
        current_extreme = float(path["low"].min())
        consumed = int((same["level_price"] >= current_extreme).sum())
        remaining = same.loc[same["level_price"] < current_extreme]
        distances = (current_extreme - remaining["level_price"]) / asian_range

    residual_density = float(
        np.exp(-np.clip(distances.to_numpy(dtype=float), 0.0, None) / 0.5).sum()
    ) if len(remaining) else 0.0
    return {
        "closes_outside": int(outside.sum()),
        "closes_inside": int(inside.sum()),
        "reclaim": float(reclaim),
        "reclaim_delay_bars": float(reclaim_positions[0] + 1) if reclaim else math.nan,
        "reclaim_depth_range_fraction": float(reclaim_depth),
        "landmark_return_range_fraction": float(signed_return),
        "landmark_mfe_range_fraction": float(mfe),
        "landmark_mae_range_fraction": float(mae),
        "extreme_extension_range_fraction": float(extension),
        "retest_touch": float(retest_touch),
        "retest_hold": float(retest_hold),
        "reversal_swing_break": float(swing_break),
        "current_close_from_boundary_range": float(reclaim_depth),
        "levels_consumed_through_landmark": consumed,
        "remaining_levels_beyond_landmark": int(len(remaining)),
        "residual_density_landmark": residual_density,
    }


def _geometry(
    event: pd.Series,
    entry_bar: pd.Series,
) -> dict[str, float] | None:
    is_long = str(event["side"]) == "DOWN"
    entry = float(entry_bar["open_ask" if is_long else "open_bid"])
    asian_range = float(event["asian_range_price"])
    sweep_extreme = float(event["sweep_extreme"])
    stop = (
        sweep_extreme - ADVERSE_BARRIER_FRACTION * asian_range
        if is_long
        else sweep_extreme + ADVERSE_BARRIER_FRACTION * asian_range
    )
    midpoint = float(event["asian_midpoint"])
    risk = entry - stop if is_long else stop - entry
    reward = midpoint - entry if is_long else entry - midpoint
    if risk <= 0 or reward <= 0:
        return None
    pip = PIP_SIZE[str(event["instrument"])]
    slippage = STRESS_PIPS * pip
    stressed_entry = entry + slippage if is_long else entry - slippage
    stressed_stop = stop - slippage if is_long else stop + slippage
    stressed_risk = (
        stressed_entry - stressed_stop if is_long else stressed_stop - stressed_entry
    )
    stressed_reward = (
        midpoint - stressed_entry if is_long else stressed_entry - midpoint
    )
    spread = float(entry_bar["open_ask"] - entry_bar["open_bid"])
    return {
        "entry_price": entry,
        "stop_price": stop,
        "risk_price": risk,
        "reward_price": reward,
        "reward_risk": reward / risk,
        "reward_risk_stress_010": (
            stressed_reward / stressed_risk
            if stressed_risk > 0 and stressed_reward > 0
            else math.nan
        ),
        "spread_pips": spread / pip,
        "spread_risk_fraction": spread / risk,
    }


def build_pair_landmark_ledger(
    events: pd.DataFrame,
    levels: pd.DataFrame,
    source_directory: Path,
    *,
    symbol: str,
    start_year: int = 2015,
    end_year: int = 2019,
) -> pd.DataFrame:
    frame = _parse_events(events)
    symbol = symbol.upper()
    frame = frame.loc[
        frame["instrument"].eq(symbol)
        & frame["year"].between(start_year, end_year)
    ].copy()
    if frame.empty:
        raise ValueError(f"{symbol}: no early-entry events in requested partition")
    level_map = {
        event_id: group.loc[:, ["level_side", "level_price"]].copy()
        for event_id, group in levels.loc[levels["event_id"].isin(frame["event_id"])].groupby(
            "event_id", sort=False
        )
    }
    rows: list[dict[str, Any]] = []
    for year, year_events in frame.groupby("year", sort=True):
        bars = _midpoint_bars(load_bid_ask_minutes(source_directory, symbol, int(year)))
        for _, event in year_events.sort_values(
            ["sweep_timestamp_utc", "event_id"], kind="mergesort"
        ).iterrows():
            if bool(event["two_sided_ambiguous"]):
                continue
            midpoint_time = event["midpoint_first_passage_utc"]
            barrier_time = event["barrier_first_passage_utc"]
            if pd.notna(midpoint_time) and pd.notna(barrier_time) and midpoint_time == barrier_time:
                continue
            event_levels = level_map.get(
                str(event["event_id"]),
                pd.DataFrame(columns=["level_side", "level_price"]),
            )
            sweep_time = pd.Timestamp(event["sweep_timestamp_utc"])
            for landmark, landmark_time in _landmark_times(event, bars).items():
                if pd.notna(midpoint_time) and midpoint_time <= landmark_time:
                    continue
                if pd.notna(barrier_time) and barrier_time <= landmark_time:
                    continue
                if not _before_1000(landmark_time):
                    continue
                next_bar = _next_active_bar(bars, landmark_time)
                if next_bar.empty:
                    continue
                entry_time = pd.Timestamp(next_bar.index[0])
                if not _before_1000(entry_time):
                    continue
                geometry = _geometry(event, next_bar.iloc[0])
                if geometry is None:
                    continue
                target = bool(
                    pd.notna(midpoint_time)
                    and midpoint_time > landmark_time
                    and (pd.isna(barrier_time) or midpoint_time < barrier_time)
                    and _before_1000(pd.Timestamp(midpoint_time))
                )
                path = bars.loc[(bars.index >= sweep_time) & (bars.index <= landmark_time)]
                if path.empty:
                    continue
                record = event.to_dict()
                record.update(_path_features(path, event, event_levels))
                record.update(geometry)
                record.update(
                    {
                        "landmark": landmark,
                        "landmark_timestamp_utc": landmark_time.isoformat(),
                        "entry_timestamp_utc": entry_time.isoformat(),
                        "landmark_elapsed_minutes": (
                            landmark_time - sweep_time
                        ).total_seconds() / 60.0,
                        "landmark_bar_count": int(len(path)),
                        "entry_delay_minutes": (
                            entry_time - landmark_time
                        ).total_seconds() / 60.0,
                        "target": int(target),
                    }
                )
                rows.append(record)
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError(f"{symbol}: early-entry ledger is empty")
    duplicates = result.duplicated(["event_id", "landmark"])
    if duplicates.any():
        raise ValueError(f"{symbol}: duplicate event-landmark rows")
    return result.sort_values(
        ["landmark", "landmark_timestamp_utc", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def add_cross_pair_landmark_features(ledger: pd.DataFrame) -> pd.DataFrame:
    result = ledger.copy()
    result["landmark_timestamp_utc"] = pd.to_datetime(
        result["landmark_timestamp_utc"], utc=True, errors="raise"
    )
    for column in (
        "other_pair_known",
        "other_pair_same_side",
        "other_pair_reclaim",
        "other_pair_return_range_fraction",
    ):
        result[column] = 0.0 if column == "other_pair_known" else math.nan
    for _, indices in result.groupby("trade_date", sort=False).groups.items():
        day = result.loc[list(indices)].sort_values(
            ["landmark_timestamp_utc", "landmark_bar_count", "event_id"],
            kind="mergesort",
        )
        for index, row in day.iterrows():
            other = day.loc[
                day["instrument"].ne(row["instrument"])
                & day["landmark_timestamp_utc"].le(row["landmark_timestamp_utc"])
            ]
            if other.empty:
                continue
            latest = other.iloc[-1]
            result.at[index, "other_pair_known"] = 1.0
            result.at[index, "other_pair_same_side"] = float(
                latest["side"] == row["side"]
            )
            result.at[index, "other_pair_reclaim"] = float(latest["reclaim"])
            result.at[index, "other_pair_return_range_fraction"] = float(
                latest["landmark_return_range_fraction"]
            )
    return result.sort_values(
        ["landmark", "landmark_timestamp_utc", "instrument", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)
