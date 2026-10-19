# -*- coding: utf-8 -*-
"""Segunda fase (19-oct-2026): ¿lo que aportan las dominancias es NUEVO o ya lo da la regla de TOTAL2 (documento 06)?

Regla vigente (documento 06, 2.5): TOTAL2 (capitalización sin BTC) cierra BAJO su media de 20 días → tamaño × 1,5.
TOTAL2 aquí = capitalización total × (1 − dominancia de BTC / 100) (TradingView CRYPTOCAP, mismas velas del repositorio).

1. Dentro de cada estado de TOTAL2, ¿siguen separando la dominancia de USDT subiendo y ETH/BTC subiendo?
2. Robustez de USDT.D: media de 10-50 días y pendiente a 3-10 días.
3. Cartera: R por unidad de caída (R total ÷ peor caída, operaciones en orden de salida) con:
   base (× 1,5 TOTAL2), + × 1,5 con USDT.D subiendo, + × 0,5 con ETH/BTC subiendo, y combinaciones; por épocas.
"""
import sys, os, itertools
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas

X = pd.read_csv(os.path.join(AQUI, 'montaje_dominancias_ops.csv'), parse_dates=['entrada', 'salida'])
c = lambda a: velas(a, '1d').cierre
tot, btcd, usdt, eb = c('capitalizacion_total'), c('dominancia_btc'), c('dominancia_usdt'), c('ETH_BTC')
t2 = (tot * (1 - btcd / 100)).dropna()
dia = X.entrada.dt.floor('D') - pd.Timedelta(days=1)
def en(s): return s.reindex(dia).values
X['T2_bajo_m20'] = en((t2 < t2.rolling(20).mean()).astype(float))
def pend(s, n, k):
    m = s.rolling(n).mean(); return (m > m.shift(k)).astype(float)
X['USDT_sube'] = en(pend(usdt, 20, 5)); X['ETHBTC_sube'] = en(pend(eb, 20, 5))
X = X.dropna(subset=['T2_bajo_m20', 'USDT_sube', 'ETHBTC_sube'])
def tt(a, b): return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b)) if min(len(a), len(b)) > 4 else np.nan

print('1) Dentro de cada estado de TOTAL2 (regla vigente)')
print('   TOTAL2 bajo su media 20:', f"{X[X.T2_bajo_m20 == 1].R.mean():+.2f} R (n={int(X.T2_bajo_m20.sum())})",
      ' sobre:', f"{X[X.T2_bajo_m20 == 0].R.mean():+.2f} R (n={int((X.T2_bajo_m20 == 0).sum())})")
print('   correlación USDT.D sube ~ TOTAL2 bajo:', round(X[['USDT_sube', 'T2_bajo_m20']].corr().iloc[0, 1], 2),
      '| ETH/BTC sube ~ TOTAL2 bajo:', round(X[['ETHBTC_sube', 'T2_bajo_m20']].corr().iloc[0, 1], 2))
for var in ['USDT_sube', 'ETHBTC_sube']:
    for est in (1, 0):
        G = X[X.T2_bajo_m20 == est]
        si, no = G[G[var] == 1].R, G[G[var] == 0].R
        eps = []
        for a, b in (('2018', '2022'), ('2022', '2027'), ('2024', '2027')):
            E = G[(G.entrada >= a) & (G.entrada < b)]
            eps.append(round(E[E[var] == 1].R.mean() - E[E[var] == 0].R.mean(), 2))
        print(f'   {var:12s} con TOTAL2 {"BAJO " if est else "SOBRE"} media: sí {si.mean():+.2f} (n={len(si)}) no {no.mean():+.2f} (n={len(no)})'
              f'  dif {si.mean() - no.mean():+.2f}  t {tt(si, no):.2f}  por épocas 18-21/22-26/24-26 {eps}')

print('\n2) Robustez de «USDT.D media sube» (diferencia de R y t; todas las operaciones)')
filas = []
for n, k in itertools.product((10, 15, 20, 30, 50), (3, 5, 10)):
    v = en(pend(usdt, n, k)); m = ~np.isnan(v)
    si, no = X.R[m & (v == 1)], X.R[m & (v == 0)]
    e = [X.R[m & (v == 1) & (X.entrada >= a) & (X.entrada < b)].mean() - X.R[m & (v == 0) & (X.entrada >= a) & (X.entrada < b)].mean()
         for a, b in (('2018', '2022'), ('2022', '2027'), ('2024', '2027'))]
    filas.append({'media': n, 'pend': k, 'dif': si.mean() - no.mean(), 't': tt(si, no), 'n_si': len(si), 'positiva_3_epocas': all(x > 0 for x in e)})
print(pd.DataFrame(filas).round(2).to_string(index=False))

print('\n3) Cartera (todas las monedas, R por operación × tamaño; orden de salida)')
def cartera(w, desde='2018', hasta='2027'):
    m = (X.entrada >= desde) & (X.entrada < hasta)
    r = (X.R * w)[m].values[np.argsort(X.salida[m].values)]
    eq = np.cumsum(r); dd = (eq - np.maximum.accumulate(np.r_[0, eq])[1:]).min()
    return eq[-1], dd, eq[-1] / abs(dd) if dd < 0 else np.nan
base = np.where(X.T2_bajo_m20 == 1, 1.5, 1.0)
reglas = {
    'A · vigente (TOTAL2 × 1,5)': base,
    'B · + USDT.D sube × 1,5': base * np.where(X.USDT_sube == 1, 1.5, 1),
    'C · + ETH/BTC sube × 0,5': base * np.where(X.ETHBTC_sube == 1, 0.5, 1),
    'D · B + C': base * np.where(X.USDT_sube == 1, 1.5, 1) * np.where(X.ETHBTC_sube == 1, 0.5, 1),
    'E · solo USDT.D (sin TOTAL2)': np.where(X.USDT_sube == 1, 1.5, 1.0),
    'F · sin nada (todo × 1)': np.ones(len(X)),
}
out = []
for nom, w in reglas.items():
    f = {'regla': nom}
    for ep, a, b in (('todo', '2018', '2027'), ('18-21', '2018', '2022'), ('22-26', '2022', '2027'), ('24-26', '2024', '2027')):
        R, dd, ratio = cartera(w, a, b)
        f[f'R_{ep}'], f[f'caida_{ep}'], f[f'ratio_{ep}'] = R, dd, ratio
    f['R_medio_por_unidad_tamaño'] = (X.R * w).sum() / w.sum()
    out.append(f)
O = pd.DataFrame(out); pd.set_option('display.width', 250)
print(O.round(2).to_string(index=False))
O.to_csv(os.path.join(AQUI, 'montaje_dominancias_cartera.csv'), index=False)
X.to_csv(os.path.join(AQUI, 'montaje_dominancias_ops2.csv'), index=False)
