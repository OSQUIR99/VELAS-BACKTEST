"""19-oct: ¿USDT.D subiendo sigue aportando ENCIMA de la nota de puntos aprobada (doc. 17, punto 9)?
Variantes: nota tal cual; nota × 1,5 con USDT.D (lo aprobado en dominancias); USDT.D como +1 punto dentro de la nota;
ETH −1 punto con ETH/BTC subiendo. Caída valorada a diario (mtm). Señal: media 20 d más alta que hace 5 d, cierre diario anterior."""
import pandas as pd, numpy as np
import paso26lib as P
from motor import cargar
from mtm import *
from evaluar import EPOCAS_C
pd.set_option('display.width', 250)
X = P.construir()
M = X[X.pata == 'principal'].copy()
M['n'] = [int(((M.entrada < t) & (M.salida > t) & (M.activo != a)).sum()) for t, a in zip(M.entrada, M.activo)]
# pivote alto diario 5/5 confirmado; «recién roto» = cierre de la vela de señal por encima de él
def piv_serie(act):
    d = cargar(act, '1d'); dhi = d.maximo.values; ph = np.full(len(d), np.nan); last = np.nan
    for k in range(len(d)):
        j = k - 5
        if j >= 5 and dhi[j] > dhi[j - 5:j].max() and dhi[j] >= dhi[j + 1:k + 1].max(): last = dhi[j]
        ph[k] = last
    s = pd.Series(ph, index=d.index + pd.Timedelta('1D')); return s[~s.index.duplicated()]
def al(s, t): return s.reindex(s.index.union(pd.DatetimeIndex([t]))).ffill().loc[t]
def senal_media(nombre, n=20, k=5):
    c = cargar(nombre, '1d').cierre; m = c.rolling(n).mean(); r = (m > m.shift(k)); r.index = r.index + pd.Timedelta('1D'); return r[~r.index.duplicated()]
usdt, ebs = senal_media('dominancia_usdt'), senal_media('ETH_BTC')
usdt_lag2 = usdt.copy(); usdt_lag2.index = usdt_lag2.index + pd.Timedelta('2D')
pv = {a: piv_serie(a) for a in P.CR}
piv_roto, U, U2, EB = [], [], [], []
for _, t in M.iterrows():
    h_tc = t.señal + pd.Timedelta('4h')
    p = al(pv[t.activo], h_tc); cs = t.e  # aproximación: cierre de la vela de señal ≈ apertura de la entrada
    piv_roto.append(float(p == p and cs > p))
    U.append(float(bool(al(usdt, h_tc)))); U2.append(float(bool(al(usdt_lag2, h_tc)))); EB.append(float(bool(al(ebs, h_tc))))
M['piv_roto'], M['usdt'], M['usdt2'], M['ethbtc'] = piv_roto, U, U2, EB
pts0 = 2 * M.t2.astype(float) - M.grande.astype(float) - M.estirada.astype(float) - M.piv_roto - (M.n >= 3).astype(float)
def mapa(p): return np.select([p >= 2, p == 1, p == 0, p == -1], [1.5, 1.25, 1.0, 0.5], 0.25)
key = X.activo + X.señal.astype(str)
wbase = P.pesos({'prom': True, 'estirada': False}, X) / np.where(X.t2, 1.5, 1.0)  # promediado, sin TOTAL2 (va en la nota)
def peso(wmain):
    mp = dict(zip(key[M.index], wmain)); return pd.Series(wbase.values * key.map(mp).fillna(1.0).values, index=X.index).clip(0, 5)
eth = (M.activo == 'ETH').values
V = {'0 · nota de puntos (aprobada 20:58)': mapa(pts0),
     'A · nota × 1,5 con USDT.D subiendo': mapa(pts0) * np.where(M.usdt == 1, 1.5, 1),
     'B · USDT.D subiendo = +1 punto': mapa(pts0 + M.usdt),
     'B2 · igual, USDT.D con 2 días de retraso': mapa(pts0 + M.usdt2),
     'C · ETH −1 punto con ETH/BTC subiendo': mapa(pts0 - (eth & (M.ethbtc == 1))),
     'D · B + C': mapa(pts0 + M.usdt - (eth & (M.ethbtc == 1)))}
rows = []
for k, wm in V.items():
    w = peso(np.asarray(wm, float)); p = mtm(X, w); r = {'variante': k}
    for nm, a, b in PERIODOS:
        Rt, dd, ra = medir(p, a, b); r[nm] = f'{Rt:+.0f}/{dd:.1f}→{ra:.2f}'
    for e0, e1 in EPOCAS_C:
        _, _, ra = medir(p, e0, e1); r[e0] = round(ra, 2)
    r['exp'] = round(w[X.pata == 'principal'].mean(), 2); rows.append(r); print(r, flush=True)
R = pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv('/home/claude/work/paso_usdt.csv', index=False)
print('R medio por USDT.D dentro de cada nota:'); print(M.groupby([pts0.clip(-2, 2), M.usdt]).R.agg(['count', 'mean']).round(2).unstack().to_string())
for e in ['2023', '2024']:
    s = M.entrada >= e; print(e, 'USDT.D sí', round(M.R[s & (M.usdt == 1)].mean(), 2), (s & (M.usdt == 1)).sum(), 'no', round(M.R[s & (M.usdt == 0)].mean(), 2))
M.to_pickle('/home/claude/work/paso_usdt_M.pkl')
