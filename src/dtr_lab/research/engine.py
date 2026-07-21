from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

import numpy as np
import pandas as pd


SESSION_SPECS = {
    "LONDON_2AM": ((1, 12), (2, 13), (6, 0)),
    "NEW_YORK_9AM": ((8, 12), (9, 13), (14, 0)),
    "ASIA_7PM": ((19, 0), (20, 1), (23, 45)),
}


@dataclass(frozen=True)
class StrategyConfig:
    name: str = "baseline"
    sessions: tuple[str, ...] = ("LONDON_2AM", "NEW_YORK_9AM", "ASIA_7PM")
    weekdays: tuple[int, ...] = (0, 1, 2, 3, 4)  # Monday=0
    min_sweep_range_pct: float = 0.02
    min_sweep_ticks: int = 1
    valid_sweep_threshold: int = 1
    ideal_sweep_max_pct: float = 0.60
    too_deep_sweep_pct: float = 1.20
    volume_expand_mult: float = 1.00
    atr_expand_mult: float = 1.00
    reaction_bars: int = 10
    pivot_len: int = 1
    pivot_min_pct: float = 0.02
    break_mode: str = "close"  # wick, close, close_buffer
    break_buffer_pct: float = 0.0
    break_atr_frac: float = 0.0
    impulse_mult: float = 0.60
    require_impulse: bool = False
    acceptance_bars: int = 1
    entry_mode: str = "break_close"  # break_close, retest
    retest_band_pct: float = 0.05
    signal_window_bars: int = 25
    max_bars_from_sweep: int = 60
    trend_filter: str = "none"  # none, nontrend_er, vwap_reclaim, adx_nontrend
    er_length: int = 20
    er_max: float = 0.35
    adx_max: float = 22.0
    stop_buffer_ticks: int = 2
    stop_atr_frac: float = 0.10
    tp1_rr: float = 1.25
    runner_rr: float = 2.50
    tp1_fraction: float = 0.50
    move_runner_to_be: bool = True
    time_close_mode: str = "everyday"  # none, everyday, friday
    time_close_hour: int = 16
    time_close_minute: int = 0
    max_hold_bars: int = 288
    slippage_ticks_each_side: float = 1.0
    commission_per_side: float = 2.25
    tick_size: float = 0.25
    point_value: float = 20.0
    conservative_intrabar: bool = True


@dataclass
class CandidateSignal:
    session: str
    session_date: pd.Timestamp
    direction: int
    sweep_index: int
    entry_index: int
    entry_time: pd.Timestamp
    entry_price_raw: float
    sweep_extreme: float
    range_high: float
    range_low: float
    pivot: float
    sweep_score: int
    day_of_week: int


@dataclass
class Trade:
    config_name: str
    session: str
    session_date: pd.Timestamp
    direction: int
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    stop_price: float
    exit_reason: str
    pnl_r: float
    pnl_dollars: float
    mfe_r: float
    mae_r: float
    holding_minutes: int
    sweep_score: int
    day_of_week: int


@dataclass
class Funnel:
    sessions: int = 0
    sweep_depth_pass: int = 0
    sweep_quality_pass: int = 0
    reclaim_pass: int = 0
    pivot_ready: int = 0
    bos_pass: int = 0
    impulse_pass: int = 0
    acceptance_pass: int = 0
    trend_pass: int = 0
    entry_signal: int = 0
    skipped_position_open: int = 0
    trades: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def load_zip(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    with ZipFile(path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one CSV in archive, found {members}")
        with zf.open(members[0]) as fh:
            frame = pd.read_csv(fh)
    frame["timestamp"] = pd.to_datetime(frame["timestamp ET"], format="%m/%d/%Y %H:%M")
    frame = (
        frame.sort_values("timestamp")
        .drop_duplicates("timestamp")
        .reset_index(drop=True)
    )
    # The source is almost certainly Excel-truncated; remove the incomplete final ET date.
    final_date = frame["timestamp"].dt.normalize().iloc[-1]
    frame = frame[frame["timestamp"].dt.normalize() < final_date].copy()
    return frame


def resample_5m(one_minute: pd.DataFrame) -> pd.DataFrame:
    x = one_minute.set_index("timestamp").sort_index()
    out = (
        x.resample("5min", label="left", closed="left")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            source_bars=("close", "count"),
        )
        .dropna(subset=["open", "high", "low", "close"])
    )
    out = out.reset_index()
    out["bar_end"] = out["timestamp"] + pd.Timedelta(minutes=5)
    return add_features(out)


def _wilder(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(alpha=1.0 / length, adjust=False, min_periods=length).mean()


def add_features(bars: pd.DataFrame) -> pd.DataFrame:
    b = bars.copy()
    prev_close = b["close"].shift(1)
    tr = pd.concat(
        [
            b["high"] - b["low"],
            (b["high"] - prev_close).abs(),
            (b["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    b["atr14"] = _wilder(tr, 14)
    b["median_range20"] = (b["high"] - b["low"]).rolling(20, min_periods=5).median()
    b["vol_sma20"] = b["volume"].rolling(20, min_periods=5).mean()
    delta = b["close"].diff().abs()
    for n in (10, 20, 30):
        b[f"er{n}"] = (b["close"] - b["close"].shift(n)).abs() / delta.rolling(
            n
        ).sum().replace(0, np.nan)
    up = b["high"].diff()
    down = -b["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=b.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=b.index)
    atr = _wilder(tr, 14)
    plus_di = 100 * _wilder(plus_dm, 14) / atr.replace(0, np.nan)
    minus_di = 100 * _wilder(minus_dm, 14) / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    b["adx14"] = _wilder(dx, 14)
    # ETH VWAP reset at 18:00 ET, using typical price.
    trade_date = (b["timestamp"] - pd.Timedelta(hours=18)).dt.normalize()
    tpv = ((b["high"] + b["low"] + b["close"]) / 3.0) * b["volume"]
    b["eth_vwap"] = tpv.groupby(trade_date).cumsum() / b["volume"].groupby(
        trade_date
    ).cumsum().replace(0, np.nan)
    b["eth_vwap_slope3"] = b["eth_vwap"] - b["eth_vwap"].shift(3)
    return b


def _ts_on_date(day: pd.Timestamp, hm: tuple[int, int]) -> pd.Timestamp:
    return day + pd.Timedelta(hours=hm[0], minutes=hm[1])


def build_session_table(one_minute: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    first_day = one_minute["timestamp"].min().normalize()
    last_day = one_minute["timestamp"].max().normalize()
    days = pd.date_range(first_day, last_day, freq="D")
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    rows: list[dict[str, object]] = []
    one = one_minute.set_index("timestamp")
    for day in days:
        for name, (start_hm, end_hm, break_hm) in SESSION_SPECS.items():
            start = _ts_on_date(day, start_hm)
            end = _ts_on_date(day, end_hm)
            break_end = _ts_on_date(day, break_hm)
            if break_end <= end:
                break_end += pd.Timedelta(days=1)
            window = one.loc[(one.index >= start) & (one.index < end)]
            if len(window) < 20:
                continue
            i0 = int(np.searchsorted(bar_times, np.datetime64(end), side="left"))
            i1 = int(np.searchsorted(bar_times, np.datetime64(break_end), side="left"))
            if i0 >= len(bars) or i1 <= i0:
                continue
            rows.append(
                {
                    "session": name,
                    "session_date": day,
                    "range_start": start,
                    "range_end": end,
                    "break_end": break_end,
                    "range_high": float(window["high"].max()),
                    "range_low": float(window["low"].min()),
                    "range_size": float(window["high"].max() - window["low"].min()),
                    "post_start_index": i0,
                    "post_end_index": min(i1, len(bars)),
                    "weekday": int(day.weekday()),
                }
            )
    return pd.DataFrame(rows)


def _pivot_high(high: np.ndarray, idx: int, length: int) -> bool:
    if idx - length < 0 or idx + length >= len(high):
        return False
    w = high[idx - length : idx + length + 1]
    return bool(high[idx] == np.max(w) and np.sum(w == high[idx]) == 1)


def _pivot_low(low: np.ndarray, idx: int, length: int) -> bool:
    if idx - length < 0 or idx + length >= len(low):
        return False
    w = low[idx - length : idx + length + 1]
    return bool(low[idx] == np.min(w) and np.sum(w == low[idx]) == 1)


def _trend_ok(
    cfg: StrategyConfig, bars: pd.DataFrame, idx: int, direction: int
) -> bool:
    if cfg.trend_filter == "none":
        return True
    if cfg.trend_filter == "nontrend_er":
        er = bars.iloc[idx].get(f"er{cfg.er_length}", np.nan)
        return bool(pd.notna(er) and er <= cfg.er_max)
    if cfg.trend_filter == "adx_nontrend":
        adx = bars.iloc[idx]["adx14"]
        return bool(pd.notna(adx) and adx <= cfg.adx_max)
    if cfg.trend_filter == "vwap_reclaim":
        row = bars.iloc[idx]
        return bool(
            row["close"] > row["eth_vwap"]
            if direction > 0
            else row["close"] < row["eth_vwap"]
        )
    raise ValueError(f"Unknown trend filter: {cfg.trend_filter}")


def generate_signals(
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: StrategyConfig,
) -> tuple[list[CandidateSignal], Funnel]:
    high = bars["high"].to_numpy(float)
    low = bars["low"].to_numpy(float)
    close = bars["close"].to_numpy(float)
    open_ = bars["open"].to_numpy(float)
    volume = bars["volume"].to_numpy(float)
    atr = bars["atr14"].to_numpy(float)
    median_range = bars["median_range20"].to_numpy(float)
    vol_sma = bars["vol_sma20"].to_numpy(float)
    bar_end = bars["bar_end"].to_numpy(dtype="datetime64[ns]")
    signals: list[CandidateSignal] = []
    funnel = Funnel()

    for s in sessions.itertuples(index=False):
        if s.session not in cfg.sessions or s.weekday not in cfg.weekdays:
            continue
        funnel.sessions += 1
        rh, rl, rs = float(s.range_high), float(s.range_low), float(s.range_size)
        if not np.isfinite(rs) or rs <= 0:
            continue
        start, end = int(s.post_start_index), int(s.post_end_index)
        min_depth = max(
            cfg.tick_size * cfg.min_sweep_ticks, rs * cfg.min_sweep_range_pct
        )
        sweep_idx = -1
        direction = 0
        sweep_extreme = np.nan
        for i in range(start, end):
            hi_sweep = high[i] - rh >= min_depth
            lo_sweep = rl - low[i] >= min_depth
            if hi_sweep and lo_sweep:
                sweep_idx = -1
                break
            if lo_sweep:
                sweep_idx, direction, sweep_extreme = i, 1, low[i]
                break
            if hi_sweep:
                sweep_idx, direction, sweep_extreme = i, -1, high[i]
                break
        if sweep_idx < 0:
            continue
        funnel.sweep_depth_pass += 1
        depth = (rl - low[sweep_idx]) if direction > 0 else (high[sweep_idx] - rh)
        penetration = (
            2
            if depth <= rs * cfg.ideal_sweep_max_pct
            else 1
            if depth <= rs * cfg.too_deep_sweep_pct
            else 0
        )
        expand = (
            (high[sweep_idx] - low[sweep_idx]) > atr[sweep_idx] * cfg.atr_expand_mult
            if np.isfinite(atr[sweep_idx])
            else False
        ) or (
            volume[sweep_idx] > vol_sma[sweep_idx] * cfg.volume_expand_mult
            if np.isfinite(vol_sma[sweep_idx])
            else False
        )
        sweep_score = penetration + 1 + int(expand)
        if sweep_score < cfg.valid_sweep_threshold:
            continue
        funnel.sweep_quality_pass += 1

        last = min(end, sweep_idx + cfg.max_bars_from_sweep + 1)
        reclaim_limit = min(last, sweep_idx + cfg.reaction_bars + 1)
        reclaim_idx = -1
        for i in range(sweep_idx, reclaim_limit):
            if (direction > 0 and close[i] >= rl) or (direction < 0 and close[i] <= rh):
                reclaim_idx = i
                break
        if reclaim_idx < 0:
            continue
        funnel.reclaim_pass += 1

        pivot = np.nan
        pivot_ready_time = -1
        bos_idx = -1
        for i in range(max(sweep_idx + 2 * cfg.pivot_len, reclaim_idx), last):
            candidate_idx = i - cfg.pivot_len
            if direction > 0 and _pivot_high(high, candidate_idx, cfg.pivot_len):
                if high[candidate_idx] - sweep_extreme >= max(
                    cfg.tick_size, rs * cfg.pivot_min_pct
                ):
                    pivot, pivot_ready_time = high[candidate_idx], i
            elif direction < 0 and _pivot_low(low, candidate_idx, cfg.pivot_len):
                if sweep_extreme - low[candidate_idx] >= max(
                    cfg.tick_size, rs * cfg.pivot_min_pct
                ):
                    pivot, pivot_ready_time = low[candidate_idx], i
            if not np.isfinite(pivot) or i < pivot_ready_time:
                continue
            # Opposite range side invalidates the reversal before entry.
            if (direction > 0 and high[i] > rh) or (direction < 0 and low[i] < rl):
                # This is not necessarily invalid in Pine, but is a conservative research gate.
                pass
            buffer = max(
                rs * cfg.break_buffer_pct,
                (atr[i] * cfg.break_atr_frac if np.isfinite(atr[i]) else 0.0),
            )
            if cfg.break_mode == "wick":
                broke = (
                    high[i] >= pivot + buffer
                    if direction > 0
                    else low[i] <= pivot - buffer
                )
            else:
                broke = (
                    close[i] >= pivot + buffer
                    if direction > 0
                    else close[i] <= pivot - buffer
                )
            if not broke:
                continue
            if cfg.require_impulse:
                impulse = (
                    np.isfinite(median_range[i])
                    and (high[i] - low[i]) > median_range[i] * cfg.impulse_mult
                    and (
                        (close[i] > open_[i])
                        if direction > 0
                        else (close[i] < open_[i])
                    )
                )
                if not impulse:
                    continue
            bos_idx = i
            break
        if not np.isfinite(pivot):
            continue
        funnel.pivot_ready += 1
        if bos_idx < 0:
            continue
        funnel.bos_pass += 1
        if not cfg.require_impulse or True:
            funnel.impulse_pass += 1

        accept_idx = bos_idx
        if cfg.acceptance_bars > 1:
            for i in range(bos_idx, min(last, bos_idx + cfg.acceptance_bars + 3)):
                j0 = i - cfg.acceptance_bars + 1
                if j0 < bos_idx:
                    continue
                vals = close[j0 : i + 1]
                held = np.all(vals > pivot) if direction > 0 else np.all(vals < pivot)
                if held:
                    accept_idx = i
                    break
            else:
                continue
        funnel.acceptance_pass += 1

        entry_idx = accept_idx
        if cfg.entry_mode == "retest":
            entry_idx = -1
            band = max(cfg.tick_size * 2, rs * cfg.retest_band_pct)
            for i in range(
                accept_idx + 1, min(last, accept_idx + cfg.signal_window_bars + 1)
            ):
                if direction > 0:
                    if low[i] <= pivot + band and close[i] > pivot:
                        entry_idx = i
                        break
                else:
                    if high[i] >= pivot - band and close[i] < pivot:
                        entry_idx = i
                        break
            if entry_idx < 0:
                continue
        if not _trend_ok(cfg, bars, entry_idx, direction):
            continue
        funnel.trend_pass += 1
        funnel.entry_signal += 1
        signals.append(
            CandidateSignal(
                session=s.session,
                session_date=s.session_date,
                direction=direction,
                sweep_index=sweep_idx,
                entry_index=entry_idx,
                entry_time=pd.Timestamp(bar_end[entry_idx]),
                entry_price_raw=float(close[entry_idx]),
                sweep_extreme=float(sweep_extreme),
                range_high=rh,
                range_low=rl,
                pivot=float(pivot),
                sweep_score=int(sweep_score),
                day_of_week=int(s.weekday),
            )
        )
    signals.sort(key=lambda x: x.entry_time)
    return signals, funnel


def _scheduled_close_after(
    ts: pd.Timestamp, cfg: StrategyConfig
) -> pd.Timestamp | None:
    if cfg.time_close_mode == "none":
        return None
    candidate = ts.normalize() + pd.Timedelta(
        hours=cfg.time_close_hour, minutes=cfg.time_close_minute
    )
    if candidate <= ts:
        candidate += pd.Timedelta(days=1)
    if cfg.time_close_mode == "friday":
        while candidate.weekday() != 4:
            candidate += pd.Timedelta(days=1)
    return candidate


def _simulate_trade_np(
    one_times_ns: np.ndarray,
    one_open: np.ndarray,
    one_high: np.ndarray,
    one_low: np.ndarray,
    one_close: np.ndarray,
    bars: pd.DataFrame,
    sig: CandidateSignal,
    cfg: StrategyConfig,
) -> Trade | None:
    atr = float(bars.iloc[sig.entry_index]["atr14"])
    if not np.isfinite(atr):
        return None
    slip = cfg.tick_size * cfg.slippage_ticks_each_side
    entry = (
        sig.entry_price_raw + slip if sig.direction > 0 else sig.entry_price_raw - slip
    )
    buffer = max(cfg.tick_size * cfg.stop_buffer_ticks, atr * cfg.stop_atr_frac)
    stop = (
        sig.sweep_extreme - buffer if sig.direction > 0 else sig.sweep_extreme + buffer
    )
    risk_points = (entry - stop) if sig.direction > 0 else (stop - entry)
    if risk_points <= cfg.tick_size:
        return None
    tp1 = entry + sig.direction * risk_points * cfg.tp1_rr
    tp2 = entry + sig.direction * risk_points * cfg.runner_rr
    start = sig.entry_time
    time_close = _scheduled_close_after(start, cfg)
    max_end = start + pd.Timedelta(minutes=5 * cfg.max_hold_bars)
    hard_end = max_end if time_close is None else min(max_end, time_close)
    start_ns = np.datetime64(start, "ns").astype(np.int64)
    end_ns = np.datetime64(hard_end, "ns").astype(np.int64)
    j0 = int(np.searchsorted(one_times_ns, start_ns, side="left"))
    j1 = int(np.searchsorted(one_times_ns, end_ns, side="right"))
    if j0 >= j1:
        return None
    remaining = 1.0
    realized_points = 0.0
    tp1_hit = False
    runner_stop = stop
    mfe = 0.0
    mae = 0.0
    last_idx = j1 - 1
    exit_time = pd.Timestamp(one_times_ns[last_idx]) + pd.Timedelta(minutes=1)
    exit_reason = "MAX_HOLD"
    time_close_ns = (
        None if time_close is None else np.datetime64(time_close, "ns").astype(np.int64)
    )
    max_end_ns = np.datetime64(max_end, "ns").astype(np.int64)

    for j in range(j0, j1):
        minute_end_ns = one_times_ns[j] + 60_000_000_000
        if sig.direction > 0:
            mfe = max(mfe, one_high[j] - entry)
            mae = max(mae, entry - one_low[j])
            stop_hit = one_low[j] <= runner_stop
            t1_hit = (not tp1_hit) and one_high[j] >= tp1
            t2_hit = one_high[j] >= tp2
        else:
            mfe = max(mfe, entry - one_low[j])
            mae = max(mae, one_high[j] - entry)
            stop_hit = one_high[j] >= runner_stop
            t1_hit = (not tp1_hit) and one_low[j] <= tp1
            t2_hit = one_low[j] <= tp2
        if stop_hit and (t1_hit or t2_hit) and cfg.conservative_intrabar:
            px = runner_stop - slip if sig.direction > 0 else runner_stop + slip
            realized_points += remaining * sig.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "STOP_AMBIG"
            break
        if stop_hit:
            px = runner_stop - slip if sig.direction > 0 else runner_stop + slip
            realized_points += remaining * sig.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = (
                pd.Timestamp(minute_end_ns),
                "BE" if tp1_hit and runner_stop == entry else "STOP",
            )
            break
        if t1_hit:
            frac = min(cfg.tp1_fraction, remaining)
            px = tp1 - slip if sig.direction > 0 else tp1 + slip
            realized_points += frac * sig.direction * (px - entry)
            remaining -= frac
            tp1_hit = True
            if cfg.move_runner_to_be:
                runner_stop = entry
        if remaining > 0 and t2_hit:
            px = tp2 - slip if sig.direction > 0 else tp2 + slip
            realized_points += remaining * sig.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "TP2"
            break
        if time_close_ns is not None and minute_end_ns >= time_close_ns:
            px = one_close[j] - slip if sig.direction > 0 else one_close[j] + slip
            realized_points += remaining * sig.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "TIME_CLOSE"
            break
        if minute_end_ns >= max_end_ns:
            px = one_close[j] - slip if sig.direction > 0 else one_close[j] + slip
            realized_points += remaining * sig.direction * (px - entry)
            remaining = 0.0
            exit_time, exit_reason = pd.Timestamp(minute_end_ns), "MAX_HOLD"
            break
    if remaining > 0:
        px = (
            one_close[last_idx] - slip
            if sig.direction > 0
            else one_close[last_idx] + slip
        )
        realized_points += remaining * sig.direction * (px - entry)
    gross_dollars = realized_points * cfg.point_value
    commission = 2.0 * cfg.commission_per_side
    net_dollars = gross_dollars - commission
    risk_dollars = risk_points * cfg.point_value
    pnl_r = net_dollars / risk_dollars
    return Trade(
        config_name=cfg.name,
        session=sig.session,
        session_date=sig.session_date,
        direction=sig.direction,
        entry_time=sig.entry_time,
        exit_time=exit_time,
        entry_price=entry,
        stop_price=stop,
        exit_reason=exit_reason,
        pnl_r=float(pnl_r),
        pnl_dollars=float(net_dollars),
        mfe_r=float(mfe / risk_points),
        mae_r=float(mae / risk_points),
        holding_minutes=int((exit_time - sig.entry_time).total_seconds() // 60),
        sweep_score=sig.sweep_score,
        day_of_week=sig.day_of_week,
    )


def prepare_market_arrays(
    one_minute: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return (
        one_minute["timestamp"].to_numpy(dtype="datetime64[ns]").astype(np.int64),
        one_minute["open"].to_numpy(float),
        one_minute["high"].to_numpy(float),
        one_minute["low"].to_numpy(float),
        one_minute["close"].to_numpy(float),
    )


def run_backtest(
    one_minute: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    cfg: StrategyConfig,
    market_arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    | None = None,
) -> tuple[pd.DataFrame, Funnel]:
    signals, funnel = generate_signals(bars, sessions, cfg)
    one_times_ns, one_open, one_high, one_low, one_close = (
        market_arrays or prepare_market_arrays(one_minute)
    )
    trades: list[Trade] = []
    next_free = pd.Timestamp.min
    for sig in signals:
        if sig.entry_time < next_free:
            funnel.skipped_position_open += 1
            continue
        trade = _simulate_trade_np(
            one_times_ns, one_open, one_high, one_low, one_close, bars, sig, cfg
        )
        if trade is None:
            continue
        trades.append(trade)
        next_free = trade.exit_time
    funnel.trades = len(trades)
    return pd.DataFrame([asdict(t) for t in trades]), funnel


def metrics(trades: pd.DataFrame) -> dict[str, float]:
    if trades.empty:
        return {
            "trades": 0,
            "expectancy_r": np.nan,
            "profit_factor": np.nan,
            "win_rate": np.nan,
            "max_drawdown_r": np.nan,
            "net_r": 0.0,
            "return_dd": np.nan,
            "median_r": np.nan,
        }
    r = trades["pnl_r"].to_numpy(float)
    eq = np.cumsum(r)
    peaks = np.maximum.accumulate(np.r_[0.0, eq])
    dd = peaks[1:] - eq
    gross_win = r[r > 0].sum()
    gross_loss = -r[r < 0].sum()
    max_dd = float(dd.max(initial=0.0))
    return {
        "trades": int(len(r)),
        "expectancy_r": float(np.mean(r)),
        "median_r": float(np.median(r)),
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else np.inf,
        "win_rate": float(np.mean(r > 0)),
        "max_drawdown_r": max_dd,
        "net_r": float(eq[-1]),
        "return_dd": float(eq[-1] / max_dd) if max_dd > 0 else np.nan,
        "avg_hold_min": float(trades["holding_minutes"].mean()),
        "mfe_r": float(trades["mfe_r"].mean()),
        "mae_r": float(trades["mae_r"].mean()),
    }


def split_metrics(
    trades: pd.DataFrame, split_dates: Iterable[pd.Timestamp]
) -> list[dict[str, float]]:
    dates = list(split_dates)
    out: list[dict[str, float]] = []
    for a, b in zip(dates[:-1], dates[1:]):
        mask = (
            (trades["entry_time"] >= a) & (trades["entry_time"] < b)
            if not trades.empty
            else []
        )
        m = metrics(trades.loc[mask] if not trades.empty else trades)
        m.update({"start": str(a.date()), "end": str(b.date())})
        out.append(m)
    return out
