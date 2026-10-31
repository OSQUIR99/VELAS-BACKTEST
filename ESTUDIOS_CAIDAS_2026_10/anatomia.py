import numpy as np, pandas as pd, pickle
from comun import Cartera, HOY
from factores import cierre
C=Cartera(); O=C.O; M=C.M
T=pd.read_parquet('operaciones_factores.parquet')
ep=pickle.load(open('epis_a.pkl','rb'))
btc=cierre('BTC'); spx=cierre('sp500'); oro=cierre('oro'); brent=cierre('petroleo_brent'); y10=None
L=pd.read_parquet('linea.parquet')
F=pd.read_parquet('factores.parquet')
def ch(s,a,b):
    s=s[(s.index>=a)&(s.index<=b)]; return f'{(s.iloc[-1]/s.iloc[0]-1)*100:+.0f}%' if len(s)>1 else '-'
T['salida']=O.t_salida.reindex(T.index).values if False else pd.to_datetime(O.t_salida.values[T.index.values])
for a,b,c,prof in ep['eps'][:8]:
    g=T[(T.salida>=a)&(T.salida<=b+pd.Timedelta(days=1))]
    cr=g[g.familia=='cripto REBOTE 4H']
    lin=L.linea.asof(a); 
    print(f'\n### {a.date()} → {b.date()} caída {prof:.1f} R | BTC {ch(btc,a,b)} · S&P {ch(spx,a,b)} · oro {ch(oro,a,b)} · Brent {ch(brent,a,b)} | línea liquidez {lin:.0f}')
    print(f'   cerradas en el tramo: {len(g)} ({(g.R<0).sum()} perdedoras), R {g.R.sum():+.1f} | cripto {len(cr)} ops, {(cr.R<0).sum()} perdedoras, R {cr.R.sum():+.1f}; monedas {cr.activo.value_counts().to_dict()}')
    peor=g.sort_values('R').head(6)
    print('   peores:', '; '.join(f"{r.familia.split()[0]} {r.activo} {pd.Timestamp(r.t).strftime('%d-%m')} {r.R:+.1f}" for _,r in peor.iterrows()))
    print('   al empezar: abiertas', int(T[(pd.to_datetime(T.t)<a)&(T.salida>a)].shape[0]), '| factores:', {k: int(F[k].asof(a)) for k in ['btc_bajo200','vix_alto','dolar_sube','tipos_suben','liquidez_baja','B21_semis_flojos','financiacion_alta']})
