from lab import *
te=O.t_entrada.values; ts=O.t_salida.values; rf=M.rf
def enfriar(fam_mask, dias=3, f=0.0, nperd=1, por='activo', solo_motivos=None, ventana=None):
    """tam × f para una entrada si en los `dias` anteriores (por salida) el mismo activo (o la familia) tuvo nperd salidas en pérdida."""
    w=np.ones(len(O)); idx=np.flatnonzero(fam_mask)
    ord_=idx[np.argsort(te[idx])]
    for k in ord_:
        lim=te[k]-np.timedelta64(int(dias*24),'h')
        cand=idx[(ts[idx]<=te[k])&(ts[idx]>lim)&(rf[idx]<0)]
        if por=='activo': cand=cand[act[cand]==act[k]]
        if solo_motivos is not None: cand=cand[np.isin(O.motivo_salida.values[cand],solo_motivos)]
        if len(cand)>=nperd: w[k]=f
    return w
if __name__=='__main__':
    s0,e0,_=run(); ref=C.met3(e0); print(linea('base vigente',e0))
    cr=(L=='cripto')&BASEV
    for d in [1,2,3,5,7]:
        for f in [0.0,0.5]:
            w=enfriar(cr,d,f); s,e,_=run(tm=w); print(linea(f'cripto mismo activo, pérdida <{d}d → ×{f} (n={int((w<1).sum())})',e,ref),flush=True)
    for d in [2,3]:
        for n in [2,3]:
            w=enfriar(cr,d,0.0,nperd=n,por='familia'); s,e,_=run(tm=w); print(linea(f'cripto familia {n} pérdidas <{d}d → fuera (n={int((w<1).sum())})',e,ref),flush=True)
            w=enfriar(cr,d,0.5,nperd=n,por='familia'); s,e,_=run(tm=w); print(linea(f'cripto familia {n} pérdidas <{d}d → ×0,5 (n={int((w<1).sum())})',e,ref),flush=True)
