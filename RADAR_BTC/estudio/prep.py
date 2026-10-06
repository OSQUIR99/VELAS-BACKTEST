# -*- coding: utf-8 -*-
"""Prepara un panel diario (UTC) con BTC + derivados + macro tal y como se conocía cada día."""
import json, io
import numpy as np, pandas as pd

D = 'datos'

def btc_diario():
    b = pd.read_parquet(f'{D}/CRIPTO/BTC/1d.parquet')
    b['fecha'] = pd.to_datetime(b['fecha']).dt.normalize()
    b = b.set_index('fecha').rename(columns={'apertura': 'o', 'maximo': 'h', 'minimo': 'l', 'cierre': 'c', 'volumen': 'v'})
    return b

def perp_diario():
    p = pd.read_parquet(f'{D}/CRIPTO_PERPETUOS/BTC/15m.parquet')
    p['fecha'] = pd.to_datetime(p['fecha'])
    p = p.set_index('fecha')
    d = p.resample('1D').agg({'cierre': 'last', 'volumen': 'sum'}).rename(columns={'cierre': 'perp_c', 'volumen': 'perp_v'})
    f = pd.read_parquet(f'{D}/CRIPTO_PERPETUOS/BTC/financiacion.parquet')
    f['fecha'] = pd.to_datetime(f['fecha'])
    fd = f.set_index('fecha')['tasa'].resample('1D').sum().rename('funding_dia')  # suma de los 3 cobros del día
    return d.join(fd, how='outer')

def fred():
    out = {}
    for fn in ['bonos_fred_macro.json', 'bonos_fred_extra.json']:
        m = json.load(open(f'{D}/RENTA_FIJA/brutos/{fn}'))
        for k, txt in m.items():
            s = pd.read_csv(io.StringIO(txt))
            s.columns = ['fecha', k]
            s['fecha'] = pd.to_datetime(s['fecha'])
            s[k] = pd.to_numeric(s[k], errors='coerce')
            out[k] = s.set_index('fecha')[k].dropna()
    return out

def yahoo():
    y = pd.read_csv(f'{D}/RENTA_FIJA/brutos/bonos_yahoo_precios.csv', low_memory=False)
    y = y[~y['simbolo'].isin(['#DIVIDENDOS', 'simbolo'])]
    y['fecha'] = pd.to_datetime(y['fecha'], errors='coerce')
    y['cierre'] = pd.to_numeric(y['cierre'], errors='coerce')
    w = y.pivot_table(index='fecha', columns='simbolo', values='cierre', aggfunc='last')
    return w.rename(columns={'DX-Y.NYB': 'DXY', '^VIX': 'VIX', '^MOVE': 'MOVE', '^TNX': 'TNX', 'GC=F': 'ORO'})

# retraso típico de publicación (días) para no usar datos que aún no se conocían
RETRASO = {'diario': 1, 'NFCI': 6, 'WALCL': 2, 'ICSA': 5, 'CCSA': 12}
DIARIAS = ['DGS10', 'DGS2', 'DGS3MO', 'DFII10', 'DFII5', 'T10YIE', 'T5YIFR', 'T10Y2Y', 'T10Y3M', 'DFF',
           'DFEDTARU', 'DTWEXBGS', 'DCOILWTICO', 'VIXCLS', 'BAA10Y', 'BAMLH0A0HYM2', 'DEXJPUS', 'DGS1']

def panel():
    b = btc_diario()
    idx = pd.date_range(b.index.min(), b.index.max(), freq='D')
    P = b.reindex(idx)
    P = P.join(perp_diario().reindex(idx))
    F = fred()
    for k in DIARIAS:
        if k in F:
            s = F[k].copy(); s.index = s.index + pd.Timedelta(days=RETRASO['diario'])
            P[k] = s.reindex(idx, method='ffill')
    for k in ['NFCI', 'WALCL', 'ICSA']:
        s = F[k].copy(); s.index = s.index + pd.Timedelta(days=RETRASO[k])
        P[k] = s.reindex(idx, method='ffill')
    # mensuales: usar la tabla semanal 'conocido ese día' (ya lleva el retraso de publicación)
    sm = pd.read_csv(f'{D}/RENTA_FIJA/semanal_macro_conocido_ese_dia.csv', parse_dates=['viernes']).set_index('viernes')
    for k in ['CPI', 'CORECPI', 'UNRATE', 'M2SL', 'SAHMREALTIME', 'PAYEMS', 'FEDTGT', 'TP10']:
        if k in sm:
            P[k] = sm[k].reindex(idx, method='ffill')
    Y = yahoo()
    for k in ['QQQ', 'SPY', 'DXY', 'VIX', 'MOVE', 'GLD', 'HYG', 'TLT', 'TNX']:
        s = Y[k].dropna().copy(); s.index = s.index + pd.Timedelta(days=1)  # el cierre de EE. UU. se conoce al día siguiente en UTC
        P['y_' + k] = s.reindex(idx, method='ffill')
    return P

if __name__ == '__main__':
    P = panel()
    P.to_parquet('panel_diario.parquet')
    print(P.shape, P.index.min(), P.index.max())
    print(P.iloc[-1].to_string())
