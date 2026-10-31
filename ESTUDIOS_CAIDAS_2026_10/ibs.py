# Primera medida rápida de la candidata de YouTube «IBS en SPY» (Build Alpha) en el motor real.
import sys, numpy as np, pandas as pd
from cortos import diario, atr_wilder
d=diario('sp500'); d=d[d.index>='2000-01-01']
ibs=(d.cierre-d.minimo)/(d.maximo-d.minimo).replace(0,np.nan)
atr=atr_wilder(diario('sp500'))
c=d.cierre.values; idx=d.index; ops=[]; dia=[]
i=0
while i<len(d)-1:
    if ibs.iloc[i]<0.2 and np.isfinite(atr.get(idx[i],np.nan)):
        E=c[i]; R=2.5*float(atr[idx[i]]); k=i+1; lat=[]
        while k<len(d) and not (ibs.iloc[k]>0.8): lat.append((idx[k],(c[k]-E)/R)); k+=1
        if k>=len(d): break
        X=c[k]; rb=(X-E)/R-0.0001*E/R
        oid=f'ibs_spy-{idx[i].strftime("%Y%m%d")}'
        ops.append(dict(id=oid,familia='ibs_spy',activo='SPX',direccion=1,t_senal=idx[i]+pd.Timedelta(hours=20),t_entrada=idx[i]+pd.Timedelta(hours=20),
                        t_salida=idx[k]+pd.Timedelta(hours=20),entrada=E,sl_inicial=E-R,salida=X,r_bruto=rb,tam_R=1.0,r_final=rb,estrellas=np.nan,
                        mae_R=min([v for _,v in lat]+[rb,0]),mfe_R=max([v for _,v in lat]+[rb,0]),motivo_salida='ibs>0.8',bloque='bolsa_eeuu'))
        for f,v in lat: dia.append(dict(id=oid,fecha=f,r_latente=v))
        dia.append(dict(id=oid,fecha=idx[k],r_latente=rb))
        i=k
    else: i+=1
O=pd.DataFrame(ops); D=pd.DataFrame(dia)
O.to_parquet('listas_ibs/ibs_spy.parquet'); D.to_parquet('listas_ibs/ibs_spy_diario.parquet')
w=O[O.t_entrada>='2018-05-01']
print('IBS SPY: operaciones desde 2018-05', len(w), '| R por operación', round(w.r_bruto.mean(),3), '| acierto', round((w.r_bruto>0).mean()*100), '% | R/año sola', round(w.r_bruto.sum()/8.47,2))
