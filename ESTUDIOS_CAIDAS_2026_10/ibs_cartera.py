import numpy as np, pandas as pd
from comun import Cartera, LISTAS_CORTOS
C=Cartera(extra=(LISTAS_CORTOS,'/home/claude/caidas/listas_ibs'))
ibs=(C.L=='ibs_spy')&(C.O.t_entrada>=C.desde).values
for nb,base in C.bases.items():
    rb,eqb=C.sim(base); qb=C.met3(eqb)
    print(nb,'BASE',C.fmt(qb))
    for f in (1.0,0.5):
        rr,eq=C.sim(base|ibs, tam_mult=np.where(ibs,f,1.0)); q=C.met3(eq)
        print(f'   + IBS SPY a {f} R', C.fmt(q), '| PASA' if C.pasa(q,qb) else '| no', '| boot', C.bootstrap(eqb,eq,500), '| escalada', round(q[0]['R_ano']*qb[0]['caida']/q[0]['caida'],1))
