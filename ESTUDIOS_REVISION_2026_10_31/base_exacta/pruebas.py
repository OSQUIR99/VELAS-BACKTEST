from base import *
sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10')
from b21 import serie_b21
LQ=pd.read_parquet('/home/claude/velas-backtest/LIQUIDEZ/linea_reconstruida_2026_10.parquet')
vie=(O.t_entrada.dt.normalize()-pd.Timedelta(days=1))
lin=LQ.linea.reindex(vie,method='ffill').values; imp=LQ.impulso.reindex(vie,method='ffill').values
d13=(LQ.linea-LQ.linea.shift(13)).reindex(vie,method='ffill').values
baja=(lin<33)|(d13<0); alta=(lin>50)&(d13>0); muybaja=lin<33
largo=O.direccion.values==1
b21=serie_b21().reindex(O.t_entrada.dt.normalize()).fillna(False).values.astype(bool)
resto=largo&~np.isin(L,['cripto','shy','corto_sector','corto_indices_credito'])
M=C.M
def e1_una(base):
    k=np.flatnonzero(E1&base); k=k[np.argsort(M.t_ent[k])]; ok=np.ones(len(O),bool); fin=np.datetime64('1900-01-01')
    for j in k:
        if M.t_ent[j]<fin: ok[j]=False
        else: fin=M.t_sal[j]
    return ok
FAM={'Oro':(L=='metales')&(act=='oro'),'SHY':L=='shy','Petróleo L1':(L=='petroleo')&(C.senal=='L1'),'Petróleo L2/L3':(L=='petroleo')&np.isin(C.senal,['L2','L3']),
     'Petróleo X1/X3':L=='x_petroleo','Corto petróleo':L=='corto_petroleo','E1 S&P':E1&(act=='SPX'),'E1 Nasdaq':E1&(act=='NDX'),'E1 Dow':E1&(act=='DJI'),'C10':L=='c10',
     'SOL':(L=='cripto')&(act=='SOL'),'LINK':(L=='cripto')&(act=='LINK'),'ZEC':(L=='cripto')&(act=='ZEC'),'N1':n1,'Cortos sector e índices':ex}
filas=[]
for nb,base in (('con N1',BASE|n1),('sin N1',BASE)):
    rb,eqb=C.sim(base); qb=C.met3(eqb)
    V={'N1 (quitar / poner)':dict(mask=base^n1),'B21 · largos no cripto a la mitad':dict(tam=np.where(resto&b21,0.5,1.0)),'E1e · una E1 a la vez':dict(mask=base&e1_una(base))}
    for f,m in FAM.items():
        V[f+' · × 0,5 liquidez baja']=dict(tam=np.where(m&baja,0.5,1.0)); V[f+' · × 1,5 liquidez alta']=dict(tam=np.where(m&alta,1.5,1.0)); V[f+' · no abrir línea < 33']=dict(mask=base&~(m&muybaja))
    V['Cartera × 0,75/1,25 línea']=dict(tam=np.where(muybaja,0.75,np.where(lin>50,1.25,1.0))); V['Cartera × 0,75 (< 33)']=dict(tam=np.where(muybaja,0.75,1.0))
    for s in ('btc_sem_impulso','btc_sem_linea'): V['BTC semanal · '+s]=dict(mask=base|((L==s)&W))
    for nr,v in V.items():
        rr,eq=C.sim(v.get('mask',base),tam_mult=v.get('tam')); q=C.met3(eq)
        filas.append(dict(v=nb,regla=nr,pasa=all(q[i]['ratio']>qb[i]['ratio'] for i in range(3)),r=q[0]['ratio'],r1=q[1]['ratio'],r2=q[2]['ratio'],b=qb[0]['ratio'],b1=qb[1]['ratio'],b2=qb[2]['ratio'],Ra=q[0]['R_ano']-qb[0]['R_ano'],dca=q[0]['caida']-qb[0]['caida'],boot=C.bootstrap(eqb,eq,300) if all(q[i]['ratio']>qb[i]['ratio'] for i in range(3)) else np.nan))
    print(nb,'base',C.fmt(qb),flush=True)
T=pd.DataFrame(filas); T.to_csv('pruebas.csv',index=False); pd.set_option('display.width',250)
print(T[T.pasa|T.regla.str.startswith(('N1','B21','E1e','BTC'))].round(3).to_string(index=False))
