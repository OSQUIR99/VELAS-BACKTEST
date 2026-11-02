import sys; sys.path.insert(0,'/home/claude/velas-backtest'); sys.path.insert(0,'/home/claude/velas-backtest/ACTUALIZACION')
import pandas as pd, numpy as np
from tv import velas_tv
vxv=pd.read_pickle('vxv.pkl')
t=velas_tv('CBOE:VIX3M','1d',n=5000)
print(t.head(2)); print(t.tail(2))
t=t.set_index(pd.to_datetime(t['fecha']) if 'fecha' in t.columns else t.index)
t.index=(pd.to_datetime(t.index)+pd.Timedelta(hours=6)).normalize()
t.to_pickle('vix3m_tv.pkl')
for s in (-1,0,1):
    j=pd.concat([t.cierre.astype(float).shift(s),vxv],axis=1,keys=['tv','fred'],sort=True).dropna()
    print(s,(abs(j.tv-j.fred)<0.02).mean().round(4),len(j), j.index.min())
