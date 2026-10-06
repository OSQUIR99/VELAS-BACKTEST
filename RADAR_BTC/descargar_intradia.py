# -*- coding: utf-8 -*-
"""Descarga velas de 4 h y 1 h de BTCUSDT (Binance contado) CON el volumen comprador agresivo, desde 2017.
Uso (Terminal del Mac):
    cd "$HOME/Desktop/VELAS PARA BACKTEST/RADAR_BTC"
    python3 descargar_intradia.py
Tarda 1-3 minutos. Crea brutos/binance_btc_4h_taker.csv y brutos/binance_btc_1h_taker.csv
"""
import json, os, time, urllib.request
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, 'brutos'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36'}

def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            print('   reintento', i + 1, e); time.sleep(3)
    raise RuntimeError(url)

def bajar(intervalo, paso_ms):
    filas, ini = [], 1502928000000
    while True:
        k = get(f'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval={intervalo}&limit=1000&startTime={ini}')
        if not k: break
        filas += k
        ini = k[-1][0] + paso_ms
        print(f'   {intervalo}: {len(filas)} velas', end='\r')
        if len(k) < 1000: break
        time.sleep(0.25)
    ruta = os.path.join(OUT, f'binance_btc_{intervalo}_taker.csv')
    with open(ruta, 'w') as f:
        f.write('t,o,h,l,c,v,qv,n,taker_buy_v\n')
        for x in filas:
            f.write(f'{x[0]},{x[1]},{x[2]},{x[3]},{x[4]},{x[5]},{x[7]},{x[8]},{x[9]}\n')
    print(f'OK   {intervalo}: {len(filas)} velas -> {ruta}')

if __name__ == '__main__':
    for iv, ms in [('4h', 4 * 3600000), ('1h', 3600000)]:
        try:
            bajar(iv, ms)
        except Exception as e:
            print('FALLO', iv, e)
    print('Hecho. Avisa a Claude.')
