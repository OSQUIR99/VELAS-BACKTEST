from base import *
cn=(L=='connors_qqq')&W; me=(L=='mensuales')&W
r0,e0=C.sim(BASE); q0=C.met3(e0); print('BASE (sin N1, sin T1/T2)',C.fmt(q0))
for nom,m in (('Connors en lugar de E1',(BASE&~E1)|cn),('Connors encima de E1',BASE|cn),('solo quitar E1',BASE&~E1)):
    r,e=C.sim(m); q=C.met3(e); ok=all(q[i]['ratio']>q0[i]['ratio'] for i in range(3))
    print(f'{nom:28s}',C.fmt(q),'PASA' if ok else 'no','boot',round(C.bootstrap(e0,e,500),2),flush=True)
cfg=dict(freno=(999,1.0),freno_modo='latente',prioridad='descorr'); r0,e0=C.sim(BASE,cfg=cfg); q0=C.met3(e0)
for nom,m in (('SIN FRENO Connors en lugar de E1',(BASE&~E1)|cn),('SIN FRENO Connors encima',BASE|cn)):
    r,e=C.sim(m,cfg=cfg); q=C.met3(e); print(nom,' / '.join(f"{q[i]['ratio']-q0[i]['ratio']:+.2f}" for i in range(3)))
