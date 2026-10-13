# -*- coding: utf-8 -*-
"""Núcleo del estudio de liquidez: carga, ATR, ZigZag causal y utilidades."""
import numpy as np, pandas as pd
from numba import njit

import os
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + os.sep  # carpeta VELAS PARA BACKTEST
ACTIVOS = {
    'BTC':       ('CARPETA_DE_BACKTEST/CRIPTO/BTC', None),
    'sp500':     ('CARPETA_DE_BACKTEST/TRADICIONAL/sp500', '1965-01-01'),
    'nasdaq100': ('CARPETA_DE_BACKTEST/TRADICIONAL/nasdaq100', '1990-01-01'),
    'oro':       ('CARPETA_DE_BACKTEST/TRADICIONAL/oro', '1975-01-01'),
    'plata':     ('CARPETA_DE_BACKTEST/TRADICIONAL/plata', '2009-09-01'),
    'brent':     ('CARPETA_DE_BACKTEST/TRADICIONAL/petroleo_brent', '1990-01-01'),
}
NOMBRE = {'BTC': 'Bitcoin', 'sp500': 'S&P 500', 'nasdaq100': 'Nasdaq 100',
          'oro': 'Oro', 'plata': 'Plata', 'brent': 'Petróleo Brent'}
HORAS_TF = {'15m': 0.25, '1h': 1, '4h': 4, '1d': 24}


def cargar(activo, tf):
    ruta, desde = ACTIVOS[activo]
    df = pd.read_parquet(f'{BASE}{ruta}/{tf}.parquet').rename(columns={
        'apertura': 'o', 'maximo': 'h', 'minimo': 'l', 'cierre': 'c', 'volumen': 'v'})
    df = df.sort_values('fecha').drop_duplicates('fecha').reset_index(drop=True)
    if desde is not None and tf == '1d':
        df = df[df.fecha >= desde].reset_index(drop=True)
    # quitar velas planas o rotas
    ok = (df.h >= df.l) & (df.h > 0) & (df.l > 0)
    df = df[ok].reset_index(drop=True)
    df['atr'] = atr(df.h.values, df.l.values, df.c.values, 14)
    df['ema200'] = df.c.ewm(span=200, adjust=False).mean()
    df['atr50'] = atr(df.h.values, df.l.values, df.c.values, 50)
    return df


def atr(h, l, c, n=14):
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.empty_like(tr)
    out[0] = tr[0]
    a = 1.0 / n
    for i in range(1, len(tr)):
        out[i] = out[i - 1] + a * (tr[i] - out[i - 1])
    return out


@njit(cache=True)
def _zigzag(h, l, a, k, start):
    """ZigZag causal: un giro se confirma cuando el precio se aleja k*ATR del extremo.
    Devuelve arrays: idx del extremo, precio, tipo (+1 máximo, -1 mínimo), idx de confirmación."""
    n = len(h)
    idx = np.empty(n, np.int64); px = np.empty(n); tp = np.empty(n, np.int64); cf = np.empty(n, np.int64)
    m = 0
    # arranque: buscamos el primer movimiento de k*ATR
    hi = h[start]; hi_i = start; lo = l[start]; lo_i = start
    d = 0
    i = start + 1
    while i < n and d == 0:
        if h[i] > hi:
            hi = h[i]; hi_i = i
        if l[i] < lo:
            lo = l[i]; lo_i = i
        if hi - lo > k * a[i]:
            if hi_i > lo_i:
                # el último fue el máximo: el mínimo queda confirmado, seguimos buscando máximo
                idx[m] = lo_i; px[m] = lo; tp[m] = -1; cf[m] = i; m += 1
                d = 1; ext = hi; ext_i = hi_i
            else:
                idx[m] = hi_i; px[m] = hi; tp[m] = 1; cf[m] = i; m += 1
                d = -1; ext = lo; ext_i = lo_i
        i += 1
    while i < n:
        if d == 1:
            if h[i] > ext:
                ext = h[i]; ext_i = i
            elif l[i] < ext - k * a[i]:
                idx[m] = ext_i; px[m] = ext; tp[m] = 1; cf[m] = i; m += 1
                d = -1; ext = l[i]; ext_i = i
        else:
            if l[i] < ext:
                ext = l[i]; ext_i = i
            elif h[i] > ext + k * a[i]:
                idx[m] = ext_i; px[m] = ext; tp[m] = -1; cf[m] = i; m += 1
                d = 1; ext = h[i]; ext_i = i
        i += 1
    return idx[:m], px[:m], tp[:m], cf[:m]


def zigzag(df, k=2.5, start=50):
    i, p, t, c = _zigzag(df.h.values, df.l.values, df.atr.values, float(k), start)
    return pd.DataFrame({'i': i, 'p': p, 't': t, 'cf': c})


@njit(cache=True)
def primer_cruce(arr, desde, nivel, por_debajo):
    """Primer índice >= desde donde arr cruza el nivel (low<nivel si por_debajo, high>nivel si no). -1 si nunca."""
    n = len(arr)
    for j in range(desde, n):
        if por_debajo:
            if arr[j] < nivel:
                return j
        else:
            if arr[j] > nivel:
                return j
    return -1


@njit(cache=True)
def carrera(h, l, desde, arriba, abajo, maxb):
    """Desde la barra 'desde' (incluida), qué se toca antes: arriba (+1) o abajo (-1). 0 si ninguno en maxb.
    Si una misma vela toca ambos, se cuenta como -1 si abrir... (ambiguo => 2)."""
    n = len(h)
    fin = min(n, desde + maxb)
    for j in range(desde, fin):
        up = h[j] >= arriba
        dn = l[j] <= abajo
        if up and dn:
            return 2, j
        if up:
            return 1, j
        if dn:
            return -1, j
    return 0, fin - 1


def eficiencia(c, a, b):
    """Kaufman: avance neto / recorrido total de cierres entre a y b."""
    if b <= a + 1:
        return np.nan
    seg = c[a:b + 1]
    tot = np.abs(np.diff(seg)).sum()
    return abs(seg[-1] - seg[0]) / tot if tot > 0 else np.nan
