# ruff: noqa
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

EXPECTED={
"FOMC_DAY":(14,-5.558986884983001,-0.39707049178450005),
"FOMC_PRE":(9,-7.618852964020001,-0.8465392182244446),
"FOMC_POST":(5,2.0598660790370005,0.4119732158074001),
"CPI_DAY":(18,1.7580679104219996,0.09767043946788886),
"NFP_DAY":(9,1.3704940632130005,0.15227711813477784),
"EXPIRATION_WEEK":(27,-2.0858621308149994,-0.07725415299314813),
"ROLL_WINDOW":(25,-0.5758652580270003,-0.02303461032108001),
}

def main():
    p=argparse.ArgumentParser();p.add_argument("--results",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=pd.read_csv(a.results/"event_roll_results.csv").set_index("category")
    for name,(n,net,exp) in EXPECTED.items():
        assert int(r.loc[name,"trades"])==n
        assert np.isclose(float(r.loc[name,"net_r"]),net,atol=1e-9,rtol=0)
        assert np.isclose(float(r.loc[name,"expectancy_r"]),exp,atol=1e-9,rtol=0)
    labels=pd.read_csv(a.results/"event_roll_trade_labels.csv")
    ew=labels.EXPIRATION_WEEK.astype(bool);rw=labels.ROLL_WINDOW.astype(bool)
    overlap={}
    for name,mask in {"expiration_only":ew&~rw,"roll_only":rw&~ew,"intersection":ew&rw,"neither":~ew&~rw}.items():
        x=labels.loc[mask,"pnl_r"].astype(float);overlap[name]={"trades":int(len(x)),"net_r":float(x.sum()),"expectancy_r":float(x.mean())}
    assert overlap["intersection"]["trades"]==18
    assert np.isclose(overlap["intersection"]["net_r"],-5.199166628706001,atol=1e-9,rtol=0)
    assert overlap["expiration_only"]["net_r"]>0 and overlap["roll_only"]["net_r"]>0
    review={"decision":"INDEPENDENT_REVIEW_PASS","metrics_exact":True,"overlap_exact":True,"overlap_decomposition":overlap,"conclusion":"Retain E6; no event exclusion."}
    a.output.write_text(json.dumps(review,indent=2,sort_keys=True))
if __name__=="__main__":main()
