import pandas as pd, numpy as np
from core import *
from estudio2 import salida, resultado
pd.set_option('display.width',250)
rng=np.random.default_rng(11)
# ---------- 1) ¿Dónde poner el stop? entrada al confirmarse el giro, objetivo extremo contrario, stop a distintas distancias bajo el mínimo
rows=[]
for a in ACTIVOS:
    for tf in ['1h','4h','1d']:
        df=cargar(a,tf)
        for lado in ['largo','corto']:
            if lado=='largo': h,l,c=df.h.values,df.l.values,df.c.values
            else: h,l,c=-df.l.values,-df.h.values,-df.c.values
            A=df.atr.values; z=zigzag(pd.DataFrame({'h':h,'l':l,'atr':A}),2.5)
            zi,zp,zt,zc=z.i.values,z.p.values,z.t.values,z.cf.values
            for p in range(2,len(z)-1):
                if zt[p]!=-1: continue
                Ln,H1,cf=zp[p],zp[p-1],zc[p]; a_=A[zi[p]]; ent=c[cf]
                if H1<=ent: continue
                for x in [0.1,0.5,1.0,1.5]:
                    stop=Ln-x*a_
                    sal,_,_=salida(h,l,c,cf+1,ent,stop,H1,2000)
                    R,m=resultado(ent,sal,stop)
                    Rb=(sal-ent)/(ent-stop)
                    rows.append(dict(activo=a,tf=tf,x=x,R=R,Rb=Rb,R_obj=(H1-ent)/(ent-stop),win=sal>=H1))
s=pd.DataFrame(rows)
s['p_azar']=1/(1+s.R_obj)
print('STOP bajo el minimo: esperanza bruta (sin comisiones) y ventaja de acierto sobre el azar')
print(s.groupby(['tf','x']).agg(n=('Rb','size'),Rbruto=('Rb','mean'),Rneto=('R','mean'),acierto=('win','mean'),azar=('p_azar','mean')).round(3))
s.to_parquet('ev_stop.parquet')
