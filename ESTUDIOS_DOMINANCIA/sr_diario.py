# -*- coding: utf-8 -*-
"""Zonas de pivote en DIARIO + confirmación con velas diarias (15-oct-2026, petición de Óscar).

Zonas: giros diarios (máximo/mínimo con n días a cada lado), solo los ya confirmados en esa fecha,
agrupados si están a menos de 'tol'; cuentan si tienen >= mt giros.
Modo 'rebote': toque de la zona viniendo de lejos y luego k velas diarias que confirman el giro
  (k cierres seguidos a favor; k=0 = entrar al cierre del toque). Soporte -> A, resistencia -> B.
Modo 'rotura': cierre que atraviesa la zona más de tol, confirmado por k cierres más del otro lado.
  Rotura de soporte -> B, rotura de resistencia -> A.
Se opera al cierre siguiente; se mantiene H semanas o hasta invalidación; después 50/50.
Cada lado y cada modo por separado. Se mira la rejilla entera, no la mejor fila.
"""
import sys, os, itertools
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from rotacion_dominancia import simular, metricas, tramos
from soportes_resistencias import PARES, rentab

def zonas_por_dia(dd, n, tol, mt):
    """Para cada día, lista de zonas conocidas (recalculada solo cuando se confirma un giro)."""
    hi, lo = dd.maximo.values, dd.minimo.values
    nuevos = {}
    for i in range(n, len(dd) - n):
        for v, es in ((hi[i], hi[i] == hi[i - n:i + n + 1].max()), (lo[i], lo[i] == lo[i - n:i + n + 1].min())):
            if es: nuevos.setdefault(i + n, []).append(np.log(v))
    piv, zonas, out = [], [], []
    for i in range(len(dd)):
        if i in nuevos:
            piv = sorted(piv + nuevos[i]); grupos, g = [], []
            for v in piv:
                if g and v - g[0] > tol: grupos.append(g); g = []
                g.append(v)
            if g: grupos.append(g)
            zonas = [float(np.exp(np.mean(x))) for x in grupos if len(x) >= mt]
        out.append(zonas)
    return out

def senales(dd, zonas, lado, modo, tol, k):
    c, hi, lo = dd.cierre.values, dd.maximo.values, dd.minimo.values
    s = 1 if lado == 'soporte' else -1
    out, i = [], 25
    while i < len(dd) - 1:
        hecho = False
        for L in zonas[i]:
            lejos = ((c[i - 5:i] - L) * s > 3 * tol * L).all()
            if not lejos: continue
            if modo == 'rebote':
                toque = (lo[i] <= L * (1 + tol)) if s == 1 else (hi[i] >= L * (1 - tol))
                if not toque or (c[i] - L) * s < -tol * L: continue
                if k == 0: out.append((dd.index[i], L, i)); hecho = True; break
                seguidas, j = 0, i + 1
                while j < min(i + 11, len(dd)):
                    if (c[j] - L) * s < -2 * tol * L: break
                    seguidas = seguidas + 1 if (c[j] - c[j - 1]) * s > 0 else 0
                    if seguidas >= k: out.append((dd.index[j], L, j)); hecho = True; break
                    j += 1
            else:  # rotura: viene de lejos y en los 10 días siguientes cierra al otro lado
                for j in range(i, min(i + 11, len(dd) - k)):
                    if all((c[j + q] - L) * s < -tol * L for q in range(k + 1)):
                        out.append((dd.index[j + k], L, j + k)); hecho = True; break
            if hecho: break
        i += 10 if hecho else 1
    return out

def correr(activos, sufijo=''):
    R = rentab(); filas = []
    for activo in activos:
        dd = velas(activo, '1d'); dd = dd[dd.index >= '2016-01-01']
        A, B, _ = PARES[activo]
        idx = R['BTC'].dropna().index; idx = idx[idx >= '2018-01-01']
        rA, rB = R[A].reindex(idx).fillna(0), R[B].reindex(idx).fillna(0)
        base, _ = simular(rA, rB, pd.Series(0.5, idx)); mb = metricas(base); tb = tramos(base)
        pos = {d: i for i, d in enumerate(dd.index)}
        for n, tol, mt in itertools.product((3, 5), (0.015, 0.025), (2, 3)):
            zonas = zonas_por_dia(dd, n, tol, mt)
            for lado, modo, k in itertools.product(('soporte', 'resistencia'), ('rebote', 'rotura'), (0, 1, 2, 3)):
                if modo == 'rotura' and k == 0: continue
                sig = [x for x in senales(dd, zonas, lado, modo, tol, k) if x[0] >= pd.Timestamp('2018-01-01')]
                s = 1 if lado == 'soporte' else -1
                # peso: rebote en soporte o rotura de resistencia -> A (1.0)
                objetivo = 1.0 if (modo == 'rebote') == (s == 1) else 0.0
                sd = {d: L for d, L, _ in sig}
                for H in (2, 4, 8):
                    peso = pd.Series(0.5, idx); cur, fin, L = 0.5, None, None
                    for d in idx:
                        if d in sd: cur, fin, L = objetivo, d + pd.Timedelta(weeks=H), sd[d]
                        elif fin is not None:
                            cd = dd.cierre.get(d)
                            # invalidación: el precio vuelve más de 2·tol contra la apuesta
                            contra = (s if modo == 'rebote' else -s)
                            if d >= fin or (cd is not None and (cd - L) * contra < -2 * tol * L): cur, fin = 0.5, None
                        peso.loc[d] = cur
                    eq, _ = simular(rA, rB, peso); m = metricas(eq); t = tramos(eq)
                    filas.append(dict(activo=activo, lado=lado, modo=modo, n=n, tol=tol, mt=mt, k=k, H=H,
                                      senales=len(sig), total=m['total'], mdd=m['mdd'], ratio=m['ratio'],
                                      base_ratio=mb['ratio'], base_total=mb['total'],
                                      t1=t.get('2018-21', np.nan) - tb.get('2018-21', 0),
                                      t2=t.get('2022-26', np.nan) - tb.get('2022-26', 0)))
    df = pd.DataFrame(filas)
    df['mejora'] = df.ratio > df.base_ratio
    df['ambos'] = (df.t1 > 0) & (df.t2 > 0)
    df.to_csv(os.path.join(AQUI, f'sr_diario{sufijo}.csv'), index=False)
    return df

if __name__ == '__main__':
    df = correr(['ETH_BTC', 'dominancia_btc', 'dominancia_usdt', 'others_fuera_top10'])
    pd.set_option('display.width', 250)
    g = df.groupby(['activo', 'lado', 'modo']).agg(combos=('ratio', 'size'), senales=('senales', 'median'),
          ratio_med=('ratio', 'median'), base=('base_ratio', 'first'), pct_mejora=('mejora', 'mean'),
          pct_ambos=('ambos', 'mean'))
    print(g.round(2).to_string())
    print('\nPor nº de velas de confirmación (k):')
    print(df.groupby(['activo', 'k']).agg(senales=('senales', 'median'), pct_mejora=('mejora', 'mean'), pct_ambos=('ambos', 'mean')).round(2).to_string())
