import os, numpy as np, pandas as pd, shutil
import nuevas as N
from cortos import diario
from linea import fred
from comun import Cartera, LISTAS_CORTOS
spx=diario('sp500'); vix=diario('vix').cierre; vxv=fred('VXVCLS','2007-01-01'); vxv.index=vxv.index.normalize()
r=(vix/vxv.reindex(vix.index).ffill()).reindex(spx.index)
real=((r<1)&(r.shift(1)>1)).fillna(False).values
car='/home/claude/caidas/listas_placebo'; os.makedirs(car,exist_ok=True)
def escribir(ent,nombre,hold=8,tam=1.0):
    for f in os.listdir(car): os.remove(os.path.join(car,f))
    O,D=N.run(spx,ent,lambda j,ei: j-ei>=hold,stop_fn=lambda e,a:e*0.8,nombre='plac',desde='2008-01-01',tam=tam)
    O.to_parquet(f'{car}/plac.parquet'); D.to_parquet(f'{car}/plac_diario.parquet'); return len(O)
C=Cartera(extra=(LISTAS_CORTOS,car))
def medir(cfg,v):
    C.usar_base_31oct=cfg; base=C.bases[v]
    C.O  # listas ya cargadas al crear; recargar para cada placebo
    return base
rng=np.random.default_rng(3); idx=spx.index; elig=np.flatnonzero(idx>='2008-01-01')
res=[]
for it in range(41):
    if it==0: ent=real; nom='real'
    else:
        ent=np.zeros(len(idx),bool); ent[rng.choice(elig,real[elig].sum(),replace=False)]=True; nom=f'p{it}'
    escribir(ent,nom)
    Ci=Cartera(extra=(LISTAS_CORTOS,car))
    nm=(Ci.L=='plac')&(Ci.O.t_entrada>=Ci.desde).values
    for cfg in (False,True):
        Ci.usar_base_31oct=cfg
        for v in ('a · con S1 (listas originales)','b · sin S1'):
            base=Ci.bases[v]; rb,eqb=Ci.sim(base); qb=Ci.met3(eqb); rr,eq=Ci.sim(base|nm); q=Ci.met3(eq)
            res.append(dict(it=nom,cfg=cfg,v=v[0],d=q[0]['ratio']-qb[0]['ratio'],pasa=all(q[i]['ratio']>qb[i]['ratio'] for i in range(3))))
    if it%10==0: print(it,flush=True)
R=pd.DataFrame(res); R.to_csv('placebo_n1.csv',index=False)
real_=R[R.it=='real']; pl=R[R.it!='real']
print('real:', real_[['cfg','v','d','pasa']].to_string(index=False))
g=pl.groupby('it').agg(pasa=('pasa','sum'),d=('d','mean'))
print('placebos que pasan en las 4 versiones:', int((g.pasa==4).sum()),'de',len(g),'| en ≥3:', int((g.pasa>=3).sum()),
      '| mejora media del ratio placebo', round(g.d.mean(),3),'| real', round(real_.d.mean(),3), '| placebos con mejora ≥ real:', int((g.d>=real_.d.mean()).sum()))
