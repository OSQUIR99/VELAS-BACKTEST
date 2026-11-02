from base import *
from exp2 import FAM, tm_of
r0,e0,q0=run()
for f in FAM:
    if f=='shy': continue
    for v in (0.5,0.75,1.25,1.5,2.0):
        w={g:1.0 for g in FAM}; w[f]=v; r,e,q=run(tm=tm_of(w))
        if ok(q,q0) or (q[0]['ratio']>q0[0]['ratio']):
            print(f'{f:12s} x{v}',C.fmt(q),'PASA' if ok(q,q0) else '-',[round(x,2) for x in ultimos(e)],flush=True)
