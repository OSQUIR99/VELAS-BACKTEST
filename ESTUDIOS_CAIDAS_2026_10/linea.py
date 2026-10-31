# -*- coding: utf-8 -*-
"""Línea de liquidez del proyecto (herramientas/liquidez.py, versión V5 y «con impulso»), rehecha con las mismas fuentes
(Reserva Federal de San Luis y TradingView) y los mismos retrasos de publicación. Salida: linea.parquet (viernes)."""
import sys, time, subprocess, urllib.request
import numpy as np, pandas as pd
from tvtest import tv

UA = {'User-Agent': 'curl/8.5.0'}
CAL = pd.date_range('2008-01-01', '2026-10-31', freq='D')


def fred(sid, desde='2005-01-01'):
    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={desde}'
    for _ in range(4):
        try:
            txt = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode(); break
        except Exception:
            time.sleep(3)
    else:
        txt = subprocess.run(['curl', '-sS', '-m', '90', url], capture_output=True, text=True).stdout
    filas = [l.split(',') for l in txt.strip().splitlines()[1:]]
    s = pd.Series({pd.Timestamp(f): (float(v) if v not in ('', '.') else np.nan) for f, v in filas}, dtype=float)
    return s.dropna().sort_index()


def pit(s, lag, limite=None):
    s = s.dropna().copy(); s.index = s.index + pd.Timedelta(days=lag)
    s = s[~s.index.duplicated(keep='last')]
    return s.reindex(CAL.union(s.index)).ffill(limit=limite).reindex(CAL)


def calcular():
    fed = fred('WALCL'); tga = fred('WDTGAL'); rrp = fred('RRPONTSYD') * 1000
    rrp_w = rrp.reindex(fed.index, method='ffill').fillna(0)
    net = (fed - tga - rrp_w).dropna()
    luz1 = pit(net / net.rolling(52).mean() - 1, 2, 16)
    baa = fred('BAA10Y'); luz2 = pit(baa - baa.rolling(126).max(), 1, 7)
    fx = {'EUR': pit(fred('DEXUSEU'), 7, 10), 'JPY': 1 / pit(fred('DEXJPUS'), 7, 10), 'CNY': 1 / pit(fred('DEXCHUS'), 7, 10),
          'GBP': pit(fred('DEXUSUK'), 7, 10), 'USD': pd.Series(1.0, index=CAL)}
    cb = {'USD': ('ECONOMICS:USCBBS', 2, 16), 'EUR': ('ECONOMICS:EUCBBS', 5, 21), 'JPY': ('ECONOMICS:JPCBBS', 7, 45),
          'CNY': ('ECONOMICS:CNCBBS', 30, 75), 'GBP': ('ECONOMICS:GBCBBS', 2, 21)}
    U = {cur: pit(tv(sym, '1W', 2000), 6 + lag, lim) * fx[cur] for cur, (sym, lag, lim) in cb.items()}
    gli = pd.DataFrame(U).sum(axis=1, min_count=5); gli13 = gli / gli.shift(91) - 1
    m2 = {'USD': ('ECONOMICS:USM2', 28, 75), 'EUR': ('ECONOMICS:EUM2', 30, 75), 'JPY': ('ECONOMICS:JPM2', 15, 75),
          'CNY': ('ECONOMICS:CNM2', 30, 75), 'GBP': ('ECONOMICS:GBM2', 32, 75)}
    M = {cur: pit(tv(sym, '1W', 2000), 6 + lag, lim) * fx[cur] for cur, (sym, lag, lim) in m2.items()}
    gm2 = pd.DataFrame(M).sum(axis=1, min_count=5); gm213 = gm2 / gm2.shift(91) - 1
    dxy = tv('TVC:DXY', '1D', 5500); dxy63 = pit(dxy / dxy.shift(63) - 1, 0, 5)
    piezas = {'liquidez_neta': luz1, 'credito': -luz2, 'liquidez_global': gli13, 'dolar': -dxy63, 'masa_global': gm213}
    vier = CAL[CAL.dayofweek == 4]
    pc = {}
    for k, v in piezas.items():
        w = v.reindex(vier).dropna()
        pc[k] = w.expanding(min_periods=104).apply(lambda x: (x[:-1] < x[-1]).mean() + 0.5 * (x[:-1] == x[-1]).mean(), raw=True) * 100
    PC = pd.DataFrame(pc).reindex(vier)
    lin = PC.mean(axis=1, skipna=False).dropna()
    Ls = (lin + 0.5 * (lin - lin.shift(13))).dropna()
    out = pd.DataFrame({'linea': lin, 'impulso': Ls})
    return out, PC


if __name__ == '__main__':
    out, PC = calcular()
    out.to_parquet('/home/claude/caidas/linea.parquet')
    print(out.dropna().iloc[[0, -1]]); print(len(out.dropna()))
    print(out.tail(6))
