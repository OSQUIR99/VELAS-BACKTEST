import numpy as np, pandas as pd
from comun import Cartera, HOY
from b21 import serie_b21, afectadas
C=Cartera(); O=C.O; M=C.M; L=C.L
base=C.bases['a · con S1 (listas originales)']
b21=serie_b21()
# 1) solape B21 con cortos abiertos
rb,eqb=C.sim(base)
d=pd.date_range(C.desde,HOY,freq='D')
abierto=pd.Series(False,index=d)
for k in np.flatnonzero((rb.s>0)&C.cortos_exentos):
    abierto[(d>=O.t_entrada.iloc[k].normalize())&(d<=O.t_salida.iloc[k].normalize())]=True
on=b21.reindex(d).fillna(False)
print('Días con algún corto abierto:', int(abierto.sum()), '| de ellos con B21 encendido:', f'{(on[abierto]).mean()*100:.0f} %', '| B21 encendido en general:', f'{on.mean()*100:.0f} %')
# 2) B21 por años (diferencia de R)
largo=O.direccion.values==1
resto=largo&~np.isin(L,['cripto','shy','corto_sector','corto_indices_credito'])
af=afectadas(C,b21,resto&base)
r2,eq2=C.sim(base,tam_mult=np.where(af,0.5,1.0))
dy=(eq2-eqb).resample('YE').last(); dy=dy.diff().fillna(dy)
print('B21 frente a la base, por año (R):', {k.year: round(v,1) for k,v in dy[(dy.index>=C.desde)&(dy.index<=HOY+pd.Timedelta(days=80))].items()})
# 3) estado actual de la caída en el backtest
e=eqb[(eqb.index>=C.desde)&(eqb.index<=HOY)]
print('Caída de la cartera del backtest a', e.index[-1].date(), ':', round(float(e.iloc[-1]-e.max()),1), 'R desde el máximo del', e.idxmax().date())
# 4) escalado de la base a −15,3 R
for nb,m in C.bases.items():
    lo,hi=0.5,3.0
    for _ in range(12):
        mid=(lo+hi)/2; r,eq=C.sim(m,mult=mid); q=C.met3(eq)
        lo,hi=(mid,hi) if q[0]['caida']<=15.3 else (lo,mid)
    r,eq=C.sim(m,mult=lo); q=C.met3(eq); print('escalada a −15,3 R', nb, round(lo,2), round(q[0]['R_ano'],1))
# 5) E1 sola en la cartera: peores tramos
fam_e1=C.e1
c1=M.curva(rb.s,mascara=fam_e1); e1=c1[(c1.index>=C.desde)&(c1.index<=HOY)]
dd=e1-e1.cummax(); print('E1 en la cartera: R por año', {y: round(float(g.iloc[-1]-g.iloc[0]),1) for y,g in e1.groupby(e1.index.year)})
