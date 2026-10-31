import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from scipy.stats import spearmanr
D=pickle.load(open('datos.pkl','rb')); bh=D['BTCh']; L=np.log; rng=np.random.default_rng(5)
A=['MSTR','MARA','RIOT','CLSK','WULF','HUT','CIFR','IREN','CORZ','BITF']
EP=[('2020-22','2020-09-01','2022-12-31'),('2023-24','2023-01-01','2024-12-31'),('2025-26','2025-01-01','2026-12-31')]
def pv(x,y,n=500):
    ok=~(np.isnan(x)|np.isnan(y)); x,y=x[ok],y[ok]; r=spearmanr(x,y)[0]
    p=np.array([spearmanr(np.roll(x,int(rng.integers(30,len(x)-30))),y)[0] for _ in range(n)]); return r,(np.sum(np.abs(p)>=abs(r))+1)/(n+1)
print('\n== 2) Horario (2023-26): BTC de la hora anterior -> la acción en la hora siguiente')
for a in A:
    h=D.get(a+'_h'); 
    if h is None: continue
    t=h.index; b0=np.array([bh.asof(x-pd.Timedelta(minutes=150)) for x in t]); b1=np.array([bh.asof(x-pd.Timedelta(minutes=90)) for x in t])
    d=pd.DataFrame({'y':L(h.c/h.o).values,'x':L(b1/b0)},index=t)
    d=d[d.index.hour!=d.index.to_series().groupby(d.index.date).transform('min').dt.hour]   # sin la primera hora (hueco)
    r,p=pv(d.x.values,d.y.values,300)
    s=np.sign(d.x).where(d.x.abs()>0.005,0); q=(s*d.y-0.001*s.abs()); x=q[s!=0]
    by=' · '.join(f'{yy}: {spearmanr(*d[d.index.year==yy][["x","y"]].dropna().values.T)[0]:+.3f}' for yy in (2023,2024,2025,2026))
    print(f'{a:5s} correlación {r:+.3f} (p {p:.3f}) [{by}] · regla |BTC hora|>0,5 %: n {len(x)}, {x.mean()*100:+.3f} %/op neto, acierto {(x>0).mean()*100:.0f} %')
