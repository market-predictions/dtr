from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import time

import numpy as np
import pandas as pd

from .config import SequenceConfig
from .detector import attach_map
from .validation_direction import _selected_map_direction
from .validation_short_direction import _map_allows_short, _short_event_row

MINIMUM_MATCH_FRACTION = 0.90


@dataclass(frozen=True)
class _PreparedShortPools:
    bars: pd.DataFrame
    exact: dict[tuple[object, ...], np.ndarray]
    weekday: dict[tuple[object, ...], np.ndarray]
    broad: dict[tuple[object, ...], np.ndarray]


_POOL_CACHE: dict[tuple[int, int, SequenceConfig], _PreparedShortPools] = {}


def _session_label(timestamp: pd.Timestamp) -> str:
    clock = timestamp.time()
    return "RTH" if time(9, 30) <= clock < time(16, 0) else "OVERNIGHT"


def _half_hour_bucket(timestamp: pd.Timestamp) -> int:
    return timestamp.hour * 2 + timestamp.minute // 30


def _stable_offset(
    *,
    arm_id: str,
    signal_time: pd.Timestamp,
    seed: int,
    pool_size: int,
) -> int:
    payload = f"{arm_id}|short|{signal_time.isoformat()}|{seed}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % pool_size


def _group_indices(
    bars: pd.DataFrame,
    columns: list[str],
) -> dict[tuple[object, ...], np.ndarray]:
    result: dict[tuple[object, ...], np.ndarray] = {}
    for key, group in bars.groupby(columns, sort=False, observed=True):
        normalized = key if isinstance(key, tuple) else (key,)
        result[normalized] = group.index.to_numpy(dtype=np.int64)
    return result


def _prepare_short_pools(
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    config: SequenceConfig,
) -> _PreparedShortPools:
    key = (id(execution_bars), id(map_bars), config)
    cached = _POOL_CACHE.get(key)
    if cached is not None:
        return cached

    bars = attach_map(execution_bars, map_bars, config).reset_index(drop=True).copy()
    bars["signal_time"] = pd.to_datetime(bars["bar_end"])
    bars = bars.sort_values("signal_time").reset_index(drop=True)
    bars["year"] = bars["signal_time"].dt.year
    bars["month"] = bars["signal_time"].dt.month
    bars["weekday"] = bars["signal_time"].dt.weekday
    bars["session"] = bars["signal_time"].map(_session_label)
    bars["bucket"] = bars["signal_time"].map(_half_hour_bucket)
    bars["map_allows"] = [
        _map_allows_short(int(ema), int(breakout), config)
        for ema, breakout in zip(
            bars["ema_map_direction"].fillna(0),
            bars["breakout_map_direction"].fillna(0),
            strict=True,
        )
    ]

    eligible = np.isfinite(bars["atr"]) & bars["map_allows"]
    if "full_bar" in bars:
        eligible &= bars["full_bar"].fillna(False).astype(bool)
    if "gap_minutes" in bars:
        eligible &= bars["gap_minutes"].fillna(0).le(config.gap_reset_minutes)
    bars = bars.loc[eligible].reset_index(drop=True)

    prepared = _PreparedShortPools(
        bars=bars,
        exact=_group_indices(
            bars,
            ["year", "month", "weekday", "session", "bucket"],
        ),
        weekday=_group_indices(
            bars,
            ["year", "weekday", "session", "bucket"],
        ),
        broad=_group_indices(
            bars,
            ["year", "session", "bucket"],
        ),
    )
    _POOL_CACHE.clear()
    _POOL_CACHE[key] = prepared
    return prepared


def matched_time_short_events(
    full_events: pd.DataFrame,
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    config: SequenceConfig,
    *,
    seed: int,
) -> pd.DataFrame:
    """Build deterministic short pseudo entries without using future returns."""

    if full_events.empty:
        result = pd.DataFrame()
        result.attrs["match_fraction"] = 0.0
        return result

    prepared = _prepare_short_pools(execution_bars, map_bars, config)
    bars = prepared.bars
    original_times = set(pd.to_datetime(full_events["signal_time"]))
    used: set[pd.Timestamp] = set()
    rows: list[dict[str, object]] = []

    for event in full_events.sort_values("signal_time").itertuples(index=False):
        original = pd.Timestamp(event.signal_time)
        risk_width = float(event.protective_boundary) - float(event.breakout_close)
        if not np.isfinite(risk_width) or risk_width <= 0:
            continue

        session = _session_label(original)
        bucket = _half_hour_bucket(original)
        candidate_pools = (
            prepared.exact.get(
                (original.year, original.month, original.weekday(), session, bucket)
            ),
            prepared.weekday.get(
                (original.year, original.weekday(), session, bucket)
            ),
            prepared.broad.get((original.year, session, bucket)),
        )
        pool = next(
            (
                candidate
                for candidate in candidate_pools
                if candidate is not None and len(candidate) >= 2
            ),
            None,
        )
        if pool is None:
            continue

        start = _stable_offset(
            arm_id=config.arm_id,
            signal_time=original,
            seed=seed,
            pool_size=len(pool),
        )
        selected = None
        for step in range(len(pool)):
            candidate = bars.iloc[int(pool[(start + step) % len(pool)])]
            candidate_time = pd.Timestamp(candidate["signal_time"])
            if candidate_time in used or candidate_time in original_times:
                continue
            if abs((candidate_time - original).total_seconds()) < 24 * 60 * 60:
                continue
            selected = candidate
            break
        if selected is None:
            continue

        signal_time = pd.Timestamp(selected["signal_time"])
        used.add(signal_time)
        close_price = float(selected["close"])
        selected_map = _selected_map_direction(
            int(selected["ema_map_direction"]),
            int(selected["breakout_map_direction"]),
            config,
        )
        rows.append(
            _short_event_row(
                arm_id=f"{config.arm_id}__MATCHED_SHORT",
                model="ema_break",
                step1_time=signal_time,
                retest_time=None,
                signal_time=signal_time,
                base_lock_time=pd.Timestamp(selected["timestamp"]),
                protective_boundary=close_price + risk_width,
                breakout_close=close_price,
                atr_at_signal=float(selected["atr"]),
                map_direction_step1=selected_map,
                map_direction_signal=selected_map,
            )
        )

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("signal_time").reset_index(drop=True)
    result.attrs["match_fraction"] = len(result) / len(full_events)
    return result
