# Harness de mejoras (2-nov-2026): base vigente = sin tercio (vol BTC ≤ 0,10) + E1 y Connors fuera del freno
import sys, os, glob, tempfile, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10'); sys.path.insert(0,'/home/claude/vol/code')
import numpy as np, pandas as pd, comun
from base import px
GH='/home/claude/velas-backtest/MOTOR/listas'; REC='/home/claude/velas-backtest/MOTOR/listas_reconstruidas'
X=pd.read_pickle('/home/claude/vol/data/X_vol.pkl'); PCT=X.pct.shift(1)
O0=pd.read_parquet(GH+'/cripto_realista.parquet'); D0=pd.read_parquet(GH+'/cripto_realista_diario.parquet')
_H={}
def h4(a):
    if a not in _H: _H[a]=px(a,'4h')
    return _H[a]
def sin_tercio(O,D,cond):
    O=O.copy(); D=D.copy(); n=0
    dia=pd.to_datetime(O.t_entrada).dt.normalize()
    for k in np.flatnonzero(cond & (O.activo.values!='SOL') & O.parcial.values.astype(bool)):
        o=O.iloc[k]; R=o.entrada-o.sl_inicial; h=h4(o.activo); seg=h[(h.index>=o.t_entrada)&(h.index<=o.t_salida)]
        tt=seg.index[seg.high>=o.entrada+R]
        if len(tt)==0: continue
        tp=tt[0].normalize()
        O.iat[k,O.columns.get_loc('r_bruto')]=(o.r_bruto-1/3)*1.5
        O.iat[k,O.columns.get_loc('r_final')]=(o.r_bruto-1/3)*1.5*o.tam_R
        m=(D.id==o.id)&(pd.to_datetime(D.fecha)>=tp)
        D.loc[m,'r_latente_unidad']=(D.loc[m,'r_latente_unidad']-1/3)*1.5
        D.loc[m,'r_latente']=D.loc[m,'r_latente_unidad']*o.tam_R; n+=1
    return O,D,n
def cond_base(O):
    dia=pd.to_datetime(O.t_entrada).dt.normalize()
    return PCT.reindex(dia).values<=0.10
def cartera(O,D):
    tmp=tempfile.mkdtemp(prefix='mej_')
    for p in glob.glob(GH+'/*.parquet'):
        b=os.path.basename(p)
        if b.startswith('cripto_realista'): continue
        os.symlink(p,os.path.join(tmp,b))
    O.to_parquet(tmp+'/cripto_realista.parquet'); D.to_parquet(tmp+'/cripto_realista_diario.parquet')
    comun.LISTAS_GH=tmp
    return comun.Cartera(extra=(REC,))
def mascaras(C):
    O=C.O; L=C.L; act=C.act; d=(O.t_entrada>=C.desde).values
    W=C.W|(d&np.isin(L,['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq']))
    E1=(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX'])&W
    nucleo=(np.isin(L,['cripto','petroleo','corto_petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
    ex=np.isin(L,['corto_sector','corto_indices_credito'])&W; cn=(L=='yt_connors_qqq')&W
    C.cortos_exentos=ex
    return dict(BASE=nucleo|ex|cn, EX=ex|E1|cn, E1=E1, cn=cn, ex=ex, W=W)
def evalua(C,m,ex,tm=None,cfg=None):
    r,e=C.sim(m,exentas=ex,tam_mult=tm,cfg=cfg); return r,e,C.met3(e)
def met24(C,e):
    return comun.met_eq(e,pd.Timestamp('2024-01-01'))['ratio']
def informe(C,nom,q,q0,e,e0):
    ok=all(q[i]['ratio']>q0[i]['ratio'] for i in range(3))
    print(f'{nom:52s}',C.fmt(q),f'| 24-26 {met24(C,e):.2f}','PASA' if ok else '-','boot',round(C.bootstrap(e0,e,300),2),flush=True)
    return ok
def base_nueva():
    O,D,n=sin_tercio(O0,D0,cond_base(O0)); C=cartera(O,D); M=mascaras(C); r,e,q=evalua(C,M['BASE'],M['EX']); return C,M,r,e,q
