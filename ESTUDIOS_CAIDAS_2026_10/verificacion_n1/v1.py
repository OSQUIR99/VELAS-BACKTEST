import sys; sys.path.insert(0,'/home/claude/velas-backtest')
import pandas as pd, numpy as np, io, subprocess
from cargar import velas
def day(n):
    d=velas(n,'1d').copy(); raw=pd.to_datetime(d.index)
    d.index=(raw+pd.Timedelta(hours=6)).normalize(); d['raw']=raw; return d[~d.index.duplicated(keep='last')]
vix=day('vix'); spx=day('sp500')
print('VIX stamp hours', pd.Series(vix.raw.dt.strftime('%H:%M')).value_counts().head())
print('SPX stamp hours', pd.Series(spx.raw.dt.strftime('%H:%M')).value_counts().head())
print(vix.tail(3)[['raw','cierre']]); print(spx.tail(3)[['raw','cierre']])
txt=subprocess.run(['curl','-sS','-m','90','https://fred.stlouisfed.org/graph/fredgraph.csv?id=VXVCLS&cosd=2007-01-01'],capture_output=True,text=True).stdout
f=pd.read_csv(io.StringIO(txt)); f.columns=['d','v']; f['v']=pd.to_numeric(f.v,errors='coerce'); vxv=f.dropna().set_index(pd.to_datetime(f.dropna().d)).v
vxv.to_pickle('vxv.pkl')
# FRED VIXCLS as alignment check of TV vix
txt=subprocess.run(['curl','-sS','-m','90','https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=2007-01-01'],capture_output=True,text=True).stdout
f=pd.read_csv(io.StringIO(txt)); f.columns=['d','v']; f['v']=pd.to_numeric(f.v,errors='coerce'); fv=f.dropna().set_index(pd.to_datetime(f.dropna().d)).v
j=pd.concat([vix.cierre,fv],axis=1,keys=['tv','fred']).dropna()
for s in (-1,0,1):
    jj=pd.concat([vix.cierre.shift(s),fv],axis=1,keys=['tv','fred']).dropna(); print('shift',s,'match<0.02:',(abs(jj.tv-jj.fred)<0.02).mean().round(3), len(jj))
