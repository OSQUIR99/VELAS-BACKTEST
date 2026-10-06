import pandas as pd, numpy as np
from core import *
import estudio2, estudio4
df=cargar('BTC','15m')
E=[];C=[];F=[]
for lado in ['largo','corto']:
    e,c=estudio2.analizar(df,2.5,lado,semilla=5); e['lado']=lado; c['lado']=lado; E.append(e); C.append(c)
    f=estudio4.analizar(df,lado); f['lado']=lado; F.append(f)
pd.concat(E).to_parquet('ev2_btc15.parquet'); pd.concat(C).to_parquet('ctrl2_btc15.parquet'); pd.concat(F).to_parquet('ev4_btc15.parquet')
