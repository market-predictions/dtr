from __future__ import annotations

import pandas as pd

AMSTERDAM_TZ = "Europe/Amsterdam"
REVERSAL_START_MINUTE = 9 * 60
FOLLOW_END_MINUTE = 11 * 60


def _as_utc(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column], utc=True, errors="coerce")


def enforce_window_and_two_sided_labels(events: pd.DataFrame) -> pd.DataFrame:
    """Apply the frozen 09:00 lower bound and sequential two-sided ambiguity rule.

    The primitive engine records first passages after each 08:00-10:00 sweep.
    This postprocessor ensures that a midpoint first reached before 09:00 is
    descriptive `EARLY_MIDPOINT`, not primary 09:00-10:00 success. It also marks
    an event ambiguous when the opposite Asian boundary is swept after the event
    begins but before that event resolves.
    """
    if events.empty:
        out = events.copy()
        out["early_midpoint"] = pd.Series(dtype=bool)
        return out

    out = events.copy()
    sweep_utc = _as_utc(out, "sweep_timestamp_utc")
    midpoint_utc = _as_utc(out, "midpoint_first_passage_utc")
    barrier_utc = _as_utc(out, "barrier_first_passage_utc")
    midpoint_local = midpoint_utc.dt.tz_convert(AMSTERDAM_TZ)
    midpoint_minute = midpoint_local.dt.hour * 60 + midpoint_local.dt.minute
    out["early_midpoint"] = midpoint_utc.notna() & (
        midpoint_minute < REVERSAL_START_MINUTE
    )

    early = out["early_midpoint"] & ~out["two_sided_ambiguous"].astype(bool)
    out.loc[early, "midpoint_success_09_10"] = False
    out.loc[early, "primary_outcome"] = "EARLY_MIDPOINT"

    for (_, trade_date), group in out.groupby(
        ["instrument", "trade_date"], sort=False, dropna=False
    ):
        group_sweep = sweep_utc.loc[group.index]
        for index in group.index:
            side = str(out.at[index, "side"])
            opposite_side = "DOWN" if side == "UP" else "UP"
            opposite = group.loc[group["side"].astype(str) == opposite_side]
            if opposite.empty or pd.isna(group_sweep.at[index]):
                continue
            later_opposite_times = group_sweep.loc[opposite.index]
            later_opposite_times = later_opposite_times.loc[
                later_opposite_times > group_sweep.at[index]
            ]
            if later_opposite_times.empty:
                continue
            resolution_candidates = [
                timestamp
                for timestamp in (midpoint_utc.at[index], barrier_utc.at[index])
                if pd.notna(timestamp)
            ]
            if resolution_candidates:
                resolution = min(resolution_candidates)
            else:
                follow_end = (
                    pd.Timestamp(trade_date)
                    .tz_localize(AMSTERDAM_TZ)
                    .replace(hour=11, minute=0)
                    .tz_convert("UTC")
                )
                resolution = follow_end
            if later_opposite_times.min() <= resolution:
                out.at[index, "two_sided_ambiguous"] = True
                out.at[index, "midpoint_success_09_10"] = False
                out.at[index, "full_range_success"] = False
                out.at[index, "early_midpoint"] = False
                out.at[index, "primary_outcome"] = "TWO_SIDED_AMBIGUOUS"

    return out
