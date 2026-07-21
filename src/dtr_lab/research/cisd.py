from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd

from . import engine as base
from .integrity import (
    _BASE_GENERATE_SIGNALS,
    _BASE_SIMULATE_TRADE,
    _first_unsafe_gap_between,
    _gap_intervals,
    _gap_table,
    _sanitize_sessions,
    prepare_market_arrays,
)

CISDPolicy = Literal[
    "observe",
    "sequence_confirm",
    "last_candle_confirm",
    "sequence_recent_3",
    "sequence_recent_6",
    "sequence_retest",
]

_SIGNAL_CONFIG_FIELDS = (
    "sessions",
    "weekdays",
    "min_sweep_range_pct",
    "min_sweep_ticks",
    "valid_sweep_threshold",
    "ideal_sweep_max_pct",
    "too_deep_sweep_pct",
    "volume_expand_mult",
    "atr_expand_mult",
    "reaction_bars",
    "pivot_len",
    "pivot_min_pct",
    "break_mode",
    "break_buffer_pct",
    "break_atr_frac",
    "impulse_mult",
    "require_impulse",
    "acceptance_bars",
    "entry_mode",
    "retest_band_pct",
    "signal_window_bars",
    "max_bars_from_sweep",
    "trend_filter",
    "er_length",
    "er_max",
    "adx_max",
    "tick_size",
)


@dataclass(frozen=True)
class CISDSequence:
    direction: int
    start_index: int
    end_index: int
    sequence_anchor: float
    last_anchor: float
    length: int
    body_displacement: float
    epoch: int


@dataclass(frozen=True)
class CISDAnnotation:
    sequence_confirmed: bool = False
    last_candle_confirmed: bool = False
    direction: int = 0
    sequence_start_index: int = -1
    sequence_end_index: int = -1
    sequence_confirm_index: int = -1
    last_sequence_start_index: int = -1
    last_sequence_end_index: int = -1
    last_confirm_index: int = -1
    sequence_anchor: float = np.nan
    last_anchor: float = np.nan
    sequence_age_bars: int = -1
    last_age_bars: int = -1
    sequence_length: int = 0
    last_sequence_length: int = 0
    body_displacement: float = np.nan
    body_displacement_atr: float = np.nan
    sequence_anchor_distance_atr: float = np.nan
    minutes_sweep_to_confirm: int = -1
    minutes_confirm_to_entry: int = -1
    sequence_retest: bool = False
    sequence_retest_index: int = -1
    sequence_retest_on_entry_bar: bool = False
    bars_retest_to_entry: int = -1
    epoch: int = -1


@dataclass(frozen=True)
class CISDVariant:
    name: str
    policy: CISDPolicy

    @property
    def max_age_bars(self) -> int | None:
        return {
            "sequence_recent_3": 3,
            "sequence_recent_6": 6,
        }.get(self.policy)


@dataclass(frozen=True)
class PreparedCISD:
    signals: tuple[base.CandidateSignal, ...]
    annotations: tuple[CISDAnnotation, ...]
    sessions: int
    signal_config_signature: tuple[object, ...]


@dataclass
class CISDFunnel:
    sessions: int = 0
    entry_signals: int = 0
    sequence_confirmed: int = 0
    last_candle_confirmed: int = 0
    signals_filtered: int = 0
    skipped_position_open: int = 0
    skipped_unsafe_gap_bridge: int = 0
    trades: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def baseline_variants() -> tuple[CISDVariant, ...]:
    return (
        CISDVariant("CISD_OBSERVE", "observe"),
        CISDVariant("CISD_SEQUENCE_CONFIRM", "sequence_confirm"),
        CISDVariant("CISD_LAST_CANDLE_CONFIRM", "last_candle_confirm"),
        CISDVariant("CISD_SEQUENCE_RECENT_3", "sequence_recent_3"),
        CISDVariant("CISD_SEQUENCE_RECENT_6", "sequence_recent_6"),
        CISDVariant("CISD_SEQUENCE_RETEST", "sequence_retest"),
    )


def _signal_config_signature(cfg: base.StrategyConfig) -> tuple[object, ...]:
    return tuple(getattr(cfg, field) for field in _SIGNAL_CONFIG_FIELDS)


def _epoch_arrays(bars: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    if "state_epoch_end" in bars.columns:
        epoch = bars["state_epoch_end"].to_numpy(dtype=np.int64)
    else:
        epoch = np.zeros(len(bars), dtype=np.int64)
    if "contains_reset_gap" in bars.columns:
        reset = bars["contains_reset_gap"].to_numpy(dtype=bool)
    else:
        reset = np.zeros(len(bars), dtype=bool)
    return epoch, reset


def _is_opposite(direction: int, open_price: float, close_price: float) -> bool:
    if direction == 1:
        return close_price < open_price
    return close_price > open_price


def _crossed(direction: int, close_price: float, anchor: float) -> bool:
    if direction == 1:
        return close_price > anchor
    return close_price < anchor


def _sequences_for_signal(
    bars: pd.DataFrame,
    signal: base.CandidateSignal,
) -> list[CISDSequence]:
    if signal.sweep_index < 0 or signal.entry_index >= len(bars):
        return []
    if signal.sweep_index > signal.entry_index:
        return []

    open_price = bars["open"].to_numpy(float)
    close_price = bars["close"].to_numpy(float)
    epoch, reset = _epoch_arrays(bars)
    signal_epoch = int(epoch[signal.entry_index])
    window = range(signal.sweep_index, signal.entry_index + 1)
    if any(reset[i] or int(epoch[i]) != signal_epoch for i in window):
        return []

    sequences: list[CISDSequence] = []
    i = signal.sweep_index
    while i <= signal.entry_index:
        if not _is_opposite(signal.direction, open_price[i], close_price[i]):
            i += 1
            continue
        start = i
        displacement = 0.0
        while i <= signal.entry_index and _is_opposite(
            signal.direction, open_price[i], close_price[i]
        ):
            displacement += abs(close_price[i] - open_price[i])
            i += 1
        end = i - 1
        sequences.append(
            CISDSequence(
                direction=signal.direction,
                start_index=start,
                end_index=end,
                sequence_anchor=float(open_price[start]),
                last_anchor=float(open_price[end]),
                length=end - start + 1,
                body_displacement=float(displacement),
                epoch=signal_epoch,
            )
        )
    return sequences


def _first_confirmation(
    bars: pd.DataFrame,
    direction: int,
    anchor: float,
    start_index: int,
    end_index: int,
) -> int:
    close_price = bars["close"].to_numpy(float)
    for index in range(start_index, end_index + 1):
        if _crossed(direction, close_price[index], anchor):
            return index
    return -1


def annotate_signal(bars: pd.DataFrame, signal: base.CandidateSignal) -> CISDAnnotation:
    epoch, _ = _epoch_arrays(bars)
    if signal.entry_index >= len(epoch):
        return CISDAnnotation()
    signal_epoch = int(epoch[signal.entry_index])
    sequences = _sequences_for_signal(bars, signal)
    if not sequences:
        return CISDAnnotation(epoch=signal_epoch)

    # Only the newest opposite-delivery sequence may be active at the entry
    # decision. The start of a newer sequence expires every older sequence,
    # including one that confirmed earlier, so stale structure cannot leak into
    # the current decision state.
    sequence = sequences[-1]
    confirmation_start = sequence.end_index + 1
    if confirmation_start > signal.entry_index:
        return CISDAnnotation(epoch=signal_epoch)
    sequence_confirm = _first_confirmation(
        bars,
        signal.direction,
        sequence.sequence_anchor,
        confirmation_start,
        signal.entry_index,
    )
    last_confirm = _first_confirmation(
        bars,
        signal.direction,
        sequence.last_anchor,
        confirmation_start,
        signal.entry_index,
    )

    latest_sequence = (
        (sequence, sequence_confirm) if sequence_confirm >= 0 else None
    )
    latest_last = (sequence, last_confirm) if last_confirm >= 0 else None
    sequence_event = latest_sequence[0] if latest_sequence else None
    last_event = latest_last[0] if latest_last else None
    diagnostic_event = sequence_event or last_event
    if diagnostic_event is None:
        return CISDAnnotation(epoch=signal_epoch)

    sequence_confirm_index = latest_sequence[1] if latest_sequence else -1
    last_confirm_index = latest_last[1] if latest_last else -1
    reference_confirm = (
        sequence_confirm_index if sequence_confirm_index >= 0 else last_confirm_index
    )
    atr = float(bars.iloc[reference_confirm].get("atr14", np.nan))
    body_atr = (
        diagnostic_event.body_displacement / atr
        if np.isfinite(atr) and atr > 0
        else np.nan
    )
    sequence_anchor = sequence_event.sequence_anchor if sequence_event else np.nan
    anchor_distance_atr = (
        abs(signal.entry_price_raw - sequence_anchor) / atr
        if sequence_event is not None and np.isfinite(atr) and atr > 0
        else np.nan
    )

    retest = False
    retest_index = -1
    if (
        sequence_event is not None
        and sequence_confirm_index >= 0
        and sequence_confirm_index < signal.entry_index
    ):
        window = bars.iloc[sequence_confirm_index + 1 : signal.entry_index + 1]
        touch_mask = (
            (window["low"] <= sequence_event.sequence_anchor)
            & (window["high"] >= sequence_event.sequence_anchor)
        )
        if touch_mask.any():
            retest = True
            retest_index = int(window.index[touch_mask][0])

    bar_end = pd.to_datetime(bars["bar_end"])
    confirm_time = pd.Timestamp(bar_end.iloc[reference_confirm])
    sweep_time = pd.Timestamp(bar_end.iloc[signal.sweep_index])
    return CISDAnnotation(
        sequence_confirmed=sequence_confirm_index >= 0,
        last_candle_confirmed=last_confirm_index >= 0,
        direction=signal.direction,
        sequence_start_index=(sequence_event.start_index if sequence_event else -1),
        sequence_end_index=(sequence_event.end_index if sequence_event else -1),
        sequence_confirm_index=sequence_confirm_index,
        last_sequence_start_index=(last_event.start_index if last_event else -1),
        last_sequence_end_index=(last_event.end_index if last_event else -1),
        last_confirm_index=last_confirm_index,
        sequence_anchor=(sequence_event.sequence_anchor if sequence_event else np.nan),
        last_anchor=(last_event.last_anchor if last_event else np.nan),
        sequence_age_bars=(
            signal.entry_index - sequence_confirm_index if sequence_confirm_index >= 0 else -1
        ),
        last_age_bars=(
            signal.entry_index - last_confirm_index if last_confirm_index >= 0 else -1
        ),
        sequence_length=(sequence_event.length if sequence_event else 0),
        last_sequence_length=(last_event.length if last_event else 0),
        body_displacement=diagnostic_event.body_displacement,
        body_displacement_atr=body_atr,
        sequence_anchor_distance_atr=anchor_distance_atr,
        minutes_sweep_to_confirm=int((confirm_time - sweep_time).total_seconds() // 60),
        minutes_confirm_to_entry=int(
            (signal.entry_time - confirm_time).total_seconds() // 60
        ),
        sequence_retest=retest,
        sequence_retest_index=retest_index,
        sequence_retest_on_entry_bar=(retest_index == signal.entry_index),
        bars_retest_to_entry=(
            signal.entry_index - retest_index if retest_index >= 0 else -1
        ),
        epoch=signal_epoch,
    )


def annotate_signals(
    bars: pd.DataFrame,
    signals: list[base.CandidateSignal] | tuple[base.CandidateSignal, ...],
) -> list[CISDAnnotation]:
    return [annotate_signal(bars, signal) for signal in signals]


def variant_passes(annotation: CISDAnnotation, variant: CISDVariant) -> bool:
    if variant.policy == "observe":
        return True
    if variant.policy == "last_candle_confirm":
        return annotation.last_candle_confirmed
    if not annotation.sequence_confirmed:
        return False
    if variant.policy == "sequence_retest":
        return annotation.sequence_retest
    max_age = variant.max_age_bars
    return max_age is None or annotation.sequence_age_bars <= max_age


def prepare_cisd_context(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: base.StrategyConfig,
) -> PreparedCISD:
    safe_sessions = _sanitize_sessions(one_minute, bars, sessions)
    signal_sessions = safe_sessions.loc[
        ~safe_sessions["integrity_range_gap_rejected"]
    ].copy()
    signals, base_funnel = _BASE_GENERATE_SIGNALS(bars, signal_sessions, cfg)
    annotations = annotate_signals(bars, signals)
    return PreparedCISD(
        signals=tuple(signals),
        annotations=tuple(annotations),
        sessions=int(base_funnel.sessions),
        signal_config_signature=_signal_config_signature(cfg),
    )


def _trade_row(trade: base.Trade, annotation: CISDAnnotation) -> dict[str, object]:
    return {
        **asdict(trade),
        **{f"cisd_{key}": value for key, value in asdict(annotation).items()},
    }


def _empty_trade_frame() -> pd.DataFrame:
    base_columns = [field.name for field in base.Trade.__dataclass_fields__.values()]
    annotation_columns = [
        f"cisd_{field.name}" for field in CISDAnnotation.__dataclass_fields__.values()
    ]
    return pd.DataFrame(columns=[*base_columns, *annotation_columns])


def simulate_cisd_variant(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    cfg: base.StrategyConfig,
    variant: CISDVariant,
    prepared: PreparedCISD,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[pd.DataFrame, CISDFunnel, pd.DataFrame]:
    if prepared.signal_config_signature != _signal_config_signature(cfg):
        raise ValueError("Prepared CISD context does not match signal-generating config")

    signal_rows: list[dict[str, object]] = []
    for signal, annotation in zip(prepared.signals, prepared.annotations, strict=True):
        signal_rows.append(
            {
                **asdict(signal),
                **{f"cisd_{key}": value for key, value in asdict(annotation).items()},
                "variant_pass": variant_passes(annotation, variant),
            }
        )

    one_times_ns, one_open, one_high, one_low, one_close = (
        market_arrays or prepare_market_arrays(one_minute)
    )
    gaps = _gap_table(one_minute)
    unsafe_previous_ns, unsafe_current_ns = _gap_intervals(gaps, "reject_trade_bridge")

    rows: list[dict[str, object]] = []
    next_free = pd.Timestamp.min
    sequence_confirmed = 0
    last_confirmed = 0
    filtered = 0
    skipped_position = 0
    bridge_rejections = 0

    for signal, annotation in zip(prepared.signals, prepared.annotations, strict=True):
        sequence_confirmed += int(annotation.sequence_confirmed)
        last_confirmed += int(annotation.last_candle_confirmed)
        if not variant_passes(annotation, variant):
            filtered += 1
            continue
        if signal.entry_time < next_free:
            skipped_position += 1
            continue
        trade = _BASE_SIMULATE_TRADE(
            one_times_ns,
            one_open,
            one_high,
            one_low,
            one_close,
            bars,
            signal,
            cfg,
        )
        if trade is None:
            continue
        gap_ns = _first_unsafe_gap_between(
            unsafe_previous_ns,
            unsafe_current_ns,
            signal.entry_time,
            trade.exit_time,
        )
        if gap_ns is not None:
            bridge_rejections += 1
            next_free = max(next_free, pd.Timestamp(gap_ns))
            continue
        rows.append(_trade_row(trade, annotation))
        next_free = trade.exit_time

    trades = pd.DataFrame(rows) if rows else _empty_trade_frame()
    funnel = CISDFunnel(
        sessions=prepared.sessions,
        entry_signals=len(prepared.signals),
        sequence_confirmed=sequence_confirmed,
        last_candle_confirmed=last_confirmed,
        signals_filtered=filtered,
        skipped_position_open=skipped_position,
        skipped_unsafe_gap_bridge=bridge_rejections,
        trades=len(rows),
    )
    return trades, funnel, pd.DataFrame(signal_rows)


def run_cisd_backtest(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: base.StrategyConfig,
    variant: CISDVariant,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[pd.DataFrame, CISDFunnel, pd.DataFrame]:
    prepared = prepare_cisd_context(one_minute, bars, sessions, cfg)
    return simulate_cisd_variant(
        one_minute,
        bars,
        cfg,
        variant,
        prepared,
        market_arrays=market_arrays,
    )


def trade_identity(frame: pd.DataFrame) -> set[tuple[object, ...]]:
    if frame.empty:
        return set()
    work = frame.copy()
    for column in ("session_date", "entry_time"):
        work[column] = pd.to_datetime(work[column])
    columns = ["session", "session_date", "direction", "entry_time"]
    return set(map(tuple, work[columns].itertuples(index=False, name=None)))


def compare_cisd_portfolios(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
) -> tuple[dict[str, int], pd.DataFrame]:
    reference_keys = trade_identity(reference)
    candidate_keys = trade_identity(candidate)
    removed = reference_keys - candidate_keys
    added = candidate_keys - reference_keys
    rows: list[dict[str, object]] = []
    for status, keys, source in (
        ("removed", removed, reference),
        ("added", added, candidate),
    ):
        if source.empty:
            continue
        work = source.copy()
        work["session_date"] = pd.to_datetime(work["session_date"])
        work["entry_time"] = pd.to_datetime(work["entry_time"])
        for key in sorted(keys, key=str):
            mask = (
                (work["session"] == key[0])
                & (work["session_date"] == key[1])
                & (work["direction"] == key[2])
                & (work["entry_time"] == key[3])
            )
            row = work.loc[mask].iloc[0]
            rows.append({"status": status, **row.to_dict()})
    return {
        "retained": len(reference_keys & candidate_keys),
        "removed": len(removed),
        "added": len(added),
    }, pd.DataFrame(rows)
