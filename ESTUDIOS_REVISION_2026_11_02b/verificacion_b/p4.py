from b import *
FL = dict(freno=(4,0.5), freno_modo='latente', prioridad='descorr')
for piso in (False, True):
  for f in (1.5, 1.0):
    for fr in (4, 3, 5):
        cfg = dict(FL, freno=(fr,0.5))
        res = {}
        for k in EXV:
            q, e, r, _ = montaje(flujo=f, piso=piso, exv=k, cfg=cfg, devolver=True); res[k]=(q,e)
        q0,e0 = res['vigente (ex|E1|cn)']
        print(f'--- piso={piso} BTC x{f} freno {fr}R')
        for k,(q,e) in res.items():
            extra = '' if k.startswith('vigente') else f" | pasa vs vigente: {C.pasa(q,q0)} | boot(vigente->esta) {C.bootstrap(e0,e):.3f}"
            print(f'  {k:28s}', C.fmt(q), extra, flush=True)
