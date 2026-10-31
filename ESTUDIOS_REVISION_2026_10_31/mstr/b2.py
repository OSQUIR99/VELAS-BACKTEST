import pickle, numpy as np, pandas as pd
from scipy.stats import spearmanr
d=pickle.load(open('d.pkl','rb')); L=np.log; rng=np.random.default_rng(3)
d['bin']=L(d.bc/d.bo)                       # BTC durante la sesión
d['eoc']=d.oc-1.0*d.bin                     # MSTR en la sesión, descontado BTC (beta ~1; se ajusta abajo)
a=d[['oc','bin']].dropna(); beta=np.polyfit(a.bin,a.oc,1)[0]; d['eoc']=d.oc-beta*d.bin
d['gapres']=d.gap-0.95*d.bnight              # cuánto se quedó corto el hueco
EP=[('2020-22','2020-09-01','2022-12-31'),('2023-24','2023-01-01','2024-12-31'),('2025-26','2025-01-01','2026-12-31')]
def pl(x,y,dd,n=800):
    a=dd[[x,y]].dropna(); r=spearmanr(a[x],a[y])[0]; xs=a[x].values
    p=np.array([spearmanr(np.roll(xs,int(rng.integers(30,len(xs)-30))),a[y])[0] for _ in range(n)])
    return r,(np.sum(np.abs(p)>=abs(r))+1)/(n+1)
print('beta sesión',round(beta,2))
for x,y,nom in (('bnight','bin','BTC noche -> BTC en la sesión (control)'),('bnight','eoc','BTC noche -> MSTR en la sesión DESCONTANDO BTC'),('gapres','oc','hueco corto/largo -> MSTR en la sesión'),('gapres','eoc','hueco corto/largo -> MSTR descontando BTC')):
    r,p=pl(x,y,d); print(f'{nom}: {r:+.3f} (p {p:.3f}) | '+' '.join(f'{e} {spearmanr(*d[(d.index>=a_)&(d.index<=b_)][[x,y]].dropna().values.T)[0]:+.3f}' for e,a_,b_ in EP))
# regla: a la apertura de MSTR, a favor de lo que hizo BTC en la noche si |BTC noche| > umbral; salida al cierre; coste 0,1 % ida y vuelta
for u in (0.0,0.01,0.02,0.03):
    s=np.sign(d.bnight).where(d.bnight.abs()>u,0); r=(s*d.oc-0.001*s.abs()).fillna(0)
    out=[]
    for e,a_,b_ in EP+[('todo','2020-09-01','2026-12-31')]:
        x=r[(r.index>=a_)&(r.index<=b_)]; eq=x.cumsum(); dd=(eq-eq.cummax()).min(); n=int((s[(s.index>=a_)&(s.index<=b_)]!=0).sum())
        tr=x[s[(s.index>=a_)&(s.index<=b_)]!=0]
        out.append(f'{e}: n {n} · media {tr.mean()*100:+.2f} %/op · acierto {(tr>0).mean()*100:.0f} % · ganancia/caída {eq.iloc[-1]/abs(dd):.2f}')
    print(f'umbral {u*100:.0f} %: '+' | '.join(out))
# ¿y en el hueco? residual del hueco por tamaño de la noche
d['bq']=pd.qcut(d.bnight,5,labels=False)
print(d.groupby('bq')[['bnight','gap','oc','eoc']].mean().mul(100).round(2))
