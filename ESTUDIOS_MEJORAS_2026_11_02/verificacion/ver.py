# Verificador independiente: monta su propia carpeta, máscara, tam_base y multiplicadores.
import sys, os, glob, tempfile, time, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/velas-backtest/MOTOR')
import numpy as np, pandas as pd
import recomendacion as RC, analisis as A
G='/home/claude/velas-backtest/MOTOR/listas'; R='/home/claude/velas-backtest/MOTOR/listas_reconstruidas'
HOY=pd.Timestamp('2026-10-20'); CORTE=pd.Timestamp('2022-01-01')
def montar(tercio=True):
    tmp=tempfile.mkdtemp(prefix='ver_')
    for p in glob.glob(G+'/*.parquet'):
        b=os.path.basename(p)
        if tercio and b.startswith('cripto_realista'):
            continue
        os.symlink(p,os.path.join(tmp,b))
    if tercio:
        os.symlink(R+'/referencia/cripto_realista_sin_tercio_vol10.parquet',tmp+'/cripto_realista.parquet')
        os.symlink(R+'/referencia/cripto_realista_sin_tercio_vol10_diario.parquet',tmp+'/cripto_realista_diario.parquet')
    for n in ('corto_indices_credito','yt_connors_qqq','n1_vixvxv'):   # corto_sector: se queda la de MOTOR/listas (como el análisis)
        for suf in ('','_diario'): os.symlink(f'{R}/{n}{suf}.parquet',f'{tmp}/{n}{suf}.parquet')
    return tmp
class V:
    def __init__(s,tercio=True):
        s.tmp=montar(tercio); O,D,M=RC.preparar(s.tmp); s.O,s.D,s.M=O,D,M
        assert O.id.is_unique, 'ids repetidos'
        L=O.lista.values; act=O.activo.astype(str).values; s.L,s.act=L,act
        s.sen=O.senal.astype(str).values
        s.desde=A.inicio_ventana(O)
        t=(O.t_entrada>=s.desde).values
        enc=O.en_cartera.values
        fam_enc=np.isin(L,['cripto','petroleo','x_petroleo','c10','shy'])|((L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX']))|((L=='metales')&(act=='oro'))
        fam_libre=np.isin(L,['corto_petroleo','corto_sector','corto_indices_credito','yt_connors_qqq'])
        s.base=t&((fam_enc&enc)|fam_libre)
        s.exentas=t&(np.isin(L,['corto_sector','corto_indices_credito','yt_connors_qqq'])|((L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX'])))
        # tam_base: SHY a 3.333 $ (1 R = 301 $), cortos de bolsa x2
        tb=np.ones(len(O)); shy=L=='shy'
        dist=((O.entrada-O.sl_inicial)/O.entrada).values+(O['hueco'].fillna(0).values if 'hueco' in O.columns else 0)
        tb[shy]=np.minimum(1.0,(3333.0*dist/301.0)[shy]/O.tam_R.values[shy])
        tb[np.isin(L,['corto_sector','corto_indices_credito'])]=2.0
        s.tb=tb
    def mult(s,corto_pet=1,petroleo=1,x_pet=1,pet_no_L1=None,extra=None):
        m=np.ones(len(s.O)); L=s.L
        m[L=='corto_petroleo']=corto_pet; m[L=='petroleo']=petroleo; m[L=='x_petroleo']=x_pet
        if pet_no_L1 is not None: m[(L=='petroleo')&(s.sen!='L1')]=pet_no_L1
        if extra is not None: m=m*extra
        return m
    def sim(s,tm=None,freno=(4,0.5),mask=None):
        cfg=dict(freno=freno,freno_modo='latente',prioridad='descorr')
        cfg['tam_mult']=(tm if tm is not None else 1.0)*s.tb
        sf=s.M.sin_freno.copy(); s.M.sin_freno=sf|s.exentas
        try:
            rr=s.M.simular(cfg,mascara=s.base if mask is None else mask); eq=s.M.curva(rr.s)
        finally: s.M.sin_freno=sf
        return rr,eq
def dd(e):
    v=e.values; return float((np.maximum.accumulate(v)-v).max())
def met(eq,a,b=None):
    e=eq[(eq.index>=a)&((eq.index<b) if b is not None else (eq.index<=HOY))]
    e=e-e.iloc[0]; y=(e.index[-1]-e.index[0]).days/365.25; d=dd(e); ra=e.iloc[-1]/y
    return ra,d,ra/d
def tres(eq,desde):
    return [met(eq,desde),met(eq,desde,CORTE),met(eq,CORTE)]
def fmt(q): return ' / '.join(f'{x[2]:.2f}' for x in q)+f' | R/año {q[0][0]:.1f} ({q[1][0]:.1f}/{q[2][0]:.1f}) | caída {q[0][1]:.1f} ({q[1][1]:.1f}/{q[2][1]:.1f})'
def episodios(eq,desde):
    e=eq[(eq.index>=desde)&(eq.index<=HOY)].values; pk=np.maximum.accumulate(e); d=pk-e
    res=[];i=0
    while i<len(e):
        if d[i]>0:
            j=i
            while j<len(e) and d[j]>0: j+=1
            res.append(d[i:j].max()); i=j
        else: i+=1
    return sorted(res,reverse=True)
def anual(eq,desde):
    out={}
    for y in range(desde.year,2027):
        a=max(desde,pd.Timestamp(f'{y}-01-01')); b=pd.Timestamp(f'{y+1}-01-01')
        e=eq[(eq.index>=a-pd.Timedelta(days=1))&(eq.index<b)&(eq.index<=HOY)]
        out[y]=(round(e.iloc[-1]-e.iloc[0],1), round(dd(e-e.iloc[0]),1))
    return out
