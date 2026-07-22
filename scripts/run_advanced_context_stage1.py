# ruff: noqa
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.research import engine
from dtr_lab.research.integrity import _gap_intervals, _gap_table
from dtr_lab.research.manifest import load_manifest

ROOT = Path('/mnt/data/dtr-shift3-work')
BASE = Path('/mnt/data/dtr-advanced-baseline')
OUT = Path('/mnt/data/dtr-advanced-results')
OUT.mkdir(exist_ok=True)
SEED = 20260722

SESSION_SPECS = {
    'LONDON_2AM': ((1, 11), (2, 12), (6, 0)),
    'NEW_YORK_9AM': ((8, 11), (9, 12), (14, 0)),
    'ASIA_7PM': ((19, 0), (20, 1), (23, 45)),
}

FAMILY_CATEGORIES = {
    'F1_D1_DIRECTION': ['aligned', 'countertrend', 'neutral'],
    'F2_H4_DIRECTION': ['aligned', 'countertrend', 'neutral'],
    'F3_DIRECTION_CONFLUENCE': ['both_aligned', 'mixed', 'both_countertrend', 'one_or_both_neutral'],
    'F4_D1_VOLATILITY': ['low_0_33', 'middle_33_67', 'high_67_100'],
    'F5_HTF_TREND_STRENGTH': ['nontrend', 'transition', 'strong_trend'],
    'F6_RANGE_VOLATILITY_FIT': ['compressed', 'normal', 'expanded'],
    'F7_VOLATILITY_TRANSITION': ['contracting', 'stable', 'expanding'],
    'F8_PRIOR_DAY_LOCATION': ['near_directional_extreme_le_0_25ATR', 'inside_midrange', 'outside_prior_range'],
    'F9_PRIOR_WEEK_LOCATION': ['near_directional_extreme_le_0_40ATR', 'inside_week', 'outside_week'],
    'F10_OVERNIGHT_GAP': ['mean_reversion_aligned', 'continuation_aligned', 'small_gap_abs_lt_0_10ATR'],
    'F11_VOLUME_CONTEXT': ['low', 'normal', 'high'],
    'F12_VWAP_AND_VALUE_LOCATION': ['reversion_toward_value', 'extension_away_from_value', 'crossing_value'],
}


def wilder(s: pd.Series, length: int) -> pd.Series:
    return s.ewm(alpha=1.0 / length, adjust=False, min_periods=length).mean()


def add_ohlc_features(frame: pd.DataFrame, *, daily: bool) -> pd.DataFrame:
    x = frame.copy()
    prev_close = x['close'].shift(1)
    tr = pd.concat([
        x['high'] - x['low'],
        (x['high'] - prev_close).abs(),
        (x['low'] - prev_close).abs(),
    ], axis=1).max(axis=1)
    x['atr20'] = wilder(tr, 20)
    x['atr14'] = wilder(tr, 14)
    x['ema20'] = x['close'].ewm(span=20, adjust=False, min_periods=20).mean()
    x['ema50'] = x['close'].ewm(span=50, adjust=False, min_periods=50).mean()
    slope_lag = 5 if daily else 3
    x['ema20_slope_norm'] = (x['ema20'] - x['ema20'].shift(slope_lag)) / x['atr20'].replace(0, np.nan)
    delta = x['close'].diff().abs()
    x['er20'] = (x['close'] - x['close'].shift(20)).abs() / delta.rolling(20, min_periods=20).sum().replace(0, np.nan)
    up = x['high'].diff()
    down = -x['low'].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=x.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=x.index)
    atr = wilder(tr, 14)
    plus_di = 100 * wilder(plus_dm, 14) / atr.replace(0, np.nan)
    minus_di = 100 * wilder(minus_dm, 14) / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    x['adx14'] = wilder(dx, 14)
    if daily:
        logret = np.log(x['close']).diff()
        x['rv20'] = logret.rolling(20, min_periods=20).std(ddof=1) * np.sqrt(252)
        x['atr_change5'] = x['atr20'] / x['atr20'].shift(5) - 1.0
        x['rv_change5'] = x['rv20'] / x['rv20'].shift(5) - 1.0
    return x


def trailing_percentile(series: pd.Series, window: int, min_periods: int) -> pd.Series:
    vals = series.to_numpy(float)
    out = np.full(len(vals), np.nan)
    for i, value in enumerate(vals):
        if not np.isfinite(value):
            continue
        start = max(0, i - window + 1)
        hist = vals[start:i + 1]
        hist = hist[np.isfinite(hist)]
        if len(hist) >= min_periods:
            out[i] = float(np.mean(hist <= value))
    return pd.Series(out, index=series.index)


def same_session_prior_percentile(df: pd.DataFrame, value_col: str, window: int = 126, min_periods: int = 40) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for _, idx in df.groupby('session', sort=False).groups.items():
        idx = list(idx)
        vals = df.loc[idx, value_col].to_numpy(float)
        result = np.full(len(vals), np.nan)
        for pos, value in enumerate(vals):
            if not np.isfinite(value):
                continue
            hist = vals[max(0, pos - window):pos]
            hist = hist[np.isfinite(hist)]
            if len(hist) >= min_periods:
                result[pos] = float(np.mean(hist <= value))
        out.loc[idx] = result
    return out


def metrics(trades: pd.DataFrame) -> dict[str, float]:
    return engine.metrics(trades)


def portfolio_from_mask(signal_rows: pd.DataFrame, cached_trades: dict[int, object], mask: pd.Series) -> tuple[pd.DataFrame, int]:
    rows = []
    next_free = pd.Timestamp.min
    qualifying = 0
    for row in signal_rows.loc[mask.fillna(False)].sort_values('entry_time').itertuples():
        qualifying += 1
        trade = cached_trades.get(int(row.signal_id))
        if trade is None or pd.Timestamp(row.entry_time) < next_free:
            continue
        rows.append(asdict(trade))
        next_free = pd.Timestamp(trade.exit_time)
    return pd.DataFrame(rows), qualifying


def cost_expectancy(trades: pd.DataFrame, ticks_each_side: float) -> float:
    if trades.empty:
        return float('nan')
    extra_ticks = ticks_each_side - 1.0
    risk = (trades['entry_price'] - trades['stop_price']).abs().to_numpy(float)
    stressed = trades['pnl_r'].to_numpy(float) - (2.0 * extra_ticks * 0.25) / risk
    return float(np.mean(stressed))


def period_nets(trades: pd.DataFrame) -> tuple[dict[str, float], dict[str, float]]:
    if trades.empty:
        return ({'2023': 0.0, '2024': 0.0, '2025': 0.0}, {})
    t = trades.copy()
    dt = pd.to_datetime(t['entry_time'])
    years = {str(y): float(t.loc[dt.dt.year == y, 'pnl_r'].sum()) for y in (2023, 2024, 2025)}
    half = dt.dt.year.astype(str) + 'H' + ((dt.dt.month.sub(1) // 6) + 1).astype(str)
    halves = {str(k): float(v) for k, v in t.groupby(half)['pnl_r'].sum().items()}
    return years, halves


def concentration(trades: pd.DataFrame, net_r: float) -> tuple[float, float]:
    if trades.empty or net_r <= 0:
        return float('inf'), float('inf')
    session_nets = trades.groupby('session')['pnl_r'].sum()
    dt = pd.to_datetime(trades['entry_time'])
    half = dt.dt.year.astype(str) + 'H' + ((dt.dt.month.sub(1) // 6) + 1).astype(str)
    half_nets = trades.groupby(half)['pnl_r'].sum()
    return float(session_nets.max() / net_r), float(half_nets.max() / net_r)


def return_vector(trades: pd.DataFrame, opportunity_index: pd.MultiIndex) -> np.ndarray:
    if trades.empty:
        return np.zeros(len(opportunity_index), dtype=float)
    work = trades.copy()
    work['session_date'] = pd.to_datetime(work['session_date']).dt.normalize()
    s = work.groupby(['session_date', 'session'])['pnl_r'].sum()
    return s.reindex(opportunity_index, fill_value=0.0).to_numpy(float)


def familywise_adjusted_p(diff_matrix: np.ndarray, dates: np.ndarray, iterations: int = 5000, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    n, k = diff_matrix.shape
    means = diff_matrix.mean(axis=0)
    std = diff_matrix.std(axis=0, ddof=1)
    se = std / np.sqrt(n)
    observed_t = np.divide(means, se, out=np.zeros_like(means), where=se > 0)
    centered = diff_matrix - means
    unique_dates = pd.Index(dates).unique()
    groups = [np.flatnonzero(dates == d) for d in unique_dates]
    rng = np.random.default_rng(seed)
    maxima = np.empty(iterations, dtype=float)
    for i in range(iterations):
        chosen = rng.integers(0, len(groups), size=len(groups))
        rows = np.concatenate([groups[j] for j in chosen])
        sample = centered[rows]
        sm = sample.mean(axis=0)
        ss = sample.std(axis=0, ddof=1) / np.sqrt(len(rows))
        st = np.divide(sm, ss, out=np.zeros_like(sm), where=ss > 0)
        maxima[i] = np.max(st)
    p = np.array([(np.sum(maxima >= t) + 1) / (iterations + 1) if t > 0 else 1.0 for t in observed_t])
    return observed_t, p


def bootstrap_interval(trades: pd.DataFrame, unit: str, iterations: int = 2000, seed: int = SEED) -> tuple[float, float]:
    if trades.empty:
        return float('nan'), float('nan')
    t = trades.copy()
    dt = pd.to_datetime(t['entry_time'])
    if unit == 'month':
        labels = dt.dt.to_period('M').astype(str)
    elif unit == 'date':
        labels = dt.dt.normalize().astype(str)
    else:
        raise ValueError(unit)
    groups = [g['pnl_r'].to_numpy(float) for _, g in t.groupby(labels)]
    rng = np.random.default_rng(seed)
    vals = np.empty(iterations)
    for i in range(iterations):
        chosen = rng.integers(0, len(groups), size=len(groups))
        sample = np.concatenate([groups[j] for j in chosen])
        vals[i] = sample.mean()
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def main() -> None:
    manifest = load_manifest(ROOT / 'configs/manifests/nq_candidate_0_1_causal_gap.yaml')
    cfg = manifest.strategy_config()
    engine.SESSION_SPECS = SESSION_SPECS

    one = engine.load_zip(ROOT / 'data/raw/NQ_Futures_-_1min_Bar_2022_2025.zip').copy()
    one['timestamp'] = one['timestamp'] - pd.Timedelta(minutes=1)
    one = one.sort_values('timestamp').reset_index(drop=True)
    bars = pd.read_pickle(BASE / 'bars.pkl')
    sessions = pd.read_csv(BASE / 'sessions.csv', parse_dates=['session_date', 'range_start', 'range_end', 'break_end'])
    eligible = sessions.loc[
        sessions['session'].isin(cfg.sessions)
        & sessions['weekday'].isin(cfg.weekdays)
        & ~sessions['integrity_range_gap_rejected'].astype(bool)
    ].copy().sort_values(['range_start', 'session'])

    # Minute-level causal values.
    one['eth_day'] = (one['timestamp'] - pd.Timedelta(hours=18)).dt.normalize()
    one['tpv'] = ((one['high'] + one['low'] + one['close']) / 3.0) * one['volume']
    one['eth_vwap_1m'] = one.groupby('eth_day')['tpv'].cumsum() / one.groupby('eth_day')['volume'].cumsum().replace(0, np.nan)

    # Completed ETH daily bars.
    daily = one.groupby('eth_day', as_index=False).agg(
        open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'), volume=('volume', 'sum')
    ).sort_values('eth_day').reset_index(drop=True)
    daily = add_ohlc_features(daily, daily=True)
    daily['atr_pct126'] = trailing_percentile(daily['atr20'], 126, 60)
    daily['rv_pct126'] = trailing_percentile(daily['rv20'], 126, 60)
    daily['complete_time'] = daily['eth_day'] + pd.Timedelta(days=1, hours=17)

    # Completed four-hour bars anchored to the ETH open.
    one['h4_start'] = (one['timestamp'] - pd.Timedelta(hours=18)).dt.floor('4h') + pd.Timedelta(hours=18)
    h4 = one.groupby('h4_start', as_index=False).agg(
        open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'), volume=('volume', 'sum')
    ).sort_values('h4_start').reset_index(drop=True)
    h4 = add_ohlc_features(h4, daily=False)
    h4['complete_time'] = h4['h4_start'] + pd.Timedelta(hours=4)

    # Completed CME-style week (Sunday 18:00 through Friday 17:00).
    eth_day = daily['eth_day']
    daily['week_start'] = eth_day - pd.to_timedelta((eth_day.dt.weekday + 1) % 7, unit='D')
    weekly = daily.groupby('week_start', as_index=False).agg(
        week_high=('high', 'max'), week_low=('low', 'min'), week_close=('close', 'last')
    ).sort_values('week_start')
    weekly['complete_time'] = weekly['week_start'] + pd.Timedelta(days=5, hours=17)

    # Session range features known at range end.
    times = one['timestamp'].to_numpy(dtype='datetime64[ns]')
    opens = one['open'].to_numpy(float)
    volumes = one['volume'].to_numpy(float)
    vwaps = one['eth_vwap_1m'].to_numpy(float)
    range_open, range_volume, range_vwap = [], [], []
    for s in eligible.itertuples(index=False):
        j0 = int(np.searchsorted(times, np.datetime64(pd.Timestamp(s.range_start)), side='left'))
        j1 = int(np.searchsorted(times, np.datetime64(pd.Timestamp(s.range_end)), side='left'))
        range_open.append(float(opens[j0]) if j0 < len(opens) else np.nan)
        range_volume.append(float(np.sum(volumes[j0:j1])) if j1 > j0 else np.nan)
        range_vwap.append(float(vwaps[j1 - 1]) if j1 > j0 else np.nan)
    eligible['range_open'] = range_open
    eligible['range_volume'] = range_volume
    eligible['range_vwap_end'] = range_vwap
    eligible['range_mid'] = (eligible['range_high'] + eligible['range_low']) / 2.0

    # Merge the latest completed HTF bars available before range_start.
    session_features = eligible.sort_values('range_start').copy()
    daily_cols = ['complete_time', 'high', 'low', 'close', 'atr20', 'ema20', 'ema50', 'ema20_slope_norm', 'adx14', 'rv20', 'atr_pct126', 'rv_pct126', 'atr_change5', 'rv_change5']
    session_features = pd.merge_asof(
        session_features, daily[daily_cols].sort_values('complete_time'),
        left_on='range_start', right_on='complete_time', direction='backward', allow_exact_matches=True,
        suffixes=('', '_d1')
    ).rename(columns={
        'high': 'prev_d1_high', 'low': 'prev_d1_low', 'close': 'prev_d1_close', 'atr20': 'd1_atr20',
        'ema20': 'd1_ema20', 'ema50': 'd1_ema50', 'ema20_slope_norm': 'd1_ema20_slope_norm',
        'adx14': 'd1_adx14', 'rv20': 'd1_rv20', 'atr_pct126': 'd1_atr_pct126', 'rv_pct126': 'd1_rv_pct126',
        'atr_change5': 'd1_atr_change5', 'rv_change5': 'd1_rv_change5', 'complete_time': 'd1_complete_time'
    })
    h4_cols = ['complete_time', 'close', 'atr20', 'ema20', 'ema50', 'ema20_slope_norm', 'adx14', 'er20']
    session_features = pd.merge_asof(
        session_features.sort_values('range_start'), h4[h4_cols].sort_values('complete_time'),
        left_on='range_start', right_on='complete_time', direction='backward', allow_exact_matches=True,
        suffixes=('', '_h4')
    ).rename(columns={
        'close': 'h4_close', 'atr20': 'h4_atr20', 'ema20': 'h4_ema20', 'ema50': 'h4_ema50',
        'ema20_slope_norm': 'h4_ema20_slope_norm', 'adx14': 'h4_adx14', 'er20': 'h4_er20',
        'complete_time': 'h4_complete_time'
    })
    session_features = pd.merge_asof(
        session_features.sort_values('range_start'), weekly[['complete_time', 'week_high', 'week_low', 'week_close']].sort_values('complete_time'),
        left_on='range_start', right_on='complete_time', direction='backward', allow_exact_matches=True
    ).rename(columns={'complete_time': 'week_complete_time'})

    session_features['range_atr_ratio'] = session_features['range_size'] / session_features['d1_atr20']
    session_features = session_features.sort_values(['session', 'range_start']).reset_index(drop=True)
    session_features['range_atr_percentile'] = same_session_prior_percentile(session_features, 'range_atr_ratio')
    session_features['range_volume_median60'] = session_features.groupby('session')['range_volume'].transform(
        lambda s: s.shift(1).rolling(60, min_periods=20).median()
    )
    session_features['range_volume_ratio'] = session_features['range_volume'] / session_features['range_volume_median60']

    # Generate and independently simulate all signals once.
    signals, funnel = engine.generate_signals(bars, eligible, cfg)
    one_times = one['timestamp'].to_numpy(dtype='datetime64[ns]').astype(np.int64)
    one_open = one['open'].to_numpy(float)
    one_high = one['high'].to_numpy(float)
    one_low = one['low'].to_numpy(float)
    one_close = one['close'].to_numpy(float)
    gaps = _gap_table(one)
    unsafe_prev, unsafe_curr = _gap_intervals(gaps, 'reject_trade_bridge')
    cached_trades: dict[int, object] = {}
    signal_records = []
    for signal_id, sig in enumerate(signals):
        trade = engine._simulate_trade_np(
            one_times, one_open, one_high, one_low, one_close, bars, sig, cfg,
            unsafe_previous_ns=unsafe_prev, unsafe_current_ns=unsafe_curr, gap_policy='liquidate'
        )
        if trade is not None:
            cached_trades[signal_id] = trade
        b = bars.iloc[sig.entry_index]
        signal_records.append({
            'signal_id': signal_id, 'session': sig.session, 'session_date': pd.Timestamp(sig.session_date).normalize(),
            'direction': sig.direction, 'entry_time': sig.entry_time, 'entry_index': sig.entry_index,
            'entry_price_raw': sig.entry_price_raw, 'sweep_index': sig.sweep_index, 'sweep_extreme': sig.sweep_extreme,
            'range_high_signal': sig.range_high, 'range_low_signal': sig.range_low, 'pivot': sig.pivot,
            'sweep_score_signal': sig.sweep_score, 'day_of_week_signal': sig.day_of_week,
            'entry_volume': float(b['volume']),
            'entry_rel_volume': float(b['volume'] / b['vol_sma20']) if np.isfinite(b['vol_sma20']) and b['vol_sma20'] != 0 else np.nan,
            'entry_vwap': float(b['eth_vwap']),
        })
    signal_rows = pd.DataFrame(signal_records)
    signal_rows = signal_rows.merge(
        session_features, on=['session_date', 'session'], how='left', validate='many_to_one', suffixes=('', '_session')
    )

    # Directional and regime classifications.
    signal_rows['d1_trend_dir'] = np.select(
        [(signal_rows['d1_ema20'] > signal_rows['d1_ema50']) & (signal_rows['d1_ema20_slope_norm'] > 0),
         (signal_rows['d1_ema20'] < signal_rows['d1_ema50']) & (signal_rows['d1_ema20_slope_norm'] < 0)],
        [1, -1], default=0
    )
    signal_rows['h4_trend_dir'] = np.select(
        [(signal_rows['h4_ema20'] > signal_rows['h4_ema50']) & (signal_rows['h4_ema20_slope_norm'] > 0),
         (signal_rows['h4_ema20'] < signal_rows['h4_ema50']) & (signal_rows['h4_ema20_slope_norm'] < 0)],
        [1, -1], default=0
    )
    def relative_cat(trend: pd.Series) -> np.ndarray:
        return np.select([trend == signal_rows['direction'], trend == -signal_rows['direction']], ['aligned', 'countertrend'], default='neutral')
    signal_rows['F1_D1_DIRECTION'] = relative_cat(signal_rows['d1_trend_dir'])
    signal_rows['F2_H4_DIRECTION'] = relative_cat(signal_rows['h4_trend_dir'])
    signal_rows['F3_DIRECTION_CONFLUENCE'] = np.select(
        [(signal_rows['F1_D1_DIRECTION'] == 'aligned') & (signal_rows['F2_H4_DIRECTION'] == 'aligned'),
         (signal_rows['F1_D1_DIRECTION'] == 'countertrend') & (signal_rows['F2_H4_DIRECTION'] == 'countertrend'),
         (signal_rows['F1_D1_DIRECTION'] == 'neutral') | (signal_rows['F2_H4_DIRECTION'] == 'neutral')],
        ['both_aligned', 'both_countertrend', 'one_or_both_neutral'], default='mixed'
    )
    vol_score = signal_rows[['d1_atr_pct126', 'd1_rv_pct126']].mean(axis=1)
    signal_rows['F4_D1_VOLATILITY'] = np.select([vol_score < 1/3, vol_score >= 2/3], ['low_0_33', 'high_67_100'], default='middle_33_67')
    signal_rows.loc[vol_score.isna(), 'F4_D1_VOLATILITY'] = 'unavailable'
    nontrend = (signal_rows['d1_adx14'] < 20) & (signal_rows['h4_adx14'] < 20) & (signal_rows['h4_er20'] < 0.25)
    strong = ((signal_rows['d1_adx14'] >= 25) & (signal_rows['h4_adx14'] >= 25)) | (signal_rows['h4_er20'] >= 0.35)
    signal_rows['F5_HTF_TREND_STRENGTH'] = np.select([nontrend, strong], ['nontrend', 'strong_trend'], default='transition')
    signal_rows.loc[signal_rows[['d1_adx14','h4_adx14','h4_er20']].isna().any(axis=1), 'F5_HTF_TREND_STRENGTH'] = 'unavailable'
    rp = signal_rows['range_atr_percentile']
    signal_rows['F6_RANGE_VOLATILITY_FIT'] = np.select([rp < 1/3, rp >= 2/3], ['compressed', 'expanded'], default='normal')
    signal_rows.loc[rp.isna(), 'F6_RANGE_VOLATILITY_FIT'] = 'unavailable'
    transition_score = signal_rows[['d1_atr_change5', 'd1_rv_change5']].mean(axis=1)
    signal_rows['F7_VOLATILITY_TRANSITION'] = np.select([transition_score < -0.05, transition_score > 0.05], ['contracting', 'expanding'], default='stable')
    signal_rows.loc[transition_score.isna(), 'F7_VOLATILITY_TRANSITION'] = 'unavailable'

    day_dist = np.where(signal_rows['direction'] > 0,
                        (signal_rows['range_low'] - signal_rows['prev_d1_low']).abs(),
                        (signal_rows['range_high'] - signal_rows['prev_d1_high']).abs()) / signal_rows['d1_atr20']
    outside_day = (signal_rows['range_mid'] < signal_rows['prev_d1_low']) | (signal_rows['range_mid'] > signal_rows['prev_d1_high'])
    signal_rows['F8_PRIOR_DAY_LOCATION'] = np.select([day_dist <= 0.25, outside_day], ['near_directional_extreme_le_0_25ATR', 'outside_prior_range'], default='inside_midrange')
    signal_rows.loc[~np.isfinite(day_dist), 'F8_PRIOR_DAY_LOCATION'] = 'unavailable'

    week_dist = np.where(signal_rows['direction'] > 0,
                         (signal_rows['range_low'] - signal_rows['week_low']).abs(),
                         (signal_rows['range_high'] - signal_rows['week_high']).abs()) / signal_rows['d1_atr20']
    outside_week = (signal_rows['range_mid'] < signal_rows['week_low']) | (signal_rows['range_mid'] > signal_rows['week_high'])
    signal_rows['F9_PRIOR_WEEK_LOCATION'] = np.select([week_dist <= 0.40, outside_week], ['near_directional_extreme_le_0_40ATR', 'outside_week'], default='inside_week')
    signal_rows.loc[~np.isfinite(week_dist), 'F9_PRIOR_WEEK_LOCATION'] = 'unavailable'

    gap_norm = (signal_rows['range_open'] - signal_rows['prev_d1_close']) / signal_rows['d1_atr20']
    signal_rows['F10_OVERNIGHT_GAP'] = np.select(
        [gap_norm.abs() < 0.10, gap_norm * signal_rows['direction'] < 0],
        ['small_gap_abs_lt_0_10ATR', 'mean_reversion_aligned'], default='continuation_aligned'
    )
    signal_rows.loc[gap_norm.isna(), 'F10_OVERNIGHT_GAP'] = 'unavailable'

    volume_score = np.sqrt(signal_rows['range_volume_ratio'] * signal_rows['entry_rel_volume'])
    signal_rows['F11_VOLUME_CONTEXT'] = np.select([volume_score < 0.85, volume_score > 1.15], ['low', 'high'], default='normal')
    signal_rows.loc[volume_score.isna(), 'F11_VOLUME_CONTEXT'] = 'unavailable'

    range_side = np.sign(signal_rows['range_mid'] - signal_rows['range_vwap_end'])
    entry_side = np.sign(signal_rows['entry_price_raw'] - signal_rows['entry_vwap'])
    toward = signal_rows['direction'] * (signal_rows['entry_vwap'] - signal_rows['entry_price_raw']) > 0
    crossing = range_side != entry_side
    signal_rows['F12_VWAP_AND_VALUE_LOCATION'] = np.select([crossing, toward], ['crossing_value', 'reversion_toward_value'], default='extension_away_from_value')
    signal_rows.loc[signal_rows[['range_vwap_end','entry_vwap']].isna().any(axis=1), 'F12_VWAP_AND_VALUE_LOCATION'] = 'unavailable'

    # Baseline reconstruction from cached independent signal simulations.
    baseline_trades, baseline_qualifying = portfolio_from_mask(signal_rows, cached_trades, pd.Series(True, index=signal_rows.index))
    baseline_csv = pd.read_csv(BASE / 'trades.csv')
    stable_cols = ['session','session_date','direction','entry_time','exit_time','entry_price','stop_price','exit_reason','pnl_r']
    left = baseline_trades[stable_cols].copy().reset_index(drop=True)
    right = baseline_csv[stable_cols].copy().reset_index(drop=True)
    for c in ['session_date','entry_time','exit_time']:
        left[c] = pd.to_datetime(left[c])
        right[c] = pd.to_datetime(right[c])
    keys=['session','session_date','direction','entry_time']
    lm=left.merge(right, on=keys, how='outer', suffixes=('_left','_right'), indicator=True)
    changed = lm.loc[lm['_merge'] == 'both'].copy()
    changed['delta'] = changed['pnl_r_left'] - changed['pnl_r_right']
    mismatch = (len(left) != len(right) or (lm['_merge'] != 'both').any() or (changed['delta'].abs() > 1e-12).any())
    if mismatch:
        print('BASELINE_MISMATCH', {'left_len': len(left), 'right_len': len(right), 'left_net': float(left.pnl_r.sum()), 'right_net': float(right.pnl_r.sum())})
        print(lm.loc[lm['_merge']!='both'].head(30).to_string(index=False))
        print('changed common', changed.loc[changed.delta.abs()>1e-12].head(30).to_string(index=False))
        raise RuntimeError('Independent cached-signal reconstruction does not match frozen baseline')


    opportunity_index = pd.MultiIndex.from_frame(
        eligible[['session_date','session']].assign(session_date=lambda d: pd.to_datetime(d['session_date']).dt.normalize()).drop_duplicates().sort_values(['session_date','session'])
    )
    baseline_vector = return_vector(baseline_trades, opportunity_index)
    baseline_metrics = metrics(baseline_trades)

    rows = []
    vectors: dict[tuple[str,str], np.ndarray] = {}
    trade_outputs: dict[tuple[str,str], pd.DataFrame] = {}
    for family, categories in FAMILY_CATEGORIES.items():
        for category in categories:
            mask = signal_rows[family] == category
            trades, qualifying = portfolio_from_mask(signal_rows, cached_trades, mask)
            m = metrics(trades)
            years, halves = period_nets(trades)
            session_share, half_share = concentration(trades, m['net_r'])
            month_lo, month_hi = bootstrap_interval(trades, 'month')
            date_lo, date_hi = bootstrap_interval(trades, 'date', seed=SEED+1)
            record = {
                'family': family, 'category': category, 'qualifying_signals': qualifying,
                'available_signals': int((signal_rows[family] != 'unavailable').sum()),
                'eligible_sessions': len(opportunity_index), 'r_per_100_sessions': m['net_r'] / len(opportunity_index) * 100,
                **m, 'two_tick_expectancy_r': cost_expectancy(trades, 2.0),
                'four_tick_expectancy_r': cost_expectancy(trades, 4.0),
                'month_bootstrap_lo95': month_lo, 'month_bootstrap_hi95': month_hi,
                'date_bootstrap_lo95': date_lo, 'date_bootstrap_hi95': date_hi,
                'session_max_net_share': session_share, 'halfyear_max_net_share': half_share,
                'net_2023': years.get('2023', 0.0), 'net_2024': years.get('2024', 0.0), 'net_2025': years.get('2025', 0.0),
            }
            for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2']:
                record[f'net_{h}'] = halves.get(h, 0.0)
            rows.append(record)
            vectors[(family, category)] = return_vector(trades, opportunity_index)
            trade_outputs[(family, category)] = trades

    results = pd.DataFrame(rows)
    for family, categories in FAMILY_CATEGORIES.items():
        dates = pd.to_datetime(opportunity_index.get_level_values('session_date')).normalize().to_numpy()
        diff_matrix = np.column_stack([vectors[(family, c)] - baseline_vector for c in categories])
        tvals, pvals = familywise_adjusted_p(diff_matrix, dates, seed=SEED + list(FAMILY_CATEGORIES).index(family))
        edge_matrix = np.column_stack([vectors[(family, c)] for c in categories])
        edge_t, edge_p = familywise_adjusted_p(edge_matrix, dates, seed=SEED + 100 + list(FAMILY_CATEGORIES).index(family))
        for c, t, p, et, ep in zip(categories, tvals, pvals, edge_t, edge_p, strict=True):
            sel = (results['family'] == family) & (results['category'] == c)
            results.loc[sel, 'incremental_t_per_session'] = t
            results.loc[sel, 'familywise_incremental_p'] = p
            results.loc[sel, 'edge_t_per_session'] = et
            results.loc[sel, 'familywise_edge_p'] = ep

    # Promotion gate, plus transparent component flags.
    base_rr = baseline_metrics['return_dd']
    base_exp = baseline_metrics['expectancy_r']
    for idx, r in results.iterrows():
        year_nets = [r['net_2023'], r['net_2024'], r['net_2025']]
        year_ok = all(v > 0 for v in year_nets) or (sum(v > 0 for v in year_nets) >= 2 and min(year_nets) >= -5)
        effect_ok = (r['expectancy_r'] >= base_exp + 0.03) or (
            r['max_drawdown_r'] <= baseline_metrics['max_drawdown_r'] * 0.80 and r['expectancy_r'] >= base_exp
        )
        flags = {
            'gate_sample': bool(r['trades'] >= 250 and r['qualifying_signals'] >= baseline_qualifying * 0.50),
            'gate_effect': bool(effect_ok),
            'gate_return_dd': bool(r['return_dd'] >= base_rr * 1.15),
            'gate_years': bool(year_ok),
            'gate_cost': bool(r['two_tick_expectancy_r'] > 0),
            'gate_concentration': bool(r['session_max_net_share'] <= 0.60 and r['halfyear_max_net_share'] <= 0.60),
            'gate_familywise': bool(r['familywise_incremental_p'] <= 0.05),
        }
        for k, v in flags.items():
            results.loc[idx, k] = v
        results.loc[idx, 'decision'] = 'HOLD_FOR_FRESH_OOS' if all(flags.values()) else (
            'DIAGNOSTIC_ONLY' if flags['gate_sample'] and (flags['gate_effect'] or flags['gate_return_dd']) else 'REJECT'
        )

    # Stability measure used only to determine whether limited interaction tests are allowed.
    for idx, r in results.iterrows():
        stable = 0
        for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2']:
            start = pd.Timestamp(h[:4] + ('-01-01' if h.endswith('H1') else '-07-01'))
            end = start + pd.DateOffset(months=6)
            bt = baseline_trades[(pd.to_datetime(baseline_trades['entry_time']) >= start) & (pd.to_datetime(baseline_trades['entry_time']) < end)]
            ct = trade_outputs[(r['family'], r['category'])]
            ct = ct[(pd.to_datetime(ct['entry_time']) >= start) & (pd.to_datetime(ct['entry_time']) < end)]
            if len(ct) >= 10 and ct['pnl_r'].mean() > (bt['pnl_r'].mean() if len(bt) else 0):
                stable += 1
        results.loc[idx, 'halfyears_expectancy_above_baseline'] = stable
        results.loc[idx, 'interaction_parent_eligible'] = bool(stable >= 4 and (r['trades'] >= 250 or r['trades'] >= baseline_metrics['trades'] * 0.55))

    results = results.sort_values(['decision','return_dd','expectancy_r'], ascending=[True,False,False]).reset_index(drop=True)
    results.to_csv(OUT / 'univariate_results.csv', index=False)
    signal_rows.to_csv(OUT / 'signal_context.csv', index=False)
    independent_rows = []
    for signal_id, trade in cached_trades.items():
        row = {'signal_id': signal_id, **asdict(trade)}
        independent_rows.append(row)
    pd.DataFrame(independent_rows).sort_values('signal_id').to_csv(OUT / 'signal_independent_trades.csv', index=False)
    session_features.to_csv(OUT / 'session_context.csv', index=False)

    # Compact family table and audit metadata.
    family_best = results.sort_values(['family','return_dd'], ascending=[True,False]).groupby('family', as_index=False).first()
    family_best.to_csv(OUT / 'family_best.csv', index=False)
    audit = {
        'study_id': 'DTR_ADVANCED_CONTEXT_20260722',
        'baseline': baseline_metrics,
        'baseline_signals': len(signal_rows),
        'baseline_qualifying_signals': baseline_qualifying,
        'eligible_sessions': len(opportunity_index),
        'funnel_before_position_overlap': funnel.as_dict(),
        'feature_thresholds': {
            'volatility_percentile': [1/3, 2/3],
            'trend_strength_nontrend': 'D1 ADX<20 and H4 ADX<20 and H4 ER20<0.25',
            'trend_strength_strong': '(D1 ADX>=25 and H4 ADX>=25) or H4 ER20>=0.35',
            'volatility_transition': 'mean(ATR20 change5,RV20 change5) below -5% / above +5%',
            'prior_day_near': '0.25 D1 ATR',
            'prior_week_near': '0.40 D1 ATR',
            'small_gap': '0.10 D1 ATR',
            'volume_score': 'sqrt(range volume ratio * entry relative volume), low<0.85, high>1.15',
        },
        'files': {},
    }
    for name in ['univariate_results.csv','family_best.csv','signal_context.csv','signal_independent_trades.csv','session_context.csv']:
        audit['files'][name] = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
    (OUT / 'stage1_audit.json').write_text(json.dumps(audit, indent=2, default=str))

    print(json.dumps({
        'baseline': baseline_metrics,
        'signals': len(signal_rows), 'eligible_sessions': len(opportunity_index),
        'decisions': results['decision'].value_counts().to_dict(),
        'interaction_parent_eligible': results.loc[results['interaction_parent_eligible'], ['family','category','trades','expectancy_r','return_dd','halfyears_expectancy_above_baseline']].to_dict('records'),
        'top_by_return_dd': results.nlargest(10, 'return_dd')[['family','category','trades','expectancy_r','net_r','max_drawdown_r','return_dd','familywise_incremental_p','decision']].to_dict('records'),
    }, indent=2, default=str))


if __name__ == '__main__':
    main()
