from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

PIP_SIZE = 0.0001
PIP_FACTOR = 1.0 / PIP_SIZE
ROUND_STEP_PIPS = 50
LQP_STEP_PIPS = 250
PRIMARY_RESET_PIPS = 25
HORIZONS_MINUTES = (5, 15, 30, 60, 120, 240, 1440)


@dataclass(frozen=True)
class YearData:
    year: int
    timestamp_ms: np.ndarray
    timestamp: pd.DatetimeIndex
    mid_open: np.ndarray
    mid_high: np.ndarray
    mid_low: np.ndarray
    mid_close: np.ndarray
    spread_close_pips: np.ndarray
    active: np.ndarray


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _load_side(path: Path, prefix: str) -> pd.DataFrame:
    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    frame = pd.read_csv(
        path,
        usecols=cols,
        dtype={
            "timestamp": "int64",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        },
    )
    return frame.rename(columns={c: f"{prefix}_{c}" for c in cols if c != "timestamp"})


def load_year(data_dir: Path, year: int) -> YearData:
    bid_path = data_dir / f"gbpusd_m1_bid_{year}.csv.gz"
    ask_path = data_dir / f"gbpusd_m1_ask_{year}.csv.gz"
    bid = _load_side(bid_path, "bid")
    ask = _load_side(ask_path, "ask")
    if len(bid) != len(ask):
        raise ValueError(f"Bid/ask row-count mismatch for {year}: {len(bid)} vs {len(ask)}")
    if not np.array_equal(bid["timestamp"].to_numpy(), ask["timestamp"].to_numpy()):
        raise ValueError(f"Bid/ask timestamp mismatch for {year}")
    frame = bid.join(ask.drop(columns=["timestamp"]))
    timestamps_ms = frame["timestamp"].to_numpy(dtype=np.int64)
    timestamps = pd.to_datetime(timestamps_ms, unit="ms", utc=True)
    active = ((frame["bid_volume"] > 0.0) & (frame["ask_volume"] > 0.0)).to_numpy(
        dtype=bool
    )
    return YearData(
        year=year,
        timestamp_ms=timestamps_ms,
        timestamp=timestamps,
        mid_open=((frame["bid_open"] + frame["ask_open"]) / 2.0).to_numpy(),
        mid_high=((frame["bid_high"] + frame["ask_high"]) / 2.0).to_numpy(),
        mid_low=((frame["bid_low"] + frame["ask_low"]) / 2.0).to_numpy(),
        mid_close=((frame["bid_close"] + frame["ask_close"]) / 2.0).to_numpy(),
        spread_close_pips=((frame["ask_close"] - frame["bid_close"]) * PIP_FACTOR).to_numpy(),
        active=active,
    )


def audit_year(data_dir: Path, year: int) -> dict:
    audit_path = data_dir / f"gbpusd_m1_{year}_audit.json"
    expected = json.loads(audit_path.read_text(encoding="utf-8"))
    year_data = load_year(data_dir, year)
    deltas = np.diff(year_data.timestamp_ms) / 60000.0
    active_spread = year_data.spread_close_pips[year_data.active]
    result = {
        "year": year,
        "rows": int(len(year_data.timestamp_ms)),
        "expected_rows_bid": int(expected["sides"]["bid"]["rows"]),
        "expected_rows_ask": int(expected["sides"]["ask"]["rows"]),
        "duplicate_timestamps": int(pd.Index(year_data.timestamp_ms).duplicated().sum()),
        "nonpositive_deltas": int((deltas <= 0).sum()),
        "median_delta_minutes": float(np.median(deltas)),
        "active_rows": int(year_data.active.sum()),
        "inactive_rows": int((~year_data.active).sum()),
        "negative_spread_rows": int((active_spread < 0).sum()),
        "median_spread_pips": float(np.median(active_spread)),
        "p95_spread_pips": float(np.quantile(active_spread, 0.95)),
        "start_utc": year_data.timestamp[0].isoformat(),
        "end_utc": year_data.timestamp[-1].isoformat(),
        "bid_sha256_ok": sha256_file(data_dir / expected["sides"]["bid"]["file"])
        == expected["sides"]["bid"]["sha256"],
        "ask_sha256_ok": sha256_file(data_dir / expected["sides"]["ask"]["file"])
        == expected["sides"]["ask"]["sha256"],
    }
    if (
        result["rows"] != result["expected_rows_bid"]
        or result["rows"] != result["expected_rows_ask"]
    ):
        raise ValueError(f"Audit row-count failure for {year}")
    if (
        result["duplicate_timestamps"]
        or result["nonpositive_deltas"]
        or result["negative_spread_rows"]
    ):
        raise ValueError(f"Audit integrity failure for {year}: {result}")
    if not result["bid_sha256_ok"] or not result["ask_sha256_ok"]:
        raise ValueError(f"Checksum failure for {year}")
    return result


def candidate_levels(close: np.ndarray) -> np.ndarray:
    finite_close = close[np.isfinite(close)]
    low_pips = int(
        np.floor(finite_close.min() * PIP_FACTOR / ROUND_STEP_PIPS) * ROUND_STEP_PIPS
    )
    high_pips = int(
        np.ceil(finite_close.max() * PIP_FACTOR / ROUND_STEP_PIPS) * ROUND_STEP_PIPS
    )
    return np.arange(
        low_pips,
        high_pips + ROUND_STEP_PIPS,
        ROUND_STEP_PIPS,
        dtype=np.int64,
    )


def _accepted_crossings(
    close_pips: np.ndarray,
    active: np.ndarray,
    level_pips: int,
    direction: int,
    reset_pips: int,
) -> list[int]:
    previous = close_pips[:-1]
    current = close_pips[1:]
    valid_pair = active[:-1] & active[1:]
    if direction == 1:
        raw = np.flatnonzero(
            valid_pair & (previous < level_pips) & (current >= level_pips)
        ) + 1
        reset_idx = np.flatnonzero(active & (close_pips <= level_pips - reset_pips))
    elif direction == -1:
        raw = np.flatnonzero(
            valid_pair & (previous > level_pips) & (current <= level_pips)
        ) + 1
        reset_idx = np.flatnonzero(active & (close_pips >= level_pips + reset_pips))
    else:
        raise ValueError("direction must be +1 or -1")

    accepted: list[int] = []
    last_accepted = -1
    for index in raw:
        reset_position = np.searchsorted(reset_idx, index, side="left") - 1
        if reset_position >= 0 and int(reset_idx[reset_position]) > last_accepted:
            accepted.append(int(index))
            last_accepted = int(index)
    return accepted


def _first_passage_symmetric(
    high: np.ndarray,
    low: np.ndarray,
    entry: float,
    direction: int,
    threshold_pips: float,
) -> str:
    upper = entry + threshold_pips * PIP_SIZE
    lower = entry - threshold_pips * PIP_SIZE
    if direction == 1:
        favorable = np.flatnonzero(high >= upper)
        adverse = np.flatnonzero(low <= lower)
    else:
        favorable = np.flatnonzero(low <= lower)
        adverse = np.flatnonzero(high >= upper)
    favorable_index = int(favorable[0]) if len(favorable) else None
    adverse_index = int(adverse[0]) if len(adverse) else None
    if favorable_index is None and adverse_index is None:
        return "timeout"
    if favorable_index is not None and (
        adverse_index is None or favorable_index < adverse_index
    ):
        return "follow_through"
    if adverse_index is not None and (
        favorable_index is None or adverse_index < favorable_index
    ):
        return "reversal"
    return "ambiguous_same_minute"


def detect_events(
    year_data: YearData,
    reset_pips: int = PRIMARY_RESET_PIPS,
    horizons: Iterable[int] = HORIZONS_MINUTES,
    min_active_ratio: float = 0.80,
) -> pd.DataFrame:
    horizons = tuple(sorted(set(int(horizon) for horizon in horizons)))
    max_horizon = max(horizons)
    close_pips = year_data.mid_close * PIP_FACTOR
    levels = candidate_levels(year_data.mid_close[year_data.active])
    records: list[dict] = []

    for level_pips in levels:
        level = level_pips * PIP_SIZE
        roundness_class = "whole_100" if level_pips % 100 == 0 else "half_100"
        phase_250 = int(level_pips % LQP_STEP_PIPS)
        is_lqp = phase_250 == 0
        for direction in (1, -1):
            accepted = _accepted_crossings(
                close_pips,
                year_data.active,
                int(level_pips),
                direction,
                reset_pips,
            )
            for index in accepted:
                if index + max_horizon >= len(year_data.mid_close) or index < 240:
                    continue
                entry = float(year_data.mid_close[index])
                record = {
                    "year": year_data.year,
                    "timestamp": year_data.timestamp[index],
                    "timestamp_ms": int(year_data.timestamp_ms[index]),
                    "week": year_data.timestamp[index].strftime("%G-W%V"),
                    "month": int(year_data.timestamp[index].month),
                    "hour_utc": int(year_data.timestamp[index].hour),
                    "session_4h": int(year_data.timestamp[index].hour // 4),
                    "level": level,
                    "level_pips": int(level_pips),
                    "phase_250": phase_250,
                    "is_lqp": bool(is_lqp),
                    "roundness_class": roundness_class,
                    "direction": int(direction),
                    "entry_mid": entry,
                    "entry_overshoot_pips": float(
                        direction * (entry - level) * PIP_FACTOR
                    ),
                    "spread_pips": float(year_data.spread_close_pips[index]),
                    "pre_return_60_pips": float(
                        direction
                        * (entry - year_data.mid_close[index - 60])
                        * PIP_FACTOR
                    ),
                    "pre_range_240_pips": float(
                        (
                            year_data.mid_high[index - 240 : index].max()
                            - year_data.mid_low[index - 240 : index].min()
                        )
                        * PIP_FACTOR
                    ),
                }
                for horizon in horizons:
                    active_ratio = float(
                        year_data.active[index + 1 : index + horizon + 1].mean()
                    )
                    record[f"active_ratio_{horizon}m"] = active_ratio
                    if active_ratio < min_active_ratio:
                        record[f"return_{horizon}m_pips"] = np.nan
                        record[f"mfe_{horizon}m_pips"] = np.nan
                        record[f"mae_{horizon}m_pips"] = np.nan
                        continue
                    future_close = float(year_data.mid_close[index + horizon])
                    window_high = year_data.mid_high[index + 1 : index + horizon + 1]
                    window_low = year_data.mid_low[index + 1 : index + horizon + 1]
                    record[f"return_{horizon}m_pips"] = float(
                        direction * (future_close - entry) * PIP_FACTOR
                    )
                    if direction == 1:
                        record[f"mfe_{horizon}m_pips"] = float(
                            (window_high.max() - entry) * PIP_FACTOR
                        )
                        record[f"mae_{horizon}m_pips"] = float(
                            (window_low.min() - entry) * PIP_FACTOR
                        )
                    else:
                        record[f"mfe_{horizon}m_pips"] = float(
                            (entry - window_low.min()) * PIP_FACTOR
                        )
                        record[f"mae_{horizon}m_pips"] = float(
                            (entry - window_high.max()) * PIP_FACTOR
                        )
                if record.get("active_ratio_60m", 0.0) >= min_active_ratio:
                    record["fp_10p_60m"] = _first_passage_symmetric(
                        year_data.mid_high[index + 1 : index + 61],
                        year_data.mid_low[index + 1 : index + 61],
                        entry,
                        direction,
                        10.0,
                    )
                else:
                    record["fp_10p_60m"] = "invalid_inactive"
                records.append(record)

    events = pd.DataFrame.from_records(records)
    if events.empty:
        return events
    events = events.sort_values(["timestamp_ms", "level_pips", "direction"]).reset_index(
        drop=True
    )
    events.insert(
        0,
        "event_id",
        [f"GBPUSD-{year_data.year}-{i:06d}" for i in range(1, len(events) + 1)],
    )
    return events


def stratified_phase_effect(
    events: pd.DataFrame,
    outcome: str,
    phase: int,
    years: Iterable[int] | None = None,
) -> dict:
    frame = events.copy()
    if years is not None:
        frame = frame[frame["year"].isin(list(years))]
    frame = frame[np.isfinite(frame[outcome])].copy()
    frame["treated"] = frame["phase_250"].eq(phase)
    strata_cols = ["year", "direction", "roundness_class", "session_4h"]
    pieces: list[tuple] = []
    matched_treated = 0
    matched_control = 0
    for key, group in frame.groupby(strata_cols, observed=True):
        treated = group.loc[group["treated"], outcome]
        control = group.loc[~group["treated"], outcome]
        if len(treated) == 0 or len(control) == 0:
            continue
        weight = len(treated) * len(control) / (len(treated) + len(control))
        pieces.append(
            (weight, float(treated.mean() - control.mean()), len(treated), len(control), key)
        )
        matched_treated += len(treated)
        matched_control += len(control)
    if not pieces:
        return {
            "phase": phase,
            "outcome": outcome,
            "effect": np.nan,
            "n_treated": 0,
            "n_control": 0,
            "n_strata": 0,
        }
    total_weight = sum(piece[0] for piece in pieces)
    effect = sum(piece[0] * piece[1] for piece in pieces) / total_weight
    return {
        "phase": int(phase),
        "outcome": outcome,
        "effect": float(effect),
        "n_treated": int(matched_treated),
        "n_control": int(matched_control),
        "n_strata": int(len(pieces)),
    }


def bootstrap_phase_effect(
    events: pd.DataFrame,
    outcome: str,
    phase: int,
    years: Iterable[int],
    n_boot: int = 1000,
    seed: int = 260805,
) -> dict:
    frame = events[
        events["year"].isin(list(years)) & np.isfinite(events[outcome])
    ].copy()
    point = stratified_phase_effect(frame, outcome, phase)["effect"]
    if frame.empty or not np.isfinite(point):
        return {
            "phase": phase,
            "outcome": outcome,
            "point": point,
            "ci_low": np.nan,
            "ci_high": np.nan,
            "n_boot": 0,
        }

    week_key = frame["year"].astype(str) + "|" + frame["week"].astype(str)
    week_codes, week_uniques = pd.factorize(week_key, sort=True)
    week_year = np.array(
        [int(str(week).split("|", 1)[0]) for week in week_uniques], dtype=int
    )
    stratum_index = pd.MultiIndex.from_frame(
        frame[["year", "direction", "roundness_class", "session_4h"]]
    )
    stratum_codes, stratum_uniques = pd.factorize(stratum_index, sort=True)
    treated = frame["phase_250"].eq(phase).to_numpy(dtype=bool)
    outcome_values = frame[outcome].to_numpy(dtype=float)
    number_of_weeks = len(week_uniques)
    number_of_strata = len(stratum_uniques)
    random = np.random.default_rng(seed + phase)
    values = np.empty(n_boot, dtype=float)
    kept = 0
    year_week_ids = {
        year: np.flatnonzero(week_year == year) for year in np.unique(week_year)
    }

    for _ in range(n_boot):
        week_weights = np.zeros(number_of_weeks, dtype=float)
        for ids in year_week_ids.values():
            sampled = random.choice(ids, size=len(ids), replace=True)
            week_weights += np.bincount(sampled, minlength=number_of_weeks)
        observation_weights = week_weights[week_codes]
        treated_weights = observation_weights * treated
        control_weights = observation_weights * (~treated)
        treated_count = np.bincount(
            stratum_codes, weights=treated_weights, minlength=number_of_strata
        )
        control_count = np.bincount(
            stratum_codes, weights=control_weights, minlength=number_of_strata
        )
        treated_sum = np.bincount(
            stratum_codes,
            weights=treated_weights * outcome_values,
            minlength=number_of_strata,
        )
        control_sum = np.bincount(
            stratum_codes,
            weights=control_weights * outcome_values,
            minlength=number_of_strata,
        )
        valid = (treated_count > 0) & (control_count > 0)
        if not np.any(valid):
            continue
        differences = (
            treated_sum[valid] / treated_count[valid]
            - control_sum[valid] / control_count[valid]
        )
        harmonic = (
            treated_count[valid]
            * control_count[valid]
            / (treated_count[valid] + control_count[valid])
        )
        values[kept] = np.sum(harmonic * differences) / np.sum(harmonic)
        kept += 1

    distribution = values[:kept]
    return {
        "phase": int(phase),
        "outcome": outcome,
        "point": float(point),
        "ci_low": float(np.quantile(distribution, 0.025)) if len(distribution) else np.nan,
        "ci_high": float(np.quantile(distribution, 0.975)) if len(distribution) else np.nan,
        "n_boot": int(len(distribution)),
    }


def summarize_events(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    periods = {
        "development_2015_2019": events[events.year <= 2019],
        "internal_validation_2020_2021": events[events.year >= 2020],
        "all_2015_2021": events,
    }
    for period, subset in periods.items():
        for label, group in subset.groupby("is_lqp"):
            valid = group[np.isfinite(group["return_60m_pips"])]
            rows.append(
                {
                    "period": period,
                    "group": "LQP" if label else "non_LQP_round",
                    "events_total": len(group),
                    "events_valid_60m": len(valid),
                    "mean_return_60m_pips": valid["return_60m_pips"].mean(),
                    "median_return_60m_pips": valid["return_60m_pips"].median(),
                    "mean_mfe_60m_pips": valid["mfe_60m_pips"].mean(),
                    "mean_mae_60m_pips": valid["mae_60m_pips"].mean(),
                    "follow_through_10p_rate": (
                        valid["fp_10p_60m"] == "follow_through"
                    ).mean(),
                    "reversal_10p_rate": (
                        valid["fp_10p_60m"] == "reversal"
                    ).mean(),
                    "mean_spread_pips": valid["spread_pips"].mean(),
                }
            )
    return pd.DataFrame(rows)
