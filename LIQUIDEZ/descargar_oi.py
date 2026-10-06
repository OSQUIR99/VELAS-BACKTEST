# -*- coding: utf-8 -*-
"""Descarga el interés abierto de BTCUSDT (Binance futuros, cada 5 min) desde data.binance.vision
y lo guarda en oi_btc.parquet. Tarda unos minutos (un archivo por día desde sept-2020)."""
import io, zipfile, datetime as dt, urllib.request, concurrent.futures as cf
import numpy as np, pandas as pd
URL = 'https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{}.zip'

def bajar(d):
    try:
        with urllib.request.urlopen(URL.format(d), timeout=30) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
            return pd.read_csv(z.open(z.namelist()[0]))
    except Exception:
        return None

if __name__ == '__main__':
    dias = pd.date_range('2020-09-01', '2026-09-29').date
    with cf.ThreadPoolExecutor(12) as ex:
        partes = [p for p in ex.map(bajar, dias) if p is not None]
    oi = pd.concat(partes, ignore_index=True)
    oi['fecha'] = pd.to_datetime(oi.create_time)
    oi = oi.sort_values('fecha').drop_duplicates('fecha')[['fecha', 'sum_open_interest', 'sum_open_interest_value',
                                                           'count_long_short_ratio', 'sum_taker_long_short_vol_ratio']]
    x = oi.sum_open_interest
    r = x / x.rolling(12, min_periods=1).median()
    oi.loc[(x <= 0) | (r < 0.7) | (r > 1.4), 'sum_open_interest'] = np.nan   # limpia ceros y saltos erróneos
    oi['sum_open_interest'] = oi.sum_open_interest.ffill()
    oi.to_parquet('oi_btc.parquet')
    print(len(oi), oi.fecha.min(), oi.fecha.max())
