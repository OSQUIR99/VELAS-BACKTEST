from ver import *
v=V(True); O=v.O; L=v.L; sen=v.sen
_,e0=v.sim(v.mult()); q0=tres(e0,v.desde)
cp=np.flatnonzero((L=='corto_petroleo')&v.base)
fe=O.t_senal.dt.date.values
grupos=sorted(set((pd.Timestamp(O.t_entrada[k]).to_period('M')) for k in cp))
print('señales (meses) de CORTO PETRÓLEO en ventana:',[str(g) for g in grupos])
print('--- quitar el ×2 a un mes de señales (WTI+Brent) cada vez; K6 y K2')
for g in grupos:
    sel=np.array([pd.Timestamp(O.t_entrada[k]).to_period('M')==g for k in cp]); ks=cp[sel]
    for nom,base in (('K6',v.mult(corto_pet=2)),('K2',v.mult(2,0.75,0.75))):
        tm=base.copy(); tm[ks]=1.0; _,e=v.sim(tm); q=tres(e,v.desde)
        print(f'  sin x2 en {g} ({nom})',fmt(q),'PASA' if all(q[i][2]>q0[i][2] for i in range(3)) else '-')
for nom,base in (('K6',v.mult(corto_pet=2)),('K2',v.mult(2,0.75,0.75))):
    tm=base.copy(); ks=[k for k in cp if pd.Timestamp(O.t_entrada[k]).to_period('M') in (pd.Period('2020-02'),pd.Period('2018-11'))]; tm[ks]=1.0
    _,e=v.sim(tm); q=tres(e,v.desde); print(f'  sin x2 en 2018-11 y 2020-02 ({nom})',fmt(q),'PASA' if all(q[i][2]>q0[i][2] for i in range(3)) else '-')
# reparto de la mejora de K6 por operación (contribución directa)
s0=np.load('s_B0.npy'); s6=np.load('s_K6.npy')
dlt=(s6-s0)*O.r_final.values; print('mejora directa K6 total',round(dlt.sum(),2),'de ella feb-2020',round(dlt[cp[[pd.Timestamp(O.t_entrada[k]).to_period('M')==pd.Period('2020-02') for k in cp]]].sum(),2),'nov-2018',round(dlt[cp[[pd.Timestamp(O.t_entrada[k]).to_period('M')==pd.Period('2018-11') for k in cp]]].sum(),2))
