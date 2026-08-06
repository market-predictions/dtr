from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .sequence_common import (
    HEALTHY_STATES,
    LOCATION_RULES,
    TARGETS,
    asof_value,
    direction_relation,
    first_index,
    location_mask,
    pivot_day_metadata,
    stage_at_window,
    target_outcome,
    validate_time_index,
)

LOCATION_PIVOT_DAYS = 5
PRIMARY_PIVOT_DAYS = 5
SENSITIVITY_PIVOT_DAYS = 10


def _validate_inputs(
    daily_bars: pd.DataFrame,
    monthly_context: pd.DataFrame,
    d1_structure: pd.DataFrame,
    h4_bars: pd.DataFrame,
    h4_structure: pd.DataFrame,
    h4_health: pd.DataFrame,
) -> None:
    for label, frame in (
        ("daily bars", daily_bars),
        ("monthly context", monthly_context),
        ("D1 structure", d1_structure),
        ("H4 bars", h4_bars),
        ("H4 structure", h4_structure),
        ("H4 health", h4_health),
    ):
        validate_time_index(frame, label)
    if not daily_bars.index.equals(monthly_context.index):
        raise ValueError("daily bars and monthly context indexes must match")
    if not daily_bars.index.equals(d1_structure.index):
        raise ValueError("daily bars and D1 structure indexes must match")
    if not h4_bars.index.equals(h4_structure.index):
        raise ValueError("H4 bars and structure indexes must match")
    if not h4_bars.index.equals(h4_health.index):
        raise ValueError("H4 bars and health indexes must match")

    required_daily = {"bar_start_utc", "open", "high", "low", "close"}
    required_monthly = {
        "month_id",
        "month_open",
        "M1",
        "M2",
        "M3",
        "M4",
        "P",
        "R2",
        "S2",
    }
    required_h4 = {"bar_start_utc", "open", "high", "low", "close"}
    if required_daily - set(daily_bars):
        raise ValueError("daily bars missing staged-sequence columns")
    if required_monthly - set(monthly_context):
        raise ValueError("monthly context missing staged-sequence columns")
    if required_h4 - set(h4_bars):
        raise ValueError("H4 bars missing staged-sequence columns")
    if {"confirmed_direction", "events"} - set(h4_structure):
        raise ValueError("H4 structure missing staged-sequence columns")
    if "health_state" not in h4_health:
        raise ValueError("H4 health missing health_state")


def _annotated_h4(
    h4_bars: pd.DataFrame,
    h4_structure: pd.DataFrame,
    h4_health: pd.DataFrame,
) -> pd.DataFrame:
    h4 = h4_bars.copy()
    metadata = pivot_day_metadata(h4["bar_start_utc"])
    metadata.index = h4.index
    return (
        h4.join(metadata)
        .join(
            h4_structure[["confirmed_direction", "events"]].rename(
                columns={
                    "confirmed_direction": "h4_direction",
                    "events": "h4_events",
                }
            )
        )
        .join(h4_health[["health_state"]])
    )


def _location(
    month_path: pd.DataFrame,
    *,
    side: str,
    month_open_timestamp: pd.Timestamp,
    month_open: float,
    zone_low: float,
    zone_high: float,
    location_rule: str,
) -> tuple[pd.Timestamp, int, str] | None:
    open_inside = (
        zone_low <= month_open < zone_high
        if side == "BULL"
        else zone_low < month_open <= zone_high
    )
    if open_inside:
        return month_open_timestamp, 1, "MONTH_OPEN"
    early = month_path.loc[
        month_path["pivot_day_ordinal"].le(LOCATION_PIVOT_DAYS)
    ]
    timestamp = first_index(
        location_mask(
            early,
            side=side,
            zone_low=zone_low,
            zone_high=zone_high,
            location_rule=location_rule,
        )
    )
    if timestamp is None:
        return None
    source = "H4_CLOSE" if location_rule == "CLOSE_IN_ZONE" else "H4_RANGE_TOUCH"
    return timestamp, int(month_path.loc[timestamp, "pivot_day_ordinal"]), source


def _structure_and_health(
    month_path: pd.DataFrame,
    *,
    side: str,
    location_timestamp: pd.Timestamp,
) -> tuple[
    pd.Timestamp | None,
    pd.Timestamp | None,
    pd.Timestamp | None,
]:
    event_name = f"{side}_TREND_CONFIRMED"
    search = month_path.loc[
        (month_path.index > location_timestamp)
        & month_path["pivot_day_ordinal"].le(SENSITIVITY_PIVOT_DAYS)
    ]
    structure_timestamp = first_index(
        search["h4_events"].fillna("").str.contains(event_name)
    )
    if structure_timestamp is None:
        return None, None, None

    after_structure = month_path.loc[
        (month_path.index >= structure_timestamp)
        & month_path["pivot_day_ordinal"].le(SENSITIVITY_PIVOT_DAYS)
    ]
    invalid_matches = after_structure.index[
        after_structure["h4_direction"].astype(str).ne(side).to_numpy(dtype=bool)
    ]
    failed_timestamp = (
        None if len(invalid_matches) == 0 else pd.Timestamp(invalid_matches[0])
    )
    before_failure = after_structure
    if failed_timestamp is not None:
        before_failure = before_failure.loc[
            before_failure.index < failed_timestamp
        ]
    healthy = (
        before_failure["h4_direction"].astype(str).eq(side)
        & before_failure["health_state"].astype(str).isin(HEALTHY_STATES[side])
    )
    return structure_timestamp, first_index(healthy), failed_timestamp


def build_staged_monthly_sequence(
    daily_bars: pd.DataFrame,
    monthly_context: pd.DataFrame,
    d1_structure: pd.DataFrame,
    h4_bars: pd.DataFrame,
    h4_structure: pd.DataFrame,
    h4_health: pd.DataFrame,
    *,
    location_rule: str = "CLOSE_IN_ZONE",
) -> pd.DataFrame:
    if location_rule not in LOCATION_RULES:
        raise ValueError(f"unsupported location rule: {location_rule}")
    _validate_inputs(
        daily_bars,
        monthly_context,
        d1_structure,
        h4_bars,
        h4_structure,
        h4_health,
    )
    h4 = _annotated_h4(h4_bars, h4_structure, h4_health)
    daily_context = daily_bars[["bar_start_utc"]].join(monthly_context)
    month_rows = daily_context.groupby("month_id", sort=True).first()

    rows: list[dict[str, object]] = []
    for month_id, month in month_rows.iterrows():
        level_values = np.asarray(
            [
                month["month_open"],
                month["M1"],
                month["M2"],
                month["M3"],
                month["M4"],
                month["P"],
                month["R2"],
                month["S2"],
            ],
            dtype=float,
        )
        if not np.isfinite(level_values).all():
            continue
        month_path = h4.loc[h4["month_id"].eq(int(month_id))].copy()
        if month_path.empty:
            continue
        month_open_timestamp = pd.Timestamp(month["bar_start_utc"])
        primary_path = month_path.loc[
            month_path["pivot_day_ordinal"].le(PRIMARY_PIVOT_DAYS)
        ]
        sensitivity_path = month_path.loc[
            month_path["pivot_day_ordinal"].le(SENSITIVITY_PIVOT_DAYS)
        ]
        if primary_path.empty or sensitivity_path.empty:
            continue
        primary_landmark = pd.Timestamp(primary_path.index[-1])
        sensitivity_landmark = pd.Timestamp(sensitivity_path.index[-1])

        for side in ("BULL", "BEAR"):
            if side == "BULL":
                zone_low, zone_high = float(month["M2"]), float(month["P"])
            else:
                zone_low, zone_high = float(month["P"]), float(month["M3"])
            location = _location(
                month_path,
                side=side,
                month_open_timestamp=month_open_timestamp,
                month_open=float(month["month_open"]),
                zone_low=zone_low,
                zone_high=zone_high,
                location_rule=location_rule,
            )
            if location is None:
                continue
            location_timestamp, location_day, location_source = location

            direction_at_location = asof_value(
                location_timestamp,
                h4_structure,
                "confirmed_direction",
            )
            health_at_location = asof_value(
                location_timestamp,
                h4_health,
                "health_state",
            )
            preexisting_aligned = str(direction_at_location) == side
            d1_at_location = asof_value(
                location_timestamp,
                d1_structure,
                "confirmed_direction",
            )

            (
                structure_timestamp,
                health_timestamp,
                failed_timestamp,
            ) = _structure_and_health(
                month_path,
                side=side,
                location_timestamp=location_timestamp,
            )
            structure_day = (
                math.nan
                if structure_timestamp is None
                else int(
                    month_path.loc[
                        structure_timestamp,
                        "pivot_day_ordinal",
                    ]
                )
            )
            health_day = (
                math.nan
                if health_timestamp is None
                else int(
                    month_path.loc[
                        health_timestamp,
                        "pivot_day_ordinal",
                    ]
                )
            )
            d1_at_signal = (
                np.nan
                if health_timestamp is None
                else asof_value(
                    health_timestamp,
                    d1_structure,
                    "confirmed_direction",
                )
            )

            primary_stage = stage_at_window(
                preexisting_aligned=preexisting_aligned,
                structure_timestamp=structure_timestamp,
                health_timestamp=health_timestamp,
                structure_failed_timestamp=failed_timestamp,
                landmark_timestamp=primary_landmark,
                side=side,
                h4_structure=h4_structure,
                h4_health=h4_health,
            )
            sensitivity_stage = stage_at_window(
                preexisting_aligned=preexisting_aligned,
                structure_timestamp=structure_timestamp,
                health_timestamp=health_timestamp,
                structure_failed_timestamp=failed_timestamp,
                landmark_timestamp=sensitivity_landmark,
                side=side,
                h4_structure=h4_structure,
                h4_health=h4_health,
            )

            for target_tier, target_name in TARGETS[side]:
                target = float(month[target_name])
                signal = target_outcome(
                    month_path,
                    h4_structure,
                    side=side,
                    target=target,
                    start_timestamp=health_timestamp,
                    month_open_timestamp=month_open_timestamp,
                )
                primary_outcome = target_outcome(
                    month_path,
                    h4_structure,
                    side=side,
                    target=target,
                    start_timestamp=primary_landmark,
                    month_open_timestamp=month_open_timestamp,
                )
                sensitivity_outcome = target_outcome(
                    month_path,
                    h4_structure,
                    side=side,
                    target=target,
                    start_timestamp=sensitivity_landmark,
                    month_open_timestamp=month_open_timestamp,
                )
                rows.append(
                    {
                        "month_id": int(month_id),
                        "year": int(month_id) // 100,
                        "side": side,
                        "location_rule": location_rule,
                        "month_open_timestamp": month_open_timestamp,
                        "month_open": float(month["month_open"]),
                        "zone_low": zone_low,
                        "zone_high": zone_high,
                        "location_timestamp": location_timestamp,
                        "location_pivot_day": location_day,
                        "location_source": location_source,
                        "h4_direction_at_location": direction_at_location,
                        "h4_health_at_location": health_at_location,
                        "preexisting_aligned": preexisting_aligned,
                        "d1_direction_at_location": d1_at_location,
                        "d1_relation_at_location": direction_relation(
                            side,
                            d1_at_location,
                        ),
                        "structure_timestamp": (
                            pd.NaT
                            if structure_timestamp is None
                            else structure_timestamp
                        ),
                        "structure_pivot_day": structure_day,
                        "structure_failed_timestamp": (
                            pd.NaT
                            if failed_timestamp is None
                            else failed_timestamp
                        ),
                        "health_timestamp": (
                            pd.NaT
                            if health_timestamp is None
                            else health_timestamp
                        ),
                        "health_pivot_day": health_day,
                        "health_same_bar_as_structure": (
                            structure_timestamp is not None
                            and health_timestamp == structure_timestamp
                        ),
                        "health_strictly_after_structure": (
                            structure_timestamp is not None
                            and health_timestamp is not None
                            and health_timestamp > structure_timestamp
                        ),
                        "d1_direction_at_signal": d1_at_signal,
                        "d1_relation_at_signal": (
                            "NO_SIGNAL"
                            if health_timestamp is None
                            else direction_relation(side, d1_at_signal)
                        ),
                        "stage_primary": primary_stage,
                        "stage_sensitivity": sensitivity_stage,
                        "sequence_complete_primary": primary_stage
                        in {"COMPLETE_ACTIVE", "COMPLETE_DECAYED"},
                        "sequence_complete_sensitivity": sensitivity_stage
                        in {"COMPLETE_ACTIVE", "COMPLETE_DECAYED"},
                        "sequence_active_primary": (
                            primary_stage == "COMPLETE_ACTIVE"
                        ),
                        "sequence_active_sensitivity": (
                            sensitivity_stage == "COMPLETE_ACTIVE"
                        ),
                        "primary_landmark_timestamp": primary_landmark,
                        "sensitivity_landmark_timestamp": sensitivity_landmark,
                        "target_tier": target_tier,
                        "target_name": target_name,
                        "target": target,
                        **{
                            f"signal_{key}": value
                            for key, value in signal.items()
                        },
                        **{
                            f"primary_{key}": value
                            for key, value in primary_outcome.items()
                        },
                        **{
                            f"sensitivity_{key}": value
                            for key, value in sensitivity_outcome.items()
                        },
                    }
                )

    output = pd.DataFrame(rows)
    if output.empty:
        return output
    output["opportunity_id"] = (
        output["month_id"].astype(str)
        + "::"
        + output["side"]
        + "::"
        + output["location_rule"]
    )
    side_counts = (
        output.drop_duplicates(["month_id", "side"])
        .groupby("month_id", sort=False)["side"]
        .nunique()
    )
    output["dual_zone_month"] = output["month_id"].map(side_counts).gt(1)
    return output
