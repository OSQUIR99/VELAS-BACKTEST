import pandas as pd, numpy as np
from datos import *
def met(r, nom, cost):
    r=r.dropna()-cost
    yrs=(r.index[-1]-r.index[0]).days/365.25
    eq=r.cumsum(); dd=(eq.cummax()-eq).max()
    an=r.sum()/yrs
    def sub(a,b):
        x=r[(r.index.year>=a)&(r.index.year<=b)]
        if len(x)<20: return float('nan')
        e=x.cumsum(); y=(x.index[-1]-x.index[0]).days/365.25; return (x.sum()/y)/max((e.cummax()-e).max(),1e-9)
    print(f"{nom:52s} n={len(r):4d} media {r.mean()*100:+.3f}% acierta {(r>0).mean()*100:.0f}% | %/año {an*100:+.1f} caída {dd*100:.1f}% ratio {an/dd if dd>0 else 0:+.2f} | 2006-14 {sub(2006,2014):+.2f} 2015-21 {sub(2015,2021):+.2f} 2022-26 {sub(2022,2026):+.2f}")
# S&P 4 h desde 2006: entrar a las 13:30 ET en el sentido (o contra) del tramo 9:30-13:30, salir al cierre
s4=dias_sp('4h'); g=s4.groupby('dia'); Q=pd.DataFrame({'o':g.apertura.first(),'m':g.cierre.first(),'c':g.cierre.last(),'n':g.size()}); Q=Q[Q.n==2]
Q.index=pd.to_datetime(Q.index); r1=Q.m/Q.o-1; r2=Q.c/Q.m-1
print('Coste S&P en Quantfury: ~0,02 % ida y vuelta; BTC: 0,05 %')
for u in [0.0,0.005,0.01]:
    m=r1.abs()>u
    met((np.sign(r1)*r2)[m],f'S&P SEGUIR la mañana (|mañana|>{u*100:.1f}%) 2006-26',0.0002)
    met((-np.sign(r1)*r2)[m],f'S&P IR EN CONTRA de la mañana (|mañana|>{u*100:.1f}%)',0.0002)
# S&P 1 h desde 2020: en contra/a favor de la 1ª hora, de 10:30 al cierre
T=pd.read_pickle('T1h.pkl'); T.index=pd.to_datetime(T.index)
for u in [0.0,0.003,0.006]:
    m=T.r1.abs()>u
    met((np.sign(T.r1)*T.rr)[m],f'S&P SEGUIR 1ª hora (|1ª h|>{u*100:.1f}%) 2020-26',0.0002)
    met((-np.sign(T.r1)*T.rr)[m],f'S&P EN CONTRA de la 1ª hora (|1ª h|>{u*100:.1f}%)',0.0002)
# BTC: en contra de los primeros 30 min, salir al cierre de bolsa (2017-26)
b=btc5(); d=dias_sp('1d'); d=d[d.index>='2017-09-01']; t0=pd.DatetimeIndex(d.index)
o=precio_en(b,t0)[0]; m30=precio_en(b,t0+pd.Timedelta(minutes=30))[0]; c=precio_en(b,t0+pd.Timedelta(minutes=390))[0]
x=pd.Series(m30/o-1,index=t0); y=pd.Series(c/m30-1,index=t0)
for u in [0.0,0.005,0.01]:
    m=x.abs()>u
    met((-np.sign(x)*y)[m],f'BTC EN CONTRA de los 30 min (|30 min|>{u*100:.1f}%)',0.0005)
    met((-np.sign(x)*y)[m&(x<0)],f'BTC compra si baja en 30 min (>{u*100:.1f}%)',0.0005)
