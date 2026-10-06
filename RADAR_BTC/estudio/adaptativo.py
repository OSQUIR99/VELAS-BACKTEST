# -*- coding: utf-8 -*-
"""Pesos adaptativos: cada bloque pesa según lo bien que ha avisado en los 2 años anteriores (solo datos ya conocidos)."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
D = pd.read_parquet('radar_historico.parquet')
BL = ['macro', 'liquidez', 'estructura', 'catalizadores']
BASE = {'macro': 0.375, 'liquidez': 0.2, 'estructura': 0.25, 'catalizadores': 0.1}
def auc(x, y):
    m = x.notna() & y.notna()
    return roc_auc_score(y[m], x[m]) if m.sum() > 150 and y[m].nunique() > 1 else np.nan
fechas = pd.date_range('2019-09-01', D.index.max(), freq='MS')
W = {}
for f in fechas:
    fin = f - pd.Timedelta(days=31); ini = fin - pd.Timedelta(days=730)
    s = D.loc[ini:fin]
    w = {}
    for b in BL:
        a = auc(s[b], s['desplome'])
        w[b] = BASE[b] * (0.25 + 1.5 * max(0, (a if not np.isnan(a) else 0.5) - 0.5) / 0.2)  # suelo 25 % del peso base
    W[f] = w
W = pd.DataFrame(W).T
W = W.div(W.sum(axis=1), axis=0)
Wd = W.reindex(D.index, method='ffill')
tot = (Wd['macro'] * D.macro.fillna(50) + Wd['liquidez'] * D.liquidez.fillna(50) + Wd['estructura'] * D.estructura + Wd['catalizadores'] * D.catalizadores)
D['total_adapt'] = tot
EP = {'2019-21': ('2019-09-01', '2021-12-31'), '2022-23': ('2022', '2023'), '2024-26': ('2024', '2026-08-30'), '2022-26': ('2022', '2026-08-30')}
for col in ['total', 'total_adapt']:
    print(col, {e: round(auc(D.loc[a:b, col], D.loc[a:b, 'desplome']), 2) for e, (a, b) in EP.items()})
print(W.resample('YE').mean().round(2).to_string())
W.to_csv('pesos_adaptativos_mensuales.csv')
D[['total_adapt']].to_parquet('total_adapt.parquet')
