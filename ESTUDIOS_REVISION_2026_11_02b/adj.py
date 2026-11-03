from lab import *
s0,e0,_=run(); ref=C.met3(e0); print(linea('base vigente',e0))
for aj in ['raiz','lineal']:
    cfg=dict(comun.FL); cfg['ajuste_corr']=aj
    r,e=C.sim(BASEV,cfg=cfg,exentas=EXV); print(linea(f'ajuste por correlación {aj}',e,ref),flush=True)
for obj in [4,6,8]:
    cfg=dict(comun.FL); cfg['vol_obj']=dict(obj=obj,lim=(0.5,1.0),max=1.0)
    r,e=C.sim(BASEV,cfg=cfg,exentas=EXV); print(linea(f'riesgo abierto objetivo {obj} R (solo reduce)',e,ref),flush=True)
