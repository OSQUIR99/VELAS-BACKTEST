import sys, os, shutil, glob
sys.path.insert(0,'/home/claude/m2/MOTOR'); sys.path.insert(0,'/home/claude/vol/code')
import numpy as np, pandas as pd
from recomendacion import preparar
from motor import metricas, ULT5
import analisis as A
from base import px
L='/home/claude/m2/MOTOR/listas'
CORTE=pd.Timestamp('2022-01-01'); CFG=dict(freno=(4,0.5),freno_modo='latente',prioridad='descorr')
X=pd.read_pickle('/home/claude/vol/data/X_vol.pkl'); pct_prev=X.pct.shift(1)   # percentil 3 años de la vol de BTC, día anterior
def lista_modificada(thr, dst):
    os.makedirs(dst,exist_ok=True)
    for p in glob.glob(L+'/*.parquet'):
        q=os.path.join(dst,os.path.basename(p))
        if not os.path.exists(q): os.symlink(p,q)
    O=pd.read_parquet(L+'/cripto_realista.parquet'); Dd=pd.read_parquet(L+'/cripto_realista_diario.parquet')
    dia=pd.to_datetime(O.t_entrada).dt.normalize()
    cond=(pct_prev.reindex(dia).values<=thr)&(O.activo.values!='SOL')&O.parcial.values
    O=O.copy(); Dd=Dd.copy(); n=0
    H={}
    for k in np.flatnonzero(cond):
        o=O.iloc[k]; R=o.entrada-o.sl_inicial
        if o.activo not in H: H[o.activo]=px(o.activo,'4h')
        h=H[o.activo]; seg=h[(h.index>=o.t_entrada)&(h.index<=o.t_salida)]
        tt=seg.index[seg.high>=o.entrada+R]
        if len(tt)==0: continue
        tp=tt[0].normalize()
        O.iat[k,O.columns.get_loc('r_bruto')]=(o.r_bruto-1/3)*1.5
        O.iat[k,O.columns.get_loc('r_final')]=(o.r_bruto-1/3)*1.5*o.tam_R
        m=(Dd.id==o.id)&(pd.to_datetime(Dd.fecha)>=tp)
        Dd.loc[m,'r_latente_unidad']=(Dd.loc[m,'r_latente_unidad']-1/3)*1.5
        Dd.loc[m,'r_latente']=Dd.loc[m,'r_latente_unidad']*o.tam_R
        n+=1
    for f in ['cripto_realista.parquet','cripto_realista_diario.parquet']:
        q=os.path.join(dst,f)
        if os.path.islink(q): os.unlink(q)
    O.to_parquet(dst+'/cripto_realista.parquet'); Dd.to_parquet(dst+'/cripto_realista_diario.parquet')
    return n
SECT={'XLK','SMH','XLC','XLY','XLF','XLI','XLV','XLP','XLU','XLE','XLB','XLRE'}
def correr(carpeta,base_quitar=True):
    O,D,M=preparar(carpeta); desde=A.inicio_ventana(O)
    W=O.en_cartera.values&(O.t_entrada>=desde).values&(O.lista.values!='acciones_v2')
    if base_quitar:
        a=O.activo.astype(str).str.upper().values; l=O.lista.values
        quitar=(l=='mensuales')|((l=='bolsa_e1')&np.isin(a,list(SECT)))|((l=='metales')&np.char.find(a.astype(str),'PLATA')>=0)|((l=='metales')&np.isin(a,['XAG','SILVER','XAGUSD']))
        W2=W&~quitar
        W3=W2&~((l=='bolsa_e1')&np.isin(a,['RUT','IWM']))
    out={}
    for nom,mask in [('4,01 (todo)',W),('5,20 (sin T1/T2, E1 sect., plata)',W2),('5,49 (además sin RUT)',W3)]:
        rr=M.simular(CFG,mascara=mask); eq=rr.eq
        row=[]
        for a,b in [(desde,None),(desde,CORTE),(CORTE,None),(ULT5,None)]:
            m=metricas(M,rr.s,a,b,mascara=mask,eq=eq); row.append((m['R_ano'],m['caida'],m['Rano_caida']))
        out[nom]=row
    return out,O
if __name__=='__main__':
    O,_,_=preparar(L); print(O.groupby('lista').activo.unique().apply(lambda x:list(x)[:15]).to_string())
