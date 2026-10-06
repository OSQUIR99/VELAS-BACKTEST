# -*- coding: utf-8 -*-
"""¿Cómo ha cambiado la relación de BTC con la macro y con los días de dato/Fed? (2017-2026)"""
import json
import numpy as np, pandas as pd

P = pd.read_parquet('panel_diario.parquet')
r = np.log(P['c']).diff()

# --- 1. Correlación con activos macro por año (rendimientos diarios en días hábiles de EE. UU.) ---
def ret_us(col):
    s = P[col]
    return np.log(s).diff().where(s.diff() != 0)  # solo días en que el activo se movió (hábiles)

rq = ret_us('y_QQQ'); rd = ret_us('y_DXY'); rg = ret_us('y_GLD')
dreal = P['DFII10'].diff().where(P['DFII10'].diff() != 0)
d2y = P['DGS2'].diff().where(P['DGS2'].diff() != 0)
# BTC: rendimiento acumulado entre días hábiles consecutivos (para alinear con el cierre de EE. UU.)
lc = np.log(P['c'])
mask = rq.notna()
btc_bd = lc[mask].diff()
df = pd.DataFrame({'btc': btc_bd, 'nasdaq': rq[mask], 'dolar': rd[mask], 'oro': rg[mask],
                   'tipo_real_10a': dreal[mask], 'bono_2a': d2y[mask]}).dropna(subset=['btc', 'nasdaq'])
anual = df.groupby(df.index.year).apply(lambda g: g.corr()['btc'].drop('btc')).round(2)
print('CORRELACIÓN DIARIA DE BTC CON… (por año)'); print(anual.to_string())
anual.to_csv('corr_anual.csv')

# beta de BTC al Nasdaq por año
beta = df.groupby(df.index.year).apply(lambda g: np.cov(g.btc, g.nasdaq)[0, 1] / g.nasdaq.var()).round(2)
print('\nBETA BTC/Nasdaq por año:'); print(beta.to_string())

# --- 2. Días de evento ---
ev = json.load(open('datos/RENTA_FIJA/brutos/bonos_fechas_eventos.json'))
fechas = {k: pd.to_datetime(v) for k, v in ev.items()}
absr = r.abs()
vol_norm = absr.rolling(60, min_periods=30).median().shift(1)
ratio = absr / vol_norm
periodos = [('2017-2019', '2017-08-17', '2019-12-31'), ('2020-2021', '2020-01-01', '2021-12-31'),
            ('2022-2023', '2022-01-01', '2023-12-31'), ('2024-2026', '2024-01-01', '2026-09-28')]
filas = []
for k in ['FOMC', 'CPI', 'NFP']:
    d = fechas[k]
    if k == 'FOMC':  # el comunicado sale a las 18-19 h UTC: la reacción cae en ese día y el siguiente
        dias = pd.DatetimeIndex(sorted(set(d) | set(d + pd.Timedelta(days=1))))
    else:
        dias = d
    dias = dias[(dias >= P.index.min()) & (dias <= P.index.max())]
    for nom, a, b in periodos:
        sel = dias[(dias >= a) & (dias <= b)]
        x = ratio.reindex(sel).dropna()
        filas.append(dict(evento=k, periodo=nom, n=len(x), movimiento_vs_normal=round(x.median(), 2),
                          pct_dias_movimiento_grande=round((x > 2.5).mean() * 100)))
E = pd.DataFrame(filas)
print('\nDÍAS DE EVENTO: tamaño del movimiento de BTC frente a un día normal (1,0 = igual)')
print(E.pivot(index='evento', columns='periodo', values='movimiento_vs_normal').to_string())
print('\n% de días de evento con movimiento > 2,5 veces lo normal (en días normales ~', round((ratio > 2.5).mean() * 100), '%)')
print(E.pivot(index='evento', columns='periodo', values='pct_dias_movimiento_grande').to_string())
E.to_csv('eventos_tamano.csv', index=False)

# --- 3. Dirección en días de IPC/empleo/Fed según régimen de la Fed ---
fed_sube = (P['DGS2'] - P['DFF']) > 0.25  # el mercado descuenta subidas
ciclo = P['FEDTGT'].diff(180)
reg = pd.Series(np.where(ciclo > 0.2, 'Fed subiendo', np.where(ciclo < -0.2, 'Fed bajando', 'Fed quieta')), index=P.index)
fil = []
for k in ['FOMC', 'CPI', 'NFP']:
    d = fechas[k]; d = d[(d >= P.index.min()) & (d <= P.index.max())]
    rr = (lc.shift(-1) - lc.shift(1)).reindex(d) if k == 'FOMC' else r.reindex(d)  # FOMC: 2 días
    g = pd.DataFrame({'r': rr * 100, 'reg': reg.reindex(d)}).dropna()
    for rg_, gg in g.groupby('reg'):
        fil.append(dict(evento=k, regimen=rg_, n=len(gg), media_pct=round(gg.r.mean(), 2), mediana_pct=round(gg.r.median(), 2),
                        pct_bajistas=round((gg.r < 0).mean() * 100)))
print('\nDIRECCIÓN DE BTC EN DÍAS DE EVENTO SEGÚN EL CICLO DE LA FED')
print(pd.DataFrame(fil).to_string())

# --- 4. ¿Los movimientos rápidos coinciden con eventos programados más que por azar? ---
R = pd.read_csv('movimientos_rapidos.csv', parse_dates=['dia_clave'])
todos = pd.DatetimeIndex(sorted(set(fechas['FOMC']) | set(fechas['FOMC'] + pd.Timedelta(days=1)) | set(fechas['CPI']) | set(fechas['NFP'])))
todos = todos[(todos >= P.index.min()) & (todos <= P.index.max())]
def cerca(d, ventana=1):
    return any(abs((d - t).days) <= ventana for t in todos)
base = np.mean([cerca(d) for d in P.index])
obs = R['dia_clave'].apply(cerca).mean()
print(f'\nMovimientos rápidos cuyo día clave cae a ±1 día de una Fed/IPC/empleo: {obs*100:.0f} %  (azar: {base*100:.0f} %)')
for t in ['CAIDA', 'SUBIDA']:
    print('  ', t, f"{R[R.tipo==t]['dia_clave'].apply(cerca).mean()*100:.0f} %")
