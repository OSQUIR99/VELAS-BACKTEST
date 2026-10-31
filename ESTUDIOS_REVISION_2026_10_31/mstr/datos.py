import sys, json, re, random, string, os, pickle, pandas as pd, numpy as np
sys.path.insert(0,'/home/claude/liq/herramienta'); import liquidez as LQ
import websocket
def tvohlc(simbolo, tf='1D', n=5000, timeout=60):
    kw={'header':['Origin: https://www.tradingview.com'],'timeout':timeout}
    px=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    m=re.match(r'https?://(?:([^:@]+):([^@]+)@)?([^:/]+):(\d+)',px)
    kw.update(http_proxy_host=m.group(3),http_proxy_port=int(m.group(4)),proxy_type='http')
    if m.group(1): kw['http_proxy_auth']=(m.group(1),m.group(2))
    ws=websocket.create_connection('wss://data.tradingview.com/socket.io/websocket',**kw)
    cs='cs_'+''.join(random.choices(string.ascii_lowercase,k=12))
    for f,p in [('set_auth_token',['unauthorized_user_token']),('chart_create_session',[cs,'']),
        ('resolve_symbol',[cs,'s1','='+json.dumps({'symbol':simbolo,'adjustment':'splits','session':'regular'})]),
        ('create_series',[cs,'sds_1','s1','s1',tf,n,''])]: ws.send(LQ._msg(f,p))
    filas=[]
    try:
        while True:
            raw=ws.recv()
            for parte in re.split(r'~m~\d+~m~',raw):
                if not parte: continue
                if parte.startswith('~h~'): ws.send(f'~m~{len(parte)}~m~{parte}'); continue
                try: d=json.loads(parte)
                except ValueError: continue
                mm=d.get('m')
                if mm in ('timescale_update','du'): filas+=[x['v'] for x in d['p'][1].get('sds_1',{}).get('s',[])]
                if mm in ('series_completed','symbol_error','series_error','critical_error'): raise StopIteration
    except StopIteration: pass
    finally: ws.close()
    df=pd.DataFrame([r[:6] for r in filas],columns=['t','o','h','l','c','v']).drop_duplicates('t')
    df.index=pd.to_datetime(df.t,unit='s'); return df.drop(columns='t').sort_index()
D={}
for k,s in [('MSTR','NASDAQ:MSTR'),('QQQ','NASDAQ:QQQ'),('MARA','NASDAQ:MARA'),('RIOT','NASDAQ:RIOT'),('BTC','BITSTAMP:BTCUSD')]:
    D[k]=tvohlc(s); print(k,len(D[k]),D[k].index[0],D[k].index[-1])
D['BTC1h']=tvohlc('BITSTAMP:BTCUSD','60',20000); print('BTC1h',len(D['BTC1h']),D['BTC1h'].index[0])
pickle.dump(D,open('datos.pkl','wb'))
