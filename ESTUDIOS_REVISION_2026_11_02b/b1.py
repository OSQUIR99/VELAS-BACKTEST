from lab import *
s0,e0,dd0=run(); ref=C.met3(e0); print(linea('base vigente',e0))
V={}
V['freno 2 niveles 4R×0,5 / 8R×0,25']=dict(f_freno_fn=lambda d: 0.25 if d>=8 else 0.5 if d>=4 else 1.0)
V['freno 2 niveles 4R×0,5 / 7R×0,25']=dict(f_freno_fn=lambda d: 0.25 if d>=7 else 0.5 if d>=4 else 1.0)
V['freno 2 niveles 3R×0,75 / 5R×0,5']=dict(f_freno_fn=lambda d: 0.5 if d>=5 else 0.75 if d>=3 else 1.0)
V['freno continuo 1-(dd-2)/8 [0,5-1]']=dict(f_freno_fn=lambda d: float(np.clip(1-(d-2)/8,0.5,1)))
V['freno continuo 1-(dd-3)/4 [0,5-1]']=dict(f_freno_fn=lambda d: float(np.clip(1-(d-3)/4,0.5,1)))
V['freno continuo 1-(dd-2)/6 [0,4-1]']=dict(f_freno_fn=lambda d: float(np.clip(1-(d-2)/6,0.4,1)))
cr=(L=='cripto')
V['freno: cripto nota≥2 sin reducir']=dict(freno_op=lambda k,f: 1.0 if (cr[k] and PT[k]>=2) else f)
V['freno: cripto nota≥1 sin reducir']=dict(freno_op=lambda k,f: 1.0 if (cr[k] and PT[k]>=1) else f)
V['freno: cripto nota≥2 ×1, nota≤-1 ×0,25']=dict(freno_op=lambda k,f: 1.0 if (cr[k] and PT[k]>=2) else (0.25 if (cr[k] and PT[k]<=-1) else f))
V['freno: cripto nota≤-1 ×0,25 (resto ×0,5)']=dict(freno_op=lambda k,f: 0.25 if (cr[k] and PT[k]<=-1) else f)
for k,v in V.items():
    s,e,_=run(**v); print(linea(k,e,ref),flush=True)
