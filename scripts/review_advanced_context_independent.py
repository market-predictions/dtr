# ruff: noqa
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path('/mnt/data/dtr-advanced-results')
BASE=Path('/mnt/data/dtr-advanced-baseline')
SEED=20260722


def manual_metrics(t:pd.DataFrame)->dict[str,float]:
    r=t['pnl_r'].to_numpy(float)
    if len(r)==0:return {'trades':0,'net_r':0.0,'expectancy_r':np.nan,'profit_factor':np.nan,'max_drawdown_r':np.nan,'return_dd':np.nan}
    eq=np.cumsum(r); peak=np.maximum.accumulate(np.r_[0.0,eq]); dd=peak[1:]-eq
    wins=r[r>0].sum(); losses=-r[r<0].sum(); mdd=float(dd.max(initial=0.0)); net=float(r.sum())
    return {'trades':len(r),'net_r':net,'expectancy_r':float(r.mean()),'profit_factor':float(wins/losses) if losses>0 else np.inf,'max_drawdown_r':mdd,'return_dd':float(net/mdd) if mdd>0 else np.nan}


def vector(t:pd.DataFrame,index:pd.MultiIndex)->np.ndarray:
    if t.empty:return np.zeros(len(index))
    x=t.copy();x['session_date']=pd.to_datetime(x.session_date).dt.normalize()
    return x.groupby(['session_date','session']).pnl_r.sum().reindex(index,fill_value=0.0).to_numpy(float)


def paired_date_bootstrap(diff:np.ndarray,dates:np.ndarray,iterations:int=20000)->dict[str,float]:
    unique=pd.Index(dates).unique(); groups=[np.flatnonzero(dates==d) for d in unique]
    rng=np.random.default_rng(SEED+801); vals=np.empty(iterations)
    for i in range(iterations):
        choice=rng.integers(0,len(groups),len(groups)); rows=np.concatenate([groups[j] for j in choice]); vals[i]=diff[rows].sum()
    return {'observed_net_delta_r':float(diff.sum()),'lo95_net_delta_r':float(np.quantile(vals,.025)),'hi95_net_delta_r':float(np.quantile(vals,.975)),'prob_delta_positive':float(np.mean(vals>0))}


def assert_close(a:float,b:float,label:str,tol:float=1e-9):
    if not (np.isnan(a) and np.isnan(b)) and abs(a-b)>tol:raise AssertionError(f'{label}: {a} != {b}')


def main():
    signals=pd.read_csv(ROOT/'signal_context.csv',parse_dates=['session_date','entry_time','range_start','range_end','d1_complete_time','h4_complete_time','week_complete_time'])
    sessions=pd.read_csv(ROOT/'session_context.csv',parse_dates=['session_date','range_start','range_end','d1_complete_time','h4_complete_time','week_complete_time'])
    baseline=pd.read_csv(BASE/'trades.csv',parse_dates=['session_date','entry_time','exit_time'])
    index=pd.MultiIndex.from_frame(sessions[['session_date','session']].assign(session_date=lambda d:pd.to_datetime(d.session_date).dt.normalize()).drop_duplicates().sort_values(['session_date','session']))
    dates=pd.to_datetime(index.get_level_values('session_date')).normalize().to_numpy()
    bvec=vector(baseline,index)

    causality={
      'signals':len(signals),'sessions':len(sessions),
      'd1_after_range_start':int((signals.d1_complete_time.notna()&(signals.d1_complete_time>signals.range_start)).sum()),
      'h4_after_range_start':int((signals.h4_complete_time.notna()&(signals.h4_complete_time>signals.range_start)).sum()),
      'week_after_range_start':int((signals.week_complete_time.notna()&(signals.week_complete_time>signals.range_start)).sum()),
      'range_end_after_entry':int((signals.range_end>signals.entry_time).sum()),
    }
    if any(causality[k] for k in ['d1_after_range_start','h4_after_range_start','week_after_range_start','range_end_after_entry']):
        raise AssertionError(f'causality failure {causality}')

    # Recompute every reported portfolio metric without importing project code.
    checks=[]
    broad=pd.read_csv(ROOT/'broad_exclusion_results.csv')
    for r in broad.itertuples(index=False):
        path=ROOT/f'{r.rule_id}_trades.csv'; t=pd.read_csv(path,parse_dates=['session_date','entry_time','exit_time']); m=manual_metrics(t)
        for k in ['trades','net_r','expectancy_r','profit_factor','max_drawdown_r','return_dd']:assert_close(float(m[k]),float(getattr(r,k)),f'{r.rule_id}:{k}')
        checks.append({'candidate':r.rule_id,'type':'broad','metrics_verified':True,**paired_date_bootstrap(vector(t,index)-bvec,dates)})
    inter=pd.read_csv(ROOT/'interaction_results.csv')
    for r in inter.itertuples(index=False):
        path=ROOT/f'{r.interaction_id}_trades.csv'; t=pd.read_csv(path,parse_dates=['session_date','entry_time','exit_time']); m=manual_metrics(t)
        for k in ['trades','net_r','expectancy_r','profit_factor','max_drawdown_r','return_dd']:assert_close(float(m[k]),float(getattr(r,k)),f'{r.interaction_id}:{k}')
        checks.append({'candidate':r.interaction_id,'type':'interaction','metrics_verified':True,**paired_date_bootstrap(vector(t,index)-bvec,dates)})

    paired=pd.DataFrame(checks).sort_values('observed_net_delta_r',ascending=False)
    paired.to_csv(ROOT/'independent_paired_bootstrap.csv',index=False)

    # Family completeness and feature coverage.
    family_cols=[c for c in signals.columns if c.startswith('F') and c.split('_')[0][1:].isdigit()]
    coverage=[]
    for c in family_cols:
        coverage.append({'family':c,'signals':len(signals),'available':int((signals[c]!='unavailable').sum()),'unavailable':int((signals[c]=='unavailable').sum()),'missing':int(signals[c].isna().sum()),'categories':sorted(signals[c].dropna().unique().tolist())})
    (ROOT/'feature_coverage.json').write_text(json.dumps(coverage,indent=2))

    # File and preregistration integrity.
    tracked=['univariate_results.csv','broad_exclusion_results.csv','interaction_results.csv','adversarial_threshold_sensitivity.csv','broad_exclusion_preregistration.json','interaction_preregistration.json','adversarial_threshold_preregistration.json']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    summary={
      'review_id':'DTR_ADVANCED_CONTEXT_INDEPENDENT_REVIEW_20260722',
      'causality':causality,
      'baseline_manual_metrics':manual_metrics(baseline),
      'metric_reconstruction_checks':len(checks),
      'all_metric_reconstructions_passed':True,
      'paired_bootstrap':paired.to_dict('records'),
      'hashes':hashes,
      'conclusion':'NO_HISTORICAL_PROMOTION; E5 and E6 are the strongest single-factor fresh-OOS challengers; I1 remains an under-sampled interaction challenger only.'
    }
    (ROOT/'independent_review.json').write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))

if __name__=='__main__':main()
