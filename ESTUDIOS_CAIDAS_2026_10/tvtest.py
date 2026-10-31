import os, re, json, random, string
import pandas as pd
def _msg(f, p):
    s = json.dumps({'m': f, 'p': p}, separators=(',', ':'))
    return f'~m~{len(s)}~m~{s}'
def tv(simbolo, tf='1W', n=900, timeout=40):
    import websocket
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
                 ('resolve_symbol', [cs, 'sds_sym_1', '=' + json.dumps({'symbol': simbolo, 'adjustment': 'splits', 'session': 'regular'})]),
                 ('create_series', [cs, 'sds_1', 's1', 'sds_sym_1', tf, n, ''])]:
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
                    filas += [x['v'] for x in d['p'][1].get('sds_1', {}).get('s', [])]
                elif m in ('symbol_error', 'series_error', 'critical_error'):
                    err = f'{simbolo}: {m}'
                if m == 'series_completed' or err: raise StopIteration
    except StopIteration:
        pass
    finally:
        ws.close()
    if err: raise RuntimeError(err)
    s = pd.Series({pd.Timestamp(r[0], unit='s').normalize(): float(r[4]) for r in filas})
    return s[~s.index.duplicated(keep='last')].sort_index()
if __name__=='__main__':
    s=tv('ECONOMICS:USCBBS','1W',50); print(len(s), s.tail(2))
