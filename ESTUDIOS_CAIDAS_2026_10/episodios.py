import pickle, numpy as np, pandas as pd
from comun import Cartera, HOY
C=Cartera()
O=C.O; M=C.M
def familia(k):
    l=C.L[k]; a=C.act[k]
    if l=='bolsa_e1': return 'E1 '+a
    if l=='metales': return 'oro'
    if l=='petroleo': return 'petróleo '+('S1' if C.senal[k]=='S1' else ('corto noticia' if O.direccion.values[k]==-1 else 'largo'))
    return {'cripto':'cripto','x_petroleo':'X1/X3','c10':'C10','shy':'SHY','corto_sector':'CORTO SECTOR','corto_indices_credito':'CORTO ÍNDICES'}.get(l,l)
fam=np.array([familia(k) for k in range(len(O))])
for nb in ['a · con S1 (listas originales)','c · sin petróleo']:
    base=C.bases[nb]; rr,eq=C.sim(base)
    e=eq[(eq.index>=C.desde)&(eq.index<=HOY)]
    pk=e.cummax(); dd=e-pk
    # episodios
    eps=[]; i=0; v=dd.values; idx=dd.index
    while i<len(v):
        if v[i]<0:
            j=i
            while j<len(v) and v[j]<0: j+=1
            seg=dd.iloc[i:j]; eps.append((idx[i-1] if i>0 else idx[i], seg.idxmin(), idx[j] if j<len(v) else None, -seg.min())); i=j
        else: i+=1
    eps=sorted(eps,key=lambda x:-x[3])[:8]
    curvas={f:M.curva(rr.s, mascara=(fam==f)) for f in sorted(set(fam[base]))}
    print('\n=====',nb)
    for a,b,c,prof in eps:
        att={f:float(cv[b]-cv[a]) for f,cv in curvas.items()}
        att={f:round(x,1) for f,x in sorted(att.items(), key=lambda z:z[1]) if abs(x)>=0.4}
        print(f'{a.date()} -> {b.date()} ({(b-a).days} d), recupera {c.date() if c is not None else "no"} | caída {prof:.1f} R |', att)
    pickle.dump(dict(eq=eq,s=rr.s,fam=fam,eps=eps), open(f'epis_{nb[0]}.pkl','wb'))
