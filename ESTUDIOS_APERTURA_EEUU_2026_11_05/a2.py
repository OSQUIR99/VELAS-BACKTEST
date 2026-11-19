import pandas as pd, numpy as np
from scipy import stats
from datos import *
T=pd.read_pickle('T1h.pkl')
b=btc5()
# BTC desde 2017: sesiones de EE. UU. reconstruidas con el calendario del S&P diario
d=dias_sp('1d'); d=d[d.index>='2017-09-01']
t0=pd.DatetimeIndex(d.index)  # 1d lleva la hora de apertura en UTC (13:30/14:30)
def p(t): return precio_en(b,t)[0]
R=pd.DataFrame(index=t0)
for nom,mins in [('o',0),('m15',15),('m30',30),('m60',60),('c30',360),('c',390),('n',None)]:
    if mins is None: continue
    R[nom]=p(t0+pd.Timedelta(minutes=mins))
R['n24']=np.r_[R.o.values[1:],np.nan]
R['año']=R.index.year
def cond(x,y,nom,D):
    m=x.notna()&y.notna(); x=x[m]; y=y[m]; up=x>0; dn=x<0
    print(f"{nom:40s} n={len(x)} | sube: después {y[up].mean()*100:+.3f}% (baja {(y[up]<0).mean()*100:.0f}%) | baja: después {y[dn].mean()*100:+.3f}% (sube {(y[dn]>0).mean()*100:.0f}%) | corr {np.corrcoef(x,y)[0,1]:+.3f} p {stats.pearsonr(x,y)[1]:.3f}")
# S&P con 15 m (abr-2025 → nov-2026)
s=dias_sp('15m'); g=s.groupby('dia')
S=pd.DataFrame({'o':g.apertura.first(),'m15':g.cierre.agg(lambda v:v.iloc[0]),'m30':g.cierre.agg(lambda v:v.iloc[1]),'c30':g.apertura.agg(lambda v:v.iloc[-2]),'c':g.cierre.last(),'n':g.size()})
S=S[S.n>=26]
print('== S&P 15 min (abr-2025 a nov-2026) ==')
cond(S.m15/S.o-1,S.c/S.m15-1,'15 min → cierre',S); cond(S.m30/S.o-1,S.c/S.m30-1,'30 min → cierre',S); cond(S.m30/S.o-1,S.c/S.c30-1,'30 min → última media hora',S)
# S&P 1h 2020-26: 1ª hora → última media hora y ¿cierra bajo la apertura?
s1=dias_sp('1h'); g=s1.groupby('dia'); L=pd.DataFrame({'o':g.apertura.first(),'h1':g.cierre.first(),'u_o':g.apertura.last(),'c':g.cierre.last(),'n':g.size()}); L=L[L.n>=6]
print('== S&P 1 h (2020-26) ==')
cond(L.h1/L.o-1,L.c/L.u_o-1,'1ª hora → última media hora',L)
cond(L.h1/L.o-1,L.c/L.o-1,'1ª hora → día entero (cierre frente a apertura)',L)
# S&P 4h desde 2006: primer tramo (9:30-13:30) → segundo (13:30-16:00)
s4=dias_sp('4h'); g=s4.groupby('dia'); Q=pd.DataFrame({'o':g.apertura.first(),'m':g.cierre.first(),'c':g.cierre.last(),'n':g.size()}); Q=Q[Q.n==2]
Q['año']=pd.to_datetime(Q.index).year
print('== S&P 4 h (2006-26): 9:30-13:30 → 13:30-16:00 ==')
for per,D in [('2006-26',Q),('2006-14',Q[Q.año<=2014]),('2015-21',Q[(Q.año>=2015)&(Q.año<=2021)]),('2022-26',Q[Q.año>=2022])]:
    cond(D.m/D.o-1,D.c/D.m-1,per,D)
