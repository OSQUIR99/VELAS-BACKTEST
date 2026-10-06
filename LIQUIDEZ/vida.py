import pandas as pd, numpy as np
from core import *
pd.set_option('display.width',250)
rng=np.random.default_rng(3)
rows=[]
HZ={'1h':[24,120,500],'4h':[6,30,120],'1d':[5,20,100]}
for a in ACTIVOS:
    for tf in ['1h','4h','1d']:
        df=cargar(a,tf); n=len(df)
        for lado in ['largo','corto']:
            h,l,c=(df.h.values,df.l.values,df.c.values) if lado=='largo' else (-df.l.values,-df.h.values,-df.c.values)
            A=df.atr.values; z=zigzag(pd.DataFrame({'h':h,'l':l,'atr':A}),2.5)
            zi,zp,zt,zc=z.i.values,z.p.values,z.t.values,z.cf.values
            for p in range(len(z)-2):
                if zt[p]!=-1: continue
                L=zp[p]; q=p+2
                if zp[q]<=L+0.2*A[zi[q]]: continue      # el siguiente minimo no lo dejo pendiente
                s=zc[q]
                t=primer_cruce(l,zc[p]+1,L,True)
                if 0<=t<=s: continue                    # ya barrido antes de quedar 'dejado'
                d=(c[s]-L)/A[s]
                # control: precio cualquiera a la misma distancia (en ATR), momento al azar
                s2=int(rng.integers(300,n-10)); L2=c[s2]-d*A[s2]
                t2=primer_cruce(l,s2+1,L2,True)
                for H in HZ[tf]:
                    if s+H<n: rows.append(dict(activo=a,tf=tf,lado=lado,H=H,tipo='nivel pendiente',d=d,barrido=(t>=0)&(t-s<=H)))
                    if s2+H<n: rows.append(dict(activo=a,tf=tf,lado=lado,H=H,tipo='precio cualquiera',d=d,barrido=(t2>=0)&(t2-s2<=H)))
r=pd.DataFrame(rows)
r.to_parquet('ev_vida.parquet')
t=r.pivot_table(index=['tf','H'],columns='tipo',values='barrido',aggfunc='mean')*100
print(t.round(1))
print(r.groupby(['tf','tipo']).d.median().unstack().round(2))
print((r.pivot_table(index=['activo','tf','H'],columns='tipo',values='barrido',aggfunc='mean')*100).round(1).to_string())
print(r.pivot_table(index=['tf','H'],columns=['lado','tipo'],values='barrido',aggfunc='mean').round(3)*100)
