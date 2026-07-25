from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep import fingerprint_engine as engine
from dtr_lab.strategies.asia_sweep.fingerprint_performance import (
    clear_performance_caches,
    select_pivots_indexed,
)


def test_indexed_selector_is_identical_to_frozen_selector() -> None:
    index = pd.date_range(
        "2020-01-01 12:00",
        periods=35,
        freq="1D",
        tz="Europe/Amsterdam",
    )
    frame = pd.DataFrame(
        {
            "open": 1.0,
            "high": 1.05,
            "low": 0.95,
            "close": 1.0,
            "is_active_quote": 1,
        },
        index=index,
    )
    pivots: list[engine.Level] = []
    for offset in range(1, 11):
        timestamp = index[-1] - pd.Timedelta(days=offset)
        pivots.append(
            engine.Level(
                level_id=f"m15-{offset}",
                family="M15_PIVOT",
                side="HIGH",
                price=1.20 + offset * 0.002,
                timestamp=timestamp,
            )
        )
    for offset in range(1, 26):
        timestamp = index[-1] - pd.Timedelta(days=offset)
        pivots.append(
            engine.Level(
                level_id=f"h1-{offset}",
                family="H1_PIVOT",
                side="LOW",
                price=0.80 - offset * 0.002,
                timestamp=timestamp,
            )
        )
    pivots.sort(key=lambda level: (level.timestamp, level.level_id))
    eligible_dates = [timestamp.date() for timestamp in index]
    snapshot = index[-1] + pd.Timedelta(hours=1)
    kwargs = {
        "pivots": pivots,
        "frame": frame,
        "snapshot": snapshot,
        "trade_date": index[-1].date(),
        "eligible_dates": eligible_dates,
        "pip": 0.0001,
        "atr20": 0.0100,
    }

    expected = engine._select_pivots(**kwargs)
    clear_performance_caches()
    actual = select_pivots_indexed(**kwargs)

    assert [level.level_id for level in actual] == [
        level.level_id for level in expected
    ]
    assert [level.price for level in actual] == [level.price for level in expected]
