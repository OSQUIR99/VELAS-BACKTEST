import sys; sys.path.insert(0,'/home/claude/caidas')
import numpy as np, pandas as pd
from comun import Cartera, LISTAS_CORTOS
C=Cartera(extra=(LISTAS_CORTOS,'/home/claude/caidas/listas_nuevas'))
O=C.O; print('desde',C.desde, 'cols', list(O.columns)[:40])
nm=(C.L=='n1_vixvxv')&(O.t_entrada>=C.desde).values
print('n1 in window',nm.sum(), 'R sum', O.r_final[nm].sum().round(2), 'sin_freno n1', C.M.sin_freno[nm].sum() if hasattr(C.M.sin_freno,'__len__') else C.M.sin_freno)
for cfg in (False,True):
    C.usar_base_31oct=cfg
    for v in list(C.bases)[:2]:
        b=C.bases[v]; rb,eb=C.sim(b); qb=C.met3(eb); rn,en=C.sim(b|nm); qn=C.met3(en)
        print(cfg,v[0],'base',C.fmt(qb)); print(cfg,v[0],'+n1 ',C.fmt(qn), 'ratio up all3:',all(qn[i]['ratio']>qb[i]['ratio'] for i in range(3)))
        if cfg and v[0]=='a':
            s=rn.s if hasattr(rn,'s') else None
            print(type(rn), [a for a in dir(rn) if not a.startswith('_')][:20])
