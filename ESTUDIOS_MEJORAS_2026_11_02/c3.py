from h import *
C,M,r0,e0,q0=base_nueva(); print('BASE',C.fmt(q0),f'| 24-26 {met24(C,e0):.2f}',flush=True)
O=C.O; L=C.L; act=C.act; B=M['BASE']; EX=M['EX']
fam=np.where(L=='bolsa_e1','e1',np.where(L=='metales',act,L)).astype(str)
te=pd.to_datetime(O.t_entrada); ts=pd.to_datetime(O.t_salida); rf=O.r_final.values
# --- B: pesos por familia sin mirar al futuro (solo operaciones cerradas antes de la entrada)
mes=ts.dt.to_period('M')
def pesos(tipo,ventana=24,lo=0.5,hi=1.5):
    w=np.ones(len(O)); idx_ok=np.where(B)[0]
    tab=pd.DataFrame({'f':fam[B],'m':mes[B].values,'r':rf[B]}).groupby(['f','m']).r.sum().unstack(0).fillna(0)
    tab.index=tab.index.to_timestamp(); tab=tab.reindex(pd.date_range(tab.index.min(),tab.index.max(),freq='MS')).fillna(0)
    if tipo=='invvol': s=tab.rolling(ventana,min_periods=12).std()
    sc=None
    if tipo=='invvol':
        inv=1/s.replace(0,np.nan); sc=inv.div(inv.mean(axis=1),axis=0)
    elif tipo=='sharpe':
        mu=tab.rolling(ventana,min_periods=12).mean(); sd=tab.rolling(ventana,min_periods=12).std(); sh=(mu/sd).clip(lower=0)
        sc=sh.div(sh.mean(axis=1),axis=0)
    elif tipo=='ratio_exp':
        cc=tab.cumsum(); dd=(cc.cummax()-cc).cummax().replace(0,np.nan); n=np.arange(1,len(tab)+1)[:,None]
        rr=(cc/n)/dd; rr=rr.clip(lower=0); sc=rr.div(rr.mean(axis=1),axis=0)
    sc=sc.shift(1)   # mes anterior cerrado
    for i in idx_ok:
        k=te.iloc[i].to_period('M').to_timestamp()
        if k in sc.index and fam[i] in sc.columns:
            v=sc.at[k,fam[i]]
            if np.isfinite(v): w[i]=min(hi,max(lo,v))
    return w

res=[]
for v in [24,36,48,60]:
    for lo,hi in [(0.75,1.25),(0.8,1.2),(0.9,1.1),(1.0,1.25),(0.75,1.0)]:
        _,e,q=evalua(C,B,EX,tm=pesos('sharpe',v,lo,hi)); informe(C,f'sharpe {v}m [{lo},{hi}]',q,q0,e,e0)
