# -*- coding: utf-8 -*-
"""Velas históricas de TradingView sin sesión (conexión pública por websocket, datos con retraso en algunos mercados)."""
import json, random, re, string, os
import pandas as pd
import websocket

TF = {'5m': '5', '15m': '15', '1h': '60', '4h': '240', '1d': '1D', '1w': '1W'}

def _msg(f, p):
    s = json.dumps({'m': f, 'p': p}, separators=(',', ':'))
    return f'~m~{len(s)}~m~{s}'

def velas_tv(simbolo, tf, n=5000, timeout=40, sesion='regular', ajuste='splits'):
    """DataFrame con fecha (UTC, apertura de la vela), apertura, maximo, minimo, cierre, volumen."""
    kw = {'header': ['Origin: https://www.tradingview.com'], 'timeout': timeout}
    px = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if px:
        m = re.match(r'https?://(?:([^:@]+):([^@]+)@)?([^:/]+):(\d+)', px)
        if m:
            kw.update(http_proxy_host=m.group(3), http_proxy_port=int(m.group(4)), proxy_type='http')
            if m.group(1): kw['http_proxy_auth'] = (m.group(1), m.group(2))
    ws = websocket.create_connection('wss://data.tradingview.com/socket.io/websocket', **kw)
    cs = 'cs_' + ''.join(random.choices(string.ascii_lowercase, k=12))
    for f, p in [('set_auth_token', ['unauthorized_user_token']), ('chart_create_session', [cs, '']),
                 ('resolve_symbol', [cs, 'sds_sym_1', '=' + json.dumps({'symbol': simbolo, 'adjustment': ajuste, 'session': sesion})]),
                 ('create_series', [cs, 'sds_1', 's1', 'sds_sym_1', TF[tf], n, ''])]:
        ws.send(_msg(f, p))
    filas, err = [], None
    try:
        while True:
            raw = ws.recv()
            for parte in re.split(r'~m~\d+~m~', raw):
                if not parte: continue
                if parte.startswith('~h~'): ws.send(f'~m~{len(parte)}~m~{parte}'); continue
                try: d = json.loads(parte)
                except ValueError: continue
                m = d.get('m')
                if m in ('timescale_update', 'du'):
                    s = d['p'][1].get('sds_1', {}).get('s', [])
                    filas += [x['v'] for x in s]
                elif m in ('symbol_error', 'series_error', 'critical_error'):
                    err = f'{simbolo} {tf}: {m} {d.get("p")}'
                if m == 'series_completed' or err: raise StopIteration
    except StopIteration:
        pass
    finally:
        ws.close()
    if err: raise RuntimeError(err)
    if not filas: return pd.DataFrame(columns=['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen'])
    df = pd.DataFrame([(r + [0] * 6)[:6] for r in filas], columns=['t', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen'])
    df['fecha'] = pd.to_datetime(df.t, unit='s')
    return df.drop(columns='t').drop_duplicates('fecha').sort_values('fecha')[['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']].reset_index(drop=True)
