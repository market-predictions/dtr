from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .calendar import NEW_YORK_TZ

HEALTHY_STATES = {
    "BULL": {"BULL_EXPANDING", "BULL_STABLE"},
    "BEAR": {"BEAR_EXPANDING", "BEAR_STABLE"},
}
TARGETS = {
    "BULL": (("CONSERVATIVE", "M4"), ("STRETCH", "R2")),
    "BEAR": (("CONSERVATIVE", "M1"), ("STRETCH", "S2")),
}
LOCATION_RULES = {"CLOSE_IN_ZONE", "RANGE_TOUCH"}


def validate_time_index(frame: pd.DataFrame, label: str) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError(f"{label} index must be a DatetimeIndex")
    if frame.index.tz is None:
        raise ValueError(f"{label} index must be timezone-aware")
    if frame.index.has_duplicates:
        raise ValueError(f"{label} index contains duplicates")


def pivot_day_metadata(bar_start_utc: pd.Series) -> pd.DataFrame:
    starts = pd.DatetimeIndex(pd.to_datetime(bar_start_utc, utc=True))
    local = starts.tz_convert(NEW_YORK_TZ).tz_localize(None)
    day_start = local.normalize() + pd.Timedelta(hours=17)
    day_start = day_start.where(
        local >= day_start,
        day_start - pd.Timedelta(days=1),
    )
    trading_date = day_start.normalize() + pd.Timedelta(days=1)
    month_id = (trading_date.year * 100 + trading_date.month).to_numpy(dtype=int)
    metadata = pd.DataFrame(
        {
            "trading_date": pd.DatetimeIndex(trading_date),
            "month_id": month_id,
        }
    )
    metadata["pivot_day_ordinal"] = (
        metadata.groupby("month_id", sort=False)["trading_date"]
        .rank(method="dense")
        .astype(int)
    )
    return metadata


def asof_value(
    timestamp: pd.Timestamp,
    frame: pd.DataFrame,
    column: str,
) -> object:
    eligible = frame.loc[frame.index <= timestamp, column]
    return np.nan if eligible.empty else eligible.iloc[-1]


def direction_relation(side: str, direction: object) -> str:
    if side not in HEALTHY_STATES:
        raise ValueError(f"unsupported side: {side}")
    value = "NONE" if pd.isna(direction) else str(direction)
    if value == side:
        return "ALIGNED"
    if value in {"NONE", "AMBIGUOUS_SHOCK", "WARMUP"}:
        return "NONE"
    return "OPPOSED"


def location_mask(
    path: pd.DataFrame,
    *,
    side: str,
    zone_low: float,
    zone_high: float,
    location_rule: str,
) -> pd.Series:
    if side not in HEALTHY_STATES:
        raise ValueError(f"unsupported side: {side}")
    if location_rule == "CLOSE_IN_ZONE":
        if side == "BULL":
            return path["close"].ge(zone_low) & path["close"].lt(zone_high)
        return path["close"].gt(zone_low) & path["close"].le(zone_high)
    if location_rule == "RANGE_TOUCH":
        if side == "BULL":
            return path["low"].lt(zone_high) & path["high"].ge(zone_low)
        return path["high"].gt(zone_low) & path["low"].le(zone_high)
    raise ValueError(f"unsupported location rule: {location_rule}")


def first_index(mask: pd.Series) -> pd.Timestamp | None:
    matches = mask.index[mask.to_numpy(dtype=bool)]
    return None if len(matches) == 0 else pd.Timestamp(matches[0])


def stage_at_window(
    *,
    preexisting_aligned: bool,
    structure_timestamp: pd.Timestamp | None,
    health_timestamp: pd.Timestamp | None,
    structure_failed_timestamp: pd.Timestamp | None,
    landmark_timestamp: pd.Timestamp,
    side: str,
    h4_structure: pd.DataFrame,
    h4_health: pd.DataFrame,
) -> str:
    if structure_timestamp is None or structure_timestamp > landmark_timestamp:
        return "PREEXISTING_ALIGNED" if preexisting_aligned else "LOCATION_ONLY"
    if health_timestamp is None or health_timestamp > landmark_timestamp:
        if (
            structure_failed_timestamp is not None
            and structure_failed_timestamp <= landmark_timestamp
        ):
            return "STRUCTURE_FAILED"
        return "STRUCTURE_NO_HEALTH"
    direction = asof_value(
        landmark_timestamp,
        h4_structure,
        "confirmed_direction",
    )
    health = asof_value(landmark_timestamp, h4_health, "health_state")
    if str(direction) == side and str(health) in HEALTHY_STATES[side]:
        return "COMPLETE_ACTIVE"
    return "COMPLETE_DECAYED"


def first_target_timestamp(
    path: pd.DataFrame,
    *,
    side: str,
    target: float,
) -> pd.Timestamp | None:
    mask = path["high"].ge(target) if side == "BULL" else path["low"].le(target)
    return first_index(mask)


def target_outcome(
    path: pd.DataFrame,
    h4_structure: pd.DataFrame,
    *,
    side: str,
    target: float,
    start_timestamp: pd.Timestamp | None,
    month_open_timestamp: pd.Timestamp,
) -> dict[str, object]:
    empty = {
        "target_pre_start": False,
        "target_same_bar": False,
        "target_available": False,
        "target_timestamp": pd.NaT,
        "invalidation_timestamp": pd.NaT,
        "target_invalidation_same_bar": False,
        "reached_by_month_end": False,
        "reached_before_invalidation": False,
        "bars_to_target": math.nan,
    }
    if start_timestamp is None:
        return empty

    before = path.loc[
        (path.index >= month_open_timestamp) & (path.index < start_timestamp)
    ]
    same = path.loc[path.index == start_timestamp]
    after = path.loc[path.index > start_timestamp]

    pre_timestamp = first_target_timestamp(before, side=side, target=target)
    same_timestamp = first_target_timestamp(same, side=side, target=target)
    target_timestamp = first_target_timestamp(after, side=side, target=target)

    direction_after = h4_structure.loc[
        h4_structure.index.intersection(after.index),
        "confirmed_direction",
    ]
    invalid_timestamp = first_index(direction_after.astype(str).ne(side))
    target_invalidation_same_bar = (
        target_timestamp is not None
        and invalid_timestamp is not None
        and target_timestamp == invalid_timestamp
    )

    available = pre_timestamp is None and same_timestamp is None
    reached_by_month_end = available and target_timestamp is not None
    reached_before_invalidation = (
        reached_by_month_end
        and not target_invalidation_same_bar
        and (invalid_timestamp is None or target_timestamp < invalid_timestamp)
    )
    bars_to_target = (
        int(after.index.get_loc(target_timestamp)) + 1
        if reached_by_month_end and target_timestamp in after.index
        else math.nan
    )
    return {
        "target_pre_start": pre_timestamp is not None,
        "target_same_bar": same_timestamp is not None,
        "target_available": available,
        "target_timestamp": (
            pd.NaT if target_timestamp is None else target_timestamp
        ),
        "invalidation_timestamp": (
            pd.NaT if invalid_timestamp is None else invalid_timestamp
        ),
        "target_invalidation_same_bar": target_invalidation_same_bar,
        "reached_by_month_end": reached_by_month_end,
        "reached_before_invalidation": reached_before_invalidation,
        "bars_to_target": bars_to_target,
    }
