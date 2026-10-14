"""Panel cripto · las métricas que sobrevivieron a los backtests, sacadas de fuentes públicas y gratuitas.
Sin navegador, sin claves y sin servicios de pago. Probado el 13-oct-2026 desde un servidor con las restricciones
de EE. UU. (las mismas que GitHub Actions): Binance «normal» y Bybit están bloqueados allí, así que no se usan.

Uso:
    pip install requests pandas numpy
    python3 panel_cripto_publico.py                 # lectura al último cierre diario (UTC)
    python3 panel_cripto_publico.py --json hoy.json # además guarda todo en un JSON para el panel o el bot
    python3 panel_cripto_publico.py --hasta 2026-10-12   # repite la lectura al cierre de ese día (para comparar)

Con fases_objetivas.py en la misma carpeta añade la fase de Wyckoff, la posición en la caja y el retroceso de Elliott.
Cada bloque va en su propio try: si una fuente falla, el resto sigue y el fallo queda anotado en «errores».
Las tablas de probabilidad son las medidas en 2023-26 (fuera de muestra) en la sección 6 del panel.
"""
import argparse, io, json, sys, time, zipfile
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests

S = requests.Session()
S.headers['User-Agent'] = 'panel-cripto/1.0 (lectura diaria)'
NOW = datetime.now(timezone.utc)
ALTS = ['AAVE', 'SOL', 'XRP', 'ADA', 'LINK', 'ZEC', 'BNB', 'UNI', 'HBAR', 'ONDO']
OUT = {'generado_utc': NOW.strftime('%Y-%m-%d %H:%M'), 'errores': {}}

# ------------------------------------------------------------------------------------------------
# Tablas medidas en los backtests (2023-26). Probabilidades en %.
# ------------------------------------------------------------------------------------------------
DVOL_TABLA = {   # (tope del tramo, P(día de ±5 % intradía en 7 días), P(día de ±10 %))
    'BTC': [(40, 27.4, 8.7), (50, 41.5, 4.2), (60, 63.3, 6.6), (80, 78.5, 14.1), (999, 100.0, 33.3)],
    'ETH': [(50, 54.6, 7.9), (65, 69.8, 13.4), (80, 86.9, 23.8), (999, 100.0, 27.3)],
}
BASE_10 = {'BTC': 7.4, 'ETH': 17.2}           # P(día de ±10 % intradía en 7 días), frecuencia 2023-26
ALT_VOL_TABLA = [(3, 19.6), (4, 30.0), (5, 41.7), (6, 48.6), (8, 64.2), (99, 68.7)]       # vol. diaria 30 d (%) → P(±10 %)
HYPE_VOL_TABLA = [(3, 100.0, 100.0), (4, 92.0, 25.0), (5, 97.4, 34.7), (6, 98.7, 61.9), (8, 99.3, 73.7), (99, 100.0, 64.7)]
TOQUE_ATR = [(0.1, 88), (0.25, 69), (0.5, 47), (0.75, 27), (1.0, 17), (1.5, 11), (2.0, 5), (3.0, 2), (99, 0)]   # máx/mín de ayer en 24 h
LIQ_BTC = {3.2: 53, 4.8: 36, 9.0: 12, 16.7: 2}  # BTC toca −x % en 7 días (2023-26)
UMBRAL_FIN = {'ETH': 0.03}                       # financiación media del día, % cada 8 h; el resto, 0,02

def tramo(tabla, x):
    for fila in tabla:
        if x <= fila[0]: return fila
    return tabla[-1]

def get(url, params=None, tries=3, **kw):
    for k in range(tries):
        try:
            r = S.get(url, params=params, timeout=30, **kw)
            if r.status_code == 200: return r
            if r.status_code in (429, 418): time.sleep(5 * (k + 1)); continue
            r.raise_for_status()
        except requests.RequestException:
            if k == tries - 1: raise
            time.sleep(2 * (k + 1))
    raise RuntimeError(f'sin respuesta: {url}')

def post(url, body, tries=3):
    for k in range(tries):
        try:
            r = S.post(url, json=body, timeout=30)
            if r.status_code == 200: return r
            r.raise_for_status()
        except requests.RequestException:
            if k == tries - 1: raise
            time.sleep(2 * (k + 1))

def bloque(nombre):
    """Decorador: ejecuta el bloque y, si falla, guarda el error sin parar el resto."""
    def deco(f):
        def w(*a, **kw):
            try:
                return f(*a, **kw)
            except Exception as e:
                OUT['errores'][nombre] = f'{type(e).__name__}: {e}'[:300]
                return None
        return w
    return deco

# ------------------------------------------------------------------------------------------------
# Fuentes
# ------------------------------------------------------------------------------------------------
def binance(symbol, interval='1d', limit=1000):
    """Velas al contado de Binance desde data-api.binance.vision (público, también accesible desde EE. UU.). Solo velas cerradas."""
    j = get('https://data-api.binance.vision/api/v3/klines', dict(symbol=symbol, interval=interval, limit=limit)).json()
    df = pd.DataFrame(j, columns=['t', 'open', 'high', 'low', 'close', 'volume', 'tc', 'qv', 'n', 'tb', 'tq', 'x'])
    df = df[df['tc'] < int(NOW.timestamp() * 1000)]
    df.index = pd.to_datetime(df['t'], unit='ms', utc=True)
    return df[['open', 'high', 'low', 'close', 'volume']].astype(float)

def hyperliquid_velas(coin, interval='1d', dias=1000):
    ms = {'1h': 3600e3, '4h': 14400e3, '1d': 86400e3}[interval]
    end = int(NOW.timestamp() * 1000); start = int(end - min(dias, 4999) * ms)
    j = post('https://api.hyperliquid.xyz/info', {'type': 'candleSnapshot', 'req': {'coin': coin, 'interval': interval, 'startTime': start, 'endTime': end}}).json()
    df = pd.DataFrame(j)
    df = df[df['T'] < end]
    df.index = pd.to_datetime(df['t'], unit='ms', utc=True)
    df = df.rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'})
    return df[['open', 'high', 'low', 'close', 'volume']].astype(float)

def coinmetrics(asset, metrics, start='2010-07-01'):
    rows = []; url = 'https://community-api.coinmetrics.io/v4/timeseries/asset-metrics'
    j = get(url, dict(assets=asset, metrics=','.join(metrics), frequency='1d', page_size=10000, start_time=start)).json()
    rows += j['data']
    while j.get('next_page_url'):
        j = get(j['next_page_url']).json(); rows += j.get('data', [])
    df = pd.DataFrame(rows); df.index = pd.to_datetime(df['time'], utc=True)
    return df[metrics].apply(pd.to_numeric, errors='coerce')

# ------------------------------------------------------------------------------------------------
# Utilidades de cálculo
# ------------------------------------------------------------------------------------------------
def sma(x, n): return x.rolling(n, min_periods=n).mean()
def ema(x, n): return x.ewm(span=n, adjust=False, min_periods=n).mean()
def wilder(x, n): return x.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
def atr(df, n=14):
    pc = df['close'].shift(1)
    tr = pd.concat([df['high'] - df['low'], (df['high'] - pc).abs(), (df['low'] - pc).abs()], axis=1).max(axis=1)
    return wilder(tr, n)
def rsi(c, n=14):
    d = c.diff(); up = wilder(d.clip(lower=0), n); dn = wilder((-d).clip(lower=0), n)
    return 100 - 100 / (1 + up / dn)
def tendencia(c, rapida, lenta):
    a, b = ema(c, rapida), ema(c, lenta)
    return 'alcista' if c.iloc[-1] > a.iloc[-1] > b.iloc[-1] else ('bajista' if c.iloc[-1] < a.iloc[-1] < b.iloc[-1] else 'lateral')
def tendencia_4h(c):
    m = sma(c, 200); m20 = m.shift(20)
    if c.iloc[-1] > m.iloc[-1] > m20.iloc[-1]: return 'alcista'
    if c.iloc[-1] < m.iloc[-1] < m20.iloc[-1]: return 'bajista'
    return 'lateral'
def regimen(c):
    s50, s200 = sma(c, 50), sma(c, 200)
    return bool(c.iloc[-1] > s200.iloc[-1] and s50.iloc[-1] > s50.iloc[-2]), float(s50.iloc[-1]), float(s200.iloc[-1])
def riesgo_velas(df):
    c = df['close']; r = np.log(c / c.shift(1))
    vol30 = float(r.iloc[-30:].std() * 100)
    r2 = (c / c.shift(2) - 1).abs()
    racha = bool((r2.iloc[-3:] > 0.10).any())                 # más de un 10 % en 2 días, en los 3 últimos días
    dia5 = bool((r.abs().iloc[-7:] >= 0.05).any())            # algún día de 5 % o más en los 7 últimos
    return vol30, racha, dia5

# ------------------------------------------------------------------------------------------------
# Bloques
# ------------------------------------------------------------------------------------------------
DATA = {}

@bloque('velas')
def b_velas():
    for s in ['BTC', 'ETH']:
        for iv in ['1h', '4h', '1d']:
            DATA[(s, iv)] = binance(f'{s}USDT', iv)
    for a in ALTS:
        DATA[(a, '1d')] = binance(f'{a}USDT', '1d')
    for iv in ['1h', '4h', '1d']:
        try: DATA[('HYPE', iv)] = hyperliquid_velas('HYPE', iv)
        except Exception as e: OUT['errores'][f'HYPE {iv}'] = str(e)[:200]
    ref = DATA[('BTC', '1d')].index[-1]
    OUT['fecha_cierre_diario'] = str(ref.date())
    return ref

@bloque('tendencia y régimen')
def b_tendencia():
    t = {}
    for s in ['BTC', 'ETH', 'HYPE']:
        if (s, '1d') not in DATA: continue
        d = DATA[(s, '1d')]['close']
        reg, s50, s200 = regimen(d)
        t[s] = dict(cierre=float(d.iloc[-1]), sma50=s50, sma200=s200, permiso_regimen=reg,
                    largo_1d=tendencia(d, 20, 50),
                    medio_4h=tendencia_4h(DATA[(s, '4h')]['close']) if (s, '4h') in DATA else None,
                    corto_1h=tendencia(DATA[(s, '1h')]['close'], 50, 200) if (s, '1h') in DATA else None,
                    vela_4h=str(DATA[(s, '4h')].index[-1]) if (s, '4h') in DATA else None)
    OUT['tendencia'] = t

@bloque('prima de Coinbase')
def b_prima(ref):
    cb = get('https://api.exchange.coinbase.com/products/BTC-USD/candles', dict(granularity=86400)).json()
    cb = pd.Series({pd.Timestamp(x[0], unit='s', tz='UTC'): float(x[4]) for x in cb}).sort_index().loc[:ref]
    bn = DATA[('BTC', '1d')]['close']
    u = coinmetrics('usdt', ['CapMrktCurUSD', 'SplyCur'], start=str((ref - pd.Timedelta(days=40)).date()))
    usdt = (u['CapMrktCurUSD'] / u['SplyCur'])
    fuente_usdt = 'CoinMetrics'
    kr = get('https://api.kraken.com/0/public/OHLC', dict(pair='USDTZUSD', interval=1440)).json()['result']
    kr = pd.Series({pd.Timestamp(int(x[0]), unit='s', tz='UTC'): float(x[4]) for x in list(kr.values())[0]})
    usdt = usdt.reindex(bn.index).combine_first(kr.reindex(bn.index))   # CoinMetrics; si aún no ha publicado el día, Kraken
    if pd.isna(u.reindex([ref]).iloc[0, 0]): fuente_usdt = 'CoinMetrics + Kraken (último día)'
    prem = (cb.reindex(bn.index) / (bn * usdt) - 1) * 100
    p7 = prem.rolling(7, min_periods=7).mean()
    v = float(p7.loc[ref])
    quint = [(-0.0026, -0.5), (0.00076, 0.7), (0.0036, 1.1), (0.0072, 1.7), (99, 2.1)]
    OUT['prima_coinbase'] = dict(media_7d_pct=round(v, 4), ultimo_dia_pct=round(float(prem.loc[ref]), 4), positiva=v > 0,
                                 sesgo_medio_plazo_BTC=+1 if v > 0 else 0,
                                 rentab_media_7d_en_su_quintil_pct=tramo(quint, v)[1], fuente_usdt=fuente_usdt,
                                 lectura='media de 7 días > 0 → +1 al medio plazo de BTC (+1,4 puntos a 7 días en 2023-26)')

@bloque('exceso de OI')
def b_oi(ref):
    def oi_dia(d):
        u = f'https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{d:%Y-%m-%d}.zip'
        z = zipfile.ZipFile(io.BytesIO(get(u).content)); f = z.namelist()[0]
        m = pd.read_csv(z.open(f)).sort_values('create_time')                       # el archivo no viene ordenado
        m = m[pd.to_numeric(m['sum_open_interest_value'], errors='coerce') > 0]     # los ceros son dato ausente
        return float(m['sum_open_interest_value'].iloc[-1]), len(m)
    c = DATA[('BTC', '1d')]['close']
    try:
        o1, n1 = oi_dia(ref); o0, n0 = oi_dia(ref - pd.Timedelta(days=7)); fuente = 'Binance (data.binance.vision)'
    except Exception as e:
        j = get('https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume', dict(ccy='BTC', period='1D')).json()['data']
        s = pd.Series({pd.Timestamp(int(x[0]), unit='ms', tz='UTC').floor('D'): float(x[1]) for x in j}).sort_index()
        o1, o0 = float(s.loc[ref]), float(s.loc[ref - pd.Timedelta(days=7)]); n1 = n0 = None
        fuente = f'OKX (aproximación; Binance falló: {str(e)[:60]})'
    oix = ((o1 / o0 - 1) - (c.loc[ref] / c.loc[ref - pd.Timedelta(days=7)] - 1)) * 100
    OUT['exceso_oi'] = dict(puntos=round(float(oix), 2), oi_usd_millones=round(o1 / 1e6), alarma=bool(oix > 10), fuente=fuente,
                            lectura='> 10 puntos → −1 al medio plazo de BTC (−2,5 puntos a 7 días; caída del 10 % en 7 días: 21 % frente a 9 %)')

@bloque('financiación')
def b_financiacion(ref):
    out = {}
    for s in ['BTC', 'ETH'] + ALTS:
        try:
            j = get('https://www.okx.com/api/v5/public/funding-rate-history', dict(instId=f'{s}-USDT-SWAP', limit=100)).json()['data']
            f = pd.Series({pd.Timestamp(int(x['fundingTime']), unit='ms', tz='UTC'): float(x['fundingRate']) for x in j}).sort_index()
            g = f.groupby(f.index.floor('D'))
            d = g.sum() / 3 * 100                              # % cada 8 horas (equivalente)
            v = float(d.loc[ref]) if ref in d.index else np.nan
            u = UMBRAL_FIN.get(s, 0.02)
            out[s] = dict(pct_8h=round(v, 4), max_7d=round(float(d.loc[:ref].iloc[-7:].max()), 4), umbral=u, alarma=bool(v >= u), fuente='OKX')
        except Exception as e:
            out[s] = dict(error=str(e)[:120])
        time.sleep(0.15)
    try:
        j = post('https://api.hyperliquid.xyz/info', {'type': 'fundingHistory', 'coin': 'HYPE', 'startTime': int((NOW - timedelta(days=10)).timestamp() * 1000)}).json()
        f = pd.Series({pd.Timestamp(int(x['time']), unit='ms', tz='UTC'): float(x['fundingRate']) for x in j}).sort_index()
        d = f.groupby(f.index.floor('D')).sum() / 3 * 100
        v = float(d.loc[ref]) if ref in d.index else np.nan
        out['HYPE'] = dict(pct_8h=round(v, 4), max_7d=round(float(d.loc[:ref].iloc[-7:].max()), 4), umbral=0.02, alarma=bool(v >= 0.02), fuente='Hyperliquid')
    except Exception as e:
        out['HYPE'] = dict(error=str(e)[:120])
    OUT['financiacion'] = dict(umbral_pct_8h='0,02 % (0,03 % en ETH)', por_activo=out,
                               lectura='media del día ≥ 0,02 % cada 8 h (0,03 % en ETH): bandera de riesgo; en altcoins, un día de −10 % en la semana pasa del 18 % al 57 %. '
                                       'Umbrales válidos para Binance y OKX. Hyperliquid paga unas 3 veces más: allí el equivalente es 0,05 % en BTC, 0,06 % en ETH y SOL y 0,02 % en HYPE (en SOL y HYPE: 37 % frente a 14 %).')

@bloque('Reloj de volatilidad: apertura de Nueva York')
def b_reloj(ref):
    from zoneinfo import ZoneInfo
    ny = ZoneInfo('America/New_York'); d = NOW.astimezone(ny).date()
    while True:
        t = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ny).astimezone(timezone.utc)
        if d.weekday() < 5 and t > NOW: break
        d += timedelta(days=1)
    OUT['reloj'] = dict(proxima_apertura_nueva_york_utc=t.strftime('%Y-%m-%d %H:%M'),
                        lectura='de 9:30 a 11:00 de Nueva York es la franja en la que BTC más se mueve (la 1.ª de 48 medias horas en 2023-26; '
                                'el rango de 9:30-9:45 mide un 0,6 % de mediana). No da dirección: el RRA de Álvaro pierde de -0,11 a -0,27 R por operación. '
                                'Sirve para no abrir justo antes ni poner stops ajustados en esa franja. No descuenta festivos de la bolsa.')

@bloque('DVOL y riesgo de día extremo')
def b_riesgo(ref):
    r = {}
    for s in ['BTC', 'ETH']:
        end = int(NOW.timestamp() * 1000); start = end - 60 * 86400000
        j = get('https://www.deribit.com/api/v2/public/get_volatility_index_data',
                dict(currency=s, start_timestamp=start, end_timestamp=end, resolution='1D')).json()['result']['data']
        dv = pd.Series({pd.Timestamp(x[0], unit='ms', tz='UTC'): float(x[4]) for x in j}).sort_index()
        dvol = float(dv.loc[ref])
        vol30, racha, dia5 = riesgo_velas(DATA[(s, '1d')])
        ivp = np.log(dvol) - np.log(vol30 / 100 * np.sqrt(365) * 100)
        _, p5, p10 = tramo(DVOL_TABLA[s], dvol)
        p10_aj = min(2 * BASE_10[s], 100) if (racha or dia5) else BASE_10[s]
        r[s] = dict(dvol=round(dvol, 2), vol30_diaria_pct=round(vol30, 2), dvol_menos_realizada_log=round(float(ivp), 3),
                    racha_10pct_2d=racha, dia_5pct_ultima_semana=dia5,
                    P_dia_5pct_en_7d=p5, P_dia_10pct_en_7d_por_dvol=p10, P_dia_10pct_en_7d_regla_base=p10_aj,
                    aviso_sorpresa=bool(ivp > 0.3))
    for a in ALTS + ['HYPE']:
        if (a, '1d') not in DATA: continue
        vol30, racha, dia5 = riesgo_velas(DATA[(a, '1d')])
        if a == 'HYPE':
            _, p5, p10 = tramo(HYPE_VOL_TABLA, vol30)
            r[a] = dict(vol30_diaria_pct=round(vol30, 2), racha_10pct_2d=racha, dia_5pct_ultima_semana=dia5, P_dia_5pct_en_7d=p5, P_dia_10pct_en_7d=p10)
        else:
            r[a] = dict(vol30_diaria_pct=round(vol30, 2), racha_10pct_2d=racha, dia_5pct_ultima_semana=dia5, P_dia_10pct_en_7d=tramo(ALT_VOL_TABLA, vol30)[1])
    OUT['riesgo'] = r

@bloque('niveles del día')
def b_niveles():
    d = DATA[('BTC', '1d')]; a = float(atr(d).iloc[-1]); c = float(d['close'].iloc[-1])
    hi, lo = float(d['high'].iloc[-1]), float(d['low'].iloc[-1])
    dh, dl = (hi - c) / a, (c - lo) / a
    OUT['niveles_BTC'] = dict(atr_diario=round(a, 1), maximo_ayer=hi, minimo_ayer=lo, dist_max_atr=round(dh, 2), dist_min_atr=round(dl, 2),
                              P_tocar_max_24h=tramo(TOQUE_ATR, dh)[1], P_tocar_min_24h=tramo(TOQUE_ATR, dl)[1],
                              P_tocar_caida_en_7d=LIQ_BTC)

@bloque('ciclo (200 semanas y MVRV-Z)')
def b_ciclo(ref):
    cm = coinmetrics('btc', ['PriceUSD', 'CapMrktCurUSD', 'CapMVRVCur'], start='2010-07-01').dropna(subset=['PriceUSD']).loc[:ref]
    P = cm['PriceUSD']; mcap = cm['CapMrktCurUSD']; rcap = mcap / cm['CapMVRVCur']
    p200w = P / sma(P, 1400)
    pct = p200w.dropna().rolling(1460, min_periods=730).apply(lambda a: (a[:-1] < a[-1]).mean() * 100, raw=True)
    z = (mcap - rcap) / mcap.expanding(min_periods=365).std()
    d = cm.index[-1]
    OUT['ciclo'] = dict(fecha=str(d.date()), precio_entre_media_200_semanas=round(float(p200w.iloc[-1]), 3),
                        percentil_4_anos=round(float(pct.iloc[-1]), 1), mvrv_z=round(float(z.dropna().iloc[-1]), 3),
                        fecha_mvrv=str(z.dropna().index[-1].date()),   # CoinMetrics publica el MVRV uno o dos días más tarde que el precio
                        lectura='contexto de meses: < 1,25 veces la media de 200 semanas y MVRV-Z < 1 = barato; > 2 y MVRV-Z 2-3 = caro (este ciclo)')

@bloque('ETF')
def b_etf():
    j = get('https://bitcoin-data.com/v1/etf-flow-btc').json()     # BGeometrics: 10 llamadas por hora y 15 al día, sin clave
    e = pd.Series({pd.Timestamp(x['d'], tz='UTC'): float(x['etfFlow']) for x in j}).sort_index()
    e = e.loc[:DATA[('BTC', '1d')].index[-1]]
    c = DATA[('BTC', '1d')]['close']
    usd = (e * c.reindex(e.index)).dropna() / 1e6
    w = pd.DataFrame({'usd': usd.resample('W-FRI').sum(min_count=1), 'dias': usd.resample('W-FRI').count()})
    w = w[w['dias'] >= 3]
    last = w.index[-1]; prev52 = w['usd'].iloc[-53:-1]
    p90, p10 = float(prev52.quantile(0.9)), float(prev52.quantile(0.1))
    OUT['etf'] = dict(semana_hasta=str(last.date()), dias=int(w['dias'].iloc[-1]), flujo_semana_M=round(float(w['usd'].iloc[-1])),
                      semana_anterior_M=round(float(w['usd'].iloc[-2])), p90_52s_M=round(p90), p10_52s_M=round(p10),
                      dos_semanas_de_salidas=bool(w['usd'].iloc[-1] < 0 and w['usd'].iloc[-2] < 0),
                      salida_fuerte=bool(w['usd'].iloc[-1] <= p10), entrada_fuerte=bool(w['usd'].iloc[-1] >= p90),
                      lectura='entradas fuertes: nada; salidas fuertes (≤ p10 de 52 semanas) o 2 semanas de salidas: aviso de semanas flojas')

@bloque('contexto (stablecoins y miedo)')
def b_contexto(ref):
    j = get('https://stablecoins.llama.fi/stablecoincharts/all').json()
    s = pd.Series({pd.Timestamp(int(x['date']), unit='s', tz='UTC'): float(x['totalCirculatingUSD'].get('peggedUSD', np.nan)) for x in j}).sort_index()
    f = get('https://api.alternative.me/fng/', dict(limit=40)).json()['data']
    fg = {pd.Timestamp(int(x['timestamp']), unit='s', tz='UTC'): int(x['value']) for x in f}
    OUT['contexto'] = dict(stablecoins_30d_pct=round(float((s.loc[:ref].iloc[-1] / s.loc[:ref - pd.Timedelta(days=30)].iloc[-1] - 1) * 100), 2),
                           miedo_y_codicia=fg.get(ref), nota='solo contexto: no predicen')

@bloque('altcoins')
def b_alts():
    cb = DATA[('BTC', '1d')]['close']; reg_btc, _, _ = regimen(cb)
    out = {}
    for a in ALTS:
        if (a, '1d') not in DATA: continue
        c = DATA[(a, '1d')]['close']
        s50, s200 = sma(c, 50), sma(c, 200)
        ratio = c / cb.reindex(c.index); rs50 = sma(ratio, 50)
        r14 = float(rsi(c).iloc[-1])
        alt_reg = bool(c.iloc[-1] > s200.iloc[-1] and s50.iloc[-1] > s50.iloc[-2]) if not np.isnan(s200.iloc[-1]) else None
        sobre50 = bool(c.iloc[-1] > s50.iloc[-1]); abtc = bool(rs50.iloc[-1] > rs50.iloc[-2])
        out[a] = dict(cierre=float(c.iloc[-1]), sobre_sma50=sobre50, rsi14=round(r14, 1), regimen_alt=alt_reg, alt_btc_subiendo=abtc,
                      permitida=bool(reg_btc and sobre50 and r14 > 55), regla_triple_aviso=bool(reg_btc and alt_reg and abtc))
    OUT['altcoins'] = dict(regimen_btc=reg_btc, por_moneda=out,
                           lectura='permitida = BTC en régimen + altcoin sobre su SMA50 + RSI14 > 55 (+5 puntos a 14 días en 2023-26)')

@bloque('fases (Wyckoff, caja y Elliott)')
def b_fases():
    import fases_objetivas as F
    f = {}
    for s in ['BTC', 'ETH']:
        f[f'{s} 4h'] = F.estado_wyckoff(DATA[(s, '4h')], '4h')
        f[f'{s} 1d'] = F.estado_wyckoff(DATA[(s, '1d')], '1d')
        c4 = F.caja_activa(DATA[(s, '4h')], 'WS02', '4h')
        if c4: c4['P_rompe_arriba'] = round(F.p_rompe_arriba(c4['posicion'], 'WS02', '4h'), 3)
        c1 = F.caja_activa(DATA[(s, '1d')], 'MV10', '1d')
        if c1:
            c1['P_rompe_arriba'] = round(F.p_rompe_arriba(c1['posicion'], 'MV10', '1d'), 3)
            c1['nota'] = 'en 2023-26 la fórmula diaria salió algo alta: con el cierre entre el 20 y el 40 % de la caja, rompió arriba el 25 % (40 casos)'
        f[f'{s} caja 4h (WS-02)'] = c4 or 'sin caja activa'
        f[f'{s} caja 1d (MV-10)'] = c1 or 'sin caja activa'
        f[f'{s} Elliott 4h'] = F.retroceso_elliott(DATA[(s, '4h')], s, '4h')
        f[f'{s} Elliott 1d'] = F.retroceso_elliott(DATA[(s, '1d')], s, '1d')
    if ('HYPE', '1d') in DATA:
        ch = F.caja_activa(DATA[('HYPE', '1d')], 'WS02', '1d')
        if ch:
            ch['P_rompe_arriba'] = round(F.p_rompe_arriba(ch['posicion'], 'WS02', '1d'), 3)
            ch['P_rompe_arriba_calibracion_altcoins'] = round(F.p_rompe_arriba(ch['posicion'], 'WS02', '1d', altcoin=True), 3)
            ch['nota'] = 'calibración de BTC+ETH (la de altcoins da menos); sin validar en HYPE'
        f['HYPE caja 1d (WS-02)'] = ch or 'sin caja activa'
    for k, v in f.items():
        if isinstance(v, dict) and 'historial' in v: v['historial'] = v['historial'][-6:]
    OUT['fases'] = f

# ------------------------------------------------------------------------------------------------
def resumen():
    o = OUT; L = [f"Panel cripto · cierre diario {o.get('fecha_cierre_diario')} (UTC) · generado {o['generado_utc']}"]
    t = o.get('tendencia', {}).get('BTC')
    if t: L.append(f"BTC {t['cierre']:,.0f} · permiso de régimen: {'sí' if t['permiso_regimen'] else 'no'} · diario {t['largo_1d']} · 4h {t['medio_4h']} · 1h {t['corto_1h']}")
    p = o.get('prima_coinbase')
    if p: L.append(f"Prima de Coinbase (7 d): {p['media_7d_pct']:+.4f} % → {'+1 al medio plazo' if p['positiva'] else 'sin +1'}")
    x = o.get('exceso_oi')
    if x: L.append(f"Exceso de OI: {x['puntos']:+.1f} puntos → {'ALARMA (−1)' if x['alarma'] else 'sin alarma'} ({x['fuente']})")
    f = o.get('financiacion', {}).get('por_activo', {})
    al = [k for k, v in f.items() if v.get('alarma')]
    if f: L.append(f"Financiación alta (≥ 0,02 %/8 h; ETH ≥ 0,03 %): {', '.join(al) if al else 'ninguna'} · BTC {f.get('BTC', {}).get('pct_8h')} · ETH {f.get('ETH', {}).get('pct_8h')}")
    for s in ['BTC', 'ETH']:
        r = o.get('riesgo', {}).get(s)
        if r: L.append(f"{s}: DVOL {r['dvol']} · día de ±5 % en 7 d: {r['P_dia_5pct_en_7d']} % · día de ±10 %: {r['P_dia_10pct_en_7d_regla_base']} % (racha: {r['racha_10pct_2d']}, día de 5 %: {r['dia_5pct_ultima_semana']})")
    e = o.get('etf')
    if e: L.append(f"ETF semana hasta {e['semana_hasta']}: {e['flujo_semana_M']:+,} M$ (p10/p90 de 52 semanas: {e['p10_52s_M']:+,} / {e['p90_52s_M']:+,}) · 2 semanas de salidas: {e['dos_semanas_de_salidas']}")
    c = o.get('ciclo')
    if c: L.append(f"Ciclo: precio/media 200 semanas {c['precio_entre_media_200_semanas']} (percentil {c['percentil_4_anos']}) · MVRV-Z {c['mvrv_z']}")
    a = o.get('altcoins')
    if a: L.append(f"Altcoins permitidas: {', '.join(k for k, v in a['por_moneda'].items() if v['permitida']) or 'ninguna'}")
    fz = o.get('fases', {})
    for k in ['BTC 4h', 'ETH 4h']:
        v = fz.get(k)
        if isinstance(v, dict) and v.get('estado') not in (None, 'sin caja activa'):
            L.append(f"{k}: estado {v['estado']} en la caja {v['suelo']:,.2f}-{v['techo']:,.2f} · P(salida final alcista) {v.get('P_salida_final_alcista')} % · casos parecidos {v.get('casos_parecidos')}")
            q = v.get('calidad_ruptura')
            if q: L.append(f"   ruptura: {q['celda']} → aguanta {q['aguanta']} % · toca {v['objetivo_1_altura']:,.2f} (1 altura) antes que la mitad {q['objetivo_1_altura']} % · vuelve antes a la mitad {q['vuelve_a_la_mitad']} %")
    for k in ['BTC Elliott 4h', 'ETH Elliott 4h']:
        v = fz.get(k)
        if isinstance(v, dict) and v.get('fibonacci'):
            pend = [(lv, x) for lv, x in v['fibonacci'].items() if x['estado'] == 'pendiente'][:4]
            if pend: L.append(f"{k}: tramo desde {v['precio_pivote']:,.2f} ({'sube' if v['ultimo_pivote'] == 'L' else 'baja'}), lleva {v['r_extremo']:.2f} del anterior · " +
                              ' · '.join(f"{lv} en {x['precio']:,.2f}: {x['P_llega']} %" for lv, x in pend))
    for k in ['BTC caja 4h (WS-02)', 'BTC caja 1d (MV-10)', 'ETH caja 4h (WS-02)', 'HYPE caja 1d (WS-02)']:
        v = fz.get(k)
        if isinstance(v, dict): L.append(f"{k}: posición {v['posicion']:.2f} → rompe primero arriba {v['P_rompe_arriba'] * 100:.0f} %")
    rl = o.get('reloj')
    if rl: L.append(f"Próxima apertura de Nueva York: {rl['proxima_apertura_nueva_york_utc']} UTC (franja de más volatilidad, sin dirección)")
    if o['errores']: L.append(f"Errores: {o['errores']}")
    return '\n'.join(L)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--json', default=None); ap.add_argument('--hasta', default=None)
    args = ap.parse_args()
    if args.hasta:                                   # todo se corta al final de ese día UTC
        NOW = datetime.strptime(args.hasta, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
        OUT['hasta'] = args.hasta
    ref = b_velas()
    if ref is None:
        print('No se pudieron bajar las velas de BTC:', OUT['errores']); sys.exit(1)
    b_tendencia(); b_prima(ref); b_oi(ref); b_financiacion(ref); b_riesgo(ref); b_niveles(); b_ciclo(ref); b_etf(); b_contexto(ref); b_alts(); b_fases(); b_reloj(ref)
    print(resumen())
    if args.json:
        json.dump(OUT, open(args.json, 'w'), ensure_ascii=False, indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x))
        print('Guardado en', args.json)
