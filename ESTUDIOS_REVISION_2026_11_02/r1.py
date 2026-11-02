from base2 import *
import warnings; warnings.filterwarnings('ignore')
r0,e0=C.sim(BASE); q0=C.met3(e0); print('BASE',C.fmt(q0),flush=True)
def T(nom,m,ex_=None,tm=None):
    r,e=C.sim(m,exentas=ex_,tam_mult=tm); q=C.met3(e); ok=all(q[i]['ratio']>q0[i]['ratio'] for i in range(3))
    print(f'{nom:44s}',C.fmt(q),'PASA' if ok else '-', 'boot',round(C.bootstrap(e0,e,300),2),flush=True); return e
T('Connors fuera del freno',BASE|cn,ex|cn)
T('N1 fuera del freno',BASE|n1,ex|n1)
T('Connors+N1 fuera del freno',BASE|cn|n1,ex|cn|n1)
T('E1 fuera del freno',BASE,ex|E1)
T('E1+Connors fuera del freno',BASE|cn,ex|E1|cn)
cr=(L=='cripto')
T('freno solo para cripto',BASE,BASE&~cr)
# vol de la cartera (sin mirar al futuro)
dv=e0.diff().fillna(0); vol=dv.rolling(60).std().shift(1); med=vol.expanding(250).median()
fac=(med/vol).clip(0.5,1.5); te=pd.to_datetime(O.t_entrada).dt.normalize()
f=fac.reindex(te.values,method='ffill').fillna(1).values
T('vol objetivo cartera 0,5-1,5',BASE,None,f)
T('vol objetivo cartera solo reduce',BASE,None,np.minimum(f,1))
# racha de la familia
fam=np.where(L=='bolsa_e1','e1',L); ts=pd.to_datetime(O.t_salida).values; tn=pd.to_datetime(O.t_entrada).values; rf=O.r_final.values
mfam=np.ones(len(O))
for F in np.unique(fam[BASE]):
    idx=np.where((fam==F))[0]; o=idx[np.argsort(ts[idx])]
    for i in idx:
        prev=o[ts[o]<tn[i]][-10:]
        if len(prev)>=10 and rf[prev].sum()<0: mfam[i]=0.5
T('familia con 10 últimas en negativo x0,5',BASE,None,mfam)
