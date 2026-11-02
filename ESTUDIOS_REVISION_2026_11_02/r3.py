from base2 import *
import warnings; warnings.filterwarnings('ignore')
from comun import met_eq
def run(m,ex_):
    r,e=C.sim(m,exentas=ex_); return e
e0=run(BASE,ex)
for nom,m,x in [('E1 fuera',BASE,ex|E1),('E1+Connors fuera',BASE|cn,ex|E1|cn),('E1+Connors+N1 fuera',BASE|cn|n1,ex|E1|cn|n1)]:
    e=run(m,x); q=[met_eq(e,pd.Timestamp(a)) for a in ['2024-01-01','2025-01-01']]; qb=[met_eq(e0,pd.Timestamp(a)) for a in ['2024-01-01','2025-01-01']]
    print(f'{nom:22s}','2024-26',f"{qb[0]['ratio']:.2f}->{q[0]['ratio']:.2f}",'2025-26',f"{qb[1]['ratio']:.2f}->{q[1]['ratio']:.2f}",'boot',round(C.bootstrap(e0,e,1000),2),flush=True)
