# Lista «SEGUIR LA MAÑANA» del S&P: si el S&P se mueve más de U % de 9:30 a 13:30 ET, entrar a las 13:30 en ese sentido,
# stop en la apertura del día (si vuelve ahí, el impulso ha fallado), salida al cierre (16:00). Coste 0,02 % ida y vuelta.
import os, numpy as np, pandas as pd
from datos import *
def hacer(U=0.005, contra=False, cost=0.0002, sal='listas_mom'):
    s4=dias_sp('4h'); g=s4.groupby('dia')
    Q=pd.DataFrame({'o':g.apertura.first(),'m':g.cierre.first(),'c':g.cierre.last(),'hi':g.maximo.last(),'lo':g.minimo.last(),
                    't1':g.apply(lambda x:x.index[-1]),'n':g.size()}); Q=Q[Q.n==2]
    r1=Q.m/Q.o-1; sel=r1.abs()>U; Q=Q[sel]; r1=r1[sel]
    dirn=np.sign(r1).astype(int)*(-1 if contra else 1)
    Rp=(Q.m-Q.o).abs()
    if contra: Rp=Rp  # stop simétrico: a la misma distancia al otro lado
    sl=Q.m-dirn*Rp
    tocado=np.where(dirn>0, Q.lo<=sl, Q.hi>=sl)
    salida=np.where(tocado, sl, Q.c)
    rb=dirn*(salida-Q.m)/Rp
    rf=rb-cost*Q.m/Rp
    t1=pd.to_datetime(Q.t1.values); tcierre=t1+pd.Timedelta(hours=2.5)
    nom='sp_manana_contra' if contra else 'sp_manana'
    O=pd.DataFrame({'id':[f'{nom}-{i:05d}' for i in range(len(Q))],'familia':nom,'senal':'en contra de la mañana' if contra else 'seguir la mañana',
        'activo':'SPX','direccion':dirn.values,'t_senal':t1,'t_entrada':t1,'t_salida':tcierre,'entrada':Q.m.values,'sl_inicial':sl.values,
        'salida':salida,'r_bruto':rb.values,'tam_R':1.0,'r_final':rf.values,'estrellas':np.nan,'mae_R':np.nan,'mfe_R':np.nan,
        'motivo_salida':np.where(tocado,'stop','cierre'),'bloque':'bolsa_eeuu'})
    D=pd.DataFrame({'id':O.id,'fecha':pd.to_datetime(O.t_entrada).dt.normalize(),'r_latente':O.r_final})
    os.makedirs(sal,exist_ok=True); O.to_parquet(f'{sal}/{nom}.parquet'); D.to_parquet(f'{sal}/{nom}_diario.parquet')
    return O
if __name__=='__main__':
    for c in [False,True]:
        O=hacer(contra=c); r=O.r_final; y=pd.to_datetime(O.t_entrada).dt.year
        print(O.familia.iloc[0], len(O), f'R medio {r.mean():+.3f} acierto {(r>0).mean()*100:.0f}% stops {(O.motivo_salida=="stop").mean()*100:.0f}% | por épocas', r.groupby(pd.cut(y,[2005,2014,2021,2026])).mean().round(3).tolist())
