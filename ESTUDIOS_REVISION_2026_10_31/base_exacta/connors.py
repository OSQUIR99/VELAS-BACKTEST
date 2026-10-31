import pickle, numpy as np, pandas as pd
q=pickle.load(open('/home/claude/mstr/datos.pkl','rb'))['QQQ'].copy()
q.index=(q.index+pd.Timedelta(hours=6)).normalize()
c=q.c; d=c.diff(); up=d.clip(lower=0); dn=-d.clip(upper=0)
rsi2=100-100/(1+up.ewm(alpha=1/2,adjust=False).mean()/dn.ewm(alpha=1/2,adjust=False).mean())
tr=pd.concat([q.h-q.l,(q.h-c.shift()).abs(),(q.l-c.shift()).abs()],axis=1).max(axis=1); atr=tr.ewm(alpha=1/14,adjust=False).mean()
pdm=(q.h.diff()).where((q.h.diff()>-q.l.diff())&(q.h.diff()>0),0.0); mdm=(-q.l.diff()).where((-q.l.diff()>q.h.diff())&(-q.l.diff()>0),0.0)
pdi=100*pdm.ewm(alpha=1/14,adjust=False).mean()/atr; mdi=100*mdm.ewm(alpha=1/14,adjust=False).mean()/atr
adx=(100*(pdi-mdi).abs()/(pdi+mdi)).ewm(alpha=1/14,adjust=False).mean()
sig=(c>c.rolling(250).mean())&(rsi2<20)&(adx>20)
idx=q.index; filas=[]; dia=[]; i=250
while i<len(idx)-1:
    if sig.iloc[i]:
        e=i+1; pe=q.o.iloc[e]; R=2.5*atr.iloc[i]; sl=pe-R; j=e; sal=None
        while j<len(idx):
            if q.l.iloc[j]<=sl: sal=(j,sl,'stop'); break
            if rsi2.iloc[j]>75 and j+1<len(idx): sal=(j+1,q.o.iloc[j+1],'regla'); break
            j+=1
        if sal is None: break
        k,ps,mot=sal; r=(ps-pe)/R-0.001*pe/R; tid=f'cn-{idx[e]:%Y%m%d}'
        filas.append(dict(id=tid,familia='connors_qqq',activo='QQQ',direccion=1,t_senal=idx[i]+pd.Timedelta(hours=20),t_entrada=idx[e]+pd.Timedelta(hours=13,minutes=30),
            t_salida=idx[k]+pd.Timedelta(hours=13,minutes=30),entrada=pe,sl_inicial=sl,salida=ps,r_bruto=r,tam_R=1.0,r_final=r,estrellas=np.nan,
            mae_R=float(((q.l.iloc[e:k+1]-pe)/R).min()),mfe_R=float(((q.h.iloc[e:k+1]-pe)/R).max()),motivo_salida=mot,bloque='bolsa_eeuu'))
        for t in range(e,k+1): dia.append(dict(id=tid,fecha=idx[t],r_latente=(q.c.iloc[t]-pe)/R if t<k else r))
        i=k
    else: i+=1
O=pd.DataFrame(filas); O.to_parquet('listas_extra/connors_qqq.parquet'); pd.DataFrame(dia).to_parquet('listas_extra/connors_qqq_diario.parquet')
x=O[O.t_entrada>='2018-05-01']; print('total',len(O),'desde may-2018',len(x),'R',round(x.r_final.sum(),1),'media',round(x.r_final.mean(),3))
