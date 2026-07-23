from __future__ import annotations

import hashlib
from datetime import time

import numpy as np
import pandas as pd

from .config import SequenceConfig
from .detector import attach_map
from .validation_direction import _event_row, _map_allows_long, _selected_map_direction


def _session_label(timestamp: pd.Timestamp) -> str:
    clock = timestamp.time()
    return "RTH" if time(9, 30) <= clock < time(16, 0) else "OVERNIGHT"


def _half_hour_bucket(timestamp: pd.Timestamp) -> int:
    return timestamp.hour * 2 + timestamp.minute // 30


def _stable_offset(*, arm_id: str, signal_time: pd.Timestamp, seed: int, pool_size: int) -> int:
    payload = f"{arm_id}|{signal_time.isoformat()}|{seed}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % pool_size


def matched_time_events(
    full_events: pd.DataFrame,
    execution_bars: pd.DataFrame,
    map_bars: pd.DataFrame,
    config: SequenceConfig,
    *,
    seed: int,
) -> pd.DataFrame:
    """Build deterministic risk- and time-matched pseudo entries without future returns."""

    if full_events.empty:
        return pd.DataFrame()

    bars = attach_map(execution_bars, map_bars, config).reset_index(drop=True).copy()
    bars["signal_time"] = pd.to_datetime(bars["bar_end"])
    bars["year"] = bars["signal_time"].dt.year
    bars["month"] = bars["signal_time"].dt.month
    bars["weekday"] = bars["signal_time"].dt.weekday
    bars["session"] = bars["signal_time"].map(_session_label)
    bars["bucket"] = bars["signal_time"].map(_half_hour_bucket)
    bars["map_allows"] = [
        _map_allows_long(int(ema), int(breakout), config)
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

    original_times = set(pd.to_datetime(full_events["signal_time"]))
    used: set[pd.Timestamp] = set()
    rows: list[dict[str, object]] = []

    for event in full_events.sort_values("signal_time").itertuples(index=False):
        original = pd.Timestamp(event.signal_time)
        risk_width = float(event.breakout_close) - float(event.protective_boundary)
        if not np.isfinite(risk_width) or risk_width <= 0:
            continue

        exact = bars.loc[
            (bars["year"] == original.year)
            & (bars["month"] == original.month)
            & (bars["weekday"] == original.weekday())
            & (bars["session"] == _session_label(original))
            & (bars["bucket"] == _half_hour_bucket(original))
        ]
        pools = [
            exact,
            bars.loc[
                (bars["year"] == original.year)
                & (bars["weekday"] == original.weekday())
                & (bars["session"] == _session_label(original))
                & (bars["bucket"] == _half_hour_bucket(original))
            ],
            bars.loc[
                (bars["year"] == original.year)
                & (bars["session"] == _session_label(original))
                & (bars["bucket"] == _half_hour_bucket(original))
            ],
        ]
        pool = next((candidate for candidate in pools if len(candidate) >= 2), pd.DataFrame())
        if pool.empty:
            continue

        pool = pool.sort_values("signal_time").reset_index(drop=True)
        start = _stable_offset(
            arm_id=config.arm_id,
            signal_time=original,
            seed=seed,
            pool_size=len(pool),
        )
        selected = None
        for step in range(len(pool)):
            candidate = pool.iloc[(start + step) % len(pool)]
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
            _event_row(
                arm_id=f"{config.arm_id}__MATCHED_TIME",
                model="matched_time",
                step1_time=signal_time,
                retest_time=None,
                signal_time=signal_time,
                base_lock_time=pd.Timestamp(selected["timestamp"]),
                protective_boundary=close_price - risk_width,
                breakout_close=close_price,
                atr_at_signal=float(selected["atr"]),
                map_direction_step1=selected_map,
                map_direction_signal=selected_map,
            )
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("signal_time").reset_index(drop=True)
