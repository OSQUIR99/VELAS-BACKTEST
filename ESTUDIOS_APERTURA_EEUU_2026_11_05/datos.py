import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import os; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')); from cargar import velas
def dias_sp(tf='1h', activo='sp500'):
    d=velas(activo,tf).copy(); d.index=pd.to_datetime(d.index)
    et=d.index.tz_localize('UTC').tz_convert('America/New_York'); d['dia']=et.date; d['hora_et']=et.hour+et.minute/60
    return d
def btc5():
    b=velas('BTC','5m').copy(); b.index=pd.to_datetime(b.index); return b
def precio_en(b, t_utc):
    """apertura de la vela de 5 m que empieza en t_utc (o la siguiente)"""
    i=b.index.searchsorted(t_utc); i=np.minimum(i,len(b)-1); return b.apertura.values[i], b.index[i]
def tabla():
    s=dias_sp('1h'); g=s.groupby('dia')
    T=pd.DataFrame({'abre':g.apertura.first(),'h1':g.cierre.first(),'cierra':g.cierre.last(),'n':g.size(),
                    't0':g.apply(lambda x:x.index[0])})
    T=T[(T.n>=6)]  # sesiones completas (6-7 barras); medias sesiones fuera
    T['r1']=T.h1/T.abre-1; T['rr']=T.cierra/T.h1-1
    T['t0']=pd.to_datetime(T.t0)
    b=btc5()
    t930=T.t0; t1030=t930+pd.Timedelta(hours=1); t1600=t930+pd.Timedelta(hours=6.5)
    t930n=t930.shift(-1); tprev=t1600.shift(1)
    for nom,t in [('b930',t930),('b1030',t1030),('b1600',t1600),('b930n',t930n),('bprev',tprev)]:
        ok=t.notna(); v=np.full(len(T),np.nan); v[ok.values]=precio_en(b,pd.DatetimeIndex(t[ok]))[0]; T[nom]=v
    T['b_pre']=T.b930/T.bprev-1; T['b1']=T.b1030/T.b930-1; T['brr']=T.b1600/T.b1030-1; T['b24']=T.b930n/T.b1030-1
    return T
if __name__=='__main__':
    T=tabla(); T.to_pickle('T1h.pkl'); print(T.shape); print(T[['r1','rr','b1','brr','b24']].describe().round(4))
