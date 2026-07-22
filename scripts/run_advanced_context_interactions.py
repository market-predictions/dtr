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
from run_advanced_context_broad import RULES, portfolio

OUT = Path('/mnt/data/dtr-advanced-results')
BASE = Path('/mnt/data/dtr-advanced-baseline')

INTERACTIONS = {
    'I1_NOT_COMPRESSED_AND_NOT_NEAR_PRIOR_DAY': ('E5_EXCLUDE_COMPRESSED_RANGE','E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME'),
    'I2_MIXED_NEUTRAL_CONFLUENCE_AND_NOT_COMPRESSED': ('E3_KEEP_MIXED_OR_NEUTRAL_CONFLUENCE','E5_EXCLUDE_COMPRESSED_RANGE'),
    'I3_MIXED_NEUTRAL_CONFLUENCE_AND_NOT_NEAR_PRIOR_DAY': ('E3_KEEP_MIXED_OR_NEUTRAL_CONFLUENCE','E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME'),
    'I4_NOT_D1_COUNTERTREND_AND_NOT_COMPRESSED': ('E1_EXCLUDE_D1_COUNTERTREND','E5_EXCLUDE_COMPRESSED_RANGE'),
    'I5_NOT_D1_COUNTERTREND_AND_NOT_NEAR_PRIOR_DAY': ('E1_EXCLUDE_D1_COUNTERTREND','E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME'),
    'I6_NOT_MIDDLE_D1_VOL_AND_NOT_COMPRESSED': ('E4_EXCLUDE_MIDDLE_D1_VOLATILITY','E5_EXCLUDE_COMPRESSED_RANGE'),
}


def broad_mask(rule_id: str, s: pd.DataFrame) -> pd.Series:
    mask = RULES[rule_id](s)
    if rule_id == 'E4_EXCLUDE_MIDDLE_D1_VOLATILITY':
        mask = mask | (s['F4_D1_VOLATILITY'] == 'unavailable')
    elif rule_id == 'E5_EXCLUDE_COMPRESSED_RANGE':
        mask = mask | (s['F6_RANGE_VOLATILITY_FIT'] == 'unavailable')
    elif rule_id == 'E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME':
        mask = mask | (s['F8_PRIOR_DAY_LOCATION'] == 'unavailable')
    return mask


def main() -> None:
    s = pd.read_csv(OUT/'signal_context.csv', parse_dates=['session_date','entry_time'])
    independent = pd.read_csv(OUT/'signal_independent_trades.csv', parse_dates=['session_date','entry_time','exit_time','gap_previous_timestamp','gap_current_timestamp'])
    sessions = pd.read_csv(OUT/'session_context.csv', parse_dates=['session_date'])
    opportunity_index = pd.MultiIndex.from_frame(
        sessions[['session_date','session']].assign(session_date=lambda d: pd.to_datetime(d.session_date).dt.normalize())
        .drop_duplicates().sort_values(['session_date','session'])
    )
    baseline, _ = portfolio(s, independent, pd.Series(True,index=s.index))
    bm=metrics(baseline)
    exp=json.load(open(BASE/'summary.json'))['metrics']
    if len(baseline)!=int(exp['trades']) or abs(bm['net_r']-exp['net_r'])>1e-10:
        raise RuntimeError('interaction baseline mismatch')
    base_vec=return_vector(baseline,opportunity_index)

    rows=[]; vectors=[]; portfolios={}
    for iid,(a,b) in INTERACTIONS.items():
        mask=broad_mask(a,s)&broad_mask(b,s)
        trades, qualifying=portfolio(s,independent,mask)
        m=metrics(trades)
        years,halves=period_nets(trades)
        session_share,half_share=concentration(trades,m['net_r'])
        mlo,mhi=bootstrap_interval(trades,'month',iterations=5000,seed=SEED+50)
        dlo,dhi=bootstrap_interval(trades,'date',iterations=5000,seed=SEED+51)
        rec={
            'interaction_id':iid,'parent_a':a,'parent_b':b,'qualifying_signals':qualifying,
            'eligible_sessions':len(opportunity_index),'r_per_100_sessions':m['net_r']/len(opportunity_index)*100,
            **m,
            'two_tick_expectancy_r':cost_expectancy(trades,2.0),
            'four_tick_expectancy_r':cost_expectancy(trades,4.0),
            'month_bootstrap_lo95':mlo,'month_bootstrap_hi95':mhi,
            'date_bootstrap_lo95':dlo,'date_bootstrap_hi95':dhi,
            'session_max_net_share':session_share,'halfyear_max_net_share':half_share,
            'net_2023':years.get('2023',0.0),'net_2024':years.get('2024',0.0),'net_2025':years.get('2025',0.0),
        }
        for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2']:
            rec[f'net_{h}']=halves.get(h,0.0)
        rows.append(rec); vectors.append(return_vector(trades,opportunity_index)); portfolios[iid]=trades

    result=pd.DataFrame(rows)
    dates=pd.to_datetime(opportunity_index.get_level_values('session_date')).normalize().to_numpy()
    edge=np.column_stack(vectors)
    et,ep=familywise_adjusted_p(edge,dates,iterations=10000,seed=SEED+60)
    it,ip=familywise_adjusted_p(edge-base_vec[:,None],dates,iterations=10000,seed=SEED+61)
    result['edge_t_per_session']=et; result['familywise_edge_p']=ep
    result['incremental_t_per_session']=it; result['familywise_incremental_p']=ip

    for i,r in result.iterrows():
        years=[r.net_2023,r.net_2024,r.net_2025]
        flags={
            'gate_sample':bool(r.trades>=250),
            'gate_effect':bool((r.expectancy_r>=bm['expectancy_r']+0.03) or (r.max_drawdown_r<=bm['max_drawdown_r']*.8 and r.expectancy_r>=bm['expectancy_r'])),
            'gate_return_dd':bool(r.return_dd>=bm['return_dd']*1.15),
            'gate_years':bool(all(x>0 for x in years) or (sum(x>0 for x in years)>=2 and min(years)>=-5)),
            'gate_cost':bool(r.two_tick_expectancy_r>0),
            'gate_concentration':bool(r.session_max_net_share<=.60 and r.halfyear_max_net_share<=.60),
            'gate_familywise_edge':bool(r.familywise_edge_p<=.05),
            'gate_familywise_incremental':bool(r.familywise_incremental_p<=.10),
        }
        for k,v in flags.items(): result.loc[i,k]=v
        result.loc[i,'decision']='HOLD_FOR_FRESH_OOS' if all(flags.values()) else (
            'DIAGNOSTIC_ONLY' if flags['gate_sample'] and flags['gate_effect'] and flags['gate_return_dd'] and flags['gate_cost'] else 'REJECT'
        )
        stable=0
        t=portfolios[r.interaction_id]
        for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2']:
            y=int(h[:4]); start=pd.Timestamp(y,1 if h.endswith('H1') else 7,1); end=start+pd.DateOffset(months=6)
            bt=baseline[(pd.to_datetime(baseline.entry_time)>=start)&(pd.to_datetime(baseline.entry_time)<end)]
            ct=t[(pd.to_datetime(t.entry_time)>=start)&(pd.to_datetime(t.entry_time)<end)]
            if len(ct)>=15 and ct.pnl_r.mean()>(bt.pnl_r.mean() if len(bt) else 0): stable+=1
        result.loc[i,'halfyears_expectancy_above_baseline']=stable

    result=result.sort_values(['decision','return_dd'],ascending=[True,False]).reset_index(drop=True)
    result.to_csv(OUT/'interaction_results.csv',index=False)
    for iid,t in portfolios.items(): t.to_csv(OUT/f'{iid}_trades.csv',index=False)
    audit={
        'study_id':'DTR_ADVANCED_CONTEXT_INTERACTIONS_20260722','baseline':bm,
        'preregistration_sha256':hashlib.sha256((OUT/'interaction_preregistration.json').read_bytes()).hexdigest(),
        'result_sha256':hashlib.sha256((OUT/'interaction_results.csv').read_bytes()).hexdigest(),
        'decisions':result.decision.value_counts().to_dict(),
    }
    (OUT/'interaction_audit.json').write_text(json.dumps(audit,indent=2,default=str))
    print(json.dumps({'baseline':bm,'results':result[['interaction_id','trades','expectancy_r','net_r','max_drawdown_r','return_dd','two_tick_expectancy_r','familywise_edge_p','familywise_incremental_p','halfyears_expectancy_above_baseline','decision']].to_dict('records')},indent=2,default=str))

if __name__=='__main__': main()
