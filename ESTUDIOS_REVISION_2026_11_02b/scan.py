import pandas as pd, numpy as np
d=pd.read_parquet('listas_v/cripto_realista.parquet')
d['per']=np.where(d.t_entrada<'2022-01-01','18-21','22-26'); d=d[d.t_entrada>='2018-05-01']
d['ru']=d.r_bruto  # R por unidad
d['dow']=pd.to_datetime(d.t_entrada).dt.dayofweek; d['h']=pd.to_datetime(d.t_entrada).dt.hour
cols=['t2','franja','vela_grande','estirada','max_diario_roto','eth_btc_sube','salida_neta','largos_apinados','nivel','btc_acompana','vwap_cerca','sobrecalentamiento','sin_revision','wyckoff']
for c in cols+['abiertas_otras','dow','h','estrellas','puntos']:
    try:
        g=d.groupby([c,'per']).ru.agg(['mean','count']).round(2).unstack('per')
        print('==',c); print(g.to_string())
    except Exception as e: print(c,e)
