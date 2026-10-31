import sys, numpy as np, pandas as pd
from comun import Cartera, LISTAS_CORTOS
C=Cartera(extra=(LISTAS_CORTOS,'/home/claude/caidas/listas_nuevas'))
NOMS=['n1_vixvxv','n2_martillo','n3_finmes_rut','n4_finmes_spx','n5_bono10','n6_bono30']
mult={k:float(x) for k,x in (a.split('=') for a in sys.argv[1:])} if len(sys.argv)>1 else {}
filas=[]
for cfg in (False,True):
    C.usar_base_31oct=cfg
    for nb,base in C.bases.items():
        rb,eqb=C.sim(base); qb=C.met3(eqb)
        combos=[[n] for n in NOMS]+[['n1_vixvxv','n4_finmes_spx'],['n1_vixvxv','n3_finmes_rut','n4_finmes_spx']]
        for comb in combos:
            nm=np.isin(C.L,comb)&(C.O.t_entrada>=C.desde).values
            tm=np.ones(len(C.O))
            for k,v in mult.items(): tm[C.L==k]=v
            rr,eq=C.sim(base|nm, tam_mult=tm); q=C.met3(eq)
            ok=all(q[i]['ratio']>qb[i]['ratio'] for i in range(3))
            filas.append(dict(fecha='31-oct' if cfg else '28-oct',v=nb[0],senal='+'.join(comb),r=q[0]['ratio'],r1821=q[1]['ratio'],r2226=q[2]['ratio'],
                 d=q[0]['ratio']-qb[0]['ratio'],d1821=q[1]['ratio']-qb[1]['ratio'],d2226=q[2]['ratio']-qb[2]['ratio'],Ra=q[0]['R_ano']-qb[0]['R_ano'],caida=q[0]['caida']-qb[0]['caida'],pasa=ok,boot=C.bootstrap(eqb,eq,300)))
T=pd.DataFrame(filas); T.to_csv('evalua_nuevas%s.csv'%('_'+'_'.join(sys.argv[1:]) if len(sys.argv)>1 else ''),index=False)
pd.set_option('display.width',250)
print(T.groupby('senal').agg(pasa=('pasa','sum'),d=('d','mean'),d1821=('d1821','mean'),d2226=('d2226','mean'),Ra=('Ra','mean'),caida=('caida','mean'),boot=('boot','mean')).round(3).sort_values('pasa',ascending=False).to_string())
