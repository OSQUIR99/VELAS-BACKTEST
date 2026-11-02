import sys; sys.path.insert(0,'/home/claude/mej')
from h import *
res={}
for nom in ['vol','vol_o_puntos','puntos']:
    O=pd.read_parquet(f'B_{nom}.parquet'); D=pd.read_parquet(f'B_{nom}_diario.parquet')
    C=cartera(O,D); M=mascaras(C); _,e,q=evalua(C,M['BASE'],M['EX']); res[nom]=(C,e,q)
    print(f'{nom:14s}',C.fmt(q),f'| 24-26 {met24(C,e):.2f}',flush=True)
    for fr in [(3,0.5),(5,0.5)]:
        cfg=dict(comun.FL); cfg['freno']=fr; _,e2,q2=evalua(C,M['BASE'],M['EX'],cfg=cfg); print(f'   freno {fr}',C.fmt(q2),flush=True)
C0,e0,q0=res['vol']
for nom in ['vol_o_puntos','puntos']:
    C,e,q=res[nom]; informe(C,f'{nom} frente a vol',q,q0,e,e0)
O=pd.read_parquet('L_v0.parquet'); D=pd.read_parquet('L_v0_diario.parquet'); Cv=cartera(O,D); Mv=mascaras(Cv); _,ev0,qv0=evalua(Cv,Mv['BASE'],Mv['EX'])
C,e,q=res['vol']; informe(C,'vol (stop a entrada) frente a v0',q,qv0,e,ev0)
for nom in ['vol_o_puntos','puntos']:
    C,e,q=res[nom]; informe(C,f'{nom} frente a v0',q,qv0,e,ev0)
