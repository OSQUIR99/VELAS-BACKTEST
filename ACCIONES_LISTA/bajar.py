# Baja velas diarias (con dividendos) de la lista de seguimiento por la conexión pública de TradingView (tv.py del repositorio)
import sys, csv, os, time, io
sys.path.insert(0, '/home/claude/velas-backtest/ACTUALIZACION')
from tv import velas_tv
import pandas as pd
lista = sys.argv[1]; out = '/home/claude/acciones/datos'
syms = [r['simbolo'] for r in csv.DictReader(open(lista))]
excl_pref = ('CME_MINI:', 'FX:', 'CBOT:', 'TVC:')
ETF = {'XLV','XLP','XLU','XME','JEPI','SCHD','JEPQ','TLT','SHY','IEF','VCIT','DIA'}
ok = bad = 0
for s in syms:
    if s.startswith(excl_pref) or s.split(':')[1] in ETF: continue
    f = os.path.join(out, s.replace(':','_') + '.parquet')
    if os.path.exists(f): continue
    try:
        d = velas_tv(s, '1d', n=12000, ajuste='dividends')
        if len(d) > 250: d.to_parquet(f); ok += 1
        else: bad += 1; print('poco', s, len(d), flush=True)
    except Exception as e:
        bad += 1; print('fallo', s, str(e)[:80], flush=True)
    time.sleep(1.0)
print('ok', ok, 'fallos', bad)
