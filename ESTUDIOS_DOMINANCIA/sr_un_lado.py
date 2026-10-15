# -*- coding: utf-8 -*-
"""Cada lado por separado: solo soportes o solo resistencias. Tras el toque se mantiene la
rotación H semanas o hasta que se rompa el nivel; después vuelve a 50/50."""
import sys, os
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from rotacion_dominancia import simular, metricas, tramos
from soportes_resistencias import DIBUJADOS, PARES, eventos, rentab

R = rentab(); filas = []
for activo, fijos in DIBUJADOS.items():
    w = velas(activo, '1w'); w = w[w.index >= '2016-01-01']; A, B, _ = PARES[activo]
    idx = R['BTC'].dropna().index; idx = idx[idx >= '2018-01-01']
    rA, rB = R[A].reindex(idx).fillna(0), R[B].reindex(idx).fillna(0)
    base, _ = simular(rA, rB, pd.Series(0.5, idx)); mb = metricas(base); tb = tramos(base)
    for tipo, tol, mt in [('objetivos', t, m) for t in (0.015, 0.025) for m in (2, 3)] + [('dibujados', 0.015, 0)]:
        evs = [e for e in eventos(w, tipo, tol, mt, fijos) if e[0] >= pd.Timestamp('2018-01-01')]
        for lado in ('soporte', 'resistencia'):
            for H in (4, 8, 13):
                peso = pd.Series(np.nan, idx); cur, fin, L = 0.5, None, None
                ev = {d: Lv for d, l, Lv in evs if l == lado}
                for i, d in enumerate(w.index):
                    if d in ev: cur, fin, L = (1.0 if lado == 'soporte' else 0.0), i + H, ev[d]
                    elif fin is not None:
                        s = 1 if lado == 'soporte' else -1
                        if i >= fin or (w.cierre.iloc[i] - L) * s < -2 * tol * L: cur, fin = 0.5, None
                    k = d + pd.Timedelta(days=6)
                    if k in peso.index: peso.loc[k] = cur
                eq, _ = simular(rA, rB, peso.ffill().fillna(0.5)); m = metricas(eq); t = tramos(eq)
                filas.append(dict(activo=activo, lado=lado, niveles=tipo, tol=tol, mt=mt, H=H,
                                  n=sum(1 for e in evs if e[1] == lado), total=m['total'], mdd=m['mdd'],
                                  ratio=m['ratio'], base_ratio=mb['ratio'],
                                  ambos_tramos=all(t[x] > tb[x] for x in t)))
df = pd.DataFrame(filas); df.to_csv(os.path.join(AQUI, 'sr_un_lado.csv'), index=False)
g = df[df.niveles == 'objetivos'].groupby(['activo', 'lado']).agg(
    combos=('ratio', 'size'), ratio_mediano=('ratio', 'median'), base=('base_ratio', 'first'),
    pct_mejora=('ratio', lambda r: (r > df.loc[r.index, 'base_ratio']).mean()),
    pct_ambos_tramos=('ambos_tramos', 'mean'))
print(g.round(2).to_string())
d = df[df.niveles == 'dibujados'].groupby(['activo', 'lado']).agg(ratio_mediano=('ratio', 'median'), base=('base_ratio', 'first'), pct_ambos=('ambos_tramos', 'mean'))
print('\nDIBUJADOS (con ventaja de mirar el pasado)'); print(d.round(2).to_string())
