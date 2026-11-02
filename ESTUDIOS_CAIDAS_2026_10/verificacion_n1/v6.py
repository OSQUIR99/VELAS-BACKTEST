import sys; sys.path.insert(0,'/home/claude/caidas')
import numpy as np, pandas as pd
from comun import Cartera, LISTAS_CORTOS, FL
C=Cartera(extra=(LISTAS_CORTOS,'/home/claude/caidas/listas_nuevas'))
nm=(C.L=='n1_vixvxv')&(C.O.t_entrada>=C.desde).values
cfg=dict(FL); cfg['freno']=None
for usar in (False,True):
  C.usar_base_31oct=usar
  for v in list(C.bases)[:2]:
    b=C.bases[v]; _,eb=C.sim(b,cfg=cfg); _,en=C.sim(b|nm,cfg=cfg); qb=C.met3(eb); qn=C.met3(en)
    print('no-freno',usar,v[0],C.fmt(qb)); print('        +n1',C.fmt(qn), all(qn[i]['ratio']>qb[i]['ratio'] for i in range(3)))
