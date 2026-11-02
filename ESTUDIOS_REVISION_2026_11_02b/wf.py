from lab import *
tent=O.t_entrada.values; tsal=O.t_salida.values; rn=(M.rf/np.maximum(M.tam,1e-9))  # R por unidad
def pesos_wf(años=3, minops=8, umbral=0.0, bajo=0.5, alto=None, top=0.5, clave=SUB, modo='media', mask_hist=None):
    w=np.ones(len(O)); yrs=pd.DatetimeIndex(tent).year
    mh=np.ones(len(O),bool) if mask_hist is None else mask_hist
    for y in range(2018,2027):
        t0=np.datetime64(f'{y}-01-01'); tl=np.datetime64(f'{y-años}-01-01')
        hist=mh&(tsal<t0)&(tent>=tl)
        sel=(yrs==y)
        df=pd.DataFrame(dict(k=clave[hist],r=rn[hist]))
        g=df.groupby('k').r.agg(['mean','count','sum'])
        if modo=='ratio':
            pass
        for kk,row in g.iterrows():
            if row['count']<minops: continue
            m=(clave==kk)&sel
            if row['mean']<umbral: w[m]=bajo
            elif alto is not None and row['mean']>=top: w[m]=alto
    return w
if __name__=='__main__':
    s0,e0,dd0=run(); ref=C.met3(e0); print(linea('base vigente',e0))
    for a in [2,3,4]:
        for mn in [5,8,12]:
            for u in [0.0,0.05]:
                w=pesos_wf(a,mn,u); s,e,_=run(tm=w); print(linea(f'WF {a}a min{mn} <{u} ×0,5 (n={int((w<1).sum())})',e,ref),flush=True)
    for a in [3]:
        w=pesos_wf(a,8,0.0,bajo=0.0); s,e,_=run(tm=w); print(linea('WF 3a min8 <0 → fuera',e,ref))
        w=pesos_wf(a,8,0.0,0.5,alto=1.25,top=0.5); s,e,_=run(tm=w); print(linea('WF 3a <0 ×0,5 y ≥0,5 ×1,25',e,ref))
        w=pesos_wf(a,8,0.0,1.0,alto=1.25,top=0.5); s,e,_=run(tm=w); print(linea('WF 3a solo ≥0,5 ×1,25',e,ref))
