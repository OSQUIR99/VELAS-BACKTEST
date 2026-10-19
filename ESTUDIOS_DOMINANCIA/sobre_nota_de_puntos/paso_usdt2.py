import pandas as pd, numpy as np
exec(open('paso_usdt.py').read().split("V = {")[0])
t2 = M.t2.astype(float).values
V = {'0 · nota': mapa(pts0),
     'C · ETH −1 con ETH/BTC subiendo': mapa(pts0 - (eth & (M.ethbtc == 1))),
     'E · USDT.D +1 solo sin TOTAL2 (no contar dos veces)': mapa(pts0 + M.usdt * (1 - t2)),
     'E2 · igual, 2 días de retraso': mapa(pts0 + M.usdt2 * (1 - t2)),
     'F · E + C': mapa(pts0 + M.usdt * (1 - t2) - (eth & (M.ethbtc == 1))),
     'F2 · E2 + C': mapa(pts0 + M.usdt2 * (1 - t2) - (eth & (M.ethbtc == 1)))}
rows = []
for k, wm in V.items():
    w = peso(np.asarray(wm, float)); p = mtm(X, w); r = {'variante': k}
    for nm, a, b in PERIODOS:
        Rt, dd, ra = medir(p, a, b); r[nm] = f'{Rt:+.0f}/{dd:.1f}→{ra:.2f}'
    for e0, e1 in EPOCAS_C:
        _, _, ra = medir(p, e0, e1); r[e0] = round(ra, 2)
    for a in P.CR:
        s = X.activo == a; q = mtm(X[s], w[s]); r[a] = round(medir(q)[2], 2)
    r['exp'] = round(w[X.pata == 'principal'].mean(), 2); rows.append(r)
R = pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv('/home/claude/work/paso_usdt2.csv', index=False)
# remuestreo por bloques mensuales de la mejora del ratio (todo) de E y C frente a 0, sobre P&L diario
rng = np.random.default_rng(7)
pp = {k: mtm(X, peso(np.asarray(V[k], float))) for k in ['0 · nota', 'C · ETH −1 con ETH/BTC subiendo', 'E · USDT.D +1 solo sin TOTAL2 (no contar dos veces)', 'F · E + C']}
D = pd.DataFrame(pp).fillna(0); D = D[D.index >= '2017-09-01']; mes = D.index.to_period('M'); meses = mes.unique()
def ratio(q):
    eq = q.cumsum(); dd = (eq - eq.cummax()).min(); return q.sum() / abs(dd)
res = {k: [] for k in list(pp)[1:]}
grupos = {m: D[mes == m] for m in meses}
for _ in range(1000):
    S = pd.concat([grupos[m] for m in rng.choice(meses, len(meses))], ignore_index=True)
    b0 = ratio(S.iloc[:, 0])
    for k in res: res[k].append(ratio(S[k]) - b0)
for k, v in res.items():
    v = np.array(v); print(f'{k}: mejora del ratio mediana {np.median(v):+.3f}, mejora en el {np.mean(v > 0):.0%} de las muestras')
