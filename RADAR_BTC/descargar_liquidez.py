# -*- coding: utf-8 -*-
"""Descarga los datos de LIQUIDEZ y FLUJO que la consola de Claude no puede bajar.
Uso (Terminal normal del Mac):
    cd "$HOME/Desktop/VELAS PARA BACKTEST/RADAR_BTC"
    python3 descargar_liquidez.py
Crea la carpeta brutos/ con varios ficheros. Tarda 1-2 minutos. Solo usa la librería estándar + pandas.
"""
import json, os, time, urllib.request, io, ssl
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, 'brutos'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36'}

def get(url, intentos=3):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            print('   reintento', i + 1, url[:80], e); time.sleep(3)
    raise RuntimeError('No se pudo bajar ' + url)

def paso(nombre, fn):
    try:
        fn(); print('OK  ', nombre)
    except Exception as e:
        print('FALLO', nombre, '->', e)

# 1) FRED: liquidez de bancos centrales y del Tesoro
FRED = ['WALCL', 'WTREGEN', 'RRPONTSYD', 'WRESBAL', 'ECBASSETSW', 'JPNASSETS', 'DEXUSEU', 'DEXJPUS',
        'M2SL', 'NFCI', 'ANFCI', 'DTWEXBGS', 'SOFR', 'IORB', 'DFII10', 'DGS2', 'DFF', 'BAMLH0A0HYM2', 'BAA10Y', 'VIXCLS']
def fred():
    datos, fallos = {}, []
    for s in FRED:
        try:
            txt = get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}').decode()
            if 'observation_date' not in txt[:200] and 'DATE' not in txt[:200]:
                raise RuntimeError('respuesta rara: ' + txt[:80])
            datos[s] = txt
        except Exception as e:
            fallos.append(s); print('   sin', s, '->', e)
        time.sleep(1)
    json.dump(datos, open(os.path.join(OUT, 'fred_liquidez.json'), 'w'))
    print('   FRED: bajadas', len(datos), 'de', len(FRED), '; fallos:', fallos)

# 2) Stablecoins (DefiLlama): oferta total en dólares, diaria
def stables():
    total = json.loads(get('https://stablecoins.llama.fi/stablecoincharts/all'))
    filas = [(pd.to_datetime(int(x['date']), unit='s'), x.get('totalCirculatingUSD', {}).get('peggedUSD')) for x in total]
    df = pd.DataFrame(filas, columns=['fecha', 'stables_usd'])
    for sid, nom in [(1, 'usdt_usd'), (2, 'usdc_usd')]:
        d = json.loads(get(f'https://stablecoins.llama.fi/stablecoincharts/all?stablecoin={sid}'))
        s = pd.DataFrame([(pd.to_datetime(int(x['date']), unit='s'), x.get('totalCirculatingUSD', {}).get('peggedUSD')) for x in d], columns=['fecha', nom])
        df = df.merge(s, on='fecha', how='left')
    df.to_csv(os.path.join(OUT, 'stablecoins.csv'), index=False)

# 3) Binance contado BTCUSDT diario CON volumen comprador agresivo (taker buy), desde 2017
def binance_taker():
    filas, ini = [], 1502928000000  # 17-ago-2017
    while True:
        url = f'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000&startTime={ini}'
        k = json.loads(get(url))
        if not k: break
        filas += k
        ini = k[-1][0] + 86400000
        if len(k) < 1000: break
        time.sleep(0.3)
    df = pd.DataFrame(filas, columns=['t', 'o', 'h', 'l', 'c', 'v', 'tc', 'qv', 'n', 'taker_buy_v', 'taker_buy_qv', 'x'])
    df['fecha'] = pd.to_datetime(df['t'], unit='ms')
    df[['fecha', 'o', 'h', 'l', 'c', 'v', 'qv', 'n', 'taker_buy_v', 'taker_buy_qv']].to_csv(os.path.join(OUT, 'binance_btc_1d_taker.csv'), index=False)

# 4) Coinbase BTC-USD diario (para la "prima de Coinbase" frente a Binance), desde 2017
def coinbase():
    filas = []
    fin = pd.Timestamp.utcnow().tz_localize(None).normalize()
    ini = pd.Timestamp('2017-08-01')
    while ini < fin:
        f2 = min(ini + pd.Timedelta(days=299), fin)
        url = f'https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start={ini:%Y-%m-%d}&end={f2:%Y-%m-%d}'
        filas += json.loads(get(url)); ini = f2 + pd.Timedelta(days=1); time.sleep(0.4)
    df = pd.DataFrame(filas, columns=['t', 'l', 'h', 'o', 'c', 'v'])
    df['fecha'] = pd.to_datetime(df['t'], unit='s')
    df.drop_duplicates('fecha').sort_values('fecha')[['fecha', 'o', 'h', 'l', 'c', 'v']].to_csv(os.path.join(OUT, 'coinbase_btcusd_1d.csv'), index=False)

# 5) Flujos diarios de los ETF de bitcoin al contado (Farside), desde ene-2024
def etf():
    html = get('https://farside.co.uk/btc/').decode('utf-8', 'ignore')
    open(os.path.join(OUT, 'farside_btc.html'), 'w').write(html)

if __name__ == '__main__':
    print('Descargando en', OUT)
    paso('FRED (liquidez)', fred)
    import sys
    if '--solo-fred' not in sys.argv:
        paso('Stablecoins (DefiLlama)', stables)
        paso('Binance diario con taker buy', binance_taker)
        paso('Coinbase diario', coinbase)
    paso('ETF Farside', etf)
    print('Hecho. Avisa a Claude.')
