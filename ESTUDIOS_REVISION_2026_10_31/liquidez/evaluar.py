import sys; sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10')
import numpy as np, pandas as pd
import comun
from comun import Cartera
C=Cartera(extra=('/home/claude/velas-backtest/MOTOR/listas_reconstruidas','/home/claude/liq31/listas_nuevas'))
C.usar_base_31oct=True
O=C.O; L=C.L; act=C.act; W=(O.t_entrada>=C.desde).values
LQ=pd.read_parquet('/home/claude/velas-backtest/LIQUIDEZ/linea_reconstruida_2026_10.parquet')
vie=(O.t_entrada.dt.normalize()-pd.Timedelta(days=1))     # viernes anterior (o antes)
lin=LQ.linea.reindex(vie,method='ffill').values; imp=LQ.impulso.reindex(vie,method='ffill').values
d13=(LQ.linea-LQ.linea.shift(13)).reindex(vie,method='ffill').values
baja=(lin<33)|(d13<0); alta=(lin>50)&(d13>0); muybaja=lin<33
n1=(L=='n1_vixvxv')&W
FAM={'Oro':(L=='metales')&(act=='oro'),'SHY':L=='shy','Petróleo L1':(L=='petroleo')&(C.senal=='L1'),'Petróleo L2/L3':(L=='petroleo')&np.isin(C.senal,['L2','L3']),
     'Petróleo X1/X3':L=='x_petroleo','E1 S&P':C.e1&(act=='SPX'),'E1 Nasdaq':C.e1&(act=='NDX'),'E1 Dow':C.e1&(act=='DJI'),'C10':L=='c10',
     'SOL':(L=='cripto')&(act=='SOL'),'LINK':(L=='cripto')&(act=='LINK'),'ZEC':(L=='cripto')&(act=='ZEC'),'N1 VIX/VXV':n1,
     'Cortos (sector e índices)':C.cortos_exentos}
filas=[]
for nb,b0 in C.bases.items():
    base=b0|n1; rb,eqb=C.sim(base); qb=C.met3(eqb)
    V={}
    for f,m in FAM.items():
        V[f+' · × 0,5 con liquidez baja']=dict(tam=np.where(m&baja,0.5,1.0))
        V[f+' · × 1,5 con liquidez alta']=dict(tam=np.where(m&alta,1.5,1.0))
        V[f+' · no abrir con línea < 33']=dict(mask=base&~(m&muybaja))
    V['Toda la cartera · × 0,75 (< 33) / × 1,25 (> 50)']=dict(tam=np.where(muybaja,0.75,np.where(lin>50,1.25,1.0)))
    V['Toda la cartera · igual con línea con impulso']=dict(tam=np.where(imp<33,0.75,np.where(imp>50,1.25,1.0)))
    V['Toda la cartera · solo × 0,75 (< 33)']=dict(tam=np.where(muybaja,0.75,1.0))
    for s in ('btc_sem_impulso','btc_sem_linea'): V['Señal nueva · '+s]=dict(mask=base|((L==s)&W))
    for nr,v in V.items():
        rr,eq=C.sim(v.get('mask',base),tam_mult=v.get('tam')); q=C.met3(eq)
        filas.append(dict(v=nb[0],regla=nr,pasa=all(q[i]['ratio']>qb[i]['ratio'] for i in range(3)),
            r=q[0]['ratio'],r1=q[1]['ratio'],r2=q[2]['ratio'],b=qb[0]['ratio'],b1=qb[1]['ratio'],b2=qb[2]['ratio'],Ra=q[0]['R_ano'],bRa=qb[0]['R_ano'],ca=q[0]['caida'],bca=qb[0]['caida']))
    print(nb,'base',C.fmt(qb),flush=True)
T=pd.DataFrame(filas); T.to_csv('resultados.csv',index=False)
g=T.groupby('regla').agg(pasa=('pasa','sum'),dr=('r',lambda x:0),).reset_index()
T['d']=T.r-T.b; T['d1']=T.r1-T.b1; T['d2']=T.r2-T.b2; T['dRa']=T.Ra-T.bRa; T['dca']=T.ca-T.bca
S=T.groupby('regla').agg(pasa=('pasa','sum'),d=('d','mean'),d1=('d1','mean'),d2=('d2','mean'),dRa=('dRa','mean'),dca=('dca','mean')).round(3).sort_values(['pasa','d'],ascending=False)
pd.set_option('display.width',250); print(S.head(25).to_string())
