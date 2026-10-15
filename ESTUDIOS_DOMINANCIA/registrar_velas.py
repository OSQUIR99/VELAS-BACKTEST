# -*- coding: utf-8 -*-
"""Guarda las últimas velas DIARIAS CERRADAS de las gráficas de dominancia (escáner público de TradingView).

  python3 registrar_velas.py [velas_recientes.csv]

El escáner da la vela de hoy (sin cerrar) y las anteriores con close[1], close[2]…; aquí solo se guardan las
cerradas (1, 2 y 3 días atrás), sin duplicados. Lo ejecuta GitHub cada día a las 00:25 UTC
(.github/workflows/velas_dominancias.yml) y `dominancias.py` lo une a las velas del repositorio.
"""
import sys, os, json, csv, datetime as dt, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'velas_recientes.csv')
SIMBOLOS = {'ETH_BTC': 'BINANCE:ETHBTC', 'others_fuera_top10': 'CRYPTOCAP:OTHERS',
            'total3_sin_btc_eth': 'CRYPTOCAP:TOTAL3', 'dominancia_btc': 'CRYPTOCAP:BTC.D',
            'dominancia_usdt': 'CRYPTOCAP:USDT.D', 'BTC': 'BINANCE:BTCUSDT'}
ATRAS = (1, 2, 3)

def leer():
    cols = ['time'] + [f'{c}[{k}]' for k in ATRAS for c in ('open', 'high', 'low', 'close')]
    body = json.dumps({'symbols': {'tickers': list(SIMBOLOS.values())}, 'columns': cols}).encode()
    r = urllib.request.urlopen(urllib.request.Request('https://scanner.tradingview.com/global/scan', body,
                               {'Content-Type': 'application/json'}), timeout=20)
    datos = {x['s']: x['d'] for x in json.load(r)['data']}
    filas = []
    for serie, sim in SIMBOLOS.items():
        d = datos.get(sim)
        if not d: continue
        abierta = dt.datetime.fromtimestamp(d[0], dt.timezone.utc).date()     # vela de hoy, sin cerrar
        for i, k in enumerate(ATRAS):
            o, h, l, c = d[1 + 4 * i: 5 + 4 * i]
            if None in (o, h, l, c): continue
            filas.append({'serie': serie, 'fecha': str(abierta - dt.timedelta(days=k)),
                          'apertura': o, 'maximo': h, 'minimo': l, 'cierre': c})
    return filas

def main():
    viejas = []
    if os.path.exists(SALIDA):
        with open(SALIDA) as f: viejas = list(csv.DictReader(f))
    todas = {(r['serie'], r['fecha']): r for r in viejas}
    nuevas = leer()
    for r in nuevas: todas[(r['serie'], r['fecha'])] = r      # la lectura más reciente manda
    with open(SALIDA, 'w', newline='') as f:
        w = csv.DictWriter(f, ['serie', 'fecha', 'apertura', 'maximo', 'minimo', 'cierre'])
        w.writeheader()
        for k in sorted(todas): w.writerow(todas[k])
    print(f'{len(nuevas)} velas leídas; {len(todas)} en total en {SALIDA}')

if __name__ == '__main__':
    main()
