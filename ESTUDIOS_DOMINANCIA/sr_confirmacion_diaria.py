# -*- coding: utf-8 -*-
"""Tesis de Óscar con confirmación diaria (15-oct-2026).
Zonas de pivote = giros semanales confirmados (sin mirar el futuro), agrupados.
1) Toque: el mínimo (máximo) diario entra en la zona de soporte (resistencia) viniendo de lejos.
2) Confirmación: en los 10 días siguientes, un cierre diario por encima del máximo del día del toque
   (por debajo del mínimo, en resistencia) sin haber roto la zona antes.
3) Se rota al cierre siguiente; se sale a 50/50 si se rompe la zona o pasan H semanas.
Cada lado por separado."""
import sys, os
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from rotacion_dominancia import simular, metricas, tramos
from soportes_resistencias import DIBUJADOS, PARES, giros, niveles_en, rentab

def senales(dd, w, lado, tol, mt):
    piv = giros(w); out = []; s = 1 if lado == 'soporte' else -1
    semanas = list(w.index); j = 0; niveles = []
    i = 20
    while i < len(dd) - 1:
        d = dd.index[i]
        while j < len(semanas) and semanas[j] + pd.Timedelta(days=7) <= d:
            niveles = niveles_en(semanas[j], piv, tol, mt); j += 1
        lo, hi, pc = dd.minimo.iloc[i], dd.maximo.iloc[i], dd.cierre.iloc[i - 5:i].values
        hecho = False
        for L in niveles:
            if s == 1: toque = (pc > L * (1 + 3 * tol)).all() and lo <= L * (1 + tol)
            else:      toque = (pc < L * (1 - 3 * tol)).all() and hi >= L * (1 - tol)
            if not toque: continue
            ref = hi if s == 1 else lo
            for k in range(i + 1, min(i + 11, len(dd))):
                c = dd.cierre.iloc[k]
                if (c - L) * s < -2 * tol * L: break
                if (c - ref) * s > 0: out.append((dd.index[k], L)); hecho = True; break
            if hecho: break
        i += 10 if hecho else 1
    return out

R = rentab(); filas = []
for activo in DIBUJADOS:
    w = velas(activo, '1w'); w = w[w.index >= '2016-01-01']
    dd = velas(activo, '1d'); dd = dd[dd.index >= '2016-01-01']
    A, B, _ = PARES[activo]
    idx = R['BTC'].dropna().index; idx = idx[idx >= '2018-01-01']
    rA, rB = R[A].reindex(idx).fillna(0), R[B].reindex(idx).fillna(0)
    base, _ = simular(rA, rB, pd.Series(0.5, idx)); mb = metricas(base); tb = tramos(base)
    for tol in (0.015, 0.025):
        for mt in (2, 3):
            for lado in ('soporte', 'resistencia'):
                sig = [x for x in senales(dd, w, lado, tol, mt) if x[0] >= pd.Timestamp('2018-01-01')]
                sd = dict(sig); s = 1 if lado == 'soporte' else -1
                for H in (4, 8, 13):
                    peso = pd.Series(0.5, idx); cur, fin, L = 0.5, None, None
                    for d in idx:
                        if d in sd: cur, fin, L = (1.0 if s == 1 else 0.0), d + pd.Timedelta(weeks=H), sd[d]
                        elif fin is not None and d in dd.index:
                            if d >= fin or (dd.cierre.loc[d] - L) * s < -2 * tol * L: cur, fin = 0.5, None
                        peso.loc[d] = cur
                    eq, _ = simular(rA, rB, peso); m = metricas(eq); t = tramos(eq)
                    filas.append(dict(activo=activo, lado=lado, tol=tol, mt=mt, H=H, n=len(sig),
                                      total=m['total'], mdd=m['mdd'], ratio=m['ratio'], base_ratio=mb['ratio'],
                                      ambos_tramos=all(t[x] > tb[x] for x in t)))
df = pd.DataFrame(filas); df.to_csv(os.path.join(AQUI, 'sr_confirmacion_diaria.csv'), index=False)
g = df.groupby(['activo', 'lado']).agg(senales_medias=('n', 'mean'), ratio_mediano=('ratio', 'median'),
        base=('base_ratio', 'first'), pct_mejora=('ratio', lambda r: (r > df.loc[r.index, 'base_ratio']).mean()),
        pct_ambos_tramos=('ambos_tramos', 'mean'), total_mediano=('total', 'median'))
print(g.round(2).to_string())
