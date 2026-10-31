# Repite las reglas de esta conversación sobre la base del 31-oct (SHY 10k + cortos x2) con el criterio de Óscar del
# 31-oct: basta con que suba el ratio R/año ÷ caída en todo, 2018-21 y 2022-26.
import numpy as np, pandas as pd
import reglas as R
import reglas2 as R2
C=R.C; M=R.M
filas=[]
for config in (False, True):
    C.usar_base_31oct=config
    nomc='31-oct' if config else '28-oct'
    for nb,base in C.bases.items():
        rb,eqb=C.sim(base); qb=C.met3(eqb)
        V=R.variantes(base)
        V['E1f E1 × 1,5 con la línea con impulso ≥ 50']=dict(tam=np.where(R.E1 & ~R.on_at_entry('liquidez_impulso_bajo50'),1.5,1.0))
        buena=R.PET_L & ~R.on_at_entry('dolar_sube') & ~R.on_at_entry('liquidez_baja')
        V['P6 petróleo largo × 1,5 en buen contexto']=dict(tam=np.where(buena,1.5,1.0))
        for x in (5,7): V[f'PS seguro de la cartera −{x} R']=dict(ps=x)
        for nr,v in V.items():
            MM=M
            if 'prot' in v: sel,X,g,par=v['prot']; MM,_=R.motor_protegido(sel,X,g,par)
            if 'ps' in v: MM,_=R2.seguro_ganancia(base,v['ps'])
            rr,eq=C.sim(v.get('mask',base),cfg=v.get('cfg'),tam_mult=v.get('tam'),M=MM); q=C.met3(eq)
            ok=all(q[i]['ratio']>qb[i]['ratio'] for i in range(3))
            filas.append(dict(base_fecha=nomc,version=nb[0],regla=nr,r=q[0]['ratio'],r1821=q[1]['ratio'],r2226=q[2]['ratio'],
                              base_r=qb[0]['ratio'],base_1821=qb[1]['ratio'],base_2226=qb[2]['ratio'],Ra=q[0]['R_ano'],base_Ra=qb[0]['R_ano'],
                              caida=q[0]['caida'],base_caida=qb[0]['caida'],pasa_ratio=ok))
        print(nomc,nb,'hecho',flush=True)
T=pd.DataFrame(filas); T.to_csv('revisar31.csv',index=False)
P=T.pivot_table(index='regla',columns=['base_fecha','version'],values='pasa_ratio',aggfunc='first')
P['veces']=P.sum(axis=1)
pd.set_option('display.width',250)
print(P.sort_values('veces',ascending=False).to_string())
print(T[(T.base_fecha=='31-oct')&(T.version=='a')][['regla','r','r1821','r2226','Ra','caida']].round(2).to_string(index=False))
print('BASES', T.groupby(['base_fecha','version'])[['base_r','base_1821','base_2226','base_Ra','base_caida']].first().round(2))
