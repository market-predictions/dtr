from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.fx_ten_pair_runtime import match_controls_safe

AMSTERDAM_TZ = "Europe/Amsterdam"
WINDOW_START_MINUTE = 9 * 60
WINDOW_END_MINUTE = 10 * 60


def filter_amsterdam_confirmation_window(
    rows: pd.DataFrame,
    *,
    start_minute: int = WINDOW_START_MINUTE,
    end_minute: int = WINDOW_END_MINUTE,
) -> pd.DataFrame:
    """Keep detections inside a DST-aware Amsterdam half-open clock window."""
    if rows.empty:
        return rows.copy()
    if end_minute <= start_minute:
        raise ValueError("end_minute must be greater than start_minute")
    out = rows.copy()
    detection_utc = pd.to_datetime(
        out["state_detection_timestamp"], utc=True, errors="raise"
    )
    detection_local = detection_utc.dt.tz_convert(AMSTERDAM_TZ)
    minute_of_day = detection_local.dt.hour * 60 + detection_local.dt.minute
    out = out.loc[
        (minute_of_day >= start_minute) & (minute_of_day < end_minute)
    ].copy()
    detection_local = detection_local.loc[out.index]
    minute_of_day = minute_of_day.loc[out.index]
    out["detection_amsterdam"] = detection_local.astype(str)
    # Controls are rematched in Amsterdam-local calendar strata, not inherited
    # New York buckets. This matters during the non-overlapping DST weeks.
    out["year"] = detection_local.dt.year.astype(int)
    out["weekday"] = detection_local.dt.weekday.astype(int)
    out["time_bucket"] = (minute_of_day // 30).astype(int)
    return out


def build_amsterdam_window_matches(
    rows: pd.DataFrame,
    *,
    start_minute: int = WINDOW_START_MINUTE,
    end_minute: int = WINDOW_END_MINUTE,
    controls_per_event: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    filtered = filter_amsterdam_confirmation_window(
        rows,
        start_minute=start_minute,
        end_minute=end_minute,
    )
    matched_events, matched_controls = match_controls_safe(
        filtered,
        controls_per_event=controls_per_event,
    )
    return filtered, matched_events, matched_controls
