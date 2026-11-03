import os,sys
from lab import *
k8=np.ones(len(O)); k8[L=='corto_petroleo']=2.0; k8[SUB=='petroleo:L2']=0.5
k8[SUB=='petroleo:tras-noticia (bajada)']=0.5; k8[np.isin(SUB,['x_petroleo:X1','x_petroleo:X3'])]=0.75
te=pd.to_datetime(O.t_entrada.values); ts=pd.to_datetime(O.t_salida.values)
cnm=(L=='yt_connors_qqq')&BASEV; e1n=(L=='bolsa_e1')&(act=='NDX')&BASEV
ic=np.flatnonzero(cnm); ie=np.flatnonzero(e1n)
# Connors que entra con una E1 NDX abierta (o que entra el mismo día)
c_con_e1=np.zeros(len(O),bool); e1_con_c=np.zeros(len(O),bool)
for i in ic:
    if ((te[ie]<=te[i])&(ts[ie]>te[i])).any(): c_con_e1[i]=True
for j in ie:
    if ((te[ic]<=te[j])&(ts[ic]>te[j])).any(): e1_con_c[j]=True
print('Connors con E1 NDX abierta:',c_con_e1.sum(),'de',cnm.sum(),'| E1 NDX con Connors abierta:',e1_con_c.sum(),'de',e1n.sum(),flush=True)
def ep(e): return ' · '.join(f"{met_eq(e,pd.Timestamp(a),pd.Timestamp(b))['ratio']:.2f}" for a,b in [('2018-01-01','2020-01-01'),('2020-01-01','2022-01-01'),('2022-01-01','2024-01-01'),('2024-01-01','2026-10-21')])
s,e0,_=run(tm=k8); r0=C.met3(e0); print(linea('A vigente (las dos)',e0),'| ép',ep(e0),flush=True)
V={'B Connors no abre si hay E1 NDX abierta':(BASEV&~c_con_e1,k8),
   'C E1 NDX no abre si hay Connors abierta':(BASEV&~e1_con_c,k8),
   'D Connors a ×0,5 si hay E1 NDX abierta':(BASEV,k8*np.where(c_con_e1,0.5,1.0)),
   'E E1 NDX a ×0,5 si hay Connors abierta':(BASEV,k8*np.where(e1_con_c,0.5,1.0))}
for k,(m,t) in V.items():
    s,e,_=run(mask=m,tm=t); print(linea(k,e,r0),'| ép',ep(e),'| boot',round(C.bootstrap(e0,e,1000),2),flush=True)
