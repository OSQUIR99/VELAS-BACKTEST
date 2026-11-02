import sys; sys.path.insert(0,'/home/claude/mej')
from h import *
def k8(C):
    L=C.L; s=C.O['senal'].astype(str).values if 'senal' in C.O.columns else np.array(['']*len(C.O)); t=np.ones(len(L))
    t[L=='corto_petroleo']=2.0; t[(L=='petroleo')&(s=='L2')]=0.5; t[(L=='petroleo')&(s=='tras-noticia (bajada)')]=0.5; t[L=='x_petroleo']=0.75
    return t
def corre(O,D,cfg=None):
    C=cartera(O,D); M=mascaras(C); _,e,q=evalua(C,M['BASE'],M['EX'],tm=k8(C),cfg=cfg); return C,e,q
O,D,n=sin_tercio(O0,D0,cond_base(O0)); C,e,q=corre(O,D); print('base K8 (fórmula, oficial)',C.fmt(q),f'| 24-26 {met24(C,e):.2f}',flush=True)
R={}
for nom,pre in [('v0','L'),('vol','B'),('vol_o_puntos','B'),('puntos','B')]:
    O=pd.read_parquet(f'{pre}_{nom}.parquet'); D=pd.read_parquet(f'{pre}_{nom}_diario.parquet'); R[nom]=corre(O,D)
    C,e,q=R[nom]; print(f'K8 + {nom:13s}',C.fmt(q),f'| 24-26 {met24(C,e):.2f}',flush=True)
    for fr in [(3,0.5),(5,0.5)]:
        cfg=dict(comun.FL); cfg['freno']=fr; C2,e2,q2=corre(O,D,cfg); R[(nom,fr)]=(C2,e2,q2); print(f'    freno {fr}',C2.fmt(q2),flush=True)
C0,e0,q0=R['v0']
for nom in ['vol','puntos','vol_o_puntos']:
    C,e,q=R[nom]; informe(C,f'K8: {nom} frente a v0',q,q0,e,e0)
    for fr in [(3,0.5),(5,0.5)]:
        qa=R[('v0',fr)][2]; qb=R[(nom,fr)][2]; print('    freno',fr,'PASA' if all(qb[i]['ratio']>qa[i]['ratio'] for i in range(3)) else '-',flush=True)
C,e,q=R['puntos']; C1,e1,q1=R['vol']; informe(C,'K8: puntos frente a vol',q,q1,e,e1)
