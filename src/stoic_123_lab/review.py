from __future__ import annotations

import math

import numpy as np
import pandas as pd


def independent_trade_review(
    trades: pd.DataFrame,
    published_summary: dict[str, object],
    *,
    instrument: str,
    arm_id: str,
) -> dict[str, object]:
    """Reconstruct core evidence without calling the production reporting functions."""

    if trades.empty:
        observed_count = 0
        observed_net = 0.0
        observed_expectancy = math.nan
        overlap_count = 0
        invalid_risk_count = 0
        invalid_chronology_count = 0
    else:
        ordered = trades.sort_values("entry_time").reset_index(drop=True)
        pnl = ordered["pnl_r"].astype(float).to_numpy()
        observed_count = int(pnl.size)
        observed_net = float(np.add.reduce(pnl))
        observed_expectancy = float(observed_net / observed_count)
        previous_exit = pd.to_datetime(ordered["exit_time"]).shift(1)
        overlap_count = int(
            (pd.to_datetime(ordered["entry_time"]) < previous_exit).fillna(False).sum()
        )
        invalid_risk_count = int((ordered["initial_risk_points"].astype(float) <= 0).sum())
        invalid_chronology_count = int(
            (
                (pd.to_datetime(ordered["signal_time"]) > pd.to_datetime(ordered["entry_time"]))
                | (pd.to_datetime(ordered["entry_time"]) > pd.to_datetime(ordered["exit_time"]))
                | (
                    pd.to_datetime(ordered["base_lock_time"])
                    >= pd.to_datetime(ordered["signal_time"])
                )
            ).sum()
        )

    published_count = int(published_summary["trades"])
    published_net = float(published_summary["net_r"])
    published_expectancy = float(published_summary["expectancy_r"])
    count_match = observed_count == published_count
    net_match = bool(np.isclose(observed_net, published_net, atol=1e-12, rtol=0))
    expectancy_match = (
        math.isnan(observed_expectancy)
        and math.isnan(published_expectancy)
        or np.isclose(observed_expectancy, published_expectancy, atol=1e-12, rtol=0)
    )
    passed = bool(
        count_match
        and net_match
        and expectancy_match
        and overlap_count == 0
        and invalid_risk_count == 0
        and invalid_chronology_count == 0
    )
    return {
        "instrument": instrument,
        "arm_id": arm_id,
        "status": "PASS" if passed else "FAIL",
        "observed_trades": observed_count,
        "observed_net_r": observed_net,
        "observed_expectancy_r": observed_expectancy,
        "count_match": count_match,
        "net_match": net_match,
        "expectancy_match": bool(expectancy_match),
        "overlap_count": overlap_count,
        "invalid_risk_count": invalid_risk_count,
        "invalid_chronology_count": invalid_chronology_count,
    }
