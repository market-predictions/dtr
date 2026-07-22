from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .engine import metrics


@dataclass(frozen=True)
class TimestampConclusion:
    decision: str
    best_price_basis: str
    best_rmse: float
    equivalent_best_hypotheses: int
    explanation: str

    def as_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "best_price_basis": self.best_price_basis,
            "best_rmse": self.best_rmse,
            "equivalent_best_hypotheses": self.equivalent_best_hypotheses,
            "explanation": self.explanation,
        }


def timestamp_vwap_hypotheses(one_minute: pd.DataFrame) -> tuple[pd.DataFrame, TimestampConclusion]:
    required = {"timestamp", "open", "high", "low", "close", "volume", "Vwap_ETH"}
    missing = required.difference(one_minute.columns)
    if missing:
        raise ValueError(f"Missing timestamp/VWAP columns: {sorted(missing)}")
    vendor = one_minute["Vwap_ETH"].astype(float)
    prices = {
        "close": one_minute["close"].astype(float),
        "hl2": (one_minute["high"] + one_minute["low"]) / 2.0,
        "hlc3": (one_minute["high"] + one_minute["low"] + one_minute["close"]) / 3.0,
        "ohlc4": (
            one_minute["open"]
            + one_minute["high"]
            + one_minute["low"]
            + one_minute["close"]
        )
        / 4.0,
    }
    rows: list[dict[str, object]] = []
    for label_semantics, shift_minutes in (("bar_open", 0), ("bar_close", -1)):
        interval_open = pd.to_datetime(one_minute["timestamp"]) + pd.Timedelta(
            minutes=shift_minutes
        )
        for reset_minute in (18 * 60, 18 * 60 + 1):
            trade_date = (interval_open - pd.Timedelta(minutes=reset_minute)).dt.normalize()
            denominator = one_minute["volume"].groupby(trade_date).cumsum()
            for price_name, price in prices.items():
                calculated = (price * one_minute["volume"]).groupby(trade_date).cumsum() / denominator
                error = calculated - vendor
                rows.append(
                    {
                        "label_semantics": label_semantics,
                        "interval_open_shift_minutes": shift_minutes,
                        "reset_interval_open": f"{reset_minute // 60:02d}:{reset_minute % 60:02d}",
                        "price_basis": price_name,
                        "mae": float(error.abs().mean()),
                        "rmse": float(np.sqrt(np.mean(np.square(error)))),
                        "median_abs": float(error.abs().median()),
                        "p95_abs": float(error.abs().quantile(0.95)),
                        "correlation": float(calculated.corr(vendor)),
                    }
                )
    result = pd.DataFrame(rows).sort_values(["rmse", "mae"]).reset_index(drop=True)
    best = result.iloc[0]
    equivalent = result[
        np.isclose(result["rmse"], float(best["rmse"]), rtol=0.0, atol=1e-12)
        & np.isclose(result["mae"], float(best["mae"]), rtol=0.0, atol=1e-12)
    ]
    conclusion = TimestampConclusion(
        decision="UNRESOLVED",
        best_price_basis=str(best["price_basis"]),
        best_rmse=float(best["rmse"]),
        equivalent_best_hypotheses=int(len(equivalent)),
        explanation=(
            "Vendor ETH VWAP is reproduced by cumulative HLC3 times volume, but the "
            "absence of 18:00 observations makes bar-open and bar-close label hypotheses "
            "observationally equivalent under plausible reset alignment."
        ),
    )
    return result, conclusion


def quarterly_roll_candidates(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for year in range(start.year, end.year + 1):
        for month in (3, 6, 9, 12):
            fridays = pd.date_range(
                pd.Timestamp(year=year, month=month, day=1),
                pd.Timestamp(year=year, month=month, day=28),
                freq="W-FRI",
            )
            if len(fridays) < 3:
                continue
            expiry = fridays[2]
            calendar_roll = expiry - pd.Timedelta(days=8)
            if start.normalize() <= calendar_roll <= end.normalize():
                rows.append(
                    {
                        "contract_month": f"{year}-{month:02d}",
                        "third_friday": expiry,
                        "calendar_roll_candidate": calendar_roll,
                    }
                )
    return pd.DataFrame(rows)


def attach_roll_market_dates(
    candidates: pd.DataFrame, market_dates: Iterable[pd.Timestamp]
) -> pd.DataFrame:
    dates = pd.DatetimeIndex(pd.to_datetime(list(market_dates))).normalize().unique().sort_values()
    rows: list[dict[str, object]] = []
    for row in candidates.itertuples(index=False):
        candidate = pd.Timestamp(row.calendar_roll_candidate).normalize()
        position = int(dates.searchsorted(candidate))
        choices = []
        if position < len(dates):
            choices.append(dates[position])
        if position > 0:
            choices.append(dates[position - 1])
        nearest = min(choices, key=lambda value: abs(value - candidate))
        rows.append({**row._asdict(), "nearest_market_date": nearest})
    return pd.DataFrame(rows)


def roll_adjacent_dates(
    roll_candidates: pd.DataFrame,
    market_dates: Iterable[pd.Timestamp],
    *,
    window_sessions: int,
) -> set[pd.Timestamp]:
    dates = pd.DatetimeIndex(pd.to_datetime(list(market_dates))).normalize().unique().sort_values()
    excluded: set[pd.Timestamp] = set()
    for roll_date in pd.to_datetime(roll_candidates["nearest_market_date"]):
        position = int(dates.searchsorted(roll_date))
        if position >= len(dates) or dates[position] != roll_date:
            continue
        lo = max(0, position - window_sessions)
        hi = min(len(dates), position + window_sessions + 1)
        excluded.update(pd.Timestamp(value) for value in dates[lo:hi])
    return excluded


def rollover_stress(
    trades: pd.DataFrame,
    roll_candidates: pd.DataFrame,
    market_dates: Iterable[pd.Timestamp],
    windows: Iterable[int] = (0, 1, 3),
) -> pd.DataFrame:
    work = trades.copy()
    work["session_date"] = pd.to_datetime(work["session_date"]).dt.normalize()
    baseline = metrics(work)
    rows = [
        {
            "window_sessions": -1,
            "excluded_dates": 0,
            "excluded_trades": 0,
            "excluded_net_r": 0.0,
            **baseline,
        }
    ]
    for window in windows:
        excluded_dates = roll_adjacent_dates(
            roll_candidates, market_dates, window_sessions=int(window)
        )
        mask = work["session_date"].isin(excluded_dates)
        kept = work.loc[~mask]
        removed = work.loc[mask]
        rows.append(
            {
                "window_sessions": int(window),
                "excluded_dates": len(excluded_dates),
                "excluded_trades": int(mask.sum()),
                "excluded_net_r": float(removed["pnl_r"].sum()),
                **metrics(kept),
            }
        )
    return pd.DataFrame(rows)


def session_weekday_attribution(trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    total_net = float(trades["pnl_r"].sum()) if not trades.empty else 0.0
    for (session, weekday), subset in trades.groupby(["session", "day_of_week"], sort=True):
        row = {
            "session": session,
            "day_of_week": int(weekday),
            **metrics(subset),
        }
        row["share_of_total_net"] = (
            float(row["net_r"]) / total_net if total_net != 0 else np.nan
        )
        rows.append(row)
    return pd.DataFrame(rows)


def compare_trade_sets(reference: pd.DataFrame, candidate: pd.DataFrame) -> dict[str, object]:
    key = ["session", "session_date", "direction", "entry_time"]
    left = reference.copy()
    right = candidate.copy()
    for frame in (left, right):
        frame["_trade_key"] = frame[key].astype(str).agg("|".join, axis=1)
    left_keys = set(left["_trade_key"])
    right_keys = set(right["_trade_key"])
    common = sorted(left_keys & right_keys)
    removed = left_keys - right_keys
    added = right_keys - left_keys
    left_common = left.set_index("_trade_key").loc[common]
    right_common = right.set_index("_trade_key").loc[common]
    changed = np.abs(
        left_common["pnl_r"].to_numpy(float) - right_common["pnl_r"].to_numpy(float)
    ) > 1e-12
    return {
        "removed": len(removed),
        "added": len(added),
        "changed_common": int(changed.sum()),
        "removed_net_r": float(left[left["_trade_key"].isin(removed)]["pnl_r"].sum()),
        "added_net_r": float(right[right["_trade_key"].isin(added)]["pnl_r"].sum()),
        "changed_common_delta_net_r": float(
            (
                right_common.loc[changed, "pnl_r"].to_numpy(float)
                - left_common.loc[changed, "pnl_r"].to_numpy(float)
            ).sum()
        ),
    }


def leave_one_group_out(
    trades: pd.DataFrame, group_columns: list[str] | tuple[str, ...]
) -> pd.DataFrame:
    """Measure portfolio dependence on each mutually exclusive group."""
    if trades.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    grouper: str | list[str] = (
        group_columns[0] if len(group_columns) == 1 else list(group_columns)
    )
    for key, removed in trades.groupby(grouper, sort=True):
        values = (key,) if len(group_columns) == 1 else tuple(key)
        mask = pd.Series(True, index=trades.index)
        row: dict[str, object] = {}
        for column, value in zip(group_columns, values, strict=True):
            mask &= trades[column] == value
            row[f"excluded_{column}"] = int(value) if isinstance(value, (int, np.integer)) else value
        kept = trades.loc[~mask]
        row.update(
            {
                "removed_trades": int(len(removed)),
                "removed_net_r": float(removed["pnl_r"].sum()),
                **metrics(kept),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("removed_net_r", ascending=False).reset_index(drop=True)


def rollover_discontinuity_diagnostics(
    one_minute: pd.DataFrame, roll_candidates: pd.DataFrame
) -> pd.DataFrame:
    """Describe observable price/volume discontinuities near calendar roll candidates."""
    work = one_minute.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"])
    work["market_date"] = work["timestamp"].dt.normalize()
    daily = (
        work.groupby("market_date", sort=True)
        .agg(
            first_timestamp=("timestamp", "first"),
            last_timestamp=("timestamp", "last"),
            first_open=("open", "first"),
            last_close=("close", "last"),
            volume=("volume", "sum"),
        )
        .reset_index()
    )
    daily["previous_close"] = daily["last_close"].shift(1)
    daily["previous_volume"] = daily["volume"].shift(1)
    daily["open_gap_points"] = daily["first_open"] - daily["previous_close"]
    daily["open_gap_abs_points"] = daily["open_gap_points"].abs()
    daily["volume_ratio_previous"] = daily["volume"] / daily["previous_volume"].replace(0, np.nan)
    candidates = set(pd.to_datetime(roll_candidates["nearest_market_date"]).dt.normalize())
    selected = daily[daily["market_date"].isin(candidates)].copy()
    selected["open_gap_abs_percentile_all_dates"] = [
        float((daily["open_gap_abs_points"] <= value).mean())
        for value in selected["open_gap_abs_points"]
    ]
    return selected.reset_index(drop=True)


def rollover_trade_attribution(
    trades: pd.DataFrame, roll_candidates: pd.DataFrame
) -> pd.DataFrame:
    """Attribute trades executed on each candidate roll market date."""
    work = trades.copy()
    work["session_date"] = pd.to_datetime(work["session_date"]).dt.normalize()
    rows: list[dict[str, object]] = []
    for row in roll_candidates.itertuples(index=False):
        date = pd.Timestamp(row.nearest_market_date).normalize()
        subset = work[work["session_date"] == date]
        rows.append(
            {
                "contract_month": row.contract_month,
                "calendar_roll_candidate": pd.Timestamp(row.calendar_roll_candidate),
                "nearest_market_date": date,
                **metrics(subset),
            }
        )
    return pd.DataFrame(rows)
