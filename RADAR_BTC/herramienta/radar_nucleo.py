# -*- coding: utf-8 -*-
"""RADAR DE RIESGO BTC — núcleo de cálculo (mismo código para el estudio histórico y para la revisión diaria).

Entrada: tabla diaria 'estado' con columnas en bruto (ver COLUMNAS). Las series macro van con su FECHA DE OBSERVACIÓN;
aquí se retrasan 1 día (o lo que toque) para usar solo lo que se conocía ese día.
Salida: variables, cuatro bloques 0-100 y la puntuación total 0-100.
"""
import bisect, json
import numpy as np, pandas as pd

COLUMNAS = ['o', 'h', 'l', 'c', 'v', 'taker_buy_v', 'cb_c', 'funding_dia', 'stables_usd', 'etf_flujo_musd',
            'DGS2', 'DGS10', 'DFII10', 'DFF', 'DTWEXBGS', 'NFCI', 'BAA10Y', 'WALCL', 'WTREGEN', 'RRPONTSYD',
            'VIXCLS', 'DEXJPUS', 'nasdaq_ret']
RETRASO = {'DGS2': 1, 'DGS10': 1, 'DFII10': 1, 'DFF': 1, 'DTWEXBGS': 1, 'BAA10Y': 1, 'VIXCLS': 1, 'DEXJPUS': 1,
           'nasdaq_ret': 1, 'NFCI': 6, 'WALCL': 2, 'WTREGEN': 2, 'RRPONTSYD': 1}

# dirección: +1 = valor alto -> más riesgo ; -1 = valor bajo -> más riesgo
VARS_MACRO = {'tipos_2a_menos_fed': 1, 'tipos_2a_60d': 1, 'tipos_10a_60d': 1, 'tipos_real_60d': 1,
              'cond_nfci_6s': 1, 'cond_credito_30d': 1}
VARS_LIQ = {'dolar_vs_media200': 1, 'dolar_60d': 1, 'stables_aceleracion': -1, 'etf_flujo_10d': -1, 'liq_neta_13s': -1}
PESO_LIQ_INTERNO = {'dolar_vs_media200': 1, 'dolar_60d': 1, 'stables_aceleracion': 1, 'etf_flujo_10d': 1, 'liq_neta_13s': 0.5}


def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)


def div_bajista(precio, osc, w=45, minsep=5):
    out = np.zeros(len(precio)); pv, ov = precio.values, osc.values
    for i in range(w, len(pv)):
        if np.isnan(ov[i]) or np.isnan(pv[i]): continue
        ven = pv[i - w:i - minsep]
        if len(ven) == 0 or np.all(np.isnan(ven)): continue
        j = int(np.nanargmax(ven)) + i - w
        if pv[i] >= np.nanmax(pv[i - w:i + 1]) and pv[i] > pv[j] and ov[i] < ov[j]:
            out[i] = 1
    return pd.Series(out, index=precio.index)


def variables(E):
    """E: estado diario (índice = fecha UTC, columnas COLUMNAS). Devuelve DataFrame de variables."""
    E = E.copy()
    for k, d in RETRASO.items():
        if k in E:
            E[k] = E[k].shift(d)
    macro_cols = ['DGS2', 'DGS10', 'DFII10', 'DFF', 'DTWEXBGS', 'NFCI', 'BAA10Y', 'WALCL', 'WTREGEN', 'RRPONTSYD', 'VIXCLS', 'DEXJPUS']
    E[macro_cols] = E[macro_cols].ffill(limit=10)
    c, h, l, v = E['c'], E['h'], E['l'], E['v']
    X = pd.DataFrame(index=E.index)
    X['precio'] = c
    # ---------- macro ----------
    X['tipos_2a_menos_fed'] = E['DGS2'] - E['DFF']
    X['tipos_2a_60d'] = E['DGS2'] - E['DGS2'].shift(60)
    X['tipos_10a_60d'] = E['DGS10'] - E['DGS10'].shift(60)
    X['tipos_real_60d'] = E['DFII10'] - E['DFII10'].shift(60)
    X['cond_nfci_6s'] = E['NFCI'] - E['NFCI'].shift(42)
    X['cond_credito_30d'] = E['BAA10Y'] - E['BAA10Y'].shift(30)
    # ---------- liquidez ----------
    X['dolar_vs_media200'] = E['DTWEXBGS'] / E['DTWEXBGS'].rolling(200, min_periods=150).mean() - 1
    X['dolar_60d'] = E['DTWEXBGS'].pct_change(60, fill_method=None) * 100
    st = E['stables_usd'].where(E['stables_usd'] > 2e9)
    g30 = st.pct_change(30, fill_method=None) * 100
    X['stables_30d'] = g30
    X['stables_aceleracion'] = g30 - g30.shift(30)
    X['etf_flujo_10d'] = E['etf_flujo_musd'].rolling(10, min_periods=6).sum()
    neta = E['WALCL'] / 1e3 - E['WTREGEN'] / 1e3 - E['RRPONTSYD']  # miles de millones de $
    X['liq_neta_bn'] = neta
    X['liq_neta_13s'] = neta.pct_change(91, fill_method=None) * 100
    # ---------- estructura y flujo ----------
    lo20 = l.rolling(20).min().shift(1); lo60 = l.rolling(60).min().shift(1); hi60 = h.rolling(60).max().shift(1)
    X['soporte_20d'] = lo20; X['soporte_60d'] = lo60; X['techo_60d'] = hi60
    rompe20 = c < lo20
    X['ruptura20'] = (rompe20 & ~rompe20.shift(1, fill_value=False).rolling(10).max().astype(bool)).astype(float)
    X['ruptura20_5d'] = X['ruptura20'].rolling(5).max()
    X['bajo_min60'] = (c < lo60).astype(float)
    delta_ratio = (2 * E['taker_buy_v'] - v) / v
    X['delta_ratio'] = delta_ratio
    fuerte = delta_ratio < delta_ratio.rolling(90, min_periods=60).quantile(0.2)
    X['ruptura_con_delta_vendedor_5d'] = (X['ruptura20'].astype(bool) & fuerte).astype(float).rolling(5).max()
    cvd = (2 * E['taker_buy_v'] - v).cumsum()
    X['cvd30'] = (cvd - cvd.shift(30)) / v.rolling(30).sum()
    # reintento fallido: tras una ruptura, el máximo vuelve a ±2 % del soporte roto en 10 días sin dos cierres por encima
    fallo = np.zeros(len(c)); idx = list(E.index)
    rup_dias = np.where(X['ruptura20'].values == 1)[0]
    for i in rup_dias:
        nivel = lo20.iloc[i]
        for j in range(i + 1, min(i + 11, len(c))):
            if h.iloc[j] >= nivel * 0.98:
                ok = (c.iloc[i + 1:j + 1] > nivel).astype(int)
                if not (ok.rolling(2).sum() >= 2).any():
                    fallo[j] = 1
                break
    X['reintento_fallido_10d'] = pd.Series(fallo, index=E.index).rolling(10).max()
    r = rsi(c)
    macdh = (c.ewm(span=12).mean() - c.ewm(span=26).mean()); macdh = macdh - macdh.ewm(span=9).mean()
    tp = (h + l + c) / 3; mf = tp * v
    mfi = 100 - 100 / (1 + mf.where(tp.diff() > 0, 0).rolling(14).sum() / mf.where(tp.diff() < 0, 0).rolling(14).sum())
    divs = pd.concat([div_bajista(c, r), div_bajista(c, macdh), div_bajista(c, mfi), div_bajista(c, cvd)], axis=1)
    X['div_rsi'], X['div_macd'], X['div_mfi'], X['div_cvd'] = [divs[i].rolling(25).max() for i in range(4)]
    X['n_divergencias'] = X[['div_rsi', 'div_macd', 'div_mfi', 'div_cvd']].sum(axis=1)
    X['rsi14'] = r
    X['prima_coinbase7'] = ((E['cb_c'] / c - 1) * 100).rolling(7, min_periods=4).mean()
    # ---------- posicionamiento (solo se muestra) ----------
    X['funding_7d_anual'] = E['funding_dia'].rolling(7, min_periods=4).mean() * 365 * 100
    # ---------- catalizadores: sobresaltos macro detectados ----------
    def zdiff(s, n=250):
        d = s.diff(); return d / d.rolling(n, min_periods=120).std()
    nq = E['nasdaq_ret']
    sh = pd.DataFrame({'bolsa': (nq / nq.rolling(250, min_periods=120).std()) <= -2.0,
                       'vix': zdiff(E['VIXCLS']) >= 2.5, 'tipos2a': zdiff(E['DGS2']).abs() >= 2.5,
                       'dolar': zdiff(np.log(E['DTWEXBGS'])) >= 2.0, 'yen': zdiff(np.log(E['DEXJPUS'])) <= -2.5,
                       'credito': zdiff(E['BAA10Y']) >= 2.5})
    for k in sh: X['sobresalto_' + k] = sh[k].astype(float).rolling(5).max()
    X['n_sobresaltos_5d'] = X[[k for k in X if k.startswith('sobresalto_')]].sum(axis=1)
    # ---------- sensibilidad actual de BTC a la bolsa ----------
    lr = np.log(c).diff()
    nq0 = E['nasdaq_ret'].shift(-RETRASO['nasdaq_ret'])  # sin retraso, para emparejar cada día bursátil con BTC
    m = nq0.notna()
    lc = np.log(c)
    btc_bd = lc[m].diff()  # rentabilidad de BTC entre dos cierres bursátiles consecutivos
    corr = btc_bd.rolling(60, min_periods=40).corr(nq0[m])
    X['corr_nasdaq_90d'] = corr.reindex(E.index).ffill().shift(1)  # se usa al día siguiente
    X['vol30'] = lr.rolling(30).std() * np.sqrt(365) * 100
    return X


class Percentil:
    """Percentil sin mirar el futuro: 'expandido' (histórico) o con una referencia fija (uso diario)."""
    def __init__(self, ref=None):
        self.ref = ref  # dict var -> lista ordenada de valores de referencia

    def serie(self, s, minp=365):
        if self.ref is not None and s.name in self.ref:
            arr = np.array(self.ref[s.name])
            return s.apply(lambda v: np.nan if pd.isna(v) else np.searchsorted(arr, v) / len(arr))
        vals = s.values; out = np.full(len(s), np.nan); hist = []
        for i, v in enumerate(vals):
            if not np.isnan(v):
                if len(hist) >= minp: out[i] = bisect.bisect_left(hist, v) / len(hist)
                bisect.insort(hist, v)
        return pd.Series(out, index=s.index)


def bloques(X, ref=None):
    P = Percentil(ref)
    B = pd.DataFrame(index=X.index)
    pm = pd.DataFrame({k: P.serie(X[k].rename(k)) if d > 0 else 1 - P.serie(X[k].rename(k)) for k, d in VARS_MACRO.items()})
    B['macro'] = pm.mean(axis=1, skipna=True) * 100
    pl = pd.DataFrame({k: P.serie(X[k].rename(k)) if d > 0 else 1 - P.serie(X[k].rename(k)) for k, d in VARS_LIQ.items()})
    w = pd.Series(PESO_LIQ_INTERNO)
    B['liquidez'] = (pl.mul(w).sum(axis=1, min_count=1) / pl.notna().mul(w).sum(axis=1)) * 100
    # estructura y flujo (puntos por hechos, tope 100)
    e = (40 * X['ruptura20_5d'].fillna(0) + 25 * X['ruptura_con_delta_vendedor_5d'].fillna(0) + 15 * X['bajo_min60'].fillna(0)
         + 20 * X['reintento_fallido_10d'].fillna(0)
         + 10 * ((X['n_divergencias'] >= 2) & (X['ruptura20_5d'] == 1)).astype(float))
    pc = P.serie(X['prima_coinbase7'].rename('prima_coinbase7'))
    e = e + 15 * (pc < 0.2).astype(float)
    B['estructura'] = e.clip(upper=100)
    # catalizadores detectados
    B['catalizadores'] = (X['n_sobresaltos_5d'].clip(upper=2) * 50).fillna(0)
    # peso de la macro según cuánto escucha BTC a la bolsa ahora (30 %-45 %)
    cm = ((X['corr_nasdaq_90d'] - 0.1) / 0.3).clip(0, 1).fillna(0.5)
    B['w_macro'] = 0.30 + 0.15 * cm
    return componer(B)


PESOS = {'liquidez': 0.20, 'estructura': 0.25, 'catalizadores': 0.10}


def componer(B):
    wm = B['w_macro']
    tot = wm + sum(PESOS.values())
    B['peso_macro'] = wm / tot
    B['total'] = (wm * B['macro'].fillna(50) + PESOS['liquidez'] * B['liquidez'].fillna(50)
                  + PESOS['estructura'] * B['estructura'] + PESOS['catalizadores'] * B['catalizadores'].clip(upper=100)) / tot
    return B


NIVELES = [(0, 'VERDE'), (40, 'AMARILLO'), (52, 'NARANJA'), (62, 'ROJO')]


def nivel(x):
    n = 'VERDE'
    for umbral, nombre in NIVELES:
        if x >= umbral: n = nombre
    return n


def referencia(X, columnas=None, n=400):
    """Guarda la distribución histórica (cuantiles) de cada variable para puntuar días futuros."""
    cols = columnas or (list(VARS_MACRO) + list(VARS_LIQ) + ['prima_coinbase7'])
    ref = {}
    for k in cols:
        s = X[k].dropna()
        if len(s) > 100:
            ref[k] = list(np.round(np.quantile(s, np.linspace(0, 1, n)), 6))
    return ref
