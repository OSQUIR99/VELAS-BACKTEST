import pandas as pd, numpy as np
from core import *
pd.set_option('display.width',250)
oi=pd.read_parquet('oi_btc.parquet').set_index('fecha')
fu=pd.read_parquet(BASE+'CARPETA_DE_BACKTEST/CRIPTO_PERPETUOS/BTC/financiacion.parquet'); fu['fecha']=fu.fecha.dt.floor('min'); fu=fu.set_index('fecha').tasa
ev=pd.read_parquet('ev2.parquet')
rows=[]
for tf,hrs in [('1h',1),('4h',4),('1d',24)]:
    df=cargar('BTC',tf)
    e=ev[(ev.activo=='BTC')&(ev.tf==tf)&ev.t.notna()].copy()
    e['T']=df.fecha.values[e.t.astype(int).values]
    oiv=oi.sum_open_interest
    def at(ts):
        i=oiv.index.searchsorted(ts,side='right')-1
        return oiv.iloc[i] if i>=0 else np.nan
    T=e['T']
    o0=np.array([at(x) for x in T]); o1=np.array([at(x+pd.Timedelta(hours=hrs)) for x in T])
    o24=np.array([at(x-pd.Timedelta(hours=max(24,hrs*6))) for x in T])
    e['oi_vela']=100*(o1/o0-1); e['oi_aprox']=100*(o0/o24-1)
    e.loc[e['T']<pd.Timestamp('2020-09-02'),['oi_vela','oi_aprox']]=np.nan
    fi=fu.index.searchsorted(T,side='right')-1
    e['funding']=np.where(fi>=0, fu.values[np.clip(fi,0,None)]*100, np.nan)
    e.loc[e['T']<pd.Timestamp('2022-10-02'),'funding']=np.nan
    lsr=oi.count_long_short_ratio
    e['ls_ratio']=[lsr.iloc[max(0,lsr.index.searchsorted(x,side='right')-1)] for x in T]
    e.loc[e['T']<pd.Timestamp('2020-09-02'),'ls_ratio']=np.nan
    rows.append(e)
b=pd.concat(rows); b.to_parquet('ev2_btc.parquet')
b=b[b.res.isin([1,-1])].copy(); b['giro']=(b.res==1)*100
# en espejo: para 'corto' (barridos de maximos) una caida de OI = cortos liquidados; funding se invierte de signo
b.loc[b.lado=='corto','funding']*=-1
b.loc[b.lado=='corto','ls_ratio']=1/b.loc[b.lado=='corto','ls_ratio']
for k in [1.5,2.5]:
    g=b[(b.k==k)&b.oi_vela.notna()].copy()
    print(f'\n===== k={k}  n={len(g)}  (desde sept-2020)')
    for col in ['oi_vela','oi_aprox','funding','ls_ratio']:
        gg=g.dropna(subset=[col]).copy()
        gg['bk']=gg.groupby('tf')[col].transform(lambda s: pd.qcut(s,4,labels=['Q1 bajo','Q2','Q3','Q4 alto'],duplicates='drop'))
        print('\n#',col, '(cuartiles dentro de cada temporalidad)')
        print(gg.groupby('bk').agg(n=('giro','size'),rango_min=(col,'min'),rango_max=(col,'max'),giro=('giro','mean'),E2=('E2_R','mean'),E2b=('E2b_R','mean'),E3=('E3_R','mean')).round(3))
