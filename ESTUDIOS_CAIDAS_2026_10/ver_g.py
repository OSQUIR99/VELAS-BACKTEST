import numpy as np, pandas as pd
import reglas as R
C=R.C; M=R.M; O=R.O
base=C.bases['a · con S1 (listas originales)']
M2,n=R.motor_protegido(R.CRI&base,3,0.5,False)
k=np.flatnonzero(M2.rf!=M.rf)
rb,eqb=C.sim(base)
d0=pd.Timestamp(M.dia0)
for j in k:
    print(C.act[j], O.t_entrada.iloc[j].date(), '→ salida real', O.t_salida.iloc[j].date(), f'R real {M.rf[j]:+.2f}', '| con protección sale', (d0+pd.Timedelta(days=int(M2.sal_dia[j]))).date(), f'R {M2.rf[j]:+.2f}', '| tomada' if rb.s[j]>0 else '| no tomada')
