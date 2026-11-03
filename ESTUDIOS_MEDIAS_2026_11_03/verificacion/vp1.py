import sys; sys.path.insert(0,'/home/claude/velas-backtest')
import numpy as np, pandas as pd
from cargar import velas
def atr(d,n=14):
    pc=d.cierre.shift(1); tr=pd.concat([d.maximo-d.minimo,(d.maximo-pc).abs(),(d.minimo-pc).abs()],axis=1).max(axis=1); return tr.ewm(alpha=1/n,adjust=False).mean()
res={}
for a in ['BTC','ETH','SOL','ADA','LINK','ZEC']:
  d=velas(a,'1d'); d=d[~d.index.duplicated()]; c=d.cierre.values; e=d.cierre.ewm(span=20,adjust=False).mean().values; A=atr(d).values
  o=d.apertura.values; l=d.minimo.values; idx=d.index; n=len(d)
  for stop in (True,False):
    T=[]; i=0
    while i<n-1:
      if idx[i]>=pd.Timestamp('2017-01-01') and i>0 and c[i]>e[i] and c[i-1]<=e[i-1] and A[i]>0:
        en=o[i+1]; R=2.5*A[i]; sl=en-R if stop else en*0.75; x=None
        for j in range(i+1,n):
          if l[j]<=sl: x=min(sl,o[j]); xd=j; break
          if j-(i+1)>=39:
            if j+1<n: x=o[j+1]; xd=j+1
            break
        if x is None: break
        T.append(dict(t=idx[i+1],r=(x-en-0.001*en)/R)); i=xd; continue
      i+=1
    res[(a,stop)]=pd.DataFrame(T)
for (a,stop),T in res.items():
    O=pd.read_parquet(f'/home/claude/med/l_p1_{"btc" if a=="BTC" else "6"}_{"st" if stop else "ns"}/p1_{"btc" if a=="BTC" else "6"}_{"st" if stop else "ns"}.parquet'); O=O[O.activo==a]
    print(a,stop,'mío',len(T),round(T.r.sum(),2),'suyo',len(O),round(O.r_bruto.sum(),2))
