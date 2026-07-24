from __future__ import annotations

import numpy as np
import pandas as pd

from .config import InstrumentSpec, SequenceConfig

_REQUIRED = {"gross_r", "initial_risk_points"}


def single_stream_round_trip_cost_points(
    spec: InstrumentSpec,
    config: SequenceConfig,
) -> float:
    if spec.execution_model != "single_ohlc":
        raise ValueError("exact ledger cost repricing is limited to single_ohlc execution")
    slippage = 2.0 * config.slippage_ticks_each_side * spec.tick_size
    commission = 2.0 * spec.commission_per_side / spec.point_value
    return slippage + commission


def reprice_single_stream_costs(
    trades: pd.DataFrame,
    *,
    spec: InstrumentSpec,
    config: SequenceConfig,
    arm_id: str,
) -> pd.DataFrame:
    missing = _REQUIRED.difference(trades.columns)
    if missing:
        raise ValueError(f"trade ledger missing columns required for repricing: {sorted(missing)}")
    result = trades.copy()
    if result.empty:
        if "arm_id" in result.columns:
            result["arm_id"] = arm_id
        return result
    risk = pd.to_numeric(result["initial_risk_points"], errors="raise").to_numpy(float)
    if not np.isfinite(risk).all() or bool((risk <= 0).any()):
        raise ValueError("trade ledger contains invalid initial risk")
    cost_points = single_stream_round_trip_cost_points(spec, config)
    result["arm_id"] = arm_id
    result["cost_r"] = cost_points / risk
    result["pnl_r"] = pd.to_numeric(result["gross_r"], errors="raise") - result["cost_r"]
    return result
