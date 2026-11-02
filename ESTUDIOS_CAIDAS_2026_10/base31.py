import numpy as np
from comun import Cartera
C=Cartera()
for flag in (False,True):
    C.usar_base_31oct=flag
    print('== base del 31-oct (SHY 10k + cortos x2)' if flag else '== base del 28-oct')
    for n,m in C.bases.items():
        rr,eq=C.sim(m); q=C.met3(eq); print(f'  {n:32s}',C.fmt(q))
C.usar_base_31oct=True
shy=(C.L=='shy')&C.W
import pandas as pd
print('factor SHY mediano', round(float(np.median(C.tam_base[shy])),3), 'R por tercio mediano', round(float(np.median(C.tam_base[shy]*C.O.tam_R.values[shy])),3))
