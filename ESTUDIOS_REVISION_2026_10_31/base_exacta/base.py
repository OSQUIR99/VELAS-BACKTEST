import sys; sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10')
import numpy as np, pandas as pd
import comun; pass  # comun.py ya excluye petroleo_con_s1 (antes: carpeta local sin esa lista)
from comun import Cartera
C=Cartera(extra=('/home/claude/velas-backtest/MOTOR/listas_reconstruidas','/home/claude/liq31/listas_nuevas','/home/claude/exacta/listas_extra'))
C.usar_base_31oct=True
O=C.O; L=C.L; act=C.act; W=C.W|((O.t_entrada>=C.desde).values&np.isin(L,['corto_petroleo','n1_vixvxv','btc_sem_impulso','btc_sem_linea','corto_indices_credito','corto_sector','connors_qqq']))
print(pd.Series(L[W]).value_counts().to_dict())
IDX=['SPX','DJI','NDX']
E1=(L=='bolsa_e1')&np.isin(act,IDX)&W
nucleo=(np.isin(L,['cripto','petroleo','corto_petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
ex=np.isin(L,['corto_sector','corto_indices_credito'])&W
C.cortos_exentos=ex
n1=(L=='n1_vixvxv')&W
BASE=nucleo|ex
if __name__=='__main__':
    for nom,m in (('base 31-oct sin N1',BASE),('base + N1 (vigente)',BASE|n1)):
        rr,eq=C.sim(m); print(nom,C.fmt(C.met3(eq)))
