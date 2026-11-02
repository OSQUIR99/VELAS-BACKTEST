import sys; sys.path.insert(0,'/home/claude/velas-backtest')
import pandas as pd, numpy as np
from cargar import velas
d=velas('sp500','1d').copy(); d.index=(pd.to_datetime(d.index)+pd.Timedelta(hours=6)).normalize(); d=d[~d.index.duplicated(keep='last')].astype(float)
v=velas('vix','1d').copy(); v.index=(pd.to_datetime(v.index)+pd.Timedelta(hours=6)).normalize(); v=v[~v.index.duplicated(keep='last')].cierre.astype(float)
x=pd.read_pickle('vxv.pkl'); x3=pd.read_pickle('vix3m_tv.pkl').cierre.astype(float)
# ATR wilder own
O,H,L,C=[d[k].values for k in ('apertura','maximo','minimo','cierre')]
tr=np.maximum(H-L,np.maximum(abs(H-np.r_[np.nan,C[:-1]]),abs(L-np.r_[np.nan,C[:-1]]))); tr[0]=H[0]-L[0]
atr=np.zeros(len(tr)); atr[0]=tr[0]
for k in range(1,len(tr)): atr[k]=atr[k-1]+(tr[k]-atr[k-1])/14
def trades(x3m, strict_common=False):
    vv=v.reindex(d.index); xx=x3m.reindex(d.index)
    if not strict_common: xx=x3m.reindex(v.index).ffill().reindex(d.index)
    r=(vv/xx).values; out=[]; i=0; n=len(d)
    while i<n-1:
        if d.index[i]>=pd.Timestamp('2008-01-01') and r[i]<1 and i>0 and r[i-1]>1:
            ei=i+1; e=O[ei]; R=2.5*atr[i]; st=0.8*e; xp=None
            for j in range(ei,n):
                if L[j]<=st: xp=min(st,O[j]); xd=j; break
                if j-ei>=8:
                    if j==n-1: xp=C[j]; xd=j
                    else: xp=O[j+1]; xd=j+1
                    break
            if xp is None: break
            out.append((d.index[i],d.index[ei],d.index[xd],e,xp,(xp-e-0.0002*e)/R,r[i-1],r[i])); i=xd; continue
        i+=1
    return pd.DataFrame(out,columns=['senal','ent','sal','e','xp','R','r_prev','r'])
T=trades(x); T.to_pickle('mine.pkl')
print('mine', len(T), T.R.mean().round(4), (T.R>0).mean().round(3), 'since 2018-05', (T.ent>='2018-05-01').sum())
P=pd.read_parquet('/home/claude/caidas/listas_nuevas/n1_vixvxv.parquet')
print('theirs',len(P),P.r_bruto.mean().round(4))
P['s']=P.t_senal.dt.normalize()
m=T.merge(P[['s','r_bruto','entrada','salida']],left_on='senal',right_on='s',how='outer',indicator=True)
print(m._merge.value_counts()); mm=m[m._merge=='both']; print('max|dR|',abs(mm.R-mm.r_bruto).max())
print(P[['t_senal','t_entrada','t_salida']].head(3))
T3=trades(x3); print('with TV VIX3M', len(T3), T3.R.mean().round(4))
Ts=trades(x,True); print('strict common dates',len(Ts),Ts.R.mean().round(4))
# yearly R
print(T.groupby(T.ent.dt.year).R.agg(['count','sum']).round(2).T.to_string())
sel=T.sample(5,random_state=1).sort_values('senal')
for _,row in sel.iterrows():
    s=row.senal; k=d.index.get_loc(s); p=d.index[k-1]
    print(s.date(),'prev',p.date(),'VIX',v.get(p),'/',x.get(p),'->',v.get(s),'/',x.get(s),'| TV3M',x3.get(p),x3.get(s),'| ent',row.ent.date(),'O',row.e,'exit',row.sal.date(), round(row.R,3))
