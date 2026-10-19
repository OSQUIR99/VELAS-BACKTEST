# -*- coding: utf-8 -*-
"""Tercera fase (19-oct-2026): pruebas duras de la regla D (TOTAL2 × 1,5 vigente + USDT.D sube × 1,5 + ETH/BTC sube × 0,5).
1. Fuera de muestra: las dos variables se eligieron mirando todo. Aquí: ¿se habrían elegido solo con 2018-22? y ¿qué dan en 2023-26?
2. Moneda a moneda y dejando fuera una moneda cada vez.
3. Remuestreo por bloques mensuales (2.000 veces): intervalo de la mejora del R por unidad de caída de D frente a A.
4. Placebo: cambiar USDT.D y ETH/BTC por estados desplazados al azar (mismo porcentaje de días "sí") 500 veces:
   ¿cuántas veces una regla al azar mejora tanto como D?
"""
import sys, os
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
X = pd.read_csv(os.path.join(AQUI, 'montaje_dominancias_ops2.csv'), parse_dates=['entrada', 'salida'])
rng = np.random.default_rng(7)

def ratio(R, w, idx=None):
    if idx is not None: R, w, sal = R[idx], w[idx], X.salida.values[idx]
    else: sal = X.salida.values
    o = np.argsort(sal); eq = np.cumsum((R * w)[o]); dd = (eq - np.maximum.accumulate(np.r_[0, eq])[1:]).min()
    return eq[-1] / abs(dd) if dd < 0 else np.nan, eq[-1], dd
R = X.R.values
A = np.where(X.T2_bajo_m20 == 1, 1.5, 1.0)
def D_(u, e): return A * np.where(u == 1, 1.5, 1) * np.where(e == 1, 0.5, 1)
D = D_(X.USDT_sube.values, X.ETHBTC_sube.values)

print('1) Fuera de muestra')
ins, oos = (X.entrada < '2023').values, (X.entrada >= '2023').values
for var in ['USDT_sube', 'ETHBTC_sube']:
    for nom, m in (('2018-22', ins), ('2023-26', oos)):
        s, n_ = R[m & (X[var].values == 1)], R[m & (X[var].values == 0)]
        print(f'   {var:12s} {nom}: sí {s.mean():+.2f} (n={len(s)})  no {n_.mean():+.2f} (n={len(n_)})  dif {s.mean() - n_.mean():+.2f}')
for nom, m in (('2018-22', ins), ('2023-26', oos)):
    ra, Ra, da = ratio(R, A, np.where(m)[0]); rd, Rd, dd_ = ratio(R, D, np.where(m)[0])
    print(f'   {nom}: A ratio {ra:.2f} (R {Ra:.0f}, caída {da:.1f})  ·  D ratio {rd:.2f} (R {Rd:.0f}, caída {dd_:.1f})')

print('\n2) Moneda a moneda (R medio por unidad de tamaño y ratio)')
for mon in sorted(X.moneda.unique()):
    m = np.where(X.moneda.values == mon)[0]
    ra = ratio(R, A, m)[0]; rd = ratio(R, D, m)[0]
    print(f'   {mon:5s} n={len(m):3d}  A ratio {ra:5.2f}  D ratio {rd:5.2f}  {"mejora" if rd > ra else "EMPEORA"}')
for mon in sorted(X.moneda.unique()):
    m = np.where(X.moneda.values != mon)[0]
    print(f'   sin {mon:5s}: A {ratio(R, A, m)[0]:.2f}  D {ratio(R, D, m)[0]:.2f}')

print('\n3) Remuestreo por bloques mensuales (mejora del ratio D − A)')
mes = X.entrada.dt.to_period('M').values; meses = np.unique(mes); por_mes = {k: np.where(mes == k)[0] for k in meses}
difs = []
for _ in range(2000):
    idx = np.concatenate([por_mes[k] for k in rng.choice(meses, len(meses))])
    difs.append(ratio(R, D, idx)[0] - ratio(R, A, idx)[0])
difs = np.array(difs)
print(f'   mediana {np.median(difs):+.2f}  intervalo 90 % [{np.quantile(difs, .05):+.2f}; {np.quantile(difs, .95):+.2f}]  mejora en el {np.mean(difs > 0):.0%} de las muestras')

print('\n4) Placebo: estados desplazados al azar en el tiempo')
real = ratio(R, D)[0] - ratio(R, A)[0]
u, e = X.USDT_sube.values, X.ETHBTC_sube.values
ok = 0
for _ in range(500):
    k1, k2 = rng.integers(30, len(X) - 30, 2)
    if ratio(R, D_(np.roll(u, k1), np.roll(e, k2)))[0] - ratio(R, A)[0] >= real: ok += 1
print(f'   mejora real {real:+.2f}; reglas al azar que mejoran igual o más: {ok} de 500 ({ok / 5:.1f} %)')
