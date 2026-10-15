# -*- coding: utf-8 -*-
"""Rotación con indicadores sobre las propias gráficas de dominancia (15-oct-2026).
Busca la ASIMETRÍA: cada señal se prueba usando solo el lado alcista, solo el bajista o ambos
(lo que no está activo = 50/50).

Señales sobre el cierre diario de la gráfica X (estado: +1 = X sube, -1 = X baja):
  cruce de medias (rápida/lenta), pendiente de una media, precio frente a su media,
  ruptura de rango (máximo/mínimo de N días, se mantiene hasta la ruptura contraria),
  RSI de 14 días a la contra (>70 baja, <30 sube, hasta volver a 50) y RSI a favor (>50 / <50).
Mapa: ETH/BTC sube -> ETH; BTC.D sube -> BTC; USDT.D sube -> liquidez; OTHERS sube -> alts.
"""
import sys, os
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from rotacion_dominancia import simular, metricas, tramos
from soportes_resistencias import rentab

# (activo comprado cuando X sube, activo comprado cuando X baja)
MAPA = {'ETH_BTC': ('ETH', 'BTC'), 'dominancia_btc': ('BTC', 'ALTS'),
        'dominancia_usdt': ('LIQ', 'BTC'), 'others_fuera_top10': ('ALTS', 'BTC')}

def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)

def estado_persistente(on_up, on_dn, off=None):
    s, cur = [], 0
    for u, d, o in zip(on_up, on_dn, off if off is not None else [None] * len(on_up)):
        if u: cur = 1
        elif d: cur = -1
        elif o is not None and o(cur): cur = 0
        s.append(cur)
    return np.array(s)

def senales(c):
    out = {}
    for f, s in ((10, 30), (20, 50), (50, 100), (50, 200)):
        out[f'cruce_medias_{f}_{s}'] = np.sign(c.rolling(f).mean() - c.rolling(s).mean())
    for n in (20, 50, 100):
        m = c.rolling(n).mean(); out[f'pendiente_media_{n}'] = np.sign(m - m.shift(5))
        out[f'precio_vs_media_{n}'] = np.sign(c - m)
    for n in (20, 55, 100):
        hi, lo = c.rolling(n).max().shift(1), c.rolling(n).min().shift(1)
        out[f'ruptura_rango_{n}'] = pd.Series(estado_persistente((c > hi).values, (c < lo).values), c.index)
    r = rsi(c).values
    st, cur = [], 0
    for v in r:
        if v > 70: cur = -1
        elif v < 30: cur = 1
        elif (cur == -1 and v < 50) or (cur == 1 and v > 50): cur = 0
        st.append(cur)
    out['rsi_a_la_contra'] = pd.Series(st, c.index)
    out['rsi_a_favor'] = np.sign(pd.Series(r, c.index) - 50)
    return {k: pd.Series(v, c.index).fillna(0) for k, v in out.items()}

if __name__ == '__main__':
    R = rentab(); filas = []
    for x, (Aup, Bdn) in MAPA.items():
        c = velas(x, '1d')['cierre']; c = c[c.index >= '2016-01-01']
        idx = R['BTC'].dropna().index; idx = idx[idx >= '2018-01-01']
        rA, rB = R[Aup].reindex(idx).fillna(0), R[Bdn].reindex(idx).fillna(0)
        base, _ = simular(rA, rB, pd.Series(0.5, idx)); mb = metricas(base); tb = tramos(base)
        for nombre, st in senales(c).items():
            st = st.reindex(idx).ffill().fillna(0)
            for lado in ('solo_sube', 'solo_baja', 'ambos'):
                s = st.copy()
                if lado == 'solo_sube': s[s < 0] = 0
                if lado == 'solo_baja': s[s > 0] = 0
                peso = 0.5 + 0.5 * s     # +1 -> 100 % en A ; -1 -> 100 % en B
                eq, turn = simular(rA, rB, peso); m = metricas(eq); t = tramos(eq)
                filas.append(dict(grafica=x, senal=nombre, lado=lado, total=m['total'], mdd=m['mdd'],
                                  ratio=m['ratio'], base_ratio=mb['ratio'], base_total=mb['total'],
                                  ambos_tramos=all(t[k] > tb[k] for k in t), rotaciones=round(turn)))
    df = pd.DataFrame(filas); df['mejora'] = df.ratio > df.base_ratio
    df.to_csv(os.path.join(AQUI, 'indicadores_resultados.csv'), index=False)
    pd.set_option('display.width', 250)
    g = df.groupby(['grafica', 'lado']).agg(n=('ratio', 'size'), ratio_med=('ratio', 'median'), base=('base_ratio', 'first'),
                                            pct_mejora=('mejora', 'mean'), pct_ambos=('ambos_tramos', 'mean'))
    print(g.round(2).to_string())
    print('\nTop por gráfica (mejoran y ganan en ambos tramos):')
    top = df[df.mejora & df.ambos_tramos].sort_values('ratio', ascending=False).groupby('grafica').head(6)
    print(top[['grafica', 'senal', 'lado', 'total', 'mdd', 'ratio', 'base_ratio', 'rotaciones']].round(2).to_string(index=False))
