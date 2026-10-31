import sys; sys.path.insert(0,'/home/claude/vol/code')
src=open('/home/claude/vol/code/sistema.py').read()
# variante: sin venta de 1/3 en +1R (el stop pasa a la entrada igual) cuando la entrada llega con volatilidad baja
src=src.replace("def trades(c,start='2018-01-01'):","def trades(c,start='2018-01-01',nopart=None):")
src=src.replace("        while k<n:\n            if lo[k]<=stop:\n                pxx=min(stop,o[k]); res=(1/3 if part else 0)+(2/3 if part else 1)*(pxx-ent)/R; break",
"        np_=nopart is not None and nopart.get(idx[j].normalize(),False)\n        q=0 if np_ else 1/3\n        while k<n:\n            if lo[k]<=stop:\n                pxx=min(stop,o[k]); res=(q if part else 0)+((1-q) if part else 1)*(pxx-ent)/R; break")
src=src.replace("        if res is None: res=(1/3 if part else 0)+(2/3 if part else 1)*(cl[-1]-ent)/R\n        res-=0.0005*ent/R\n        tr.append(dict(",
"        if res is None: res=(q if part else 0)+((1-q) if part else 1)*(cl[-1]-ent)/R\n        res-=0.0005*ent/R\n        tr.append(dict(np_=np_,")
src=src.split("if __name__")[0]
exec(src)
import pandas as pd, numpy as np
SYS=pd.read_pickle(D+'SYS.pkl')
X=pd.read_pickle(D+'X_vol.pkl'); bp=X.pct.shift(1)
P=[('2018','2020'),('2020','2022'),('2022','2024'),('2024','2027'),('2018','2027'),('2022','2027')]
def rat(R,ex,a,b):
    m=(R.index>=a)&(R.index<b); s=pd.Series(R[m].values,index=ex[m].values).sort_index(); cum=s.cumsum(); dd=(cum-cum.cummax()).min()
    yrs=(pd.Timestamp(min(b,'2026-10-25')) - pd.Timestamp(a)).days/365.25; return s.sum()/yrs/abs(dd)
def evaluar(name,mask_by_coin):
    out=[]
    for c in COINS:
        T=trades(c,nopart=mask_by_coin(c)); out.append(T)
    T=pd.concat(out).sort_index()
    assert len(T)==len(SYS)
    Rw=T.R.values*SYS['size'].values; R=pd.Series(Rw,index=T.index)
    base=pd.Series(SYS.R.values*SYS['size'].values,index=SYS.index)
    r0=[rat(base,SYS.exit,a,b) for a,b in P]; r1=[rat(R,T.exit,a,b) for a,b in P]
    a=T[T.np_]; print(f'{name:40s} n={len(a)} R/op aplicadas {SYS.R[T.np_.values].mean():+.2f}→{a.R.mean():+.2f} | '+' | '.join(f'{x[0][2:4]}-{x[1][2:4]} {u:.2f}→{v:.2f}' for x,u,v in zip(P,r0,r1)))
for thr in [0.1,0.2,0.3]:
    evaluar(f'BTC vol ≤{thr}: sin venta de 1/3',lambda c,thr=thr:(bp<=thr).to_dict())
    def own(c,thr=thr):
        d=px(c,'1d').close; r=np.log(d).diff(); v=r.rolling(30).std()
        p=v.rolling(1095,min_periods=365).apply(lambda x:(x<=x[-1]).mean(),raw=True).shift(1)
        return (p<=thr).to_dict()
    evaluar(f'vol propia ≤{thr}: sin venta de 1/3',own)
evaluar('Todas sin venta de 1/3 (control)',lambda c:{k:True for k in pd.date_range('2015','2027')})
