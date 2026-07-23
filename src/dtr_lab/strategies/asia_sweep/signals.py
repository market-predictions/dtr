from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from .integrity import IntervalIntegrity, audit_minute_interval
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
    return day.normalize() + pd.Timedelta(hours=hour, minutes=minute)


def _asia_bounds(
    trade_date: pd.Timestamp,
    cfg: AsiaSweepConfig,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    end = _timestamp(trade_date, cfg.asia_end_hour, cfg.asia_end_minute)
    start = _timestamp(
        trade_date - pd.Timedelta(days=1),
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
        end += pd.Timedelta(days=1)
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
    *,
    status: str,
    rejection_reason: str | None,
) -> AsiaSweepEvent:
    return AsiaSweepEvent(
        instrument=instrument,
        trade_date=trade_date.normalize(),
        execution_window=window.name,
        variant=cfg.variant.value,
        status=status,
        rejection_reason=rejection_reason,
        asia_start=asia_start,
        asia_end=asia_end,
        asia_high=asia_high,
        asia_low=asia_low,
        asia_range_points=asia_high - asia_low,
        asia_expected_minutes=asia_integrity.expected_minutes,
        asia_observed_minutes=asia_integrity.observed_minutes,
        asia_missing_minutes=asia_integrity.missing_minutes,
        asia_complete=asia_integrity.complete,
        execution_expected_minutes=execution_integrity.expected_minutes,
        execution_observed_minutes=execution_integrity.observed_minutes,
        execution_missing_minutes=execution_integrity.missing_minutes,
        execution_window_complete=execution_integrity.complete,
    )


def _attach_pre_signal_integrity(
    event: AsiaSweepEvent,
    one_minute: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> AsiaSweepEvent:
    integrity = audit_minute_interval(one_minute, start, end)
    updated = replace(
        event,
        pre_signal_expected_minutes=integrity.expected_minutes,
        pre_signal_observed_minutes=integrity.observed_minutes,
        pre_signal_missing_minutes=integrity.missing_minutes,
        pre_signal_path_complete=integrity.complete,
    )
    if integrity.complete:
        return updated
    return replace(
        updated,
        status="INELIGIBLE",
        rejection_reason="incomplete_pre_signal_path",
    )


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
            status="INELIGIBLE",
            rejection_reason="incomplete_asia_range",
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
        status="INELIGIBLE",
        rejection_reason=None,
    )
    if wb.empty:
        reason = (
            "incomplete_execution_window"
            if not execution_integrity.complete
            else "missing_execution_bars"
        )
        return replace(base, rejection_reason=reason)

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
            )
        if lower:
            sweep_pos, direction = int(pos), 1
            break
        if upper:
            sweep_pos, direction = int(pos), -1
            break

    if sweep_pos is None:
        if not execution_integrity.complete:
            return replace(base, rejection_reason="incomplete_execution_window")
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
            )
            if event.status == "INELIGIBLE":
                return event
            return replace(event, rejection_reason="no_failed_retest")
        event = replace(event, failed_retest_present=True)

    entry_row = wb.iloc[int(entry_pos)]
    audit_start = _variant_audit_start(cfg, start, entry_row)
    event = _attach_pre_signal_integrity(
        event,
        one_minute,
        audit_start,
        _bar_end(entry_row),
    )
    if event.status == "INELIGIBLE":
        return event

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
        entry_timestamp=_bar_end(entry_row),
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
    first = one["timestamp"].min().normalize() + pd.Timedelta(days=1)
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
