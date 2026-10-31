from base import *
cfg=dict(freno=(999,1.0),freno_modo='latente',prioridad='descorr')
for nom,c in (('con freno',None),('sin freno',cfg)):
    r0,e0=C.sim(BASE,cfg=c); q0=C.met3(e0); r1,e1=C.sim(BASE|n1,cfg=c); q1=C.met3(e1)
    print(nom,'base',C.fmt(q0)); print(nom,'+N1 ',C.fmt(q1))
# año a año la diferencia con freno
r0,e0=C.sim(BASE); r1,e1=C.sim(BASE|n1)
d=(e1-e0.reindex(e1.index).ffill()); dy=d.resample('YE').last(); dy=dy.diff().fillna(dy)
print('N1 aporta por año (con freno):',{k.year:round(v,1) for k,v in dy[dy.index>=C.desde].items()})
o=O[n1]; print('N1 solo por año:',o.groupby(o.t_entrada.dt.year).r_final.sum().round(1).to_dict())
