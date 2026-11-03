# Propuesta 3 (permiso de índices) y 4 (oro: soporte de la media de 50 semanas) + prueba 2 de sectores (lista)
import sys, os
sys.path.insert(0,'/home/claude/caidas'); sys.path.insert(0,'/home/claude/velas-backtest')
import numpy as np, pandas as pd, nuevas as N
from cortos import diario, rsi_wilder, atr_wilder
from cargar import velas
IDX={'SPX':'sp500','NDX':'nasdaq100','DJI':'dowjones'}
def e1_regen(perm_tipo, tam=0.5):
    OO,DD=[],[]
    for act,nom in IDX.items():
        d=diario(nom); c=d.cierre; m200=c.rolling(200).mean()
        if perm_tipo=='200': perm=(c>m200)&(m200>m200.shift(20))
        elif perm_tipo=='200m': perm=(c>m200*1.009)&(m200>m200.shift(20))
        elif perm_tipo=='20s':
            w=c.resample('W-FRI').last(); m20=w.rolling(20).mean()
            # media de 20 semanas conocida: semanas cerradas (la de la semana en curso no)
            m20d=m20.shift(1).reindex(c.index,method='ffill'); perm=(c>m20d)&(m20d>m20d.shift(20))
        r2=rsi_wilder(c); m5=c.rolling(5).mean().values; C=c.values
        en=(perm&(r2<10)).fillna(False).values
        O,D=N.run(d,en,lambda j,ei,C=C,m5=m5:(j>ei and C[j]>m5[j]) or (j-ei>=10),entrada='close',salida_modo='close',
                  stop_fn=lambda e,a:e-2.5*a,nombre=f'e1r_{perm_tipo}',activo=act,tam=tam,bloque='bolsa_eeuu',desde='1990-01-01')
        O['id']=O.id+'-'+act; D['id']=D.id+'-'+act; OO.append(O); DD.append(D)
    return pd.concat(OO,ignore_index=True),pd.concat(DD,ignore_index=True)
def guardar(O,D,nom):
    car=f'/home/claude/med/l_{nom}'; os.makedirs(car,exist_ok=True); O=O.assign(familia=nom); O.to_parquet(f'{car}/{nom}.parquet'); D.to_parquet(f'{car}/{nom}_diario.parquet')
    t=pd.to_datetime(O.t_entrada); u=O.r_bruto
    print(nom,'ops',len(O),'R/op',round(u.mean(),3),'| 2018-21',round(u[(t>='2018-05')&(t<'2022')].mean(),3),((t>='2018-05')&(t<'2022')).sum(),'| 2022-26',round(u[t>='2022'].mean(),3),(t>='2022').sum(),flush=True)
# ---- prueba 2 sectores: impulso de 12 meses, top 3, salida fuera del top 5, permiso S&P
SEC=['XLK','XLF','XLE','XLV','XLI','XLB','XLP','XLY','XLU','XLRE','XLC']
from cortos import SECTORES
def sectores_lentos(tam=0.5, desfase=0):
    spx=diario('sp500').cierre; m=spx.rolling(200).mean(); permS=(spx>m)&(m>m.shift(20))
    P={s:diario(SECTORES[s],ajustado=True) for s in SEC}
    Pn={s:diario(SECTORES[s]) for s in SEC}
    cl=pd.DataFrame({s:P[s].cierre for s in SEC})
    idx=cl.index; fm=pd.Series(idx,index=idx).groupby(idx.to_period('M')).max().values
    if desfase: fm=np.array([idx[min(len(idx)-1,max(0,idx.get_loc(x)+desfase))] for x in fm])
    ops=[]; dia=[]; abiertas={}
    W={s:Pn[s].resample('W-FRI').agg({'apertura':'first','maximo':'max','minimo':'min','cierre':'last'}).dropna() for s in SEC}
    ATRW={s:atr_wilder(W[s]) for s in SEC}
    for k,f in enumerate(fm):
        if f<pd.Timestamp('1999-06-01'): continue
        ret=(cl.loc[f]/cl.shift(252).loc[f]-1).dropna()
        rank=list(ret.sort_values(ascending=False).index)
        perm=bool(permS.reindex([f]).fillna(False).iloc[0])
        # cerrar
        for s in list(abiertas):
            if (not perm) or (s not in rank[:5]): abiertas[s]['cerrar']=f
        hueco=[s for s in abiertas if 'cerrar' not in abiertas[s]]
        if perm:
            for s in rank:
                if len(hueco)>=3: break
                if s not in hueco: abiertas.setdefault(s,{'abrir':f}); hueco.append(s)
        # ejecutar: cierres y aperturas en la apertura siguiente
        for s,v in list(abiertas.items()):
            d=Pn[s]; ii=d.index.searchsorted(f,side='right')
            if ii>=len(d): continue
            if 'cerrar' in v and 'e' in v:
                v['salida']=d.apertura.iloc[ii]; v['ts']=d.index[ii]; ops.append((s,v)); del abiertas[s]; continue
            if 'cerrar' in v and 'e' not in v: del abiertas[s]; continue
            if 'e' not in v:
                aw=ATRW[s][ATRW[s].index<=f]
                if not len(aw): del abiertas[s]; continue
                v['e']=d.apertura.iloc[ii]; v['te']=d.index[ii]; v['risk']=2.5*aw.iloc[-1]; v['sl']=v['e']-v['risk']
        # stops dentro del mes
        nxt=fm[k+1] if k+1<len(fm) else idx[-1]
        for s,v in list(abiertas.items()):
            if 'e' not in v: continue
            d=Pn[s]; seg=d[(d.index>max(v['te'],f))&(d.index<=nxt)] if v['te']<=f else d[(d.index>=v['te'])&(d.index<=nxt)]
            hit=seg[seg.minimo<=v['sl']]
            if len(hit):
                v['salida']=min(v['sl'],hit.apertura.iloc[0]); v['ts']=hit.index[0]; v['mot']='stop'; ops.append((s,v)); del abiertas[s]
    O=[];D=[]
    for n,(s,v) in enumerate(ops):
        d=Pn[s]; e=v['e']; R=v['risk']; r=(v['salida']-e-0.0002*e)/R; oid=f'sl12m-{s}-{v["te"].strftime("%Y%m%d")}-{n}'
        O.append(dict(id=oid,familia='sectores_lentos',activo=s,direccion=1,t_senal=v['te']-pd.Timedelta(hours=1),t_entrada=v['te']+pd.Timedelta(hours=13.5),
                      t_salida=v['ts']+pd.Timedelta(hours=13.5 if v.get('mot')!='stop' else 17),entrada=e,sl_inicial=e-R,salida=v['salida'],r_bruto=r,tam_R=tam,r_final=r*tam,
                      estrellas=np.nan,mae_R=0.0,mfe_R=0.0,motivo_salida=v.get('mot','regla'),bloque='bolsa_eeuu'))
        seg=d[(d.index>=v['te'])&(d.index<v['ts'])]
        for f2,c2 in seg.cierre.items(): D.append(dict(id=oid,fecha=f2,r_latente=(c2-e)/R*tam))
        D.append(dict(id=oid,fecha=v['ts'],r_latente=r*tam))
    return pd.DataFrame(O),pd.DataFrame(D)
# ---- oro: soporte de la media de 50 semanas
def oro_invalidado():
    w=velas('oro','1w').cierre; w.index=(w.index+pd.Timedelta(hours=6)).normalize()
    m=w.rolling(50).mean(); inval=pd.Series(np.nan,index=w.index)
    inval[w<m*0.972]=1; inval[w>m]=0; inval=inval.ffill().fillna(0)
    return inval  # fecha = lunes de la semana (inicio); se conoce al cierre del viernes
if __name__=='__main__':
    for p in ('200','200m','20s'):
        O,D=e1_regen(p); guardar(O,D,f'e1r_{p}')
    O,D=sectores_lentos(); guardar(O,D,'sectores_lentos')
    for dz in (3,7,11):
        O,D=sectores_lentos(desfase=dz); guardar(O.assign(id=O.id+f'-d{dz}'),D.assign(id=D.id+f'-d{dz}'),f'sectores_lentos_d{dz}')
