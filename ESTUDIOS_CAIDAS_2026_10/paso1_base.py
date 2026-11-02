import time, pickle
from comun import *
t=time.time()
C=Cartera()
print('cargado',round(time.time()-t,1),'s; desde',C.desde.date(), '| ops cortos en ventana', int(C.c_sector.sum()), int(C.c_indices.sum()), '| en_cartera cortos', bool(C.O.en_cartera.values[C.c_sector].all()))
# 1) base 5,49 (sin cortos)
rr,eq=C.sim(C.base549, exentas=np.zeros(len(C.O),bool)); q=C.met3(eq); print('BASE 5,49 (reproducción)   ', C.fmt(q))
ref=q
# 2) base + cortos en las tres versiones del petróleo
res={}
for n,m in C.bases.items():
    rr,eq=C.sim(m); q=C.met3(eq); m5,top=C.media5(eq)
    res[n]=(rr,eq,q)
    print(f'{n:32s}', C.fmt(q), '| media 5 peores', round(m5,1), [round(x,1) for x in top])
# 3) sin cortos, sin S1 y sin petróleo (para ver cuánto aportan los cortos)
for n,m in (('sin cortos, sin S1',C.base549&~C.s1),('sin cortos, sin petróleo',C.base549&~C.pet)):
    rr,eq=C.sim(m, exentas=np.zeros(len(C.O),bool)); print(f'{n:32s}', C.fmt(C.met3(eq)))
pickle.dump({k:(v[1]) for k,v in res.items()}, open('eq_bases.pkl','wb'))
print('tiempo', round(time.time()-t,1))
