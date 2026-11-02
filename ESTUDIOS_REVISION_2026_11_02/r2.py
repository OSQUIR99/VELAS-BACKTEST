from base2 import *
import warnings; warnings.filterwarnings('ignore')
FL=dict(comun.FL)
def run(m,ex_,cfg=None,tm=None):
    r,e=C.sim(m,cfg=cfg,exentas=ex_,tam_mult=tm); return e,C.met3(e)
for fr in [(3,0.5),(4,0.5),(5,0.5),(4,0.25),(4,0.75)]:
    cfg=dict(FL); cfg['freno']=fr
    e0,q0=run(BASE,ex,cfg); e1,q1=run(BASE|cn,ex|E1|cn,cfg); e2,q2=run(BASE,ex|E1,cfg)
    ok=lambda q:'PASA' if all(q[i]['ratio']>q0[i]['ratio'] for i in range(3)) else '-'
    print('freno',fr,'| base',C.fmt(q0)[:18],'| E1+Connors fuera',C.fmt(q1)[:18],ok(q1),'| E1 fuera',C.fmt(q2)[:18],ok(q2),flush=True)
# en las otras versiones del petróleo
pet=(L=='petroleo')&W
for nom,b in [('sin petróleo',BASE&~pet)]:
    e0,q0=run(b,ex); e1,q1=run(b|cn,ex|E1|cn); print(nom,C.fmt(q0)[:18],'->',C.fmt(q1)[:18])
# solo bolsa EE. UU. fuera: E1, Connors, N1
e0,q0=run(BASE,ex); e1,q1=run(BASE|cn|n1,ex|E1|cn|n1); print('E1+Connors+N1 fuera',C.fmt(q1), all(q1[i]['ratio']>q0[i]['ratio'] for i in range(3)))
# placebo: sacar del freno otra familia del mismo tamaño
for F in ['petroleo','metales','c10','x_petroleo']:
    m=(L==F)&BASE; e1,q1=run(BASE,ex|m); print('placebo fuera del freno:',F,C.fmt(q1)[:18])
