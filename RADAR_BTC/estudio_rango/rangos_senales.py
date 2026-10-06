# -*- coding: utf-8 -*-
"""Señales medidas DENTRO del rango (solo con lo ya conocido) y su capacidad de anticipar la ruptura bajista."""
import json
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

D = pd.read_parquet('rangos_4h.parquet')
c, h, l, o, v = D['c'], D['h'], D['l'], D['o'], D['v']
T, S, N = D['techo'], D['suelo'], D['N']
W = T - S
X = pd.DataFrame(index=D.index)

def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)

X['posicion'] = (c - S) / W                                   # 0 = en el suelo, 1 = en el techo
X['ancho'] = D['ancho'] * 100
X['N'] = N
X['eficiencia'] = D['er']
# toques del suelo y del techo (mínimos dentro del 15 % inferior, separados >= 3 velas)
ts, tt, pend_max, pend_min, vol_baj, comp, tend_previa = [np.full(len(D), np.nan) for _ in range(7)]
lv, hv, cv, ov, vv = l.values, h.values, c.values, o.values, v.values
for i in np.where(T.notna().values)[0]:
    n_ = int(N.values[i]); a, b = S.values[i], T.values[i]; w = b - a
    lw, hw, cw, ow, vw = lv[i - n_:i], hv[i - n_:i], cv[i - n_:i], ov[i - n_:i], vv[i - n_:i]
    cerca_s = np.where(lw <= a + 0.15 * w)[0]; cerca_t = np.where(hw >= b - 0.15 * w)[0]
    ts[i] = 1 + np.sum(np.diff(cerca_s) >= 3) if len(cerca_s) else 0
    tt[i] = 1 + np.sum(np.diff(cerca_t) >= 3) if len(cerca_t) else 0
    # pendiente de los máximos y de los mínimos (bloques de 6 velas), en anchos del rango por ventana
    k = max(3, n_ // 6)
    bh = [hw[j:j + 6].max() for j in range(0, n_ - 5, 6)]; bl = [lw[j:j + 6].min() for j in range(0, n_ - 5, 6)]
    if len(bh) >= 3:
        x = np.arange(len(bh))
        pend_max[i] = np.polyfit(x, bh, 1)[0] * len(bh) / w
        pend_min[i] = np.polyfit(x, bl, 1)[0] * len(bl) / w
    baja = cw < ow
    vol_baj[i] = vw[baja].sum() / vw.sum()
    comp[i] = (hw[-12:].max() - lw[-12:].min()) / w
    if i - 2 * n_ >= 0:
        tend_previa[i] = cv[i - n_] / cv[i - 2 * n_] - 1
X['toques_suelo'] = ts; X['toques_techo'] = tt
X['pend_maximos'] = pend_max; X['pend_minimos'] = pend_min
X['vol_velas_bajistas'] = vol_baj
X['compresion_12v'] = comp
X['tendencia_previa'] = tend_previa
X['rsi4h'] = rsi(c)
X['ret_24v'] = c.pct_change(24)
# delta real si existe
if D['taker_buy_v'].notna().any():
    dl = (2 * D['taker_buy_v'] - v)
    X['delta_24v'] = dl.rolling(24).sum() / v.rolling(24).sum()
    X['delta_en_rango'] = np.nan
    cvd = dl.cumsum()
    X['delta_en_rango'] = [(cvd.values[i - 1] - cvd.values[i - int(n_)]) / v.values[i - int(n_):i].sum() if not np.isnan(n_) else np.nan
                           for i, n_ in enumerate(N.values)]
# contexto diario: tendencia y radar
dia = c.resample('1D').last().dropna()
ema50 = dia.ewm(span=50).mean(); ema200 = dia.ewm(span=200).mean()
ctx = pd.DataFrame({'sobre_ema50d': (dia > ema50).astype(float), 'sobre_ema200d': (dia > ema200).astype(float),
                    'dist_ema50d': dia / ema50 - 1}).shift(1)  # se conoce al cerrar el día anterior
X = X.join(ctx.reindex(X.index, method='ffill'))
RH = pd.read_parquet('radar_historico.parquet')[['total', 'macro', 'liquidez', 'corr_nasdaq_90d']].shift(1)
X = X.join(RH.rename(columns={'total': 'radar_total', 'macro': 'radar_macro', 'liquidez': 'radar_liquidez'}).reindex(X.index, method='ffill'))
# financiación (desde oct-2022)
f = pd.read_parquet('datos/CRIPTO_PERPETUOS/BTC/financiacion.parquet'); f['fecha'] = pd.to_datetime(f['fecha'])
fs = f.set_index('fecha')['tasa'].rolling(3).mean()
X['funding'] = fs.reindex(X.index, method='ffill') * 3 * 365 * 100
X.loc[X.index < f['fecha'].min(), 'funding'] = np.nan
# calendario: horas hasta la próxima Fed / IPC / empleo (publicación 12:30-18:00 UTC)
ev = json.load(open('datos/RENTA_FIJA/brutos/bonos_fechas_eventos.json'))
fechas = pd.DatetimeIndex(sorted(set(pd.to_datetime(ev['CPI']) + pd.Timedelta(hours=12, minutes=30)) |
                                 set(pd.to_datetime(ev['NFP']) + pd.Timedelta(hours=12, minutes=30)) |
                                 set(pd.to_datetime(ev['FOMC']) + pd.Timedelta(hours=18))))
pos_ = fechas.searchsorted(X.index + pd.Timedelta(hours=4))
X['horas_a_evento'] = [(fechas[p] - (t + pd.Timedelta(hours=4))).total_seconds() / 3600 if p < len(fechas) else np.nan for p, t in zip(pos_, X.index)]
X['evento_48h'] = (X['horas_a_evento'] <= 48).astype(float)
X['fin_de_semana'] = (X.index.dayofweek >= 5).astype(float)
# divergencia bajista de RSI 4 h dentro del rango (precio en máximo de 30 velas sin máximo de RSI)
r = X['rsi4h']
mx = c.rolling(30).max(); X['div_rsi_4h'] = ((c >= mx * 0.995) & (r < r.rolling(30).max() - 5)).astype(float).rolling(12).max()

Y = D[['lado', 'sigue_abajo_anchos', 'falsa', 'caida_tras_ruptura']]
Z = X.join(Y)[D['techo'].notna()]
Z['rompe_abajo'] = (Z['lado'] == -1).astype(float)
Z.to_parquet('rangos_senales.parquet')

def auc(x, y):
    m = x.notna() & y.notna()
    return roc_auc_score(y[m], x[m]) if m.sum() > 200 and y[m].nunique() > 1 else np.nan

E = {'2017-21': ('2017', '2021'), '2022-26': ('2022', '2026')}
filas = []
for k in X.columns:
    filas.append({'senal': k, **{e: round(auc(Z.loc[a:b, k], Z.loc[a:b, 'rompe_abajo']), 2) for e, (a, b) in E.items()}})
T_ = pd.DataFrame(filas).set_index('senal')
T_['fuerza'] = ((T_ - .5).abs().min(axis=1) * np.sign((T_['2017-21'] - .5) * (T_['2022-26'] - .5))).round(2)
print('¿Qué anticipa que el rango se rompa ANTES por abajo? (AUC; >0,5 = valor alto -> más ruptura bajista)')
print(T_.sort_values('fuerza', ascending=False).to_string())
T_.to_csv('rangos_auc_rompe_abajo.csv')

# ¿qué separa una ruptura bajista real de una falsa?
B = Z[Z.lado == -1].copy()
B['real'] = ((B['falsa'] == 0) & (B['sigue_abajo_anchos'] >= 0.5)).astype(float)
filas = []
for k in X.columns:
    filas.append({'senal': k, **{e: round(auc(B.loc[a:b, k], B.loc[a:b, 'real']), 2) for e, (a, b) in E.items()}})
T2 = pd.DataFrame(filas).set_index('senal')
T2['fuerza'] = ((T2 - .5).abs().min(axis=1) * np.sign((T2['2017-21'] - .5) * (T2['2022-26'] - .5))).round(2)
print('\nSi rompe por abajo, ¿qué anticipa que la ruptura sea REAL (no recupera en 24 h y cae >= medio ancho)?  base', round(B.real.mean(), 2))
print(T2.sort_values('fuerza', ascending=False).to_string())
T2.to_csv('rangos_auc_ruptura_real.csv')
