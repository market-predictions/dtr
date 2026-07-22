from __future__ import annotations

from dataclasses import asdict, dataclass
from heapq import heappop, heappush
from typing import Literal

import numpy as np
import pandas as pd

from . import engine as base
from .integrity import (
    _BASE_GENERATE_SIGNALS,
    _BASE_SIMULATE_TRADE,
    _gap_intervals,
    _gap_table,
    _sanitize_sessions,
    prepare_market_arrays,
)

IFVGPolicy = Literal[
    "observe",
    "confirm_any",
    "recent_3",
    "recent_6",
    "recent_12",
    "zone_touch",
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
class IFVGEvent:
    """One causally recognized inversion fair value gap."""

    direction: int
    original_fvg_direction: int
    created_index: int
    inversion_index: int
    lower: float
    upper: float
    epoch: int


@dataclass(frozen=True)
class IFVGAnnotation:
    confirmed: bool = False
    direction: int = 0
    created_index: int = -1
    inversion_index: int = -1
    age_bars: int = -1
    lower: float = np.nan
    upper: float = np.nan
    zone_size: float = np.nan
    zone_size_atr: float = np.nan
    minutes_sweep_to_inversion: int = -1
    minutes_inversion_to_entry: int = -1
    post_inversion_zone_touch: bool = False
    epoch: int = -1


@dataclass(frozen=True)
class IFVGVariant:
    name: str
    policy: IFVGPolicy

    @property
    def max_age_bars(self) -> int | None:
        return {
            "recent_3": 3,
            "recent_6": 6,
            "recent_12": 12,
        }.get(self.policy)


@dataclass(frozen=True)
class PreparedIFVG:
    signals: tuple[base.CandidateSignal, ...]
    annotations: tuple[IFVGAnnotation, ...]
    events: tuple[IFVGEvent, ...]
    sessions: int
    signal_config_signature: tuple[object, ...]


@dataclass
class IFVGFunnel:
    sessions: int = 0
    entry_signals: int = 0
    signals_confirmed: int = 0
    signals_filtered: int = 0
    skipped_position_open: int = 0
    skipped_unsafe_gap_bridge: int = 0
    gap_liquidations: int = 0
    trades: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def baseline_variants() -> tuple[IFVGVariant, ...]:
    return (
        IFVGVariant("IFVG_OBSERVE", "observe"),
        IFVGVariant("IFVG_CONFIRM_ANY", "confirm_any"),
        IFVGVariant("IFVG_CONFIRM_RECENT_3", "recent_3"),
        IFVGVariant("IFVG_CONFIRM_RECENT_6", "recent_6"),
        IFVGVariant("IFVG_CONFIRM_RECENT_12", "recent_12"),
        IFVGVariant("IFVG_ZONE_TOUCH", "zone_touch"),
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


def detect_ifvg_events(bars: pd.DataFrame) -> list[IFVGEvent]:
    """Detect FVG creation and later inversion in one forward pass.

    Inversions are processed before new FVG creation on each bar, so a zone can never
    invert on the same bar that makes it causally knowable.
    """

    if bars.empty:
        return []
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    epoch, reset = _epoch_arrays(bars)

    active_bearish: list[tuple[float, int, int, float, float, int]] = []
    active_bullish: list[tuple[float, int, int, float, float, int]] = []
    events: list[IFVGEvent] = []
    sequence = 0
    current_epoch: int | None = None

    for i in range(len(bars)):
        bar_epoch = int(epoch[i])
        if current_epoch is None or bar_epoch != current_epoch or reset[i]:
            active_bearish.clear()
            active_bullish.clear()
            current_epoch = bar_epoch
            if reset[i]:
                continue

        while active_bearish and active_bearish[0][0] < close[i]:
            upper, _, created, lower, _, event_epoch = heappop(active_bearish)
            events.append(
                IFVGEvent(
                    direction=1,
                    original_fvg_direction=-1,
                    created_index=created,
                    inversion_index=i,
                    lower=lower,
                    upper=upper,
                    epoch=event_epoch,
                )
            )
        while active_bullish and -active_bullish[0][0] > close[i]:
            neg_lower, _, created, _, upper, event_epoch = heappop(active_bullish)
            lower = -neg_lower
            events.append(
                IFVGEvent(
                    direction=-1,
                    original_fvg_direction=1,
                    created_index=created,
                    inversion_index=i,
                    lower=lower,
                    upper=upper,
                    epoch=event_epoch,
                )
            )

        if i < 2 or reset[i - 1] or reset[i - 2]:
            continue
        if not (epoch[i - 2] == epoch[i - 1] == epoch[i]):
            continue

        if low[i] > high[i - 2]:
            lower = float(high[i - 2])
            upper = float(low[i])
            sequence += 1
            heappush(active_bullish, (-lower, sequence, i, lower, upper, bar_epoch))
        if high[i] < low[i - 2]:
            lower = float(high[i])
            upper = float(low[i - 2])
            sequence += 1
            heappush(active_bearish, (upper, sequence, i, lower, upper, bar_epoch))

    events.sort(
        key=lambda event: (event.inversion_index, event.direction, event.created_index)
    )
    return events


def _event_index(events: list[IFVGEvent]) -> dict[tuple[int, int], list[IFVGEvent]]:
    indexed: dict[tuple[int, int], list[IFVGEvent]] = {}
    for event in events:
        indexed.setdefault((event.direction, event.epoch), []).append(event)
    return indexed


def annotate_signal(
    bars: pd.DataFrame,
    signal: base.CandidateSignal,
    indexed_events: dict[tuple[int, int], list[IFVGEvent]],
) -> IFVGAnnotation:
    epoch, _ = _epoch_arrays(bars)
    if signal.entry_index >= len(epoch):
        return IFVGAnnotation()
    signal_epoch = int(epoch[signal.entry_index])
    candidates = indexed_events.get((signal.direction, signal_epoch), [])

    event: IFVGEvent | None = None
    for candidate in reversed(candidates):
        if candidate.inversion_index > signal.entry_index:
            continue
        if candidate.inversion_index < signal.sweep_index:
            break
        event = candidate
        break
    if event is None:
        return IFVGAnnotation(epoch=signal_epoch)

    touch = False
    if event.inversion_index < signal.entry_index:
        window = bars.iloc[event.inversion_index + 1 : signal.entry_index + 1]
        touch = bool(
            ((window["low"] <= event.upper) & (window["high"] >= event.lower)).any()
        )

    atr = float(bars.iloc[event.inversion_index].get("atr14", np.nan))
    zone_size = event.upper - event.lower
    bar_end = pd.to_datetime(bars["bar_end"])
    inversion_time = pd.Timestamp(bar_end.iloc[event.inversion_index])
    sweep_time = pd.Timestamp(bar_end.iloc[signal.sweep_index])
    return IFVGAnnotation(
        confirmed=True,
        direction=event.direction,
        created_index=event.created_index,
        inversion_index=event.inversion_index,
        age_bars=signal.entry_index - event.inversion_index,
        lower=event.lower,
        upper=event.upper,
        zone_size=zone_size,
        zone_size_atr=(zone_size / atr if np.isfinite(atr) and atr > 0 else np.nan),
        minutes_sweep_to_inversion=int((inversion_time - sweep_time).total_seconds() // 60),
        minutes_inversion_to_entry=int(
            (signal.entry_time - inversion_time).total_seconds() // 60
        ),
        post_inversion_zone_touch=touch,
        epoch=signal_epoch,
    )


def annotate_signals(
    bars: pd.DataFrame,
    signals: list[base.CandidateSignal] | tuple[base.CandidateSignal, ...],
    events: list[IFVGEvent] | tuple[IFVGEvent, ...] | None = None,
) -> list[IFVGAnnotation]:
    source = list(events) if events is not None else detect_ifvg_events(bars)
    indexed = _event_index(source)
    return [annotate_signal(bars, signal, indexed) for signal in signals]


def variant_passes(annotation: IFVGAnnotation, variant: IFVGVariant) -> bool:
    if variant.policy == "observe":
        return True
    if not annotation.confirmed:
        return False
    if variant.policy == "zone_touch":
        return annotation.post_inversion_zone_touch
    max_age = variant.max_age_bars
    return max_age is None or annotation.age_bars <= max_age


def prepare_ifvg_context(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: base.StrategyConfig,
) -> PreparedIFVG:
    safe_sessions = _sanitize_sessions(one_minute, bars, sessions)
    signal_sessions = safe_sessions.loc[
        ~safe_sessions["integrity_range_gap_rejected"]
    ].copy()
    signals, base_funnel = _BASE_GENERATE_SIGNALS(bars, signal_sessions, cfg)
    events = detect_ifvg_events(bars)
    annotations = annotate_signals(bars, signals, events)
    return PreparedIFVG(
        signals=tuple(signals),
        annotations=tuple(annotations),
        events=tuple(events),
        sessions=int(base_funnel.sessions),
        signal_config_signature=_signal_config_signature(cfg),
    )


def _trade_row(trade: base.Trade, annotation: IFVGAnnotation) -> dict[str, object]:
    return {
        **asdict(trade),
        "ifvg_confirmed": annotation.confirmed,
        "ifvg_direction": annotation.direction,
        "ifvg_created_index": annotation.created_index,
        "ifvg_inversion_index": annotation.inversion_index,
        "ifvg_age_bars": annotation.age_bars,
        "ifvg_lower": annotation.lower,
        "ifvg_upper": annotation.upper,
        "ifvg_zone_size": annotation.zone_size,
        "ifvg_zone_size_atr": annotation.zone_size_atr,
        "ifvg_minutes_sweep_to_inversion": annotation.minutes_sweep_to_inversion,
        "ifvg_minutes_inversion_to_entry": annotation.minutes_inversion_to_entry,
        "ifvg_post_inversion_zone_touch": annotation.post_inversion_zone_touch,
        "ifvg_epoch": annotation.epoch,
    }


def _empty_trade_frame() -> pd.DataFrame:
    base_columns = [field.name for field in base.Trade.__dataclass_fields__.values()]
    return pd.DataFrame(
        columns=[
            *base_columns,
            "ifvg_confirmed",
            "ifvg_direction",
            "ifvg_created_index",
            "ifvg_inversion_index",
            "ifvg_age_bars",
            "ifvg_lower",
            "ifvg_upper",
            "ifvg_zone_size",
            "ifvg_zone_size_atr",
            "ifvg_minutes_sweep_to_inversion",
            "ifvg_minutes_inversion_to_entry",
            "ifvg_post_inversion_zone_touch",
            "ifvg_epoch",
        ]
    )


def simulate_ifvg_variant(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    cfg: base.StrategyConfig,
    variant: IFVGVariant,
    prepared: PreparedIFVG,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[pd.DataFrame, IFVGFunnel, pd.DataFrame]:
    """Simulate one IFVG policy using a precomputed, signal-stable context."""

    if prepared.signal_config_signature != _signal_config_signature(cfg):
        raise ValueError("Prepared IFVG context does not match signal-generating config")

    signal_rows: list[dict[str, object]] = []
    for signal, annotation in zip(prepared.signals, prepared.annotations, strict=True):
        signal_rows.append(
            {
                **asdict(signal),
                **{f"ifvg_{key}": value for key, value in asdict(annotation).items()},
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
    confirmed = 0
    filtered = 0
    skipped_position = 0
    gap_liquidations = 0

    for signal, annotation in zip(prepared.signals, prepared.annotations, strict=True):
        if annotation.confirmed:
            confirmed += 1
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
            unsafe_previous_ns=unsafe_previous_ns,
            unsafe_current_ns=unsafe_current_ns,
            gap_policy="liquidate",
        )
        if trade is None:
            continue
        if trade.exit_reason == "GAP_LIQUIDATION":
            gap_liquidations += 1
        rows.append(_trade_row(trade, annotation))
        next_free = trade.exit_time

    trades = pd.DataFrame(rows) if rows else _empty_trade_frame()
    funnel = IFVGFunnel(
        sessions=prepared.sessions,
        entry_signals=len(prepared.signals),
        signals_confirmed=confirmed,
        signals_filtered=filtered,
        skipped_position_open=skipped_position,
        skipped_unsafe_gap_bridge=0,
        gap_liquidations=gap_liquidations,
        trades=len(rows),
    )
    return trades, funnel, pd.DataFrame(signal_rows)


def run_ifvg_backtest(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: base.StrategyConfig,
    variant: IFVGVariant,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[pd.DataFrame, IFVGFunnel, pd.DataFrame]:
    """Run an implementable IFVG filter and return signal-level annotations."""

    prepared = prepare_ifvg_context(one_minute, bars, sessions, cfg)
    return simulate_ifvg_variant(
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


def compare_ifvg_portfolios(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
) -> tuple[dict[str, int], pd.DataFrame]:
    """Attribute portfolio membership changes using stable reversal-signal identity."""

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
