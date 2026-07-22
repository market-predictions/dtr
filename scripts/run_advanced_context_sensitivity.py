# ruff: noqa
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_advanced_context_stage1 import concentration, cost_expectancy, metrics, period_nets
from run_advanced_context_broad import portfolio

OUT=Path('/mnt/data/dtr-advanced-results')
RANGE_THRESHOLDS=[0.25,1/3,0.40]
DAY_THRESHOLDS=[0.20,0.25,0.30]


def evaluate(label:str,mask:pd.Series,s:pd.DataFrame,independent:pd.DataFrame)->tuple[dict,pd.DataFrame]:
    trades,qualifying=portfolio(s,independent,mask)
    m=metrics(trades); years,halves=period_nets(trades); ss,hs=concentration(trades,m['net_r'])
    row={'variant':label,'qualifying_signals':qualifying,**m,'two_tick_expectancy_r':cost_expectancy(trades,2.0),'session_max_net_share':ss,'halfyear_max_net_share':hs,
         'net_2023':years.get('2023',0.0),'net_2024':years.get('2024',0.0),'net_2025':years.get('2025',0.0)}
    for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2']:row[f'net_{h}']=halves.get(h,0.0)
    return row,trades


def main():
    s=pd.read_csv(OUT/'signal_context.csv',parse_dates=['session_date','entry_time'])
    independent=pd.read_csv(OUT/'signal_independent_trades.csv',parse_dates=['session_date','entry_time','exit_time','gap_previous_timestamp','gap_current_timestamp'])
    day_dist=np.where(s['direction']>0,(s['range_low']-s['prev_d1_low']).abs(),(s['range_high']-s['prev_d1_high']).abs())/s['d1_atr20']
    day_dist=pd.Series(day_dist,index=s.index)
    rp=s['range_atr_percentile']
    rows=[]; outputs={}
    for rt in RANGE_THRESHOLDS:
        mask=(rp>=rt)|rp.isna()
        row,t=evaluate(f'RANGE_EXCLUDE_BELOW_{rt:.6f}',mask,s,independent); row.update({'range_threshold':rt,'day_threshold':np.nan,'kind':'single_range'});rows.append(row);outputs[row['variant']]=t
    for dt in DAY_THRESHOLDS:
        mask=(day_dist>dt)|day_dist.isna()
        row,t=evaluate(f'DAY_EXCLUDE_WITHIN_{dt:.2f}ATR',mask,s,independent);row.update({'range_threshold':np.nan,'day_threshold':dt,'kind':'single_day'});rows.append(row);outputs[row['variant']]=t
    for rt in RANGE_THRESHOLDS:
        for dt in DAY_THRESHOLDS:
            mask=((rp>=rt)|rp.isna())&((day_dist>dt)|day_dist.isna())
            row,t=evaluate(f'GRID_RANGE_{rt:.6f}_DAY_{dt:.2f}',mask,s,independent);row.update({'range_threshold':rt,'day_threshold':dt,'kind':'interaction_grid'});rows.append(row);outputs[row['variant']]=t
    result=pd.DataFrame(rows).sort_values(['kind','range_threshold','day_threshold'],na_position='last').reset_index(drop=True)
    result.to_csv(OUT/'adversarial_threshold_sensitivity.csv',index=False)
    grid=result[result.kind=='interaction_grid']
    summary={
      'study_id':'DTR_ADVANCED_CONTEXT_ADVERSARIAL_THRESHOLD_20260722',
      'preregistration_sha256':hashlib.sha256((OUT/'adversarial_threshold_preregistration.json').read_bytes()).hexdigest(),
      'result_sha256':hashlib.sha256((OUT/'adversarial_threshold_sensitivity.csv').read_bytes()).hexdigest(),
      'single_range':result[result.kind=='single_range'][['variant','trades','expectancy_r','net_r','max_drawdown_r','return_dd','two_tick_expectancy_r','net_2023','net_2024','net_2025']].to_dict('records'),
      'single_day':result[result.kind=='single_day'][['variant','trades','expectancy_r','net_r','max_drawdown_r','return_dd','two_tick_expectancy_r','net_2023','net_2024','net_2025']].to_dict('records'),
      'interaction_surface':{
        'trade_range':[int(grid.trades.min()),int(grid.trades.max())],
        'expectancy_range':[float(grid.expectancy_r.min()),float(grid.expectancy_r.max())],
        'net_r_range':[float(grid.net_r.min()),float(grid.net_r.max())],
        'drawdown_range':[float(grid.max_drawdown_r.min()),float(grid.max_drawdown_r.max())],
        'return_dd_range':[float(grid.return_dd.min()),float(grid.return_dd.max())],
        'all_two_tick_positive':bool((grid.two_tick_expectancy_r>0).all()),
        'all_calendar_years_positive':bool((grid[['net_2023','net_2024','net_2025']]>0).all(axis=None)),
      }
    }
    (OUT/'adversarial_threshold_summary.json').write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))

if __name__=='__main__':main()
