# -*- coding: utf-8 -*-
"""Liquidez (stablecoins), delta de volumen (Binance taker), prima de Coinbase y divergencias."""
import numpy as np, pandas as pd

U = 'datos/RADAR_BTC/brutos'
P = pd.read_parquet('panel_diario.parquet')
idx = P.index

tk = pd.read_csv(f'{U}/binance_btc_1d_taker.csv', parse_dates=['fecha']).set_index('fecha')
cb = pd.read_csv(f'{U}/coinbase_btcusd_1d.csv', parse_dates=['fecha']).set_index('fecha')
st = pd.read_csv(f'{U}/stablecoins.csv', parse_dates=['fecha']).set_index('fecha')

X = pd.DataFrame(index=idx)
# ---- delta de volumen (compras agresivas - ventas agresivas) ----
v = tk['v'].reindex(idx); tb = tk['taker_buy_v'].reindex(idx)
delta = 2 * tb - v                         # BTC
X['delta_ratio'] = (2 * tb - v) / v        # -1..1: proporción neta agresiva del día
X['delta_ratio7'] = X['delta_ratio'].rolling(7).mean()
cvd = delta.cumsum()
X['cvd30_norm'] = (cvd - cvd.shift(30)) / v.rolling(30).sum()   # delta neto de 30 días / volumen de 30 días
X['cvd90_norm'] = (cvd - cvd.shift(90)) / v.rolling(90).sum()
X['cvd_z'] = (X['cvd30_norm'] - X['cvd30_norm'].rolling(365, min_periods=120).mean()) / X['cvd30_norm'].rolling(365, min_periods=120).std()
# ---- prima de Coinbase (dólares de EE. UU. frente a Binance en USDT), media de 7 días ----
c = P['c']
X['prima_coinbase'] = (cb['c'].reindex(idx) / c - 1) * 100
X['prima_coinbase7'] = X['prima_coinbase'].rolling(7).mean()
# ---- liquidez cripto: stablecoins ----
s = st['stables_usd'].reindex(idx).ffill()
X['stables_30d'] = s.pct_change(30) * 100
X['stables_90d'] = s.pct_change(90) * 100
X['stables_acel'] = X['stables_30d'] - X['stables_30d'].shift(30)
# "pólvora seca": capitalización de stablecoins / capitalización aproximada de BTC (19,5 M BTC aprox.; se usa solo la tendencia)
X['stables_vs_btc_chg60'] = np.log(s / c).diff(60)

# ---- divergencias (a 45 días): precio hace un máximo más alto pero el oscilador / el delta no ----
def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)
r = rsi(c)
macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
macdh = macd - macd.ewm(span=9).mean()
mfi_tp = (P['h'] + P['l'] + c) / 3
mf = mfi_tp * P['v']
pos = mf.where(mfi_tp.diff() > 0, 0).rolling(14).sum(); neg = mf.where(mfi_tp.diff() < 0, 0).rolling(14).sum()
mfi = 100 - 100 / (1 + pos / neg)

def div_bajista(precio, osc, w=45, minsep=5):
    """1 si hoy el precio está en máximo de w días y supera el máximo previo de la ventana,
    pero el oscilador queda por debajo de su valor en aquel máximo previo."""
    out = pd.Series(0.0, index=precio.index)
    pv, ov = precio.values, osc.values
    for i in range(w, len(pv)):
        if np.isnan(ov[i]): continue
        ventana = pv[i - w:i - minsep]
        if len(ventana) == 0: continue
        j = np.argmax(ventana) + i - w
        if pv[i] >= pv[i - w:i + 1].max() and pv[i] > pv[j] and ov[i] < ov[j]:
            out.iloc[i] = 1.0
    return out

def div_alcista(precio, osc, w=45, minsep=5):
    return div_bajista(-precio, -osc, w, minsep)

X['div_baj_rsi'] = div_bajista(c, r)
X['div_baj_macd'] = div_bajista(c, macdh)
X['div_baj_mfi'] = div_bajista(c, mfi)
X['div_baj_cvd'] = div_bajista(c, cvd)
X['div_alc_rsi'] = div_alcista(c, r)
X['div_alc_cvd'] = div_alcista(c, cvd)
# señal persistente: hubo divergencia bajista en los últimos 10 días
for k in ['div_baj_rsi', 'div_baj_macd', 'div_baj_mfi', 'div_baj_cvd', 'div_alc_rsi', 'div_alc_cvd']:
    X[k + '_10d'] = X[k].rolling(10).max()
X['div_baj_n'] = X[['div_baj_rsi_10d', 'div_baj_macd_10d', 'div_baj_mfi_10d', 'div_baj_cvd_10d']].sum(axis=1)
# esfuerzo vs resultado (Wyckoff): delta muy vendedor pero precio que no cae (absorción) / delta comprador pero precio que no sube
ret = np.log(c).diff()
X['absorcion_venta'] = ((X['delta_ratio'] < X['delta_ratio'].rolling(90).quantile(0.15)) & (ret > -0.005)).astype(float).rolling(10).sum()
X['oferta_oculta'] = ((X['delta_ratio'] > X['delta_ratio'].rolling(90).quantile(0.85)) & (ret < 0.005)).astype(float).rolling(10).sum()
X.to_parquet('flujo_liquidez.parquet')
print(X.describe().T[['count', 'mean', 'min', 'max']].round(3).to_string())
print('\nÚltimos valores:'); print(X.iloc[-1].round(3).to_string())
