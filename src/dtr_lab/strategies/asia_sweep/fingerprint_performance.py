from __future__ import annotations

from bisect import bisect_left
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep import fingerprint_engine as engine

_PIVOT_INDEX: dict[int, dict[str, tuple[list[int], list[engine.Level]]]] = {}


def _index_pivots(
    pivots: list[engine.Level],
) -> dict[str, tuple[list[int], list[engine.Level]]]:
    key = id(pivots)
    cached = _PIVOT_INDEX.get(key)
    if cached is not None:
        return cached
    grouped: dict[str, list[engine.Level]] = {}
    for level in pivots:
        grouped.setdefault(level.family, []).append(level)
    indexed: dict[str, tuple[list[int], list[engine.Level]]] = {}
    for family, levels in grouped.items():
        ordered = sorted(levels, key=lambda level: (level.timestamp, level.level_id))
        indexed[family] = ([level.timestamp.value for level in ordered], ordered)
    _PIVOT_INDEX[key] = indexed
    return indexed


def select_pivots_indexed(
    *,
    pivots: list[engine.Level],
    frame: pd.DataFrame,
    snapshot: pd.Timestamp,
    trade_date: object,
    eligible_dates: list[object],
    pip: float,
    atr20: float,
) -> list[engine.Level]:
    """Equivalent pivot selection with indexed time bounds and early stopping.

    The original implementation filtered every pivot in each lookback, checked
    every candidate for invalidation, sorted the survivors and retained the most
    recent five M15 and three H1 levels. Iterating newest-first and stopping after
    the same number of unswept survivors is mathematically identical while
    avoiding most repeated multi-day price scans.
    """
    indexed = _index_pivots(pivots)
    selected: list[engine.Level] = []
    for family, lookback, limit in (("M15_PIVOT", 5, 5), ("H1_PIVOT", 20, 3)):
        times, levels = indexed.get(family, ([], []))
        if not levels:
            continue
        cutoff = engine._recent_eligible_cutoff(eligible_dates, trade_date, lookback)
        start_value = (
            pd.Timestamp(cutoff).tz_localize(engine.AMSTERDAM_TZ).value
            if cutoff is not None
            else times[0]
        )
        start = bisect_left(times, start_value)
        end = bisect_left(times, snapshot.value)
        tolerance = max(pip, 0.001 * atr20) if np.isfinite(atr20) else pip
        retained = 0
        for level in reversed(levels[start:end]):
            if not engine._pivot_unswept(frame, level, snapshot, tolerance):
                continue
            selected.append(level)
            retained += 1
            if retained == limit:
                break
    cluster_tolerance = max(pip, 0.03 * atr20) if np.isfinite(atr20) else pip
    selected.extend(engine._cluster_levels(selected, cluster_tolerance, snapshot))
    return selected


def install_indexed_pivot_selector() -> None:
    engine._select_pivots = select_pivots_indexed  # type: ignore[assignment]


def clear_performance_caches() -> None:
    _PIVOT_INDEX.clear()


def cache_diagnostics() -> dict[str, Any]:
    return {
        "pivot_lists": len(_PIVOT_INDEX),
        "families": sum(len(value) for value in _PIVOT_INDEX.values()),
    }
