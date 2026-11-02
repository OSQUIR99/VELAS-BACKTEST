import sys; sys.path.insert(0,'/home/claude/mej')
from h import *
res={}
for nom in ['v0','vol','vol_o_puntos','puntos']:
    O=pd.read_parquet(f'L_{nom}.parquet'); D=pd.read_parquet(f'L_{nom}_diario.parquet')
    C=cartera(O,D); M=mascaras(C); _,e,q=evalua(C,M['BASE'],M['EX']); res[nom]=(C,e,q)
    print(f'{nom:14s}',C.fmt(q),f'| 24-26 {met24(C,e):.2f}',flush=True)
    for fr in [(3,0.5),(5,0.5)]:
        cfg=dict(comun.FL); cfg['freno']=fr; _,e2,q2=evalua(C,M['BASE'],M['EX'],cfg=cfg); print(f'   freno {fr}',C.fmt(q2),flush=True)
C0,e0,q0=res['vol']
for nom in ['vol_o_puntos','puntos']:
    C,e,q=res[nom]; informe(C,f'{nom} frente a vol',q,q0,e,e0)
C0,e0,q0=res['v0']; C,e,q=res['vol']; informe(C,'vol frente a v0 (regla aprobada)',q,q0,e,e0)
