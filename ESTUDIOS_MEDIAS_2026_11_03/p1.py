# Propuesta 1: ruptura de la EMA 20 diaria en cripto, solo largos, 40 velas dentro
import sys, os
sys.path.insert(0,'/home/claude/caidas'); sys.path.insert(0,'/home/claude/velas-backtest')
import numpy as np, pandas as pd, nuevas as N
from cargar import velas
N.COSTE=0.001   # cripto: 0,1 % ida y vuelta
MON=['BTC','ETH','SOL','ADA','LINK','ZEC']
def lista(a, stop, span=20, hold=40, tam=0.5):
    d=velas(a,'1d').copy(); d=d[~d.index.duplicated()]
    e=d.cierre.ewm(span=span,adjust=False).mean()
    ent=((d.cierre>e)&(d.cierre.shift(1)<=e.shift(1))).fillna(False).values
    sf=(lambda en,at: en-2.5*at) if stop else (lambda en,at: en*0.75)
    O,D=N.run(d,ent,lambda j,ei: j-ei>=hold-1,stop_fn=sf,nombre=f'p1_ema{span}_{"st" if stop else "ns"}',activo=a,tam=tam,bloque='cripto',desde='2017-01-01')
    return O,D
if __name__=='__main__':
    for stop in (True,False):
        for grupo,mons in (('btc',['BTC']),('6',MON)):
            car=f'/home/claude/med/l_p1_{grupo}_{"st" if stop else "ns"}'; os.makedirs(car,exist_ok=True)
            OO,DD=[],[]
            for a in mons:
                O,D=lista(a,stop,tam=1.0 if grupo=='btc' else 0.5); OO.append(O); DD.append(D)
            O=pd.concat(OO,ignore_index=True); D=pd.concat(DD,ignore_index=True)
            nom=f'p1_{grupo}_{"st" if stop else "ns"}'; O['familia']=nom; O['id']=nom+'-'+O.activo+'-'+O.id.str.split('-').str[-1]
            D['id']=D.id.map(dict(zip(pd.concat(OO).id.values,O.id.values))) if False else None
            # rehacer ids del diario en el mismo orden
            D=pd.concat([d.assign(id=nom+'-'+a+'-'+d.id.str.split('-').str[-1]) for d,a in zip(DD,mons)],ignore_index=True)
            O.to_parquet(f'{car}/{nom}.parquet'); D.to_parquet(f'{car}/{nom}_diario.parquet')
            u=O.r_bruto; t=pd.to_datetime(O.t_entrada)
            w=lambda a,b: u[(t>=a)&(t<b)]
            print(nom,'ops',len(O),'R/op',round(u.mean(),3),'| 2018-21',round(w('2018-05','2022').mean(),3),len(w('2018-05','2022')),'| 2022-26',round(w('2022','2027').mean(),3),len(w('2022','2027')),'| 2023-26',round(w('2023','2027').mean(),3),'| stops',(O.motivo_salida=='stop').mean().round(2),flush=True)
