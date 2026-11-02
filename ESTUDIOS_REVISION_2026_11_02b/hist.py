from lab import *
class Hyst:
    def __init__(s,on=4,off=0,f=0.5): s.on,s.off,s.f,s.act=on,off,f,False
    def __call__(s,d):
        if not s.act and d>=s.on: s.act=True
        elif s.act and d<=s.off: s.act=False
        return s.f if s.act else 1.0
s0,e0,_=run(); ref=C.met3(e0); print(linea('base vigente (freno se suelta con caída < 4 R)',e0))
for on,off in [(4,0),(4,1),(4,2),(4,3),(3,1),(3,2),(5,2),(5,3)]:
    s,e,_=run(f_freno_fn=Hyst(on,off)); print(linea(f'freno histéresis: entra {on} R, sale {off} R',e,ref),flush=True)
