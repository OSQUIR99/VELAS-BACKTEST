# -*- coding: utf-8 -*-
"""¿Qué variables anticipaban los desplomes? Comparación en dos épocas independientes."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

S = pd.read_parquet('estudio_diario.parquet')
VAR = [c for c in S.columns if c[:2] in ('t_', 'd_', 'm_', 'c_')]
EPOCAS = {'A 2017-21': ('2017-08-17', '2021-12-31'), 'B 2022-26': ('2022-01-01', '2026-08-28'), 'C 2024-26': ('2024-01-01', '2026-08-28')}

def auc(x, y):
    m = x.notna() & y.notna()
    if m.sum() < 150 or y[m].nunique() < 2: return np.nan
    return roc_auc_score(y[m], x[m])

def tabla(lbl):
    filas = []
    for v in VAR:
        f = {'variable': v}
        for e, (a, b) in EPOCAS.items():
            s = S.loc[a:b]
            f[e] = auc(s[v], s[lbl])
        filas.append(f)
    T = pd.DataFrame(filas).set_index('variable').round(2)
    T['coherente'] = ((T['A 2017-21'] - .5) * (T['B 2022-26'] - .5) > 0) & ((T['A 2017-21'] - .5).abs() >= .05) & ((T['B 2022-26'] - .5).abs() >= .05)
    T['fuerza'] = ((T[['A 2017-21', 'B 2022-26']] - .5).abs().min(axis=1)).round(2)
    return T.sort_values('fuerza', ascending=False)

for lbl in ['desplome_relvol', 'desplome', 'subidon_relvol']:
    T = tabla(lbl)
    T.to_csv(f'auc_{lbl}.csv')
    print(f'\n=== {lbl}: AUC (0,5 = no sirve; >0,5 = valor alto -> más probable; <0,5 = valor bajo -> más probable) ===')
    print(T.to_string())
