# -*- coding: utf-8 -*-
"""Prueba histórica del radar (percentiles sin mirar el futuro) y tabla de episodios."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
import radar_nucleo as R

E = pd.read_csv('estado_historico.csv', parse_dates=['fecha']).set_index('fecha')
X = R.variables(E)
B = R.bloques(X)
c = E['c']; l = E['l']; h = E['h']
H = 30
dd = l[::-1].rolling(H, min_periods=H).min()[::-1].shift(-1) / c - 1
vol = np.log(c).diff().rolling(90).std() * np.sqrt(H)
Y = pd.DataFrame({'dd': dd, 'desplome': ((np.log1p(dd) <= -1.5 * vol).astype(float)).where(dd.notna()),
                  'desplome20': (dd <= -0.20).astype(float).where(dd.notna())})
D = X.join(B).join(Y)
D.to_parquet('radar_historico.parquet')

def auc(x, y):
    m = x.notna() & y.notna()
    return roc_auc_score(y[m], x[m]) if m.sum() > 100 and y[m].nunique() > 1 else np.nan

EP = {'2018-21': ('2018-08-17', '2021-12-31'), '2022-26': ('2022-01-01', '2026-08-30'), '2024-26': ('2024-01-01', '2026-08-30')}
print('AUC (0,5 = azar) frente a "desplome" (caída >= 1,5 desviaciones típicas en 30 días)')
filas = []
for col in ['macro', 'liquidez', 'estructura', 'catalizadores', 'total']:
    filas.append({'bloque': col, **{e: round(auc(D.loc[a:b, col], D.loc[a:b, 'desplome']), 2) for e, (a, b) in EP.items()}})
print(pd.DataFrame(filas).to_string(index=False))
print('\nTasa de desplome por nivel del total (y caída máxima media en 30 días):')
for e, (a, b) in EP.items():
    s = D.loc[a:b]
    g = s.groupby(pd.cut(s.total, [0, 40, 52, 62, 101], labels=['VERDE <40', 'AMARILLO 40-52', 'NARANJA 52-62', 'ROJO >=62']), observed=False)
    t = pd.DataFrame({'dias_%': (g.size() / len(s) * 100).round(0), 'desplome': g['desplome'].mean().round(2),
                      'desplome_-20%': g['desplome20'].mean().round(2), 'caida_max_media_%': (g['dd'].mean() * 100).round(1)})
    print(f'\n{e} (base desplome {s.desplome.mean():.2f})'); print(t.to_string())
