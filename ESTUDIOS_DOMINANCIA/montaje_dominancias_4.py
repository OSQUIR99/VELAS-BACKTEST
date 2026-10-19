# -*- coding: utf-8 -*-
"""Cuarta fase (19-oct, tras la auditoría): solo ETH/BTC sube × 0,5 (regla C) encima de la vigente (A).
Correcciones del auditor: cierres de la misma vela sumados; retraso de 1, 2 y 3 días; ajustes vecinos; peor caso intravela."""
import sys, os, itertools
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..'))
from cargar import velas
X = pd.read_csv(os.path.join(AQUI, 'montaje_dominancias_ops2.csv'), parse_dates=['entrada', 'salida'])
eb = velas('ETH_BTC', '1d').cierre
A = np.where(X.T2_bajo_m20 == 1, 1.5, 1.0)
def ratio(w, m):
    s = pd.Series((X.R * w)[m].values, X.salida[m].values).groupby(level=0).sum().sort_index()
    eq = s.cumsum().values; dd = (eq - np.maximum.accumulate(np.r_[0, eq])[1:]).min()
    return eq[-1] / abs(dd), eq[-1], dd
EP = {'todo': ('2018', '2027'), '18-21': ('2018', '2022'), '22-26': ('2022', '2027'), '23-26 (fuera)': ('2023', '2027'), '24-26': ('2024', '2027')}
filas = []
for n, k, lag in itertools.product((15, 20, 30, 50), (3, 5, 10), (1, 2, 3)):
    m20 = eb.rolling(n).mean(); s = (m20 > m20.shift(k)).astype(float)
    v = s.reindex(X.entrada.dt.floor('D') - pd.Timedelta(days=lag)).values
    C = A * np.where(v == 1, 0.5, 1)
    f = {'media': n, 'pend': k, 'retraso_dias': lag}
    for ep, (a, b) in EP.items():
        m = ((X.entrada >= a) & (X.entrada < b)).values
        f[ep] = ratio(C, m)[0] - ratio(A, m)[0]
    f['mejora_en_todas'] = all(f[e] > 0 for e in EP)
    filas.append(f)
T = pd.DataFrame(filas); pd.set_option('display.width', 250)
print('Mejora del ratio R/caída (C − A) por época; positivo = mejor')
print(T.round(2).to_string(index=False))
print('\nCombinaciones que mejoran en TODAS las épocas:', int(T.mejora_en_todas.sum()), 'de', len(T))
print('Solo 20/5:', T[(T.media == 20) & (T.pend == 5)][['retraso_dias'] + list(EP)].round(2).to_string(index=False))
for ep, (a, b) in EP.items():
    m = ((X.entrada >= a) & (X.entrada < b)).values
    ra, Ra, da = ratio(A, m); m20 = eb.rolling(20).mean(); v = (m20 > m20.shift(5)).astype(float).reindex(X.entrada.dt.floor('D') - pd.Timedelta(days=1)).values
    rc, Rc, dc = ratio(A * np.where(v == 1, 0.5, 1), m)
    print(f'{ep:14s} A: ratio {ra:5.2f} R {Ra:6.1f} caída {da:6.1f} | C: ratio {rc:5.2f} R {Rc:6.1f} caída {dc:6.1f}')
T.to_csv(os.path.join(AQUI, 'montaje_dominancias_C_robustez.csv'), index=False)
