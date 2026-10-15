# -*- coding: utf-8 -*-
"""Soportes en gráficas de altcoins, con y sin el tramo bajista de 2022 (15-oct-2026).
Zonas de pivote diarias (sin mirar el futuro) y toque de soporte con k velas diarias de confirmación.
Para cada toque: ¿sube 20 días después?, ¿rompe el soporte? Se compara con una fecha cualquiera.
'sin_bajista_2022' quita los toques entre el 10-nov-2021 (máximo) y el 31-dic-2022."""
import sys, os, itertools
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from sr_diario import zonas_por_dia, senales

GRAFICAS = ['others_fuera_top10', 'total3_sin_btc_eth', 'ETH', 'BNB', 'XRP', 'ADA', 'LINK', 'SOL']
BAJ = (pd.Timestamp('2021-11-10'), pd.Timestamp('2022-12-31'))
H = 20

def fuera_bajista(d): return not (BAJ[0] <= d <= BAJ[1])

filas = []
for g in GRAFICAS:
    dd = velas(g, '1d'); dd = dd[dd.index >= '2016-01-01']; c = dd.cierre
    fwd = c.shift(-H) / c - 1
    minf = c[::-1].rolling(H, min_periods=1).min()[::-1].shift(-1)
    ref = fwd['2018':].dropna()
    for n, tol, mt in itertools.product((3, 5), (0.015, 0.025), (2, 3)):
        zonas = zonas_por_dia(dd, n, tol, mt)
        for k in (0, 1, 2, 3):
            sig = [(d, L) for d, L, _ in senales(dd, zonas, 'soporte', 'rebote', tol, k) if d >= pd.Timestamp('2018-01-01')]
            for periodo in ('todo', 'sin_bajista_2022'):
                s = [(d, L) for d, L in sig if periodo == 'todo' or fuera_bajista(d)]
                s = [(d, L) for d, L in s if not np.isnan(fwd.get(d, np.nan))]
                r = ref if periodo == 'todo' else ref[[fuera_bajista(d) for d in ref.index]]
                if not s: continue
                rets = np.array([fwd[d] for d, _ in s]); rotos = np.array([minf[d] < L * (1 - 2 * tol) for d, L in s])
                filas.append(dict(grafica=g, periodo=periodo, n_piv=n, tol=tol, mt=mt, k=k, toques=len(s),
                                  sube=float((rets > 0).mean()), sube_azar=float((r > 0).mean()),
                                  ret_med=float(np.median(rets)), ret_med_azar=float(r.median()),
                                  rompe=float(rotos.mean())))
df = pd.DataFrame(filas); df.to_csv(os.path.join(AQUI, 'soportes_alts.csv'), index=False)
df['ventaja'] = df.sube - df.sube_azar
pd.set_option('display.width', 250)
print(df.groupby(['grafica', 'periodo']).agg(toques=('toques', 'median'), sube=('sube', 'median'), azar=('sube_azar', 'first'),
      ventaja=('ventaja', 'median'), pct_combos_mejor=('ventaja', lambda v: (v > 0).mean()), rompe=('rompe', 'median'),
      ret_med=('ret_med', 'median'), ret_azar=('ret_med_azar', 'first')).round(3).to_string())
print('\nPor confirmación k (sin bajista 2022, todas las gráficas):')
d2 = df[df.periodo == 'sin_bajista_2022']
print(d2.groupby('k').agg(ventaja=('ventaja', 'median'), pct_mejor=('ventaja', lambda v: (v > 0).mean()), rompe=('rompe', 'median')).round(3).to_string())
