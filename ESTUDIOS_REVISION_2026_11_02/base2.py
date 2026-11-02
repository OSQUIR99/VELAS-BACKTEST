import sys; sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10')
import numpy as np, pandas as pd, comun
from comun import Cartera
C=Cartera(extra=('/home/claude/velas-backtest/MOTOR/listas_reconstruidas',))
O=C.O; L=C.L; act=C.act; d=(O.t_entrada>=C.desde).values
W=C.W|(d&np.isin(L,['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq']))
E1=(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX'])&W
nucleo=(np.isin(L,['cripto','petroleo','corto_petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
ex=np.isin(L,['corto_sector','corto_indices_credito'])&W; C.cortos_exentos=ex
BASE=nucleo|ex; n1=(L=='n1_vixvxv')&W; cn=(L=='yt_connors_qqq')&W
