from base import *
from sim2 import simular2
import comun
M=C.M; O=C.O
CFG=dict(comun.FL); CFG['tam_mult']=C.tam_base
def run(mask=BASEV, exv=EXV, tm=None, **kw):
    cfg=dict(CFG); 
    if tm is not None: cfg['tam_mult']=C.tam_base*tm
    sf=M.sin_freno.copy(); M.sin_freno=sf|exv
    try: s,mot,dd=simular2(M,cfg,mask,**kw)
    finally: M.sin_freno=sf
    return s, M.curva(s), dd
def q3(e):
    q=C.met3(e); q2=[met_eq(e,pd.Timestamp(a)) for a in ['2024-01-01','2025-01-01']]
    return q,q2
def linea(nom,e,ref=None):
    q,q2=q3(e); ok=''
    if ref is not None: ok=' PASA' if C.pasa(q,ref) else ''
    return f"{nom:46s} {C.fmt(q)} | 24-26 {q2[0]['ratio']:.2f} 25-26 {q2[1]['ratio']:.2f}{ok}"
L=C.L; act=C.act; sen=C.senal
SUB=np.where(L=='cripto','cripto:'+act, np.where(np.isin(L,['metales','petroleo','x_petroleo','corto_petroleo']), L+':'+sen, np.where(L=='bolsa_e1','e1:'+act, L)))
PT=O.puntos.values if 'puntos' in O else np.full(len(O),np.nan)
