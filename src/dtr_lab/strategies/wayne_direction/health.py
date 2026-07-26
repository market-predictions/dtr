from __future__ import annotations

import numpy as np
import pandas as pd

from .structure_common import _validate_ohlc, average_true_range


def build_h4_health(
    frame: pd.DataFrame,
    *,
    fast_length: int = 21,
    medium_length: int = 55,
    slow_length: int = 200,
    atr_length: int = 20,
    slope_bars: int = 3,
    compression_atr: float = 0.10,
) -> pd.DataFrame:
    if not 1 < fast_length < medium_length < slow_length:
        raise ValueError("moving-average lengths must be ordered fast < medium < slow")
    if slope_bars < 1:
        raise ValueError("slope_bars must be positive")
    if compression_atr < 0.0:
        raise ValueError("compression_atr must be non-negative")

    bars = _validate_ohlc(frame)
    out = pd.DataFrame(index=bars.index)
    out["ema_fast"] = bars["close"].ewm(span=fast_length, adjust=False).mean()
    out["ema_medium"] = bars["close"].ewm(span=medium_length, adjust=False).mean()
    out["ema_slow"] = bars["close"].ewm(span=slow_length, adjust=False).mean()
    out["atr"] = average_true_range(bars, atr_length)
    out["fast_gap_atr"] = (out["ema_fast"] - out["ema_medium"]) / out["atr"]
    out["slow_gap_atr"] = (out["ema_medium"] - out["ema_slow"]) / out["atr"]
    out["fast_slope_atr"] = (
        out["ema_fast"] - out["ema_fast"].shift(slope_bars)
    ) / out["atr"]
    out["medium_slope_atr"] = (
        out["ema_medium"] - out["ema_medium"].shift(slope_bars)
    ) / out["atr"]
    out["fast_gap_change"] = out["fast_gap_atr"] - out["fast_gap_atr"].shift(
        slope_bars
    )
    out["slow_gap_change"] = out["slow_gap_atr"] - out["slow_gap_atr"].shift(
        slope_bars
    )

    states: list[str] = []
    required = [
        "ema_fast",
        "ema_medium",
        "ema_slow",
        "atr",
        "fast_gap_atr",
        "slow_gap_atr",
        "fast_slope_atr",
        "medium_slope_atr",
        "fast_gap_change",
        "slow_gap_change",
    ]
    for row in out[required].itertuples(index=False):
        values = np.asarray(row, dtype=float)
        if not np.isfinite(values).all() or row.atr <= 0.0:
            states.append("WARMUP")
            continue

        bull_order = row.ema_fast > row.ema_medium > row.ema_slow
        bear_order = row.ema_fast < row.ema_medium < row.ema_slow
        if bull_order:
            compressed = (
                row.fast_gap_atr < compression_atr
                or row.slow_gap_atr < compression_atr
            )
            if compressed:
                states.append("BULL_COMPRESSED")
            elif (
                row.fast_slope_atr > 0.0
                and row.medium_slope_atr > 0.0
                and row.fast_gap_change > 0.0
                and row.slow_gap_change >= 0.0
            ):
                states.append("BULL_EXPANDING")
            elif row.fast_slope_atr >= 0.0 and row.medium_slope_atr >= 0.0:
                states.append("BULL_STABLE")
            else:
                states.append("BULL_CONFLICTED")
        elif bear_order:
            compressed = (
                abs(row.fast_gap_atr) < compression_atr
                or abs(row.slow_gap_atr) < compression_atr
            )
            if compressed:
                states.append("BEAR_COMPRESSED")
            elif (
                row.fast_slope_atr < 0.0
                and row.medium_slope_atr < 0.0
                and row.fast_gap_change < 0.0
                and row.slow_gap_change <= 0.0
            ):
                states.append("BEAR_EXPANDING")
            elif row.fast_slope_atr <= 0.0 and row.medium_slope_atr <= 0.0:
                states.append("BEAR_STABLE")
            else:
                states.append("BEAR_CONFLICTED")
        else:
            states.append("MIXED")

    out["health_state"] = states
    return out


def attach_last_completed_h4(
    daily_ledger: pd.DataFrame,
    h4_health: pd.DataFrame,
) -> pd.DataFrame:
    if not isinstance(daily_ledger.index, pd.DatetimeIndex):
        raise TypeError("daily ledger index must be a DatetimeIndex")
    if not isinstance(h4_health.index, pd.DatetimeIndex):
        raise TypeError("H4 health index must be a DatetimeIndex")
    if daily_ledger.index.tz is None or h4_health.index.tz is None:
        raise ValueError("daily and H4 indexes must be timezone-aware")

    daily = daily_ledger.sort_index().reset_index(names="timestamp")
    health = h4_health.sort_index().reset_index(names="h4_timestamp")
    merged = pd.merge_asof(
        daily,
        health,
        left_on="timestamp",
        right_on="h4_timestamp",
        direction="backward",
        allow_exact_matches=False,
    )
    return merged.set_index("timestamp")
