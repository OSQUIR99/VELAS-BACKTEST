# -*- coding: utf-8 -*-
"""Variables (conocidas cada día) y etiquetas futuras para estudiar el riesgo de desplome de BTC."""
import json
import numpy as np, pandas as pd

def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)

def zrob(s, n=180, minp=60):
    med = s.rolling(n, min_periods=minp).median()
    mad = (s - med).abs().rolling(n, min_periods=minp).median() * 1.4826
    return (s - med) / mad.replace(0, np.nan)

def variables(P):
    c = P['c']; X = pd.DataFrame(index=P.index)
    lr = np.log(c).diff()
    # ---- técnico ----
    X['t_dist200'] = c / c.rolling(200).mean() - 1
    X['t_dist50s'] = c / c.rolling(350).mean() - 1  # media de 50 semanas
    X['t_pend50'] = c.rolling(50).mean().pct_change(20)
    X['t_ret20'] = c.pct_change(20)
    X['t_ret90'] = c.pct_change(90)
    X['t_dd365'] = c / c.rolling(365, min_periods=200).max() - 1
    hi90, lo90 = P['h'].rolling(90).max(), P['l'].rolling(90).min()
    X['t_pos90'] = (c - lo90) / (hi90 - lo90)
    X['t_vol30'] = lr.rolling(30).std() * np.sqrt(365)
    X['t_compresion'] = lr.rolling(10).std() / lr.rolling(90).std()
    X['t_rsi14'] = rsi(c)
    m1, m2, m3 = c.rolling(30).max(), c.shift(30).rolling(30).max(), c.shift(60).rolling(30).max()
    X['t_maximos_desc'] = ((m1 < m2) & (m2 < m3)).astype(float)
    X['t_vol_rel'] = P['v'] / P['v'].rolling(90).median()
    # ---- derivados (desde oct-2022) ----
    f = P['funding_dia']
    X['d_funding7'] = f.rolling(7, min_periods=5).mean() * 365 * 100  # % anualizado
    X['d_funding_z'] = zrob(f.rolling(3).mean(), 180)
    X['d_prima_perp'] = (P['perp_c'] / c - 1) * 100
    X['d_perp_spot_vol'] = zrob(np.log(P['perp_v'] / P['v']), 180)
    # ---- macro ----
    X['m_real_chg60'] = P['DFII10'] - P['DFII10'].shift(60)
    X['m_2a_chg60'] = P['DGS2'] - P['DGS2'].shift(60)
    X['m_10a_chg60'] = P['DGS10'] - P['DGS10'].shift(60)
    X['m_2a_menos_fed'] = P['DGS2'] - P['DFF']
    X['m_dolar_chg60'] = P['DTWEXBGS'].pct_change(60) * 100
    X['m_dxy_dist200'] = P['y_DXY'] / P['y_DXY'].rolling(200).mean() - 1
    X['m_nfci'] = P['NFCI']
    X['m_nfci_chg'] = P['NFCI'] - P['NFCI'].shift(42)
    X['m_fed_balance_chg13s'] = P['WALCL'].pct_change(91) * 100
    X['m_m2_anual'] = P['M2SL'].pct_change(365) * 100
    X['m_nasdaq_dist200'] = P['y_QQQ'] / P['y_QQQ'].rolling(200).mean() - 1
    X['m_nasdaq_ret20'] = P['y_QQQ'].pct_change(20)
    X['m_vix'] = P['y_VIX']
    X['m_move'] = P['y_MOVE']
    X['m_credito_chg30'] = P['BAA10Y'] - P['BAA10Y'].shift(30)
    X['m_yen_chg20'] = P['DEXJPUS'].pct_change(20) * 100  # negativo = el yen se aprecia
    X['m_petroleo_chg60'] = P['DCOILWTICO'].pct_change(60) * 100
    X['m_ciclo_fed'] = P['FEDTGT'] - P['FEDTGT'].shift(180)
    X['m_prima_plazo'] = P['TP10']
    X['m_oro_ret60'] = P['y_GLD'].pct_change(60)
    return X

def calendario(idx):
    ev = json.load(open('datos/RENTA_FIJA/brutos/bonos_fechas_eventos.json'))
    out = pd.DataFrame(index=idx)
    todos = []
    for k in ['FOMC', 'CPI', 'NFP']:
        d = pd.DatetimeIndex(pd.to_datetime(ev[k])).sort_values()
        pos = d.searchsorted(idx)
        prox = pd.Series([d[p] if p < len(d) else pd.NaT for p in pos], index=idx)
        out['c_dias_' + k.lower()] = (prox - idx.to_series()).dt.days
        todos += list(d)
    t = pd.Series(1, index=pd.DatetimeIndex(sorted(todos))).groupby(level=0).sum()
    t = t.reindex(pd.date_range(idx.min(), idx.max() + pd.Timedelta(days=10)), fill_value=0)
    out['c_eventos_7d'] = t[::-1].rolling(7, min_periods=1).sum()[::-1].reindex(idx)
    return out

def etiquetas(P, h=30):
    c = P['c']; l = P['l']; hi = P['h']
    fut_min = l[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1)
    fut_max = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1)
    E = pd.DataFrame(index=P.index)
    E['dd_fut'] = fut_min / c - 1
    E['ru_fut'] = fut_max / c - 1
    E['ret_fut'] = c.shift(-h) / c - 1
    vol = np.log(c).diff().rolling(90).std() * np.sqrt(h)
    E['desplome'] = (E['dd_fut'] <= -0.20).astype(float).where(E['dd_fut'].notna())
    E['desplome_relvol'] = (np.log1p(E['dd_fut']) <= -1.5 * vol).astype(float).where(E['dd_fut'].notna())  # caída ≥1,5 desviaciones de 30 días
    E['subidon'] = (E['ru_fut'] >= 0.25).astype(float).where(E['ru_fut'].notna())
    E['subidon_relvol'] = (np.log1p(E['ru_fut']) >= 1.5 * vol).astype(float).where(E['ru_fut'].notna())
    return E

if __name__ == '__main__':
    P = pd.read_parquet('panel_diario.parquet')
    X = variables(P).join(calendario(P.index))
    E = etiquetas(P)
    X.join(E).to_parquet('estudio_diario.parquet')
    print(X.shape)
    for k in ['desplome', 'desplome_relvol', 'subidon', 'subidon_relvol']:
        print(k, E[k].groupby(E.index.year).mean().round(2).to_dict())
