from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from .integrity import (
    IntervalActivity,
    IntervalIntegrity,
    audit_activity_interval,
    audit_minute_interval,
)
from .model import AsiaSweepConfig, AsiaSweepEvent, AsiaSweepVariant, ExecutionWindow

_REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close"}


def _validate_bars(frame: pd.DataFrame, *, name: str) -> pd.DataFrame:
    missing = _REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing required columns: {sorted(missing)}")
    out = frame.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    duplicate_mask = out["timestamp"].duplicated(keep=False)
    if bool(duplicate_mask.any()):
        duplicate_values = out.loc[duplicate_mask, "timestamp"].astype(str).unique()
        preview = ", ".join(duplicate_values[:3])
        raise ValueError(f"{name} has duplicate timestamps: {preview}")
    out = out.sort_values("timestamp").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"{name} is empty")
    return out


def _timestamp(day: pd.Timestamp, hour: int, minute: int) -> pd.Timestamp:
    """Construct a local wall-clock timestamp without elapsed-time DST drift."""

    day = pd.Timestamp(day)
    naive = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=hour,
        minute=minute,
    )
    if day.tz is None:
        return naive
    return naive.tz_localize(day.tz, ambiguous="raise", nonexistent="raise")


def _asia_bounds(
    trade_date: pd.Timestamp,
    cfg: AsiaSweepConfig,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    end = _timestamp(trade_date, cfg.asia_end_hour, cfg.asia_end_minute)
    previous_date = pd.Timestamp(trade_date) - pd.DateOffset(days=1)
    start = _timestamp(
        previous_date,
        cfg.asia_start_hour,
        cfg.asia_start_minute,
    )
    if start >= end:
        raise ValueError("Asia range start must precede end")
    return start, end


def _window_bounds(
    trade_date: pd.Timestamp,
    window: ExecutionWindow,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = _timestamp(trade_date, window.start_hour, window.start_minute)
    end = _timestamp(trade_date, window.end_hour, window.end_minute)
    if end <= start:
        next_date = pd.Timestamp(trade_date) + pd.DateOffset(days=1)
        end = _timestamp(next_date, window.end_hour, window.end_minute)
    return start, end


def _bar_end(row: pd.Series) -> pd.Timestamp:
    if "bar_end" in row.index and pd.notna(row["bar_end"]):
        return pd.Timestamp(row["bar_end"])
    return pd.Timestamp(row["timestamp"]) + pd.Timedelta(minutes=5)


def _morphology(row: pd.Series, direction: int) -> tuple[float, float]:
    high = float(row["high"])
    low = float(row["low"])
    open_ = float(row["open"])
    close = float(row["close"])
    span = high - low
    if span <= 0:
        return 0.0, 0.5
    if direction > 0:
        wick = max(0.0, min(open_, close) - low) / span
        clv = (close - low) / span
    else:
        wick = max(0.0, high - max(open_, close)) / span
        clv = (high - close) / span
    return float(wick), float(clv)


def _audit_activity(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cfg: AsiaSweepConfig,
) -> IntervalActivity | None:
    if cfg.activity_column is None:
        return None
    if cfg.maximum_consecutive_inactive_minutes is None:
        raise ValueError("activity configuration is incomplete")
    return audit_activity_interval(
        frame,
        start,
        end,
        activity_column=cfg.activity_column,
        minimum_active_minutes=cfg.minimum_active_minutes,
        maximum_consecutive_inactive_minutes=cfg.maximum_consecutive_inactive_minutes,
    )


def _grid_failure_reason(cfg: AsiaSweepConfig, legacy_reason: str) -> str:
    return "missing_minute_grid" if cfg.activity_column is not None else legacy_reason


def _base_event(
    instrument: str,
    trade_date: pd.Timestamp,
    window: ExecutionWindow,
    cfg: AsiaSweepConfig,
    asia_start: pd.Timestamp,
    asia_end: pd.Timestamp,
    asia_high: float,
    asia_low: float,
    asia_integrity: IntervalIntegrity,
    execution_integrity: IntervalIntegrity,
    asia_activity: IntervalActivity | None,
    execution_activity: IntervalActivity | None,
    *,
    status: str,
    rejection_reason: str | None,
    integrity_failure_scope: str | None = None,
) -> AsiaSweepEvent:
    return AsiaSweepEvent(
        instrument=instrument,
        trade_date=trade_date.normalize(),
        execution_window=window.name,
        variant=cfg.variant.value,
        status=status,
        rejection_reason=rejection_reason,
        integrity_failure_scope=integrity_failure_scope,
        asia_start=asia_start,
        asia_end=asia_end,
        asia_high=asia_high,
        asia_low=asia_low,
        asia_range_points=asia_high - asia_low,
        asia_expected_minutes=asia_integrity.expected_minutes,
        asia_observed_minutes=asia_integrity.observed_minutes,
        asia_missing_minutes=asia_integrity.missing_minutes,
        asia_complete=asia_integrity.complete,
        asia_active_minutes=(asia_activity.active_minutes if asia_activity else None),
        asia_inactive_minutes=(asia_activity.inactive_minutes if asia_activity else None),
        asia_max_inactive_run=(
            asia_activity.maximum_consecutive_inactive_minutes if asia_activity else None
        ),
        asia_activity_eligible=(asia_activity.eligible if asia_activity else None),
        execution_expected_minutes=execution_integrity.expected_minutes,
        execution_observed_minutes=execution_integrity.observed_minutes,
        execution_missing_minutes=execution_integrity.missing_minutes,
        execution_window_complete=execution_integrity.complete,
        execution_active_minutes=(
            execution_activity.active_minutes if execution_activity else None
        ),
        execution_inactive_minutes=(
            execution_activity.inactive_minutes if execution_activity else None
        ),
        execution_max_inactive_run=(
            execution_activity.maximum_consecutive_inactive_minutes
            if execution_activity
            else None
        ),
        execution_activity_eligible=(
            execution_activity.eligible if execution_activity else None
        ),
    )


def _attach_pre_signal_integrity(
    event: AsiaSweepEvent,
    one_minute: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cfg: AsiaSweepConfig,
) -> AsiaSweepEvent:
    integrity = audit_minute_interval(one_minute, start, end)
    activity = _audit_activity(one_minute, start, end, cfg)
    updated = replace(
        event,
        pre_signal_expected_minutes=integrity.expected_minutes,
        pre_signal_observed_minutes=integrity.observed_minutes,
        pre_signal_missing_minutes=integrity.missing_minutes,
        pre_signal_path_complete=integrity.complete,
        pre_signal_active_minutes=(activity.active_minutes if activity else None),
        pre_signal_inactive_minutes=(activity.inactive_minutes if activity else None),
        pre_signal_max_inactive_run=(
            activity.maximum_consecutive_inactive_minutes if activity else None
        ),
        pre_signal_activity_eligible=(activity.eligible if activity else None),
    )
    if not integrity.complete:
        return replace(
            updated,
            status="INELIGIBLE",
            rejection_reason=_grid_failure_reason(cfg, "incomplete_pre_signal_path"),
            integrity_failure_scope="pre_signal_path",
        )
    if activity is not None and not activity.eligible:
        return replace(
            updated,
            status="INELIGIBLE",
            rejection_reason=activity.failure_reason,
            integrity_failure_scope="pre_signal_path",
        )
    return updated


def _find_displacement(
    window_bars: pd.DataFrame,
    sweep_position: int,
    direction: int,
    sweep_midpoint: float,
    asia_high: float,
    asia_low: float,
    cfg: AsiaSweepConfig,
) -> tuple[int | None, int | None]:
    final = min(len(window_bars), sweep_position + cfg.displacement_max_bars + 1)
    for pos in range(sweep_position + 1, final):
        row = window_bars.iloc[pos]
        body_reference = float(row["_causal_body_median"])
        if not np.isfinite(body_reference) or body_reference <= 0:
            continue
        body = abs(float(row["close"]) - float(row["open"]))
        directional = (
            float(row["close"]) > float(row["open"])
            if direction > 0
            else float(row["close"]) < float(row["open"])
        )
        midpoint_pass = (
            float(row["close"]) > sweep_midpoint
            if direction > 0
            else float(row["close"]) < sweep_midpoint
        )
        inside = (
            float(row["close"]) >= asia_low
            if direction > 0
            else float(row["close"]) <= asia_high
        )
        qualifies = (
            directional
            and midpoint_pass
            and inside
            and body >= cfg.displacement_body_mult * body_reference
        )
        if qualifies:
            return pos, pos - sweep_position
    return None, None


def _find_failed_retest(
    window_bars: pd.DataFrame,
    sweep_position: int,
    direction: int,
    sweep_extreme: float,
    asia_level: float,
    cfg: AsiaSweepConfig,
) -> int | None:
    """Causal one-right-bar swing, retest, then break state machine."""

    end = min(len(window_bars), sweep_position + cfg.failed_retest_max_bars + 1)
    reaction_level: float | None = None
    reaction_confirmed_at: int | None = None
    retest_seen = False
    band = cfg.retest_band_ticks * cfg.tick_size

    for pos in range(sweep_position + 2, end):
        candidate = pos - 1
        prev = window_bars.iloc[candidate - 1]
        mid = window_bars.iloc[candidate]
        nxt = window_bars.iloc[pos]
        if reaction_level is None:
            if direction > 0:
                is_pivot = (
                    float(mid["high"]) > float(prev["high"])
                    and float(mid["high"]) > float(nxt["high"])
                )
                if is_pivot:
                    reaction_level = float(mid["high"])
                    reaction_confirmed_at = pos
            else:
                is_pivot = (
                    float(mid["low"]) < float(prev["low"])
                    and float(mid["low"]) < float(nxt["low"])
                )
                if is_pivot:
                    reaction_level = float(mid["low"])
                    reaction_confirmed_at = pos
            continue

        if reaction_confirmed_at is None or pos <= reaction_confirmed_at:
            continue

        row = window_bars.iloc[pos]
        if not retest_seen:
            if direction > 0:
                retest_seen = (
                    float(row["low"]) <= asia_level + band
                    and float(row["low"]) > sweep_extreme
                )
            else:
                retest_seen = (
                    float(row["high"]) >= asia_level - band
                    and float(row["high"]) < sweep_extreme
                )
            continue

        broke = (
            float(row["close"]) > reaction_level
            if direction > 0
            else float(row["close"]) < reaction_level
        )
        if broke:
            return pos
    return None


def _variant_audit_start(
    cfg: AsiaSweepConfig,
    window_start: pd.Timestamp,
    decision_row: pd.Series,
) -> pd.Timestamp:
    if cfg.variant != AsiaSweepVariant.DISPLACEMENT:
        return window_start
    reference_start = pd.Timestamp(decision_row["timestamp"]) - pd.Timedelta(
        minutes=5 * cfg.displacement_median_length
    )
    return min(window_start, reference_start)


def _detect_window_event(
    instrument: str,
    trade_date: pd.Timestamp,
    window: ExecutionWindow,
    one_minute: pd.DataFrame,
    bars_5m: pd.DataFrame,
    cfg: AsiaSweepConfig,
) -> AsiaSweepEvent:
    asia_start, asia_end = _asia_bounds(trade_date, cfg)
    start, end = _window_bounds(trade_date, window)
    asia_integrity = audit_minute_interval(one_minute, asia_start, asia_end)
    execution_integrity = audit_minute_interval(one_minute, start, end)
    asia_activity = _audit_activity(one_minute, asia_start, asia_end, cfg)
    execution_activity = _audit_activity(one_minute, start, end, cfg)

    if not asia_integrity.complete:
        return _base_event(
            instrument,
            trade_date,
            window,
            cfg,
            asia_start,
            asia_end,
            np.nan,
            np.nan,
            asia_integrity,
            execution_integrity,
            asia_activity,
            execution_activity,
            status="INELIGIBLE",
            rejection_reason=_grid_failure_reason(cfg, "incomplete_asia_range"),
            integrity_failure_scope="asia_range",
        )
    if asia_activity is not None and not asia_activity.eligible:
        return _base_event(
            instrument,
            trade_date,
            window,
            cfg,
            asia_start,
            asia_end,
            np.nan,
            np.nan,
            asia_integrity,
            execution_integrity,
            asia_activity,
            execution_activity,
            status="INELIGIBLE",
            rejection_reason=asia_activity.failure_reason,
            integrity_failure_scope="asia_range",
        )

    asia = one_minute[
        (one_minute["timestamp"] >= asia_start)
        & (one_minute["timestamp"] < asia_end)
    ]
    asia_high = float(asia["high"].max())
    asia_low = float(asia["low"].min())
    if not np.isfinite(asia_high) or not np.isfinite(asia_low) or asia_high <= asia_low:
        return _base_event(
            instrument,
            trade_date,
            window,
            cfg,
            asia_start,
            asia_end,
            asia_high,
            asia_low,
            asia_integrity,
            execution_integrity,
            asia_activity,
            execution_activity,
            status="INELIGIBLE",
            rejection_reason="invalid_asia_range",
        )

    bars_with_reference = bars_5m.copy()
    bodies = (bars_with_reference["close"] - bars_with_reference["open"]).abs()
    bars_with_reference["_causal_body_median"] = bodies.shift(1).rolling(
        cfg.displacement_median_length,
        min_periods=cfg.displacement_median_length,
    ).median()
    wb = bars_with_reference[
        (bars_with_reference["timestamp"] >= start)
        & (bars_with_reference["timestamp"] < end)
    ].copy().reset_index(drop=True)

    base = _base_event(
        instrument,
        trade_date,
        window,
        cfg,
        asia_start,
        asia_end,
        asia_high,
        asia_low,
        asia_integrity,
        execution_integrity,
        asia_activity,
        execution_activity,
        status="INELIGIBLE",
        rejection_reason=None,
    )
    if wb.empty:
        if not execution_integrity.complete:
            reason = _grid_failure_reason(cfg, "incomplete_execution_window")
            return replace(
                base,
                rejection_reason=reason,
                integrity_failure_scope="execution_window",
            )
        if execution_activity is not None and not execution_activity.eligible:
            return replace(
                base,
                rejection_reason=execution_activity.failure_reason,
                integrity_failure_scope="execution_window",
            )
        return replace(base, rejection_reason="missing_execution_bars")

    min_depth = cfg.min_sweep_ticks * cfg.tick_size
    sweep_pos: int | None = None
    direction = 0
    for pos, row in wb.iterrows():
        upper = float(row["high"]) - asia_high >= min_depth
        lower = asia_low - float(row["low"]) >= min_depth
        if upper and lower:
            event = replace(
                base,
                status="REJECTED",
                rejection_reason="ambiguous_double_sweep",
                first_sweep_timestamp=pd.Timestamp(row["timestamp"]),
            )
            return _attach_pre_signal_integrity(
                event,
                one_minute,
                start,
                _bar_end(row),
                cfg,
            )
        if lower:
            sweep_pos, direction = int(pos), 1
            break
        if upper:
            sweep_pos, direction = int(pos), -1
            break

    if sweep_pos is None:
        if not execution_integrity.complete:
            return replace(
                base,
                rejection_reason=_grid_failure_reason(
                    cfg,
                    "incomplete_execution_window",
                ),
                integrity_failure_scope="execution_window",
            )
        if execution_activity is not None and not execution_activity.eligible:
            return replace(
                base,
                rejection_reason=execution_activity.failure_reason,
                integrity_failure_scope="execution_window",
            )
        return replace(base, status="NO_SWEEP", rejection_reason=None)

    row = wb.iloc[sweep_pos]
    sweep_extreme = float(row["low"] if direction > 0 else row["high"])
    depth = asia_low - sweep_extreme if direction > 0 else sweep_extreme - asia_high
    reclaim = (
        float(row["close"]) >= asia_low
        if direction > 0
        else float(row["close"]) <= asia_high
    )
    wick_ratio, clv = _morphology(row, direction)
    event = replace(
        base,
        status="REJECTED",
        swept_side="LOW" if direction > 0 else "HIGH",
        direction=direction,
        first_sweep_timestamp=pd.Timestamp(row["timestamp"]),
        sweep_extreme=sweep_extreme,
        sweep_depth_points=depth,
        sweep_depth_ticks=depth / cfg.tick_size,
        sweep_depth_range_fraction=depth / (asia_high - asia_low),
        sweep_bar_open=float(row["open"]),
        sweep_bar_high=float(row["high"]),
        sweep_bar_low=float(row["low"]),
        sweep_bar_close=float(row["close"]),
        wick_ratio=wick_ratio,
        close_location_value=clv,
        closed_back_inside=reclaim,
        reclaim_delay_bars=0 if reclaim else None,
    )
    event = _attach_pre_signal_integrity(
        event,
        one_minute,
        start,
        _bar_end(row),
        cfg,
    )
    if event.status == "INELIGIBLE":
        return event
    if not reclaim:
        return replace(event, rejection_reason="no_same_bar_reclaim")

    entry_pos = sweep_pos
    if cfg.variant == AsiaSweepVariant.WICK_QUALIFIED:
        if wick_ratio < cfg.wick_ratio_min or clv < cfg.close_location_min:
            return replace(event, rejection_reason="morphology_failed")
    elif cfg.variant == AsiaSweepVariant.DISPLACEMENT:
        midpoint = (float(row["high"]) + float(row["low"])) / 2.0
        entry_pos, delay = _find_displacement(
            wb,
            sweep_pos,
            direction,
            midpoint,
            asia_high,
            asia_low,
            cfg,
        )
        if entry_pos is None:
            deadline = min(
                end,
                _bar_end(row)
                + pd.Timedelta(minutes=5 * cfg.displacement_max_bars),
            )
            audit_start = min(
                start,
                pd.Timestamp(row["timestamp"])
                - pd.Timedelta(minutes=5 * cfg.displacement_median_length),
            )
            event = _attach_pre_signal_integrity(
                event,
                one_minute,
                audit_start,
                deadline,
                cfg,
            )
            if event.status == "INELIGIBLE":
                return event
            return replace(event, rejection_reason="no_displacement")
        event = replace(
            event,
            displacement_present=True,
            displacement_delay_bars=delay,
        )
    elif cfg.variant == AsiaSweepVariant.FAILED_RETEST:
        asia_level = asia_low if direction > 0 else asia_high
        entry_pos = _find_failed_retest(
            wb,
            sweep_pos,
            direction,
            sweep_extreme,
            asia_level,
            cfg,
        )
        if entry_pos is None:
            deadline = min(
                end,
                _bar_end(row)
                + pd.Timedelta(minutes=5 * cfg.failed_retest_max_bars),
            )
            event = _attach_pre_signal_integrity(
                event,
                one_minute,
                start,
                deadline,
                cfg,
            )
            if event.status == "INELIGIBLE":
                return event
            return replace(event, rejection_reason="no_failed_retest")
        event = replace(event, failed_retest_present=True)

    entry_row = wb.iloc[int(entry_pos)]
    entry_timestamp = _bar_end(entry_row)
    audit_start = _variant_audit_start(cfg, start, entry_row)
    event = _attach_pre_signal_integrity(
        event,
        one_minute,
        audit_start,
        entry_timestamp,
        cfg,
    )
    if event.status == "INELIGIBLE":
        return event
    if entry_timestamp >= end:
        return replace(
            event,
            status="REJECTED",
            rejection_reason="entry_at_or_after_window_end",
            entry_timestamp=entry_timestamp,
        )

    entry = float(entry_row["close"])
    stop = (
        sweep_extreme - cfg.stop_buffer_ticks * cfg.tick_size
        if direction > 0
        else sweep_extreme + cfg.stop_buffer_ticks * cfg.tick_size
    )
    risk = entry - stop if direction > 0 else stop - entry
    if risk <= cfg.tick_size:
        return replace(event, rejection_reason="nonpositive_or_too_small_risk")
    target = entry + direction * risk * cfg.target_rr
    return replace(
        event,
        status="SIGNAL",
        rejection_reason=None,
        entry_timestamp=entry_timestamp,
        entry_price_raw=entry,
        stop_price_raw=stop,
        target_price_raw=target,
    )


def build_event_ledger(
    instrument: str,
    one_minute: pd.DataFrame,
    bars_5m: pd.DataFrame,
    cfg: AsiaSweepConfig,
) -> pd.DataFrame:
    """Build one deterministic record per eligible date and execution window.

    This function performs signal research only. It does not call the active DTR
    ``generate_signals`` function and does not simulate P&L.
    """

    one = _validate_bars(one_minute, name="one_minute")
    bars = _validate_bars(bars_5m, name="bars_5m")
    if cfg.activity_column is not None and cfg.activity_column not in one.columns:
        raise ValueError(
            f"one_minute missing activity column: {cfg.activity_column}"
        )
    first = one["timestamp"].min().normalize() + pd.DateOffset(days=1)
    last = one["timestamp"].max().normalize()
    rows: list[dict[str, object]] = []
    for day in pd.date_range(first, last, freq="D"):
        if day.weekday() not in cfg.weekdays:
            continue
        for window in cfg.windows:
            rows.append(
                _detect_window_event(instrument, day, window, one, bars, cfg).as_dict()
            )
    return pd.DataFrame(rows)
