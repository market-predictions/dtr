from __future__ import annotations

from functools import wraps
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.asia_sweep import fingerprint_engine


def _reversal_direction(sweep_side: str) -> str:
    if sweep_side == "UP":
        return "DOWN"
    if sweep_side == "DOWN":
        return "UP"
    raise ValueError(f"unsupported sweep side: {sweep_side}")


def _distance_in_direction(direction: str, level_price: float, reference: float) -> float:
    if direction == "UP":
        return level_price - reference
    return reference - level_price


def build_opposing_liquidity_level_records(
    *,
    event_id: str,
    instrument: str,
    trade_date: object,
    side: str,
    levels: list[fingerprint_engine.Level],
    asian_high: float,
    asian_low: float,
    asian_range: float,
    pip: float,
    atr20: float,
    pre_sweep_price: float,
    sweep_extreme: float,
    t5_price: float,
    path_0800_pre: pd.DataFrame,
    sweep_bar: pd.DataFrame,
    path_sweep_t5: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Record the external levels in the reversal direction.

    The fingerprint engine already constructs this causal level universe to
    calculate opposite-side features, but its historical evidence artifact
    retained only sweep-side records. This function serializes the previously
    omitted opposite-side levels without changing any fingerprint feature.
    """

    tolerance = max(pip, 0.001 * atr20) if np.isfinite(atr20) else pip
    _, opposing = fingerprint_engine._relevant_levels(
        levels,
        side=side,
        asian_high=asian_high,
        asian_low=asian_low,
        tolerance=tolerance,
    )
    reversal_direction = _reversal_direction(side)
    boundary = asian_low if side == "UP" else asian_high
    records: list[dict[str, Any]] = []
    for level in opposing:
        distance_boundary = _distance_in_direction(
            reversal_direction,
            level.price,
            boundary,
        )
        distance_pre = _distance_in_direction(
            reversal_direction,
            level.price,
            pre_sweep_price,
        )
        distance_t0 = _distance_in_direction(
            reversal_direction,
            level.price,
            sweep_extreme,
        )
        distance_t5 = _distance_in_direction(
            reversal_direction,
            level.price,
            t5_price,
        )
        before = fingerprint_engine._level_reached(
            path_0800_pre,
            reversal_direction,
            level.price,
        )
        by_sweep = (not before) and fingerprint_engine._level_reached(
            sweep_bar,
            reversal_direction,
            level.price,
        )
        by_t5 = (not before) and fingerprint_engine._level_reached(
            path_sweep_t5,
            reversal_direction,
            level.price,
        )
        records.append(
            {
                "event_id": event_id,
                "instrument": instrument,
                "trade_date": str(trade_date),
                "side": side,
                "level_id": level.level_id,
                "level_family": level.family,
                "level_side": level.side,
                "level_price": level.price,
                "level_timestamp_utc": level.timestamp.tz_convert("UTC").isoformat(),
                "member_count": level.member_count,
                "timeframe_diversity": level.timeframe_diversity,
                "distance_boundary_pips": distance_boundary / pip,
                "distance_boundary_range": fingerprint_engine._safe_ratio(
                    distance_boundary,
                    asian_range,
                ),
                "distance_boundary_atr": fingerprint_engine._safe_ratio(
                    distance_boundary,
                    atr20,
                ),
                "distance_pre_sweep_atr": fingerprint_engine._safe_ratio(
                    distance_pre,
                    atr20,
                ),
                "distance_t0_atr": fingerprint_engine._safe_ratio(
                    distance_t0,
                    atr20,
                ),
                "distance_t5_atr": fingerprint_engine._safe_ratio(
                    distance_t5,
                    atr20,
                ),
                "available_at_0800": distance_boundary >= -tolerance,
                "consumed_before_sweep": before,
                "consumed_by_sweep": by_sweep,
                "consumed_through_t5": by_t5,
                "remaining_beyond_t0": distance_t0 > tolerance,
                "remaining_beyond_t5": distance_t5 > tolerance,
                "in_relevant_stack": False,
            }
        )
    return records


def install_opposing_liquidity_level_recorder() -> None:
    """Extend fingerprint level evidence with the already-computed opposite side."""

    current = fingerprint_engine._liquidity_features
    if getattr(current, "_records_opposing_liquidity", False):
        return

    @wraps(current)
    def wrapped(**kwargs: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        features, records = current(**kwargs)
        records.extend(build_opposing_liquidity_level_records(**kwargs))
        return features, records

    wrapped._records_opposing_liquidity = True  # type: ignore[attr-defined]
    fingerprint_engine._liquidity_features = wrapped


def select_opposing_liquidity_levels(levels: pd.DataFrame) -> pd.DataFrame:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "side",
        "level_id",
        "level_side",
        "level_price",
        "available_at_0800",
    }
    missing = sorted(required - set(levels.columns))
    if missing:
        raise ValueError(f"missing opposing-liquidity level columns: {missing}")
    mask = (
        levels["side"].eq("DOWN") & levels["level_side"].eq("HIGH")
    ) | (
        levels["side"].eq("UP") & levels["level_side"].eq("LOW")
    )
    result = levels.loc[mask & levels["available_at_0800"].astype(bool)].copy()
    if result.empty:
        raise ValueError("opposing-liquidity level ledger is empty")
    if result.duplicated(["event_id", "level_id"]).any():
        raise ValueError("opposing-liquidity level keys must be unique")
    observed = set(zip(result["side"], result["level_side"], strict=False))
    expected = {("DOWN", "HIGH"), ("UP", "LOW")}
    missing_roles = sorted(expected - observed)
    if missing_roles:
        raise ValueError(f"missing opposing-liquidity roles: {missing_roles}")
    return result.sort_values(
        ["event_id", "level_price", "level_id"],
        kind="mergesort",
    ).reset_index(drop=True)
