from __future__ import annotations

import pandas as pd

from .model import AsiaSweepConfig
from .signals import build_event_ledger


def assert_prefix_causality(
    instrument: str,
    one_minute: pd.DataFrame,
    bars_5m: pd.DataFrame,
    cfg: AsiaSweepConfig,
) -> None:
    """Recompute each emitted signal using only data observable by its entry timestamp."""

    full = build_event_ledger(instrument, one_minute, bars_5m, cfg)
    signals = full[full["status"] == "SIGNAL"]
    for row in signals.itertuples(index=False):
        cutoff = pd.Timestamp(row.entry_timestamp)
        one_prefix = one_minute[one_minute["timestamp"] < cutoff]
        bars_prefix = bars_5m[
            (bars_5m["timestamp"] + pd.Timedelta(minutes=5)) <= cutoff
        ]
        prefix = build_event_ledger(instrument, one_prefix, bars_prefix, cfg)
        match = prefix[
            (prefix["trade_date"] == row.trade_date)
            & (prefix["execution_window"] == row.execution_window)
        ]
        if match.empty or match.iloc[0]["status"] != "SIGNAL":
            raise AssertionError(
                f"Noncausal signal: {instrument} {row.trade_date} {row.execution_window}"
            )
        if pd.Timestamp(match.iloc[0]["entry_timestamp"]) != cutoff:
            raise AssertionError(
                f"Entry timestamp changed under prefix replay: {instrument} {row.trade_date}"
            )
