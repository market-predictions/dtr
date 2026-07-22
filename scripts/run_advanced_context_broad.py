# ruff: noqa
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_advanced_context_stage1 import (
    SEED,
    bootstrap_interval,
    concentration,
    cost_expectancy,
    familywise_adjusted_p,
    metrics,
    period_nets,
    return_vector,
)

OUT = Path('/mnt/data/dtr-advanced-results')
BASE = Path('/mnt/data/dtr-advanced-baseline')

RULES = {
    'E1_EXCLUDE_D1_COUNTERTREND': lambda s: (s['F1_D1_DIRECTION'] != 'countertrend'),
    'E2_EXCLUDE_H4_COUNTERTREND': lambda s: (s['F2_H4_DIRECTION'] != 'countertrend'),
    'E3_KEEP_MIXED_OR_NEUTRAL_CONFLUENCE': lambda s: s['F3_DIRECTION_CONFLUENCE'].isin(['mixed', 'one_or_both_neutral']),
    'E4_EXCLUDE_MIDDLE_D1_VOLATILITY': lambda s: (s['F4_D1_VOLATILITY'] != 'middle_33_67'),
    'E5_EXCLUDE_COMPRESSED_RANGE': lambda s: (s['F6_RANGE_VOLATILITY_FIT'] != 'compressed'),
    'E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME': lambda s: (s['F8_PRIOR_DAY_LOCATION'] != 'near_directional_extreme_le_0_25ATR'),
}


def portfolio(signal_rows: pd.DataFrame, independent: pd.DataFrame, mask: pd.Series) -> tuple[pd.DataFrame, int]:
    trade_map = {int(r.signal_id): r._asdict() for r in independent.itertuples(index=False)}
    rows = []
    next_free = pd.Timestamp.min
    qualifying = 0
    for r in signal_rows.loc[mask.fillna(False)].sort_values('entry_time').itertuples(index=False):
        qualifying += 1
        trade = trade_map.get(int(r.signal_id))
        if trade is None or pd.Timestamp(r.entry_time) < next_free:
            continue
        trade = dict(trade)
        trade.pop('signal_id', None)
        rows.append(trade)
        next_free = pd.Timestamp(trade['exit_time'])
    return pd.DataFrame(rows), qualifying


def main() -> None:
    s = pd.read_csv(OUT / 'signal_context.csv', parse_dates=['session_date','entry_time'])
    independent = pd.read_csv(OUT / 'signal_independent_trades.csv', parse_dates=['session_date','entry_time','exit_time','gap_previous_timestamp','gap_current_timestamp'])
    session_context = pd.read_csv(OUT / 'session_context.csv', parse_dates=['session_date'])
    opportunity_index = pd.MultiIndex.from_frame(
        session_context[['session_date','session']].assign(session_date=lambda d: pd.to_datetime(d['session_date']).dt.normalize())
        .drop_duplicates().sort_values(['session_date','session'])
    )

    baseline, baseline_signals = portfolio(s, independent, pd.Series(True, index=s.index))
    bm = metrics(baseline)
    expected = json.load(open(BASE / 'summary.json'))['metrics']
    if len(baseline) != int(expected['trades']) or abs(bm['net_r'] - expected['net_r']) > 1e-10:
        raise RuntimeError('Broad-rule baseline reconstruction mismatch')
    base_vector = return_vector(baseline, opportunity_index)

    rows = []
    vectors = []
    portfolios = {}
    masks = {}
    for rule_id, fn in RULES.items():
        mask = fn(s)
        # Warm-up unavailability passes through for single-feature exclusions.
        if rule_id == 'E4_EXCLUDE_MIDDLE_D1_VOLATILITY':
            mask = mask | (s['F4_D1_VOLATILITY'] == 'unavailable')
        elif rule_id == 'E5_EXCLUDE_COMPRESSED_RANGE':
            mask = mask | (s['F6_RANGE_VOLATILITY_FIT'] == 'unavailable')
        elif rule_id == 'E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME':
            mask = mask | (s['F8_PRIOR_DAY_LOCATION'] == 'unavailable')
        trades, qualifying = portfolio(s, independent, mask)
        m = metrics(trades)
        years, halves = period_nets(trades)
        session_share, half_share = concentration(trades, m['net_r'])
        month_lo, month_hi = bootstrap_interval(trades, 'month', iterations=5000, seed=SEED+20)
        date_lo, date_hi = bootstrap_interval(trades, 'date', iterations=5000, seed=SEED+21)
        record = {
            'rule_id': rule_id,
            'qualifying_signals': qualifying,
            'eligible_sessions': len(opportunity_index),
            'r_per_100_sessions': m['net_r'] / len(opportunity_index) * 100,
            **m,
            'two_tick_expectancy_r': cost_expectancy(trades, 2.0),
            'four_tick_expectancy_r': cost_expectancy(trades, 4.0),
            'month_bootstrap_lo95': month_lo,
            'month_bootstrap_hi95': month_hi,
            'date_bootstrap_lo95': date_lo,
            'date_bootstrap_hi95': date_hi,
            'session_max_net_share': session_share,
            'halfyear_max_net_share': half_share,
            'net_2023': years.get('2023',0.0),
            'net_2024': years.get('2024',0.0),
            'net_2025': years.get('2025',0.0),
        }
        for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2']:
            record[f'net_{h}'] = halves.get(h,0.0)
        rows.append(record)
        vector = return_vector(trades, opportunity_index)
        vectors.append(vector)
        portfolios[rule_id] = trades
        masks[rule_id] = mask

    result = pd.DataFrame(rows)
    dates = pd.to_datetime(opportunity_index.get_level_values('session_date')).normalize().to_numpy()
    edge_matrix = np.column_stack(vectors)
    edge_t, edge_p = familywise_adjusted_p(edge_matrix, dates, iterations=10000, seed=SEED+30)
    diff_matrix = edge_matrix - base_vector[:,None]
    inc_t, inc_p = familywise_adjusted_p(diff_matrix, dates, iterations=10000, seed=SEED+31)
    result['edge_t_per_session'] = edge_t
    result['familywise_edge_p'] = edge_p
    result['incremental_t_per_session'] = inc_t
    result['familywise_incremental_p'] = inc_p

    base_exp = bm['expectancy_r']
    base_dd = bm['max_drawdown_r']
    base_rr = bm['return_dd']
    for i, r in result.iterrows():
        years = [r['net_2023'],r['net_2024'],r['net_2025']]
        flags = {
            'gate_sample': bool(r['trades'] >= 250),
            'gate_effect': bool((r['expectancy_r'] >= base_exp + 0.03) or (r['max_drawdown_r'] <= base_dd*0.80 and r['expectancy_r'] >= base_exp)),
            'gate_return_dd': bool(r['return_dd'] >= base_rr*1.15),
            'gate_years': bool(all(x>0 for x in years) or (sum(x>0 for x in years)>=2 and min(years)>=-5)),
            'gate_cost': bool(r['two_tick_expectancy_r'] > 0),
            'gate_concentration': bool(r['session_max_net_share'] <=0.60 and r['halfyear_max_net_share']<=0.60),
            'gate_familywise_edge': bool(r['familywise_edge_p'] <=0.05),
            'gate_familywise_incremental': bool(r['familywise_incremental_p'] <=0.10),
        }
        for k,v in flags.items():
            result.loc[i,k]=v
        result.loc[i,'decision'] = 'HOLD_FOR_FRESH_OOS' if all(flags.values()) else (
            'DIAGNOSTIC_ONLY' if flags['gate_sample'] and flags['gate_effect'] and flags['gate_return_dd'] and flags['gate_cost'] else 'REJECT'
        )

        # Half-year directional stability: expectancy above same-period baseline.
        stable = 0
        t = portfolios[r['rule_id']]
        for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2']:
            y=int(h[:4]); start=pd.Timestamp(y,1 if h.endswith('H1') else 7,1); end=start+pd.DateOffset(months=6)
            bt=baseline[(pd.to_datetime(baseline.entry_time)>=start)&(pd.to_datetime(baseline.entry_time)<end)]
            ct=t[(pd.to_datetime(t.entry_time)>=start)&(pd.to_datetime(t.entry_time)<end)]
            if len(ct)>=20 and ct.pnl_r.mean() > (bt.pnl_r.mean() if len(bt) else 0): stable +=1
        result.loc[i,'halfyears_expectancy_above_baseline']=stable
        result.loc[i,'interaction_parent_eligible']=bool(stable>=4 and r['trades']>=250)

    result=result.sort_values(['decision','return_dd'],ascending=[True,False]).reset_index(drop=True)
    result.to_csv(OUT/'broad_exclusion_results.csv',index=False)
    for rule_id,trades in portfolios.items():
        trades.to_csv(OUT/f'{rule_id}_trades.csv',index=False)

    audit={
        'study_id':'DTR_ADVANCED_CONTEXT_BROAD_EXCLUSIONS_20260722',
        'baseline':bm,
        'baseline_signals':baseline_signals,
        'eligible_sessions':len(opportunity_index),
        'preregistration_sha256':hashlib.sha256((OUT/'broad_exclusion_preregistration.json').read_bytes()).hexdigest(),
        'result_sha256':hashlib.sha256((OUT/'broad_exclusion_results.csv').read_bytes()).hexdigest(),
        'decisions':result.decision.value_counts().to_dict(),
    }
    (OUT/'broad_exclusion_audit.json').write_text(json.dumps(audit,indent=2,default=str))
    print(json.dumps({
        'baseline':bm,
        'results':result[['rule_id','trades','expectancy_r','net_r','max_drawdown_r','return_dd','two_tick_expectancy_r','familywise_edge_p','familywise_incremental_p','halfyears_expectancy_above_baseline','decision']].to_dict('records'),
    },indent=2,default=str))

if __name__=='__main__':
    main()
