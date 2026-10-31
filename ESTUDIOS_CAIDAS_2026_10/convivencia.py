import numpy as np, pandas as pd
from comun import Cartera, HOY, CORTE
C=Cartera(); O=C.O; M=C.M
def familia(k):
    l=C.L[k]
    if l=='bolsa_e1': return 'E1 índices'
    if l=='metales': return 'oro'
    if l=='petroleo':
        if C.senal[k]=='S1': return 'petróleo S1'
        return 'petróleo corto noticia' if O.direccion.values[k]==-1 else 'petróleo largo'
    return {'cripto':'cripto REBOTE 4H','x_petroleo':'X1/X3','c10':'C10','shy':'SHY','corto_sector':'CORTO SECTOR','corto_indices_credito':'CORTO ÍNDICES'}.get(l,l)
fam=np.array([familia(k) for k in range(len(O))])
base=C.bases['a · con S1 (listas originales)']
rr,eq=C.sim(base); qb=C.met3(eq); print('BASE', C.fmt(qb))
anos=(HOY-C.desde).days/365.25
mb=C.mensual(eq)
cri=C.mensual(M.curva(rr.s, mascara=(fam=='cripto REBOTE 4H')))
filas=[]
for f in sorted(set(fam[base])):
    cf=M.curva(rr.s, mascara=(fam==f)); mf=C.mensual(cf)
    contrib=float(cf[HOY]-cf[C.desde])/anos
    r2,e2=C.sim(base & (fam!=f)); q=C.met3(e2)
    filas.append(dict(familia=f, contrib_R_ano=contrib, corr_con_cripto=float(np.corrcoef(mf.reindex(cri.index).fillna(0),cri)[0,1]) if f!='cripto REBOTE 4H' else 1.0,
                      ratio_sin_ella=q[0]['ratio'], IS=q[1]['ratio'], OOS=q[2]['ratio'], Ra_sin=q[0]['R_ano'], caida_sin=q[0]['caida']))
T=pd.DataFrame(filas).sort_values('contrib_R_ano',ascending=False)
pd.set_option('display.width',200)
print(T.round(2).to_string(index=False))
# E1: diciembre de 2024 y caídas propias de E1 en la base actual
e1=M.curva(rr.s, mascara=(fam=='E1 índices'))
print('\nE1 índices en dic-2024 (3 al 19):', round(float(e1[pd.Timestamp('2024-12-19')]-e1[pd.Timestamp('2024-12-03')]),2),'R')
e=e1[(e1.index>=C.desde)&(e1.index<=HOY)]; dd=e-e.cummax()
print('E1 sola dentro de la cartera: peor caída', round(-dd.min(),1),'R el',dd.idxmin().date(), '| R/año', round(float(e.iloc[-1]-e.iloc[0])/anos,2))
# mismas fechas con E1 de sectores y Russell (lo que se quitó el 25-26 oct)
quit=(C.L=='bolsa_e1')&~np.isin(C.act,['SPX','NDX','DJI'])&C.W
r3,e3=C.sim(base|quit); q3=C.met3(e3)
cq=M.curva(r3.s, mascara=quit)
print('Si siguieran E1 sectores+Russell:', C.fmt(q3), '| dic-2024 de esas:', round(float(cq[pd.Timestamp('2024-12-19')]-cq[pd.Timestamp('2024-12-03')]),1),'R')
