# -*- coding: utf-8 -*-
"""Correlación BTC vs macro alineada en el mismo día (cierre EE. UU. ≈ cierre de la vela diaria de BTC)."""
import numpy as np, pandas as pd
from prep import yahoo, fred, btc_diario

b = btc_diario()['c']
Y = yahoo(); F = fred()
lb = np.log(b)
df = pd.DataFrame({'qqq': Y['QQQ'], 'dxy': Y['DXY'], 'gld': Y['GLD'], 'real10': F['DFII10'], 'y2': F['DGS2'], 'hy': F['BAMLH0A0HYM2']})
df = df[df.index >= b.index.min()]
df['btc'] = lb.reindex(df.index)  # vela de BTC del mismo día UTC (cierra a medianoche UTC, ~3-4 h tras Wall Street)
d = df.dropna(subset=['qqq', 'btc']).copy()
R = pd.DataFrame({'btc': d['btc'].diff(), 'nasdaq': np.log(d['qqq']).diff(), 'dolar': np.log(d['dxy']).diff(),
                  'oro': np.log(d['gld']).diff(), 'tipo_real_10a': d['real10'].diff(), 'bono_2a': d['y2'].diff()}).dropna(subset=['btc', 'nasdaq'])
anual = R.groupby(R.index.year).apply(lambda g: g.corr()['btc'].drop('btc')).round(2)
print('CORRELACIÓN DIARIA (mismo día) DE BTC CON…'); print(anual.to_string())
# semanal (más robusta a desfases horarios)
W = pd.DataFrame({'btc': lb, 'qqq': np.log(Y['QQQ']), 'dxy': np.log(Y['DXY']), 'real10': F['DFII10'], 'gld': np.log(Y['GLD'])}).ffill()
W = W[W.index >= b.index.min()].resample('W-FRI').last().diff().dropna()
anualw = W.groupby(W.index.year).apply(lambda g: g.corr()['btc'].drop('btc')).round(2)
print('\nCORRELACIÓN SEMANAL DE BTC CON…'); print(anualw.to_string())
anualw.to_csv('corr_semanal_anual.csv')
anual.to_csv('corr_diaria_anual.csv')
