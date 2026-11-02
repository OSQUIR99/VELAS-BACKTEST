import sys; sys.path.insert(0,'/home/claude/verif_2nov')
import numpy as np, pandas as pd, vc
C = vc.montar(True); O=C.O; L=C.L; s=C.senal
for l in ('petroleo','corto_petroleo','x_petroleo'):
    m=(L==l); print(l, 'total', m.sum(), 'en mascara', (m&C.mask).sum()); print(pd.Series(s[m&C.mask]).value_counts().to_dict())
