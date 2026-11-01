import sys, os, glob, tempfile
sys.path.insert(0,'/home/claude/m3/gh/MOTOR'); sys.path.insert(0,'/home/claude/vol/code')
import numpy as np, pandas as pd
import recomendacion as RC, analisis as A
from base import px
GH='/home/claude/m3/gh/MOTOR'
CORTE=pd.Timestamp('2022-01-01'); HOY=pd.Timestamp('2026-10-20')
FL=dict(freno=(4,0.5),freno_modo='latente',prioridad='descorr'); IDX=['SPX','DJI','NDX']
def carpeta(cripto_dir=None):
    tmp=tempfile.mkdtemp(prefix='exacta_')
    for p in glob.glob(GH+'/listas/*.parquet'):
        b=os.path.basename(p)
        if b.startswith('petroleo_con_s1'): continue
        if cripto_dir and b.startswith('cripto_realista'): continue
        os.symlink(p,os.path.join(tmp,b))
    for b in ['corto_indices_credito.parquet','corto_indices_credito_diario.parquet']:
        os.symlink(GH+'/listas_reconstruidas/'+b,os.path.join(tmp,b))
    if cripto_dir:
        for b in ['cripto_realista.parquet','cripto_realista_diario.parquet']: os.symlink(os.path.join(cripto_dir,b),os.path.join(tmp,b))
    return tmp
def met_eq(eq,a,b=None):
    e=eq[(eq.index>=a)&((eq.index<b) if b is not None else (eq.index<=HOY+pd.Timedelta(days=1)))]; e=e-e.iloc[0]
    yrs=(e.index[-1]-e.index[0]).days/365.25; dd=float((e.cummax()-e).max()); ra=float(e.iloc[-1]/yrs)
    return dict(R_ano=ra,caida=dd,ratio=ra/dd)
def medir(car):
    O,D,M=RC.preparar(car); L=O.lista.values; act=O.activo.astype(str).values
    desde=A.inicio_ventana(O)
    W=O.en_cartera.values&(O.t_entrada>=desde).values&(L!='acciones_v2')
    E1=(L=='bolsa_e1')&np.isin(act,IDX)
    ent=(O.t_entrada>=desde).values
    base=(np.isin(L,['cripto','petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
    cp=(L=='corto_petroleo')&ent
    ex=((L=='corto_sector')|(L=='corto_indices_credito'))&ent
    mask=base|cp|ex
    tb=np.ones(len(O)); shy=L=='shy'
    dist=((O.entrada-O.sl_inicial)/O.entrada).values+(O['hueco'].fillna(0).values if 'hueco' in O.columns else 0)
    tb[shy]=np.minimum(1.0,(3333.0*dist/301.0)[shy]/O.tam_R.values[shy]); tb[ex]=2.0
    c=dict(FL); c['tam_mult']=tb
    sf=M.sin_freno.copy(); M.sin_freno=sf|ex
    rr=M.simular(c,mascara=mask); eq=M.curva(rr.s); M.sin_freno=sf
    return [met_eq(eq,desde),met_eq(eq,desde,CORTE),met_eq(eq,CORTE)], {l:int((mask&(L==l)).sum()) for l in np.unique(L[mask])}
def fmt(q): return ' / '.join(f"{x['ratio']:.2f}" for x in q)+f" | R/año {q[0]['R_ano']:.1f} ({q[1]['R_ano']:.1f}/{q[2]['R_ano']:.1f}) | caída {q[0]['caida']:.1f} ({q[1]['caida']:.1f}/{q[2]['caida']:.1f})"
if __name__=='__main__':
    q,n=medir(carpeta()); print('BASE',fmt(q),n,flush=True)
    sys.path.insert(0,'/home/claude/m2/run')
    for thr in [0.075,0.10,0.125]:
        d=f'/home/claude/m2/listas_{thr}'
        q,_=medir(carpeta(d)); print(f'SIN TERCIO ≤{thr}',fmt(q),flush=True)
