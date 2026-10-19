import pandas as pd, numpy as np
exec(open('paso_usdt.py').read().split("V = {")[0])
import rasgos
cap = cargar('capitalizacion_total', '1d').cierre; dom = cargar('dominancia_btc', '1d').cierre
t2s = (cap * (1 - dom.reindex(cap.index).ffill() / 100)).dropna(); dist = t2s / t2s.rolling(20).mean() - 1
fr = ((dist >= 0) & (dist <= 0.06)); fr.index = fr.index + pd.Timedelta('1D'); fr = fr[~fr.index.duplicated()]
M['franja'] = [float(bool(al(fr, t.señal + pd.Timedelta('4h')))) if t.activo != 'LINK' else 0.0 for _, t in M.iterrows()]
F = np.where(M.franja == 1, 0.5, 1.0); t2 = M.t2.astype(float).values
V = {'0 · nota × franja (sistema de hoy)': mapa(pts0) * F,
     'A · + USDT.D × 1,5 (lo aprobado a las 20:47)': mapa(pts0) * F * np.where(M.usdt == 1, 1.5, 1),
     'C · + ETH −1 punto con ETH/BTC subiendo': mapa(pts0 - (eth & (M.ethbtc == 1))) * F,
     'E · + USDT.D +1 punto solo sin TOTAL2': mapa(pts0 + M.usdt * (1 - t2)) * F,
     'F · E + C': mapa(pts0 + M.usdt * (1 - t2) - (eth & (M.ethbtc == 1))) * F,
     'F2 · F con 2 días de retraso': mapa(pts0 + M.usdt2 * (1 - t2) - (eth & (M.ethbtc == 1))) * F}
rows = []
for k, wm in V.items():
    w = peso(np.asarray(wm, float)); p = mtm(X, w); r = {'variante': k}
    for nm, a, b in PERIODOS:
        Rt, dd, ra = medir(p, a, b); r[nm] = f'{Rt:+.0f}/{dd:.1f}→{ra:.2f}'
    for e0, e1 in EPOCAS_C:
        _, _, ra = medir(p, e0, e1); r[e0] = round(ra, 2)
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False)); pd.DataFrame(rows).to_csv('/home/claude/work/paso_usdt3.csv', index=False)
print('franja en', int(M.franja.sum()), 'de', len(M))
