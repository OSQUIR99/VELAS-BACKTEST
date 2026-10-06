# -*- coding: utf-8 -*-
"""Construye el ESTADO diario histórico (2017 -> hoy) a partir de los datos de la carpeta de velas."""
import io, json
import numpy as np, pandas as pd
from prep import fred, yahoo

U = 'datos/RADAR_BTC/brutos'
tk = pd.read_csv(f'{U}/binance_btc_1d_taker.csv', parse_dates=['fecha']).set_index('fecha')
idx = pd.date_range(tk.index.min(), tk.index.max() - pd.Timedelta(days=1), freq='D')  # sin la vela de hoy (incompleta)
E = tk[['o', 'h', 'l', 'c', 'v', 'taker_buy_v']].reindex(idx).astype(float)
cb = pd.read_csv(f'{U}/coinbase_btcusd_1d.csv', parse_dates=['fecha']).set_index('fecha')
E['cb_c'] = cb['c'].reindex(idx)
f = pd.read_parquet('datos/CRIPTO_PERPETUOS/BTC/financiacion.parquet'); f['fecha'] = pd.to_datetime(f['fecha'])
E['funding_dia'] = f.set_index('fecha')['tasa'].resample('1D').sum().reindex(idx)
E.loc[E.index < f['fecha'].min().normalize(), 'funding_dia'] = np.nan
st = pd.read_csv(f'{U}/stablecoins.csv', parse_dates=['fecha']).set_index('fecha')
E['stables_usd'] = (st['usdt_usd'].fillna(0) + st['usdc_usd'].fillna(0)).reindex(idx)
E['etf_flujo_musd'] = np.nan
F = fred()
for k in ['DGS2', 'DGS10', 'DFII10', 'DFF', 'DTWEXBGS', 'NFCI', 'BAA10Y', 'WALCL', 'VIXCLS', 'DEXJPUS']:
    E[k] = F[k].reindex(idx)            # en su fecha de observación (el retraso se aplica en el núcleo)
E['WTREGEN'] = np.nan; E['RRPONTSYD'] = np.nan
try:
    L = json.load(open(f'{U}/fred_liquidez.json'))
    for k in ['WTREGEN', 'RRPONTSYD', 'WALCL', 'DTWEXBGS']:
        if k in L:
            s = pd.read_csv(io.StringIO(L[k])); s.columns = ['fecha', k]; s['fecha'] = pd.to_datetime(s['fecha'])
            E[k] = pd.to_numeric(s.set_index('fecha')[k], errors='coerce').reindex(idx)
    print('liquidez FRED incorporada')
except FileNotFoundError:
    print('sin fred_liquidez.json (TGA y repo inversa quedan vacías por ahora)')
Y = yahoo()
q = np.log(Y['QQQ'].dropna()).diff()
E['nasdaq_ret'] = q.reindex(idx)
E.index.name = 'fecha'
E.to_csv('estado_historico.csv', float_format='%.8g')
print(E.shape, E.index.min().date(), E.index.max().date())
print(E.tail(3).T.to_string())
