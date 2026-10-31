import os, numpy as np, pandas as pd
import nuevas as N
from cortos import diario
from linea import fred
from comun import Cartera, LISTAS_CORTOS
spx=diario('sp500'); vix=diario('vix').cierre; vxv=fred('VXVCLS','2007-01-01'); vxv.index=vxv.index.normalize()
r=(vix/vxv.reindex(vix.index).ffill()).reindex(spx.index)
ent=((r<1)&(r.shift(1)>1)).fillna(False).values
m=spx.cierre.rolling(200).mean(); filt=(m>m.shift(20)).values
car='/home/claude/caidas/listas_vec_n1'; os.makedirs(car,exist_ok=True)
V={'v_hold5':(ent,4,1.0),'v_hold13':(ent,12,1.0),'v_05R':(ent,8,0.5),'v_15R':(ent,8,1.5),'v_filtro200':(ent&filt,8,1.0),'v_real':(ent,8,1.0)}
for k,(e,h,t) in V.items():
    O,D=N.run(spx,e,lambda j,ei,h=h: j-ei>=h,stop_fn=lambda e_,a:e_*0.8,nombre=k,desde='2008-01-01',tam=t)
    O.to_parquet(f'{car}/{k}.parquet'); D.to_parquet(f'{car}/{k}_diario.parquet'); print(k,len(O),round(O[O.t_entrada>='2018-05-01'].r_final.sum()/8.47,2))
C=Cartera(extra=(LISTAS_CORTOS,car)); res=[]
for cfg in (False,True):
    C.usar_base_31oct=cfg
    for nb,base in C.bases.items():
        rb,eqb=C.sim(base); qb=C.met3(eqb)
        for k in V:
            nm=(C.L==k)&(C.O.t_entrada>=C.desde).values; rr,eq=C.sim(base|nm); q=C.met3(eq)
            res.append(dict(k=k,cfg=cfg,v=nb[0],d=q[0]['ratio']-qb[0]['ratio'],d1821=q[1]['ratio']-qb[1]['ratio'],d2226=q[2]['ratio']-qb[2]['ratio'],Ra=q[0]['R_ano']-qb[0]['R_ano'],caida=q[0]['caida']-qb[0]['caida'],pasa=all(q[i]['ratio']>qb[i]['ratio'] for i in range(3))))
R=pd.DataFrame(res); R.to_csv('vecinos_n1.csv',index=False)
print(R.groupby('k').agg(pasa=('pasa','sum'),d=('d','mean'),d1821=('d1821','mean'),d2226=('d2226','mean'),Ra=('Ra','mean'),caida=('caida','mean')).round(3).to_string())
