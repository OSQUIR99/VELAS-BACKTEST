import sys, os, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','ESTUDIOS_CAIDAS_2026_10')); import comun
from comun import Cartera, met_eq
AQ=os.path.dirname(os.path.abspath(__file__))
C=Cartera(extra=(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','MOTOR','listas_reconstruidas'),os.path.join(AQ,'listas_mom')))
O=C.O; L=C.L; act=C.act; d=(O.t_entrada>=C.desde).values
W=C.W|(d&np.isin(L,['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq','sp_manana','sp_manana_contra']))
E1=(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX'])&W
nucleo=(np.isin(L,['cripto','petroleo','corto_petroleo','x_petroleo','c10','shy'])|E1|((L=='metales')&(act=='oro')))&W
ex=np.isin(L,['corto_sector','corto_indices_credito'])&W; C.cortos_exentos=ex
cn=(L=='yt_connors_qqq')&W; BASE=nucleo|ex|cn; EX=ex|E1|cn
sen=C.senal; k8=np.ones(len(O)); k8[L=='corto_petroleo']=2.0; k8[(L=='petroleo')&(sen=='L2')]=0.5
k8[(L=='petroleo')&(sen=='tras-noticia (bajada)')]=0.5; k8[L=='x_petroleo']=0.75
mom=(L=='sp_manana')&W; con=(L=='sp_manana_contra')&W
print('operaciones en la ventana: seguir',mom.sum(),'en contra',con.sum())
def run(m,x,tm):
    r,e=C.sim(m,exentas=x,tam_mult=tm); return e,C.met3(e)
def ep(e): return ' · '.join(f"{met_eq(e,pd.Timestamp(a),pd.Timestamp(b))['ratio']:.2f}" for a,b in [('2018-01-01','2020-01-01'),('2020-01-01','2022-01-01'),('2022-01-01','2024-01-01'),('2024-01-01','2026-10-21')])
e0,q0=run(BASE,EX,k8); print(f"{'base (lista cripto original + K8)':55s}",C.fmt(q0),'| ép',ep(e0),flush=True)
res={}
for nom,mm in [('SEGUIR la mañana',mom),('EN CONTRA de la mañana',con)]:
    for t in [0.25,0.5,1.0]:
        for fuera in [False,True]:
            tm=k8.copy(); tm[mm]=t
            e,q=run(BASE|mm, EX|(mm if fuera else np.zeros(len(O),bool)), tm)
            ok='PASA' if C.pasa(q,q0) else ''
            print(f"{nom+f' a {t} R'+(' fuera del freno' if fuera else ''):55s}",C.fmt(q),'| ép',ep(e),ok,flush=True)
            res[(nom,t,fuera)]=(e,q)
import pickle; pickle.dump({'q0':q0},open('cart_q0.pkl','wb'))
