# -*- coding: utf-8 -*-
"""ETH/BTC: zonas de pivote diarias + confirmación en velas de 4 h o 12 h (15-oct-2026).
Las dominancias no tienen velas de 4 h antes de 2026, por eso solo ETH/BTC (Binance, desde 2017).
Toque de la zona en diario; después k velas intradía seguidas a favor (rebote) o k cierres al otro
lado (rotura). Si la confirmación llega a mitad del día d, se entra al cierre de ese mismo día d.
Se compara con la confirmación en velas diarias. Cada lado y modo por separado."""
import sys, os, itertools
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from rotacion_dominancia import simular, metricas, tramos
from soportes_resistencias import rentab
from sr_diario import zonas_por_dia

def senales_intradia(dd, ib, zonas, lado, modo, tol, k):
    c, hi, lo = dd.cierre.values, dd.maximo.values, dd.minimo.values
    s = 1 if lado == 'soporte' else -1
    ic, it = ib.cierre.values, ib.index.values
    out, i = [], 25
    while i < len(dd) - 1:
        hecho = False
        for L in zonas[i]:
            if not ((c[i - 5:i] - L) * s > 3 * tol * L).all(): continue
            if modo == 'rebote':
                toque = (lo[i] <= L * (1 + tol)) if s == 1 else (hi[i] >= L * (1 - tol))
                if not toque: continue
            else:
                toque = (c[i] - L) * s < 0 or ((lo[i] - L) * s < 0 if s == 1 else (hi[i] - L) * s < 0)
                if not toque: continue
            ini = np.searchsorted(it, np.datetime64(dd.index[i]))           # velas intradía desde el día del toque
            fin = np.searchsorted(it, np.datetime64(dd.index[min(i + 10, len(dd) - 1)]))
            seguidas = 0
            for j in range(max(ini, 1), fin):
                if modo == 'rebote':
                    if (ic[j] - L) * s < -2 * tol * L: break
                    seguidas = seguidas + 1 if (ic[j] - ic[j - 1]) * s > 0 else 0
                else:
                    seguidas = seguidas + 1 if (ic[j] - L) * s < -tol * L else 0
                if seguidas >= k:
                    dia = pd.Timestamp(it[j]).normalize(); out.append((dia, L)); hecho = True; break
            if hecho: break
        i += 10 if hecho else 1
    return out

if __name__ == '__main__':
    R = rentab(); A, B = 'ETH', 'BTC'
    dd = velas('ETH_BTC', '1d'); dd = dd[dd.index >= '2016-01-01']
    h4 = velas('ETH_BTC', '4h'); h12 = h4.resample('12h').agg({'apertura': 'first', 'maximo': 'max', 'minimo': 'min', 'cierre': 'last'}).dropna()
    marcos = {'4h': h4, '12h': h12, '1d': dd}
    idx = R['BTC'].dropna().index; idx = idx[idx >= '2018-01-01']
    rA, rB = R[A].reindex(idx).fillna(0), R[B].reindex(idx).fillna(0)
    base, _ = simular(rA, rB, pd.Series(0.5, idx)); mb = metricas(base); tb = tramos(base)
    filas = []
    for n, tol, mt in itertools.product((3, 5), (0.015, 0.025), (2, 3)):
        zonas = zonas_por_dia(dd, n, tol, mt)
        for marco, ib in marcos.items():
            for lado, modo, k in itertools.product(('soporte', 'resistencia'), ('rebote', 'rotura'), (1, 2, 3, 6)):
                sig = [x for x in senales_intradia(dd, ib, zonas, lado, modo, tol, k) if x[0] >= pd.Timestamp('2018-01-01')]
                s = 1 if lado == 'soporte' else -1
                objetivo = 1.0 if (modo == 'rebote') == (s == 1) else 0.0
                # intradía: se entra al cierre del mismo día -> peso en d-1 ; diario: cierre siguiente -> peso en d
                desfase = pd.Timedelta(days=1) if marco != '1d' else pd.Timedelta(0)
                sd = {d - desfase: L for d, L in sig}
                for H in (2, 4, 8):
                    peso = pd.Series(0.5, idx); cur, fin, L = 0.5, None, None
                    for d in idx:
                        if d in sd: cur, fin, L = objetivo, d + pd.Timedelta(weeks=H), sd[d]
                        elif fin is not None:
                            cd = dd.cierre.get(d); contra = s if modo == 'rebote' else -s
                            if d >= fin or (cd is not None and (cd - L) * contra < -2 * tol * L): cur, fin = 0.5, None
                        peso.loc[d] = cur
                    eq, _ = simular(rA, rB, peso); m = metricas(eq); t = tramos(eq)
                    filas.append(dict(marco=marco, lado=lado, modo=modo, n=n, tol=tol, mt=mt, k=k, H=H, senales=len(sig),
                                      total=m['total'], mdd=m['mdd'], ratio=m['ratio'], base_ratio=mb['ratio'],
                                      ambos=all(t[x] > tb[x] for x in t)))
    df = pd.DataFrame(filas); df['mejora'] = df.ratio > df.base_ratio
    df.to_csv(os.path.join(AQUI, 'eth_btc_intradia.csv'), index=False)
    pd.set_option('display.width', 250)
    print(df.groupby(['lado', 'modo', 'marco']).agg(senales=('senales', 'median'), ratio_med=('ratio', 'median'),
          base=('base_ratio', 'first'), pct_mejora=('mejora', 'mean'), pct_ambos=('ambos', 'mean')).round(2).to_string())
