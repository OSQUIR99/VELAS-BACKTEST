# Evaluación sobre la base vigente fiel (7,28 / 6,55 / 8,23)
import sys, os, glob, tempfile, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10')
import numpy as np, pandas as pd, comun
GH='/home/claude/velas-backtest/MOTOR/listas'; REC='/home/claude/velas-backtest/MOTOR/listas_reconstruidas'
def cartera(cripto='C_base', extra=()):
    O=pd.read_parquet(f'/home/claude/med/gen/{cripto}.parquet'); D=pd.read_parquet(f'/home/claude/med/gen/{cripto}_diario.parquet')
    tmp=tempfile.mkdtemp(prefix='med_')
    for p in glob.glob(GH+'/*.parquet'):
        b=os.path.basename(p)
        if b.startswith('cripto_realista'): continue
        os.symlink(p,os.path.join(tmp,b))
    O.to_parquet(tmp+'/cripto_realista.parquet'); D.to_parquet(tmp+'/cripto_realista_diario.parquet')
    comun.LISTAS_GH=tmp
    return comun.Cartera(extra=(REC,)+tuple(extra))
def mascaras(C):
    O=C.O; L=C.L; act=C.act; d=(O.t_entrada>=C.desde).values
    W=C.W|(d&np.isin(L,['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq']))
    E1=(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX'])&W
    nucleo=(np.isin(L,['cripto','petroleo','corto_petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
    ex=np.isin(L,['corto_sector','corto_indices_credito'])&W; cn=(L=='yt_connors_qqq')&W
    C.cortos_exentos=ex
    return dict(BASE=nucleo|ex|cn, EX=ex|E1|cn, E1=E1, cn=cn, ex=ex, W=W, d=d)
def k8(C):
    L=C.L; s=C.O['senal'].astype(str).values if 'senal' in C.O.columns else np.array(['']*len(C.O)); t=np.ones(len(L))
    t[L=='corto_petroleo']=2.0; t[(L=='petroleo')&(s=='L2')]=0.5; t[(L=='petroleo')&(s=='tras-noticia (bajada)')]=0.5; t[L=='x_petroleo']=0.75
    return t
def run(C,m,ex,tm=None,cfg=None):
    t=k8(C)*(1 if tm is None else tm); r,e=C.sim(m,exentas=ex,tam_mult=t,cfg=cfg); return e,C.met3(e)
def m24(e): return comun.met_eq(e,pd.Timestamp('2024-01-01'))['ratio']
def ok(q,q0): return all(q[i]['ratio']>q0[i]['ratio'] for i in range(3))
def linea(C,nom,e,q,e0,q0,boot=True):
    b=round(C.bootstrap(e0,e,300),2) if boot else ''
    print(f'{nom:46s}',C.fmt(q),f'| 24-26 {m24(e):.2f}','PASA' if ok(q,q0) else '-','boot',b,flush=True)
