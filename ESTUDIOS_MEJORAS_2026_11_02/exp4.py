from base import *
from exp2 import FAM
import sys
r0,e0,q0=run(); print('B0',C.fmt(q0),[round(x,2) for x in ultimos(e0)],flush=True)
def tmw(**w):
    t=np.ones(len(O))
    for f,v in w.items(): t[FAM[f]]=v
    return t
K={'K1 corto_pet x2 + petroleo x0,75':dict(corto_pet=2,petroleo=0.75),
   'K2 K1 + x_petroleo x0,75':dict(corto_pet=2,petroleo=0.75,x_petroleo=0.75),
   'K3 K2 + c10 x0,5':dict(corto_pet=2,petroleo=0.75,x_petroleo=0.75,c10=0.5),
   'K4 corto_pet x2 + petroleo x0,5':dict(corto_pet=2,petroleo=0.5),
   'K5 petroleo x0,75 + x_pet x0,75 + c10 x0,5':dict(petroleo=0.75,x_petroleo=0.75,c10=0.5),
   'K6 corto_pet x2':dict(corto_pet=2)}
for nom,w in K.items():
    r,e,q=run(tm=tmw(**w)); b=C.bootstrap(e0,e,500)
    fr=[]
    for fz in ((3,0.5),(5,0.5),(4,0.75)):
        cfg=dict(comun.FL); cfg['freno']=fz
        _,eb,qb=run(cfg=cfg); _,ek,qk=run(tm=tmw(**w),cfg=cfg); fr.append(ok(qk,qb))
    print(f'{nom:44s}',C.fmt(q),'PASA' if ok(q,q0) else '-','| últimos',[round(x,2) for x in ultimos(e)],'| remuestreo',round(b,2),'| frenos 3R/5R/x0,75',fr,'| media 5 peores',round(C.media5(e)[0],2),'vs',round(C.media5(e0)[0],2),flush=True)
