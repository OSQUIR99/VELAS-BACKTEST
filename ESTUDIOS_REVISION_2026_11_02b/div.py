from lab import *
s0,e0,_=run(); ref=C.met3(e0); print(linea('base vigente',e0))
W2=C.W|(O.t_entrada>=C.desde).values
G={'plata':(L=='metales')&(act=='plata')&W2,'T1':(L=='mensuales')&(sen=='T1')&W2,'T2':(L=='mensuales')&(sen=='T2')&W2,
   'E1 sectores':(L=='bolsa_e1')&~np.isin(act,['SPX','DJI','NDX','RUT'])&W2,'E1 RUT':(L=='bolsa_e1')&(act=='RUT')&W2,
   'N1':(L=='n1_vixvxv')&W2}
for nom,m in G.items():
    for sz in [0.25,0.5]:
        for fuera in [False,True]:
            tm=np.ones(len(O)); tm[m]=sz
            x=EXV|(m if fuera else False)
            s,e,_=run(mask=BASEV|m,exv=x,tm=tm); print(linea(f'+{nom} ×{sz}{" fuera freno" if fuera else ""}',e,ref),flush=True)
