import sys,os; sys.path.insert(0,'/home/claude/med'); sys.path.insert(0,'/home/claude/caidas'); sys.path.insert(0,'/home/claude/velas-backtest')
import numpy as np, pandas as pd, nuevas as N
from cortos import diario, rsi_wilder
OO,DD=[],[]
for act,nom in {'SPX':'sp500','NDX':'nasdaq100','DJI':'dowjones'}.items():
    d=diario(nom); c=d.cierre
    w=c.resample('W-FRI').last(); m20=w.rolling(20).mean()
    # semana conocida al cierre del último día de esa semana (sin el retraso extra de una semana)
    lastday=c.groupby(c.index.to_period('W-FRI')).apply(lambda s: s.index.max())
    m=pd.Series(m20.values,index=[lastday.get(p,pd.NaT) for p in m20.index.to_period('W-FRI')]).dropna()
    m=m[m.index.notna()]; m20d=m.reindex(c.index).ffill(); perm=(c>m20d)&(m20d>m20d.shift(20))
    r2=rsi_wilder(c); m5=c.rolling(5).mean().values; C=c.values; en=(perm&(r2<10)).fillna(False).values
    O,D=N.run(d,en,lambda j,ei,C=C,m5=m5:(j>ei and C[j]>m5[j]) or (j-ei>=10),entrada='close',salida_modo='close',stop_fn=lambda e,a:e-2.5*a,nombre='e1r_20sv',activo=act,tam=0.5,bloque='bolsa_eeuu',desde='1990-01-01')
    O['id']=O.id+'-'+act; D['id']=D.id+'-'+act; OO.append(O); DD.append(D)
car='/tmp/claude-0/-home-claude/47fce85d-9c7a-50f4-80f6-5f58f99c08d1/scratchpad/v/l_e1r_20sv'; os.makedirs(car,exist_ok=True)
pd.concat(OO).assign(familia='e1r_20sv').to_parquet(car+'/e1r_20sv.parquet'); pd.concat(DD).to_parquet(car+'/e1r_20sv_diario.parquet')
from ev import *
C=cartera(extra=('/home/claude/med/l_e1r_200','/home/claude/med/l_e1r_20s',car)); M=mascaras(C); L=C.L; d=M['d']
res={}
for nm in ['e1r_200','e1r_20s','e1r_20sv']:
    m=(L==nm)&d; b=(M['BASE']&~M['E1'])|m; e,q=run(C,b,(M['EX']&~M['E1'])|m); res[nm]=q; print(nm,m.sum(),C.fmt(q))
print('20sv frente a 200', ok(res['e1r_20sv'],res['e1r_200']))
