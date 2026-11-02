import sys, os
sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10')
import numpy as np, pandas as pd, comun, warnings; warnings.filterwarnings('ignore')
TERCIO = os.environ.get('TERCIO','1')=='1'
if TERCIO: comun.LISTAS_GH='/home/claude/mej/gh'
C=comun.Cartera(extra=('/home/claude/velas-backtest/MOTOR/listas_reconstruidas',))
O=C.O; L=C.L; act=C.act; d=(O.t_entrada>=C.desde).values
W=C.W|(d&np.isin(L,['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq']))
E1=(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX'])&W
nucleo=(np.isin(L,['cripto','petroleo','corto_petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
ex=np.isin(L,['corto_sector','corto_indices_credito'])&W
n1=(L=='n1_vixvxv')&W; cn=(L=='yt_connors_qqq')&W
BASE=nucleo|ex|cn; EX=ex|E1|cn
C.cortos_exentos=EX
def run(m=None,exentas=None,tm=None,cfg=None):
    r,e=C.sim(BASE if m is None else m,cfg=cfg,exentas=EX if exentas is None else exentas,tam_mult=tm); return r,e,C.met3(e)
def ok(q,q0): return all(q[i]['ratio']>q0[i]['ratio'] for i in range(3))
def ultimos(e):
    return [comun.met_eq(e,pd.Timestamp(a))['ratio'] for a in ('2024-01-01','2025-01-01')]
