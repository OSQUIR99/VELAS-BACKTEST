import io, zipfile, subprocess, pandas as pd, numpy as np, pickle
from concurrent.futures import ThreadPoolExecutor
B='https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{}.zip'
def f(ym):
    r=subprocess.run(['curl','-sS','-m','90',B.format(ym)],capture_output=True)
    try:
        with zipfile.ZipFile(io.BytesIO(r.stdout)) as z: d=pd.read_csv(z.open(z.namelist()[0]),header=None)
        return d
    except Exception: return None
meses=pd.date_range('2020-01-01','2026-09-01',freq='MS').strftime('%Y-%m').tolist()
with ThreadPoolExecutor(8) as ex: p=[x for x in ex.map(f,meses) if x is not None]
d=pd.concat(p); t=d[0].astype('int64'); t=np.where(t>1e14,t//1000,t)
s=pd.Series(d[4].astype(float).values,index=pd.to_datetime(t,unit='ms')).sort_index(); s=s[~s.index.duplicated()]
D=pickle.load(open('datos.pkl','rb')); h=D['BTC1h'].c; s=pd.concat([s,h[h.index>s.index[-1]]])
D['BTCh']=s; pickle.dump(D,open('datos.pkl','wb')); print(len(s),s.index[0],s.index[-1])
