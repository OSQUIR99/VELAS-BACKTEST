import sys, os, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','ESTUDIOS_CAIDAS_2026_10')); import comun
from comun import Cartera, met_eq
AQ=os.path.dirname(os.path.abspath(__file__))
C=Cartera(extra=(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','MOTOR','listas_reconstruidas'),os.path.join(AQ,'listas_mom'),os.path.join(AQ,'listas_u40'),os.path.join(AQ,'listas_u75'),os.path.join(AQ,'listas_u100')))
O=C.O; L=C.L; act=C.act; d=(O.t_entrada>=C.desde).values
NUEVAS=['sp_manana','sp_manana_u40','sp_manana_u75','sp_manana_u100']
W=C.W|(d&np.isin(L,['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq']+NUEVAS))
E1=(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX'])&W
nucleo=(np.isin(L,['cripto','petroleo','corto_petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
ex=np.isin(L,['corto_sector','corto_indices_credito'])&W; C.cortos_exentos=ex
cn=(L=='yt_connors_qqq')&W; BASE=nucleo|ex|cn; EX=ex|E1|cn
sen=C.senal; k8=np.ones(len(O)); k8[L=='corto_petroleo']=2.0; k8[(L=='petroleo')&(sen=='L2')]=0.5
k8[(L=='petroleo')&(sen=='tras-noticia (bajada)')]=0.5; k8[L=='x_petroleo']=0.75
def run(m,tm,cfg=None):
    r,e=C.sim(m,exentas=EX,tam_mult=tm,cfg=cfg); return e,C.met3(e)
e0,q0=run(BASE,k8); print(f"{'base':45s}",C.fmt(q0),flush=True)
mom=(L=='sp_manana')&W
for t in [0.4,0.6]:
    tm=k8.copy(); tm[mom]=t; e,q=run(BASE|mom,tm); print(f"{f'umbral 0,5 % a {t} R':45s}",C.fmt(q),'PASA' if C.pasa(q,q0) else '',flush=True)
for n in ['sp_manana_u40','sp_manana_u75','sp_manana_u100']:
    mm=(L==n)&W; tm=k8.copy(); tm[mm]=0.5; e,q=run(BASE|mm,tm); print(f"{n+' a 0,5 R':45s}",C.fmt(q),'PASA' if C.pasa(q,q0) else '',flush=True)
tm=k8.copy(); tm[mom]=0.5; e1,q1=run(BASE|mom,tm)
print('remuestreo por meses (gana a la base):',round(C.bootstrap(e0,e1,1000),2))
for fr in [(3,0.5),(5,0.5)]:
    cfg=dict(comun.FL); cfg['freno']=fr
    ea,qa=run(BASE,k8,cfg); eb,qb=run(BASE|mom,tm,cfg); print('freno',fr,C.fmt(qa),'→',C.fmt(qb),'PASA' if C.pasa(qb,qa) else '',flush=True)
