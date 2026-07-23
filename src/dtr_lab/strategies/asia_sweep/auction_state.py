from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

SESSION_TIMEZONE = "America/New_York"
DEVELOPMENT_START = pd.Timestamp("2023-01-01", tz=SESSION_TIMEZONE)
DEVELOPMENT_END = pd.Timestamp("2024-07-01", tz=SESSION_TIMEZONE)
ROLLING_RANGE_LOOKBACK = 60
MINIMUM_RANGE_HISTORY = 20

_REQUIRED_MINUTE_COLUMNS = {
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "is_active_quote",
}


@dataclass(frozen=True)
class SessionSpec:
    name: str
    reference_start_previous_day: bool
    reference_start_hour: int
    reference_start_minute: int
    reference_end_hour: int
    reference_end_minute: int
    window_start_hour: int
    window_start_minute: int
    window_end_hour: int
    window_end_minute: int


SESSION_SPECS = (
    SessionSpec(
        name="LONDON",
        reference_start_previous_day=True,
        reference_start_hour=18,
        reference_start_minute=0,
        reference_end_hour=2,
        reference_end_minute=0,
        window_start_hour=2,
        window_start_minute=0,
        window_end_hour=6,
        window_end_minute=0,
    ),
    SessionSpec(
        name="NEW_YORK",
        reference_start_previous_day=False,
        reference_start_hour=2,
        reference_start_minute=0,
        reference_end_hour=8,
        reference_end_minute=30,
        window_start_hour=8,
        window_start_minute=30,
        window_end_hour=11,
        window_end_minute=30,
    ),
)


@dataclass(frozen=True)
class StateDetection:
    first_index: int
    first_side: str
    state: str
    detection_index: int
    reclaim_index: int | None
    opposite_index: int | None
    outside_close_count: int
    inside_hold_count: int


def _local_timestamp(day: pd.Timestamp, hour: int, minute: int) -> pd.Timestamp:
    day = pd.Timestamp(day)
    naive = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=hour,
        minute=minute,
    )
    return naive.tz_localize(
        SESSION_TIMEZONE,
        ambiguous="raise",
        nonexistent="raise",
    )


def _validate_minutes(frame: pd.DataFrame) -> pd.DataFrame:
    missing = _REQUIRED_MINUTE_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"minute frame missing columns: {sorted(missing)}")
    out = frame.copy(deep=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="raise")
    if out.empty:
        raise ValueError("minute frame is empty")
    if out["timestamp"].dt.tz is None:
        raise ValueError("minute timestamps must be timezone-aware")
    out["timestamp"] = out["timestamp"].dt.tz_convert(SESSION_TIMEZONE)
    if bool(out["timestamp"].duplicated(keep=False).any()):
        raise ValueError("minute frame contains duplicate timestamps")
    off_grid = (
        (out["timestamp"].dt.second != 0)
        | (out["timestamp"].dt.microsecond != 0)
        | (out["timestamp"].dt.nanosecond != 0)
    )
    if bool(off_grid.any()):
        raise ValueError("minute frame contains off-grid timestamps")
    for column in ("open", "high", "low", "close", "is_active_quote"):
        out[column] = pd.to_numeric(out[column], errors="raise")
        finite = np.isfinite(out[column].to_numpy(dtype=float))
        if not bool(finite.all()):
            raise ValueError(f"minute frame contains non-finite {column}")
    invalid = (
        (out["high"] < out[["open", "close"]].max(axis=1))
        | (out["low"] > out[["open", "close"]].min(axis=1))
        | (out["high"] < out["low"])
    )
    if bool(invalid.any()):
        raise ValueError("minute frame violates OHLC geometry")
    activity = set(out["is_active_quote"].astype(int).unique())
    if not activity.issubset({0, 1}):
        raise ValueError("is_active_quote must contain only zero or one")
    out["is_active_quote"] = out["is_active_quote"].astype(int)
    return out.sort_values("timestamp").reset_index(drop=True)


def _resample_five(minutes: pd.DataFrame) -> pd.DataFrame:
    indexed = minutes.set_index("timestamp")
    five = (
        indexed.resample("5min", label="left", closed="left")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            active=("is_active_quote", "max"),
            source_bars=("close", "count"),
        )
        .dropna(subset=["open", "high", "low", "close"])
    )
    five["bar_end"] = five.index + pd.Timedelta(minutes=5)
    return five


def _slice(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return frame.loc[(frame.index >= start) & (frame.index < end)]


def _active_high_low(frame: pd.DataFrame) -> tuple[float, float]:
    active = frame[frame["is_active_quote"] > 0]
    if active.empty:
        return math.nan, math.nan
    return float(active["high"].max()), float(active["low"].min())


def _prior_active_day_levels(
    minutes: pd.DataFrame,
    day: pd.Timestamp,
    *,
    cash_only: bool,
) -> tuple[float, float]:
    for distance in range(1, 9):
        candidate = pd.Timestamp(day) - pd.DateOffset(days=distance)
        if cash_only:
            start = _local_timestamp(candidate, 9, 30)
            end = _local_timestamp(candidate, 16, 0)
        else:
            start = _local_timestamp(candidate, 0, 0)
            end = start + pd.DateOffset(days=1)
        high, low = _active_high_low(_slice(minutes, start, end))
        if np.isfinite(high) and np.isfinite(low):
            return high, low
    return math.nan, math.nan


def _prior_week_levels(
    minutes: pd.DataFrame,
    day: pd.Timestamp,
) -> tuple[float, float]:
    monday = pd.Timestamp(day).normalize() - pd.Timedelta(days=day.weekday())
    start = monday - pd.Timedelta(days=7)
    return _active_high_low(_slice(minutes, start, monday))


def _reference_bounds(
    day: pd.Timestamp,
    spec: SessionSpec,
) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    reference_day = day - pd.DateOffset(days=1) if spec.reference_start_previous_day else day
    reference_start = _local_timestamp(
        reference_day,
        spec.reference_start_hour,
        spec.reference_start_minute,
    )
    reference_end = _local_timestamp(
        day,
        spec.reference_end_hour,
        spec.reference_end_minute,
    )
    window_start = _local_timestamp(
        day,
        spec.window_start_hour,
        spec.window_start_minute,
    )
    window_end = _local_timestamp(
        day,
        spec.window_end_hour,
        spec.window_end_minute,
    )
    return reference_start, reference_end, window_start, window_end


def _range_percentile(value: float, history: list[float]) -> float:
    sample = np.asarray(history[-ROLLING_RANGE_LOOKBACK:], dtype=float)
    sample = sample[np.isfinite(sample)]
    if len(sample) < MINIMUM_RANGE_HISTORY:
        return math.nan
    below = float((sample < value).sum())
    equal = float((sample == value).sum())
    return (below + 0.5 * equal) / len(sample)


def _compression_bucket(percentile: float) -> str:
    if not np.isfinite(percentile):
        return "WARMUP"
    if percentile <= 1.0 / 3.0:
        return "COMPRESSED"
    if percentile >= 2.0 / 3.0:
        return "EXPANDED"
    return "NORMAL"


def _outside_close(row: pd.Series, side: str, high: float, low: float) -> bool:
    if side == "UP":
        return float(row["close"]) > high
    if side == "DOWN":
        return float(row["close"]) < low
    raise ValueError(f"unsupported side: {side}")


def _inside_close(row: pd.Series, side: str, high: float, low: float) -> bool:
    if side == "UP":
        return float(row["close"]) <= high
    if side == "DOWN":
        return float(row["close"]) >= low
    raise ValueError(f"unsupported side: {side}")


def detect_state(window_bars: pd.DataFrame, high: float, low: float) -> StateDetection | None:
    """Classify the first boundary breach using only the frozen causal horizon."""

    if window_bars.empty:
        return None
    bars = window_bars.reset_index(drop=False)
    first_index: int | None = None
    first_side: str | None = None
    for index, row in bars.iterrows():
        upper = float(row["high"]) > high
        lower = float(row["low"]) < low
        if not upper and not lower:
            continue
        first_index = int(index)
        if upper and lower:
            first_side = "DOUBLE"
        elif upper:
            first_side = "UP"
        else:
            first_side = "DOWN"
        break
    if first_index is None or first_side is None:
        return None
    if first_side == "DOUBLE":
        return StateDetection(
            first_index=first_index,
            first_side=first_side,
            state="TWO_SIDED",
            detection_index=first_index,
            reclaim_index=None,
            opposite_index=first_index,
            outside_close_count=0,
            inside_hold_count=0,
        )

    decision_end = min(first_index + 2, len(bars) - 1)
    decision = bars.iloc[first_index : decision_end + 1]
    outside = [
        _outside_close(row, first_side, high, low)
        for _, row in decision.iterrows()
    ]
    acceptance_index: int | None = None
    for position in range(1, len(outside)):
        if outside[position - 1] and outside[position]:
            acceptance_index = int(decision.index[position])
            break

    reclaim_index: int | None = None
    rejection_index: int | None = None
    for index, row in decision.iterrows():
        if not _inside_close(row, first_side, high, low):
            continue
        reclaim_index = int(index)
        hold = bars.iloc[reclaim_index + 1 : reclaim_index + 3]
        if len(hold) == 2 and all(
            _inside_close(candidate, first_side, high, low)
            for _, candidate in hold.iterrows()
        ):
            rejection_index = reclaim_index + 2
        break

    candidates = [
        index
        for index in (acceptance_index, rejection_index)
        if index is not None
    ]
    detection_index = min(candidates) if candidates else decision_end
    if first_side == "UP":
        opposite = bars.iloc[first_index : detection_index + 1]
        opposite = opposite[opposite["low"] < low]
    else:
        opposite = bars.iloc[first_index : detection_index + 1]
        opposite = opposite[opposite["high"] > high]
    opposite_index = int(opposite.index[0]) if not opposite.empty else None

    if opposite_index is not None and opposite_index <= detection_index:
        state = "TWO_SIDED"
        detection_index = opposite_index
    elif rejection_index is not None and (
        acceptance_index is None or rejection_index < acceptance_index
    ):
        state = "REJECTION"
        detection_index = rejection_index
    elif acceptance_index is not None:
        state = "ACCEPTANCE"
        detection_index = acceptance_index
    else:
        state = "UNRESOLVED"

    outside_count = sum(
        _outside_close(row, first_side, high, low)
        for _, row in bars.iloc[first_index : detection_index + 1].iterrows()
    )
    inside_hold_count = 0
    if reclaim_index is not None:
        for _, row in bars.iloc[reclaim_index : detection_index + 1].iterrows():
            if not _inside_close(row, first_side, high, low):
                break
            inside_hold_count += 1
    return StateDetection(
        first_index=first_index,
        first_side=first_side,
        state=state,
        detection_index=detection_index,
        reclaim_index=reclaim_index,
        opposite_index=opposite_index,
        outside_close_count=int(outside_count),
        inside_hold_count=int(inside_hold_count),
    )


def _retest_descriptors(
    bars: pd.DataFrame,
    detection: StateDetection,
    high: float,
    low: float,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "retest_touch": False,
        "retest_hold": False,
        "retest_resume": False,
        "retest_detection_timestamp": pd.NaT,
    }
    if detection.state != "ACCEPTANCE" or detection.first_side == "DOUBLE":
        return result
    future = bars.iloc[detection.detection_index + 1 : detection.detection_index + 7]
    for relative_index, row in future.iterrows():
        touch = (
            float(row["low"]) <= high
            if detection.first_side == "UP"
            else float(row["high"]) >= low
        )
        if not touch:
            continue
        result["retest_touch"] = True
        hold = _outside_close(row, detection.first_side, high, low)
        if not hold:
            return result
        result["retest_hold"] = True
        resume = bars.iloc[relative_index + 1 : relative_index + 3]
        for _, candidate in resume.iterrows():
            if detection.first_side == "UP":
                resumed = (
                    float(candidate["high"]) > float(row["high"])
                    and float(candidate["close"]) > high
                )
            else:
                resumed = (
                    float(candidate["low"]) < float(row["low"])
                    and float(candidate["close"]) < low
                )
            if resumed:
                result["retest_resume"] = True
                result["retest_detection_timestamp"] = pd.Timestamp(
                    candidate["bar_end"]
                )
                return result
        return result
    return result


def _external_confluence(
    side: str,
    breach_row: pd.Series,
    high: float,
    low: float,
    levels: dict[str, float],
) -> tuple[int, str]:
    crossed: list[str] = []
    if side == "UP":
        for name in ("prior_day_high", "prior_cash_high", "prior_week_high"):
            level = levels[name]
            if np.isfinite(level) and level >= high and float(breach_row["high"]) >= level:
                crossed.append(name)
    elif side == "DOWN":
        for name in ("prior_day_low", "prior_cash_low", "prior_week_low"):
            level = levels[name]
            if np.isfinite(level) and level <= low and float(breach_row["low"]) <= level:
                crossed.append(name)
    return len(crossed), ",".join(crossed)


def _forward_metrics(
    minutes: pd.DataFrame,
    detection_time: pd.Timestamp,
    window_end: pd.Timestamp,
    direction: int,
    reference_high: float,
    reference_low: float,
    state: str,
) -> dict[str, Any]:
    blank: dict[str, Any] = {
        "anchor_timestamp": pd.NaT,
        "anchor_price": math.nan,
        "anchor_active": False,
        "midpoint_hit": None,
        "projection_hit": None,
        "opposite_boundary_hit": None,
    }
    for horizon in (5, 15, 30, 60):
        blank[f"return_{horizon}m_range_fraction"] = math.nan
        blank[f"mfe_{horizon}m_range_fraction"] = math.nan
        blank[f"mae_{horizon}m_range_fraction"] = math.nan
    blank["return_session_range_fraction"] = math.nan
    blank["mfe_session_range_fraction"] = math.nan
    blank["mae_session_range_fraction"] = math.nan
    if state not in {"ACCEPTANCE", "REJECTION"} or direction not in {-1, 1}:
        return blank
    reference_range = reference_high - reference_low
    anchor_rows = minutes.loc[minutes.index >= detection_time].head(1)
    if anchor_rows.empty or anchor_rows.index[0] > window_end:
        return blank
    anchor_timestamp = pd.Timestamp(anchor_rows.index[0])
    anchor_price = float(anchor_rows.iloc[0]["open"])
    blank["anchor_timestamp"] = anchor_timestamp
    blank["anchor_price"] = anchor_price
    blank["anchor_active"] = bool(anchor_rows.iloc[0]["is_active_quote"] > 0)
    if not blank["anchor_active"]:
        return blank
    path = minutes.loc[
        (minutes.index >= anchor_timestamp)
        & (minutes.index < window_end)
        & (minutes["is_active_quote"] > 0)
    ]
    if path.empty:
        return blank

    def metrics(subset: pd.DataFrame) -> tuple[float, float, float]:
        last = float(subset.iloc[-1]["close"])
        signed_return = direction * (last - anchor_price) / reference_range
        if direction > 0:
            mfe = (float(subset["high"].max()) - anchor_price) / reference_range
            mae = (anchor_price - float(subset["low"].min())) / reference_range
        else:
            mfe = (anchor_price - float(subset["low"].min())) / reference_range
            mae = (float(subset["high"].max()) - anchor_price) / reference_range
        return signed_return, mfe, mae

    for horizon in (5, 15, 30, 60):
        horizon_end = min(
            anchor_timestamp + pd.Timedelta(minutes=horizon),
            window_end,
        )
        subset = path.loc[path.index < horizon_end]
        if subset.empty:
            continue
        signed_return, mfe, mae = metrics(subset)
        blank[f"return_{horizon}m_range_fraction"] = signed_return
        blank[f"mfe_{horizon}m_range_fraction"] = mfe
        blank[f"mae_{horizon}m_range_fraction"] = mae
    signed_return, mfe, mae = metrics(path)
    blank["return_session_range_fraction"] = signed_return
    blank["mfe_session_range_fraction"] = mfe
    blank["mae_session_range_fraction"] = mae
    midpoint = (reference_high + reference_low) / 2.0
    projection = (
        reference_high + reference_range
        if direction > 0
        else reference_low - reference_range
    )
    if state == "REJECTION":
        blank["midpoint_hit"] = bool(
            (path["high"] >= midpoint).any()
            if direction > 0
            else (path["low"] <= midpoint).any()
        )
        blank["opposite_boundary_hit"] = bool(
            (path["high"] >= reference_high).any()
            if direction > 0
            else (path["low"] <= reference_low).any()
        )
    if state == "ACCEPTANCE":
        blank["projection_hit"] = bool(
            (path["high"] >= projection).any()
            if direction > 0
            else (path["low"] <= projection).any()
        )
    return blank


def _event_id(instrument: str, day: pd.Timestamp, session: str) -> str:
    payload = f"{instrument}|{day.strftime('%Y-%m-%d')}|{session}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_auction_state_ledger(
    instrument: str,
    one_minute: pd.DataFrame,
    *,
    development_start: pd.Timestamp = DEVELOPMENT_START,
    development_end: pd.Timestamp = DEVELOPMENT_END,
) -> pd.DataFrame:
    """Build one mechanism-level diagnostic row per first session boundary breach."""

    if not instrument:
        raise ValueError("instrument must be non-empty")
    minutes = _validate_minutes(one_minute).set_index("timestamp")
    five = _resample_five(minutes.reset_index())
    histories = {spec.name: [] for spec in SESSION_SPECS}
    rows: list[dict[str, Any]] = []
    first_day = max(
        minutes.index.min().normalize() + pd.DateOffset(days=1),
        development_start - pd.DateOffset(days=100),
    )
    last_day = min(minutes.index.max().normalize(), development_end)
    for day in pd.date_range(first_day, last_day, freq="B"):
        prior_day_high, prior_day_low = _prior_active_day_levels(
            minutes,
            day,
            cash_only=False,
        )
        prior_cash_high, prior_cash_low = _prior_active_day_levels(
            minutes,
            day,
            cash_only=True,
        )
        prior_week_high, prior_week_low = _prior_week_levels(minutes, day)
        levels = {
            "prior_day_high": prior_day_high,
            "prior_day_low": prior_day_low,
            "prior_cash_high": prior_cash_high,
            "prior_cash_low": prior_cash_low,
            "prior_week_high": prior_week_high,
            "prior_week_low": prior_week_low,
        }
        for spec in SESSION_SPECS:
            reference_start, reference_end, window_start, window_end = _reference_bounds(
                day,
                spec,
            )
            reference = _slice(minutes, reference_start, reference_end)
            reference = reference[reference["is_active_quote"] > 0]
            if reference.empty:
                continue
            reference_high = float(reference["high"].max())
            reference_low = float(reference["low"].min())
            reference_range = reference_high - reference_low
            if not np.isfinite(reference_range) or reference_range <= 0:
                continue
            percentile = _range_percentile(reference_range, histories[spec.name])
            histories[spec.name].append(reference_range)
            if day < development_start or day >= development_end:
                continue
            window = _slice(five, window_start, window_end)
            detection = detect_state(window, reference_high, reference_low)
            if detection is None:
                continue
            bars = window.reset_index(drop=False)
            breach_row = bars.iloc[detection.first_index]
            detection_row = bars.iloc[detection.detection_index]
            detection_time = pd.Timestamp(detection_row["bar_end"])
            side = detection.first_side
            breach_direction = 1 if side == "UP" else -1 if side == "DOWN" else 0
            if detection.state == "ACCEPTANCE":
                hypothesis_direction = breach_direction
            elif detection.state == "REJECTION":
                hypothesis_direction = -breach_direction
            else:
                hypothesis_direction = 0
            confluence_count, confluence_levels = _external_confluence(
                side,
                breach_row,
                reference_high,
                reference_low,
                levels,
            )
            if side == "UP":
                breach_depth = (float(breach_row["high"]) - reference_high) / reference_range
            elif side == "DOWN":
                breach_depth = (reference_low - float(breach_row["low"])) / reference_range
            else:
                breach_depth = max(
                    (float(breach_row["high"]) - reference_high) / reference_range,
                    (reference_low - float(breach_row["low"])) / reference_range,
                )
            opposite_later = False
            if side == "UP":
                later = bars.iloc[detection.detection_index + 1 :]
                opposite_later = bool((later["low"] < reference_low).any())
            elif side == "DOWN":
                later = bars.iloc[detection.detection_index + 1 :]
                opposite_later = bool((later["high"] > reference_high).any())
            retest = _retest_descriptors(bars, detection, reference_high, reference_low)
            row: dict[str, Any] = {
                "event_id": _event_id(instrument, day, spec.name),
                "instrument": instrument,
                "trade_date": day.strftime("%Y-%m-%d"),
                "session": spec.name,
                "reference_start": reference_start,
                "reference_end": reference_end,
                "window_start": window_start,
                "window_end": window_end,
                "reference_high": reference_high,
                "reference_low": reference_low,
                "reference_range": reference_range,
                "range_percentile_60": percentile,
                "compression_bucket": _compression_bucket(percentile),
                **levels,
                "first_side": side,
                "state": detection.state,
                "breach_timestamp": pd.Timestamp(breach_row["timestamp"]),
                "state_detection_timestamp": detection_time,
                "minutes_to_detection": int(
                    (detection_time - pd.Timestamp(breach_row["timestamp"]))
                    .total_seconds()
                    // 60
                ),
                "hypothesis_direction": hypothesis_direction,
                "breach_depth_range_fraction": breach_depth,
                "external_confluence_count": confluence_count,
                "external_confluence_levels": confluence_levels,
                "external_confluence": confluence_count > 0,
                "outside_close_count": detection.outside_close_count,
                "inside_hold_count": detection.inside_hold_count,
                "opposite_side_before_confirmation": detection.opposite_index is not None,
                "opposite_side_after_confirmation": opposite_later,
                **retest,
            }
            row.update(
                _forward_metrics(
                    minutes,
                    detection_time,
                    window_end,
                    hypothesis_direction,
                    reference_high,
                    reference_low,
                    detection.state,
                )
            )
            rows.append(row)
    ledger = pd.DataFrame(rows)
    if ledger.empty:
        return ledger
    if bool(ledger["event_id"].duplicated(keep=False).any()):
        raise ValueError("auction-state ledger contains duplicate event IDs")
    return ledger.sort_values(["trade_date", "instrument", "session"]).reset_index(
        drop=True
    )
