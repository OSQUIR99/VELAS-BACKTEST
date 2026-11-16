import sys, os
sys.path.insert(0, '/home/claude/contexto-cartera/BOT/codigo/estudios')
import numpy as np, pandas as pd
import origen_descargar_datos as G
os.makedirs(G.DATA, exist_ok=True)
pd.DataFrame({'semaforo': np.full(4000, np.nan)}, index=pd.date_range('2015-01-01', periods=4000)).to_parquet(os.path.join(G.DATA, 'semaforo.parquet'))
pd.read_parquet('/home/claude/velas-backtest/LIQUIDEZ/linea_reconstruida_2026_10.parquet').to_parquet(os.path.join(G.DATA, 'linea.parquet'))
for s in ['BTC', 'ETH', 'SOL', 'ADA', 'LINK', 'ZEC']: G.binance(s)
