from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

from .shadow_common import SESSION_TIMEZONE, VARIANTS


def load_source_window(
    source_zip: Path,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    with ZipFile(source_zip) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError("source ZIP must contain exactly one CSV")
        chunks: list[pd.DataFrame] = []
        with archive.open(members[0]) as handle:
            for chunk in pd.read_csv(
                handle,
                usecols=[
                    "timestamp UTC",
                    "open",
                    "high",
                    "low",
                    "close",
                    "is_active_quote",
                ],
                chunksize=250_000,
            ):
                timestamps = pd.to_datetime(
                    chunk.pop("timestamp UTC"),
                    utc=True,
                    errors="raise",
                )
                chunk["timestamp"] = timestamps.dt.tz_convert(SESSION_TIMEZONE)
                keep = (chunk["timestamp"] >= start) & (chunk["timestamp"] <= end)
                if bool(keep.any()):
                    chunks.append(chunk.loc[keep].copy())
    if not chunks:
        raise ValueError("source ZIP contains no rows in the baseline period")
    frame = pd.concat(chunks, ignore_index=True)
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    if bool(frame["timestamp"].duplicated(keep=False).any()):
        raise ValueError("baseline source has duplicate timestamps")
    return frame


def max_drawdown_r(values: pd.Series) -> float:
    cumulative = values.astype(float).reset_index(drop=True).cumsum()
    equity = pd.concat([pd.Series([0.0]), cumulative], ignore_index=True)
    drawdown = equity - equity.cummax()
    return float(-drawdown.min())


def summarize_trades(frame: pd.DataFrame) -> dict[str, object]:
    signal_count = int(len(frame))
    status_counts = frame["status"].value_counts(dropna=False).to_dict()
    exited = frame[frame["status"] == "EXITED"].copy()
    blocked = int(status_counts.get("BLOCKED", 0))
    unresolved = int(status_counts.get("UNRESOLVED", 0))
    if exited.empty:
        return {
            "signals": signal_count,
            "exited": 0,
            "blocked": blocked,
            "unresolved": unresolved,
            "net_r": None,
            "expectancy_r": None,
            "gross_expectancy_r": None,
            "win_rate": None,
            "profit_factor": None,
            "max_drawdown_r": None,
            "return_dd": None,
        }
    exited["entry_sort"] = pd.to_datetime(exited["entry_timestamp"], utc=True)
    exited = exited.sort_values(["entry_sort", "instrument", "execution_window"])
    net_r = pd.to_numeric(exited["net_r"], errors="raise")
    gross_r = pd.to_numeric(exited["gross_r"], errors="raise")
    positive = float(net_r[net_r > 0].sum())
    negative = float(-net_r[net_r < 0].sum())
    drawdown = max_drawdown_r(net_r)
    reason = exited["reason"].astype(str)
    return {
        "signals": signal_count,
        "exited": int(len(exited)),
        "blocked": blocked,
        "unresolved": unresolved,
        "net_r": float(net_r.sum()),
        "expectancy_r": float(net_r.mean()),
        "gross_expectancy_r": float(gross_r.mean()),
        "win_rate": float((net_r > 0).mean()),
        "profit_factor": positive / negative if negative > 0 else None,
        "max_drawdown_r": drawdown,
        "return_dd": float(net_r.sum() / drawdown) if drawdown > 0 else None,
        "target_rate": float(reason.isin(["TARGET", "TARGET_GAP"]).mean()),
        "stop_rate": float(reason.isin(["STOP", "STOP_GAP"]).mean()),
        "time_exit_rate": float((reason == "TIME_EXIT").mean()),
        "average_holding_minutes": float(
            pd.to_numeric(exited["holding_minutes"]).mean()
        ),
    }


def instrument_breakdowns(trades: pd.DataFrame) -> dict[str, object]:
    output: dict[str, object] = {"variants": {}}
    for variant in VARIANTS:
        subset = trades[trades["variant"] == variant].copy()
        period_rows: dict[str, object] = {}
        if not subset.empty:
            entry = pd.to_datetime(
                subset.get("entry_timestamp"),
                utc=True,
                errors="coerce",
            )
            subset["period"] = np.where(entry.dt.year == 2023, "2023", "2024_H1")
            for period, group in subset.groupby("period"):
                period_rows[str(period)] = summarize_trades(group)
        output["variants"][variant] = {
            "overall": summarize_trades(subset),
            "periods": period_rows,
            "windows": {
                str(key): summarize_trades(group)
                for key, group in subset.groupby("execution_window")
            },
            "directions": {
                str(int(key)): summarize_trades(group)
                for key, group in subset.groupby("direction")
            },
        }
    return output


def classify_variant(
    nq: dict[str, object],
    es: dict[str, object],
    pooled: dict[str, object],
    pooled_periods: dict[str, dict[str, object]],
) -> str:
    if any(value.get("expectancy_r") is None for value in (nq, es, pooled)):
        return "INVALID_BASELINE"
    signals = int(nq["signals"]) + int(es["signals"])
    blocked_unresolved = (
        int(nq["blocked"])
        + int(nq["unresolved"])
        + int(es["blocked"])
        + int(es["unresolved"])
    )
    if signals == 0 or blocked_unresolved / signals > 0.02:
        return "INVALID_BASELINE"
    pooled_expectancy = float(pooled["expectancy_r"])
    if pooled_expectancy <= 0:
        return "NOT_PROMISING_CURRENT_SPEC"
    profitability = (
        float(nq["expectancy_r"]) > 0
        and float(es["expectancy_r"]) > 0
        and pooled_expectancy >= 0.05
        and pooled.get("profit_factor") is not None
        and float(pooled["profit_factor"]) >= 1.10
        and all(
            period in pooled_periods
            and pooled_periods[period].get("net_r") is not None
            and float(pooled_periods[period]["net_r"]) > 0
            for period in ("2023", "2024_H1")
        )
    )
    if profitability and int(nq["exited"]) >= 50 and int(es["exited"]) >= 50:
        total_net = float(nq["net_r"]) + float(es["net_r"])
        concentration = max(float(nq["net_r"]), float(es["net_r"])) / total_net
        if total_net > 0 and concentration <= 0.75:
            return "PROMISING_DEVELOPMENT_SCREEN"
    if profitability:
        return "PROMISING_BUT_INSUFFICIENT_SAMPLE"
    return "MIXED_NOT_PROMOTABLE"
