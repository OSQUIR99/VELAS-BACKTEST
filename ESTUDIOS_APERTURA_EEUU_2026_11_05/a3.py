import pandas as pd, numpy as np
from scipy import stats
from datos import *
d=velas('sp500','1d'); d.index=pd.to_datetime(d.index); d=d[d.index>='1995-01-01']
g=d.apertura/d.cierre.shift(1)-1; i=d.cierre/d.apertura-1
print('días con apertura = cierre anterior (dato malo):', f"{(g.abs()<1e-6).mean()*100:.1f}%")
for per,a,b in [('1995-2005','1995','2005'),('2006-14','2006','2014'),('2015-21','2015','2021'),('2022-26','2022','2026')]:
    m=(d.index.year>=int(a))&(d.index.year<=int(b))&(g.abs()>1e-6)
    x=g[m]; y=i[m]
    for u in [0.0,0.005]:
        up=x>u; dn=x<-u
        print(f"S&P hueco {per} umbral {u*100:.1f}%: abre arriba n={up.sum()} → día {y[up].mean()*100:+.3f}% (cierra bajo la apertura {(y[up]<0).mean()*100:.0f}%) | abre abajo n={dn.sum()} → {y[dn].mean()*100:+.3f}% (cierra sobre {(y[dn]>0).mean()*100:.0f}%)")
