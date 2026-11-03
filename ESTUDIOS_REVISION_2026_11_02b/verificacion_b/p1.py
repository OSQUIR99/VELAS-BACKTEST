from b import *
import json
print('chequeo base vigente vol10 sin fiel:', C.fmt(C.met3(C.sim(C.mask, exentas=C.exentas)[1])))
print('  + K8:', C.fmt(C.met3(C.sim(C.mask, exentas=C.exentas, tam_mult=k8())[1])))
km = k8(); print('K8 ops tocadas en máscara:', {f'{l}/{s}':int(n) for (l,s),n in pd.Series(1,index=pd.MultiIndex.from_arrays([L[(km!=1)&C.mask], sen[(km!=1)&C.mask]])).groupby(level=[0,1]).sum().items()}, ' fuera de máscara tocadas:', int(((km!=1)&~C.mask).sum()))
tmF,_ = fiel.factores(O, C.cri); print('fiel con piso (fiel.py) sin K8:', C.fmt(C.met3(C.sim(C.mask, exentas=C.exentas, tam_mult=tmF)[1])))
for K in (False, True):
  for p in (True, False):
    q, eq, rr, inf = montaje(K8=K, piso=p, devolver=True)
    print(f'fiel K8={K} piso={p}:', C.fmt(q), inf)
