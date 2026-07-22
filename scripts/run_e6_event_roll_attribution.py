# ruff: noqa
from __future__ import annotations
import argparse, hashlib, json, math, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

SHA="8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc"
EXPECTED=(304,48.93754952687199,0.16097878133839472,8.632571354238342)

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def drawdown(x):
    a=np.asarray(x,float); eq=np.cumsum(a); peak=np.maximum.accumulate(np.r_[0.,eq])[1:]
    return float(np.max(peak-eq,initial=0.))

def pf(x):
    x=pd.Series(x); g=float(x[x>0].sum()); l=float(-x[x<0].sum())
    return math.inf if l==0 and g>0 else (g/l if l else 0.)

def stats(f):
    if f.empty: return dict(trades=0,net_r=0.,expectancy_r=np.nan,median_r=np.nan,profit_factor=np.nan,win_rate=np.nan,max_drawdown_r=0.,return_dd=np.nan,mfe_r=np.nan,mae_r=np.nan,stop_first_rate=np.nan,tp1_rate=np.nan,tp2_rate=np.nan,two_tick_each_side_expectancy=np.nan,negative_years=0)
    x=f.pnl_r.astype(float); d=drawdown(x); y=f.groupby(f.entry_time.dt.year).pnl_r.sum()
    return dict(trades=len(f),net_r=float(x.sum()),expectancy_r=float(x.mean()),median_r=float(x.median()),profit_factor=pf(x),win_rate=float((x>0).mean()),max_drawdown_r=d,return_dd=float(x.sum()/d) if d else np.nan,mfe_r=float(f.mfe_r.mean()),mae_r=float(f.mae_r.mean()),stop_first_rate=float(f.stop_first.mean()),tp1_rate=float(f.tp1_hit.mean()),tp2_rate=float(f.tp2_hit.mean()),two_tick_each_side_expectancy=float((x-.5/f.risk_points).mean()),negative_years=int((y<0).sum()))

def classify(m,o):
    if m["trades"]<10:return "DESCRIPTIVE_ONLY"
    core=m["expectancy_r"]<0 and m["expectancy_r"]-o["expectancy_r"]<=-.10 and m["two_tick_each_side_expectancy"]<0
    sec=sum((m["stop_first_rate"]-o["stop_first_rate"]>=.05,m["tp1_rate"]-o["tp1_rate"]<=-.05,m["negative_years"]>=2))
    return "WATCH_RISK" if core and sec>=2 else "NO_CLEAR_PATTERN"

def raw_dates(path):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:r=pd.read_csv(f,usecols=["timestamp ET","open","close"])
    r["ts"]=pd.to_datetime(r["timestamp ET"],format="%m/%d/%Y %H:%M"); r=r.sort_values("ts")
    r["eth"]=r.ts.dt.normalize()+pd.to_timedelta((r.ts.dt.hour>=18).astype(int),unit="D")
    g=r.groupby("eth").agg(first=("open","first"),last=("close","last")).reset_index()
    g["gap"]=g["first"]-g["last"].shift(); g["pct"]=g.gap.abs().rank(pct=True); q=float(g.gap.abs().dropna().quantile(.99));g["extreme"]=g.gap.abs()>=q
    return pd.DatetimeIndex(g.eth),g

def win(obs,d,l,r):
    i=obs.get_indexer([d],method="pad")[0];i=max(i,0)
    return set(obs[max(0,i-l):min(len(obs),i+r+1)])

def boot(f,n,seed):
    if f.empty:return dict(date_blocks=0,ci_low_r=np.nan,ci_high_r=np.nan,prob_positive=np.nan)
    v=f.groupby("eth_market_date").pnl_r.sum().to_numpy(); rng=np.random.default_rng(seed);s=rng.choice(v,(n,len(v)),replace=True).sum(1)
    return dict(date_blocks=len(v),ci_low_r=float(np.quantile(s,.025)),ci_high_r=float(np.quantile(s,.975)),prob_positive=float((s>0).mean()))

def main():
    a=argparse.ArgumentParser();a.add_argument("--trades",type=Path,required=True);a.add_argument("--raw-zip",type=Path,required=True);a.add_argument("--prereg",type=Path,required=True);a.add_argument("--output",type=Path,required=True);q=a.parse_args();q.output.mkdir(parents=True,exist_ok=True)
    assert digest(q.raw_zip)==SHA;p=json.loads(q.prereg.read_text());t=pd.read_csv(q.trades)
    for c in ("entry_time","exit_time","eth_market_date"):t[c]=pd.to_datetime(t[c])
    t["entry_date"]=t.entry_time.dt.normalize();b=stats(t)
    for got,exp in zip((b["trades"],b["net_r"],b["expectancy_r"],b["max_drawdown_r"]),EXPECTED,strict=True):assert np.isclose(got,exp,atol=1e-9,rtol=0)
    ds={k:set(pd.to_datetime(v)) for k,v in p["dates"].items()};obs,g=raw_dates(q.raw_zip)
    ew=set();rw=set();roll=[]
    for d in sorted(ds["EXPIRATION"]):
        if d<=obs.max():ew|=win(obs,d,5,0)
    for d in sorted(ds["ROLL"]):
        if d>obs.max():continue
        w=win(obs,d,2,2);rw|=w;z=g[g.eth.isin(w)];r=z.loc[z.gap.abs().idxmax()]
        roll.append(dict(official_roll_date=str(d.date()),largest_gap_eth_date=str(pd.Timestamp(r.eth).date()),maintenance_gap_points=float(r.gap),absolute_gap_points=abs(float(r.gap)),gap_percentile=float(r.pct),extreme_99pct=bool(r.extreme)))
    m={}
    for e in ("FOMC","CPI","NFP"):
        d=t.entry_date.isin(ds[e]);hh,mm=map(int,p["event_times_et"][e].split(":"));x=t.entry_date+pd.Timedelta(hours=hh,minutes=mm)
        m[e+"_DAY"]=d;m[e+"_PRE"]=d&(t.entry_time<x);m[e+"_POST"]=d&(t.entry_time>=x);m[e+"_CROSSING"]=d&(t.entry_time<x)&(t.exit_time>=x)
    m.update(EXPIRATION_DAY=t.entry_date.isin(ds["EXPIRATION"]),EXPIRATION_WEEK=t.eth_market_date.isin(ew),ROLL_DAY=t.eth_market_date.isin(ds["ROLL"]),ROLL_WINDOW=t.eth_market_date.isin(rw),EARLY_CLOSE=t.entry_date.isin(ds["EARLY_CLOSE"]),HOLIDAY_SHORTENED=t.entry_date.isin(ds["HOLIDAY_SHORTENED"]))
    rows=[];bi=[]
    for i,(name,mask) in enumerate(m.items()):
        on,off=t[mask],t[~mask];s,o=stats(on),stats(off);row=dict(category=name,**s,off_trades=o["trades"],off_expectancy_r=o["expectancy_r"],expectancy_gap_vs_off_r=s["expectancy_r"]-o["expectancy_r"] if len(on) else np.nan,stop_first_gap_vs_off=s["stop_first_rate"]-o["stop_first_rate"] if len(on) else np.nan,tp1_gap_vs_off=s["tp1_rate"]-o["tp1_rate"] if len(on) else np.nan);row["classification"]=classify(s,o);rows.append(row);bi.append(dict(category=name,observed_net_r=s["net_r"],**boot(on,p["inference"]["iterations"],p["inference"]["seed"]+i)))
    pd.DataFrame(rows).to_csv(q.output/"event_roll_results.csv",index=False);pd.DataFrame(bi).to_csv(q.output/"event_roll_inference.csv",index=False);pd.DataFrame(roll).to_csv(q.output/"roll_discontinuities.csv",index=False)
    labels=t[["signal_id","entry_time","exit_time","eth_market_date","session","direction","pnl_r","risk_points"]].copy()
    for k,v in m.items():labels[k]=v.to_numpy(bool)
    labels.to_csv(q.output/"event_roll_trade_labels.csv",index=False)
    print(pd.DataFrame(rows)[["category","trades","net_r","expectancy_r","classification"]].to_string(index=False))
if __name__=="__main__":main()
