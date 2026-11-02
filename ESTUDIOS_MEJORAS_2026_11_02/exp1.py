from base import *
import time
t=time.time(); r0,e0,q0=run(); print('B0',C.fmt(q0),round(time.time()-t,1),'s',flush=True)
def T(nom,**k):
    r,e,q=run(**k); print(f'{nom:48s}',C.fmt(q),'PASA' if ok(q,q0) else '-',[round(x,2) for x in ultimos(e)],flush=True); return e
# B: otras familias fuera del freno
for fam in ['c10','x_petroleo','corto_petroleo']:
    T(f'{fam} fuera del freno',exentas=EX|((L==fam)&W))
T('oro fuera del freno',exentas=EX|((L=='metales')&(act=='oro')&W))
# A: contra-freno para E1 y Connors con la caída de la cartera (día anterior)
dd=(e0.cummax()-e0).shift(1).fillna(0)
te=pd.to_datetime(O.t_entrada).dt.normalize().values
ddi=dd.reindex(te,method='ffill').fillna(0).values
for X in (2,3,4,6):
    for k in (1.5,2.0):
        tm=np.ones(len(O)); tm[(E1|cn)&(ddi>=X)]=k
        T(f'E1+Connors x{k} con caída >= {X} R',tm=tm)
