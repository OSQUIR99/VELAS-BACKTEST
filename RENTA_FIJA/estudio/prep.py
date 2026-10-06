import json, io, pandas as pd, numpy as np
f = json.load(open('bonos_fred_macro.json'))
fred = {}
for k, t in f.items():
    s = pd.read_csv(io.StringIO(t), na_values=['.'], parse_dates=['observation_date']).set_index('observation_date').iloc[:,0].dropna()
    fred[k] = s
for k,s in sorted(fred.items(), key=lambda x:x[1].index[0]):
    print(f'{k:14s} {s.index[0].date()} -> {s.index[-1].date()} n={len(s)} last={s.iloc[-1]}')
pd.to_pickle(fred, 'fred.pkl')
raw = open('bonos_yahoo_precios.csv').read().split('#DIVIDENDOS\n')
px = pd.read_csv(io.StringIO(raw[0]), parse_dates=['fecha'])
dv = pd.read_csv(io.StringIO(raw[1]), parse_dates=['fecha'])
px = px.dropna(subset=['cierre'])
px = px.drop_duplicates(['simbolo','fecha'], keep='last')
pd.to_pickle({'px':px,'dv':dv}, 'yahoo.pkl')
print(px.groupby('simbolo').fecha.agg(['min','max','count']))
