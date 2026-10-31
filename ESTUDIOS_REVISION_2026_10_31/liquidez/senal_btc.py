import pickle, numpy as np, pandas as pd, os
L=pd.read_parquet('/home/claude/velas-backtest/LIQUIDEZ/linea_reconstruida_2026_10.parquet')
B=pickle.load(open('/home/claude/mstr/datos.pkl','rb'))['BTC']; B.index=B.index.normalize()
w=B.resample('W-FRI').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
tr=pd.concat([w.h-w.l,(w.h-w.c.shift()).abs(),(w.l-w.c.shift()).abs()],axis=1).max(1); atr=tr.rolling(14).mean()
os.makedirs('listas_nuevas',exist_ok=True)
for col,nom in (('impulso','btc_sem_impulso'),('linea','btc_sem_linea')):
    s=L[col].reindex(w.index,method='ffill'); filas=[]; dia=[]; i=1
    idx=w.index
    while i<len(idx)-1:
        if s.iloc[i-1]<=50<s.iloc[i] and not np.isnan(atr.iloc[i]):
            ent_d=idx[i]+pd.Timedelta(days=3); pe=B.o.asof(ent_d); sl=pe-2.5*atr.iloc[i]; j=i+1; sal=None
            while j<len(idx):
                seg=B[(B.index>idx[j-1]+pd.Timedelta(days=3))&(B.index<=idx[j]+pd.Timedelta(days=3))]
                if (seg.l<=sl).any(): sal_d=seg.index[(seg.l<=sl).values][0]; ps=sl; mot='stop'; break
                if s.iloc[j]<=50: sal_d=idx[j]+pd.Timedelta(days=3); ps=B.o.asof(sal_d); mot='regla'; break
                j+=1
            else: break
            R=pe-sl; r=(ps-pe)/R; tid=f'{nom}-{ent_d:%Y%m%d}'
            seg=B[(B.index>=ent_d)&(B.index<=sal_d)]
            filas.append(dict(id=tid,familia=nom,activo='BTC',direccion=1,t_senal=idx[i]+pd.Timedelta(hours=21),t_entrada=ent_d,t_salida=sal_d,entrada=pe,sl_inicial=sl,salida=ps,r_bruto=r,tam_R=1.0,r_final=r,estrellas=np.nan,mae_R=float(((seg.l-pe)/R).min()),mfe_R=float(((seg.h-pe)/R).max()),motivo_salida=mot,bloque='cripto'))
            for f,c in seg.c.items(): dia.append(dict(id=tid,fecha=f,r_latente=(c-pe)/R))
            i=max(j,i+1)
        else: i+=1
    O=pd.DataFrame(filas); O.to_parquet(f'listas_nuevas/{nom}.parquet'); pd.DataFrame(dia).to_parquet(f'listas_nuevas/{nom}_diario.parquet')
    print(nom,len(O),round(O.r_final.mean(),2),O.t_entrada.min())
