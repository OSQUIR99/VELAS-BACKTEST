from b import *
km=k8(); pet=np.isin(L,['petroleo','corto_petroleo','x_petroleo'])&C.mask
nt = O.tam_R.values*km
print('petróleo tam_R tras K8: min', nt[pet].min(), ' ops <0.25:', int((pet&(nt<0.25-1e-9)).sum()), ' min sin K8', O.tam_R.values[pet].min())
tm = tam_cripto(); new = O.tam_R.values*tm
for eps in (1e-9, 1e-6, 1e-3):
    print('eps',eps,'bajo',int((C.cri&C.mask&(new<0.25-eps)).sum()), 'exactos 0.25', int((C.cri&C.mask&np.isclose(new,0.25)).sum()))
b = C.cri & C.mask & (new<0.25-1e-9)
print('bajo por activo', pd.Series(act[b]).value_counts().to_dict())
print('cripto en máscara', int((C.cri&C.mask).sum()))
q0, e0, r0, _ = montaje(devolver=True)
for f in (1.0, 1.25, 1.5, 1.75, 2.0):
    q, e, r, inf = montaje(flujo=f, devolver=True)
    print(f'BTC sn x{f}:', C.fmt(q), inf, 'pasa' if C.pasa(q,q0) else 'no pasa', ' boot', C.bootstrap(e0,e) if f!=1 else '')
