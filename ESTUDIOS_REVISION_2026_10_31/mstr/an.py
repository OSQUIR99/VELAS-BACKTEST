import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from scipy.stats import spearmanr
D=pickle.load(open('datos.pkl','rb')); bh=D['BTCh']
rng=np.random.default_rng(7)
def asof(t): return bh.asof(t)
M=D['MSTR']; Q=D['QQQ']
M=M[M.index>='2020-03-01']; idx=M.index
op=idx; cl=idx+pd.Timedelta(hours=6.5)
bo=np.array([asof(t-pd.Timedelta(minutes=60)) for t in op]); bc=np.array([asof(t-pd.Timedelta(minutes=60)) for t in cl])
df=pd.DataFrame({'mo':M.o.values,'mc':M.c.values,'qc':Q.c.reindex(idx).values,'bo':bo,'bc':bc},index=idx.normalize())
for k in ('MARA','RIOT'): df[k]=D[k].c.reindex(idx).values
L=np.log
df['rm']=L(df.mc/df.mc.shift()); df['rq']=L(df.qc/df.qc.shift()); df['rb']=L(df.bc/df.bc.shift())
for k in ('MARA','RIOT'): df['r'+k]=L(df[k]/df[k].shift())
def resid(y):
    e=pd.Series(np.nan,index=df.index); X=df[['rb','rq']].values; Y=df[y].values
    for i in range(91,len(df)):
        xs=X[i-90:i]; ys=Y[i-90:i]; ok=~np.isnan(xs).any(1)&~np.isnan(ys)
        if ok.sum()<60 or np.isnan(X[i]).any() or np.isnan(Y[i]): continue
        A=np.c_[np.ones(ok.sum()),xs[ok]]; b=np.linalg.lstsq(A,ys[ok],rcond=None)[0]
        e.iloc[i]=Y[i]-b[0]-X[i]@b[1:]
    return e
for y in ('rm','rMARA','rRIOT'): df['e'+y]=resid(y)
df['z']=df.erm/df.erm.rolling(60).std().shift()
df['zbr']=(df[['erm','erMARA','erRIOT']]>0).sum(1).where(df.erm.notna())
# futuros de BTC desde el cierre de MSTR (horas exactas)
for h,n in ((24,'b1'),(120,'b5'),(168,'b7'),(720,'b30')):
    df[n]=L(np.array([asof(t+pd.Timedelta(hours=h)) for t in cl])/df.bc.values)
    df.loc[df.index>=(bh.index[-1]-pd.Timedelta(hours=h)).normalize(),n]=np.nan
df['b5past']=L(df.bc/np.array([asof(t-pd.Timedelta(hours=120)) for t in cl]))
# futuros de MSTR
df['m1']=L(df.mc.shift(-1)/df.mc); df['m5']=L(df.mc.shift(-5)/df.mc)
df['gap']=L(df.mo/df.mc.shift()); df['bnight']=L(df.bo/df.bc.shift()); df['oc']=L(df.mc/df.mo)
df['wk']=df.index.dayofweek==0
d=df[df.index>='2020-09-01']
EP=[('2020-22','2020-09-01','2022-12-31'),('2023-24','2023-01-01','2024-12-31'),('2025-26','2025-01-01','2026-12-31')]
def ic(x,y,dd):
    a=dd[[x,y]].dropna(); return spearmanr(a[x],a[y])[0], len(a)
def plac(x,y,dd,n=1000):
    a=dd[[x,y]].dropna(); r=spearmanr(a[x],a[y])[0]; xs=a[x].values
    pl=np.array([spearmanr(np.roll(xs,int(rng.integers(30,len(xs)-30))),a[y])[0] for _ in range(n)])
    return r,(np.sum(np.abs(pl)>=abs(r))+1)/(n+1)
print('== A) residual de MSTR (y mineras) -> BTC futuro (desde el cierre de MSTR)')
for x in ('z','erMARA','erRIOT','zbr'):
  for y in ('b1','b5','b7','b30'):
    r,p=plac(x,y,d,400); print(f'{x:7s}->{y}: todo {r:+.3f} (p {p:.3f}) | '+' '.join(f'{e} {ic(x,y,d[(d.index>=a)&(d.index<=b)])[0]:+.3f}' for e,a,b in EP))
print('\n== A2) evento: residual MSTR > +1 desviación y BTC cayó en 5 días')
d2=d.copy(); ev=(d2.z>1)&(d2.b5past<0)
for e,a,b in EP+[('todo','2020-09-01','2026-12-31')]:
    m=(d2.index>=a)&(d2.index<=b); x=d2[m&ev].b7.dropna(); base=d2[m].b7.dropna()
    print(f'{e}: n {len(x)} · BTC +7d {np.expm1(x.mean())*100:+.1f} % (sube {(x>0).mean()*100:.0f} %) · normal {np.expm1(base.mean())*100:+.1f} % ({(base>0).mean()*100:.0f} %)')
print('\n== B) al revés: BTC -> MSTR')
a=d[['gap','bnight']].dropna(); b=np.polyfit(a.bnight,a.gap,1); print(f'B1 hueco de apertura de MSTR frente a BTC de la noche/fin de semana: pendiente {b[0]:.2f}, correlación {a.corr().iloc[0,1]:.2f}')
for x,y,nom in (('bnight','oc','BTC de la noche -> MSTR de apertura a cierre'),('z','m1','residual MSTR -> MSTR día siguiente'),('z','m5','residual MSTR -> MSTR 5 días'),('erm','m1','residual bruto -> MSTR día siguiente')):
    r,p=plac(x,y,d,600); print(f'{nom}: todo {r:+.3f} (p {p:.3f}) | '+' '.join(f'{e} {ic(x,y,d[(d.index>=a_)&(d.index<=b_)])[0]:+.3f}' for e,a_,b_ in EP))
# lunes: BTC del fin de semana -> MSTR lunes apertura a cierre
w=d[d.wk]; r,p=plac('bnight','oc',w,600); print(f'Lunes: BTC del finde -> MSTR apertura a cierre: {r:+.3f} (p {p:.3f}) n {len(w)}')
pickle.dump(d,open('d.pkl','wb'))
