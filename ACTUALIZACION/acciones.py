# -*- coding: utf-8 -*-
"""Velas DIARIAS de las acciones de la lista de seguimiento (ACTUALIZACION/acciones_lista.csv), desde Yahoo Finance.

  python3 ACTUALIZACION/acciones.py              # todas las de la lista
  python3 ACTUALIZACION/acciones.py --solo HST,RACE.MI

  - Primera vez de cada acción: toda su historia -> CARPETA_DE_BACKTEST/ACCIONES/<simbolo>/1d.parquet (no se vuelve a tocar).
  - Después: solo lo nuevo, en ACTUALIZACION/velas/CARPETA_DE_BACKTEST/ACCIONES/<simbolo>/... (igual que el resto de series).
  - Columnas como TRADICIONAL: fecha (apertura de la sesión, UTC), apertura, maximo, minimo, cierre, volumen.
    Precios ajustados por splits (no por dividendos), como da Yahoo. Solo velas cerradas.
  - De una en una, con pausa y reintentos (Yahoo corta con 429). Un fallo en una acción no para las demás.
"""
import os, sys, json, time, random, argparse, urllib.request, urllib.error, urllib.parse
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import actualizar as A

CARPETA = 'CARPETA_DE_BACKTEST/ACCIONES'
LISTA = os.path.join(AQUI, 'acciones_lista.csv')
COLS = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'


def yahoo(simbolo, desde=None):
    p = {'interval': '1d', 'includeAdjustedClose': 'false', 'events': 'split'}
    if desde is None:
        p.update(period1='0', period2=str(int(time.time()) + 86400))
    else:
        p.update(period1=str(int((desde - pd.Timedelta(days=7)).timestamp())), period2=str(int(time.time()) + 86400))
    ultimo = None
    for intento, espera in enumerate((0, 10, 30, 60, 120)):
        time.sleep(espera + random.uniform(0.3, 0.8))
        host = ('query1', 'query2')[intento % 2]
        url = f'https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(simbolo)}?' + urllib.parse.urlencode(p)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code == 404: raise
        except Exception as e:
            ultimo = e
    else:
        raise ultimo
    res = d['chart']['result'][0]
    ts = res.get('timestamp') or []
    if not ts: return None
    q = res['indicators']['quote'][0]
    df = pd.DataFrame({'fecha': pd.to_datetime(ts, unit='s'), 'apertura': q['open'], 'maximo': q['high'],
                       'minimo': q['low'], 'cierre': q['close'], 'volumen': q['volume']})
    df = df.dropna(subset=['apertura', 'maximo', 'minimo', 'cierre']).astype({c: float for c in COLS[1:]})
    df['fecha'] = df.fecha.astype('datetime64[ms]')
    df = df.sort_values('fecha')
    df = df[~df.fecha.dt.normalize().duplicated(keep='last')]
    # vela en curso: la sesión de hoy aún no ha cerrado
    reg = (res.get('meta', {}).get('currentTradingPeriod') or {}).get('regular') or {}
    if len(df) and reg.get('end'):
        ini, fin = pd.to_datetime(reg['start'], unit='s'), pd.to_datetime(reg['end'], unit='s')
        if df.fecha.iloc[-1] >= ini - pd.Timedelta(hours=1) and A.AHORA < fin + pd.Timedelta(minutes=20):
            df = df.iloc[:-1]
    return df.reset_index(drop=True)


def lista():
    return pd.read_csv(LISTA).yahoo.dropna().astype(str).tolist()


def actualizar_acciones(est, solo=None):
    informe = {'acciones_ok': 0, 'acciones_nuevas': 0, 'velas': 0, 'fallos': []}
    for sim in lista():
        if solo and sim not in solo: continue
        clave = f'{CARPETA}|{sim}|1d'
        e = est.get(clave)
        try:
            if e is None:
                df = yahoo(sim)
                if df is None or not len(df): raise ValueError('sin velas')
                d = os.path.join(A.RAIZ, CARPETA, sim); os.makedirs(d, exist_ok=True)
                df[COLS].to_parquet(os.path.join(d, '1d.parquet'), index=False, compression='zstd')
                est[clave] = {'base_hasta': str(df.fecha.max()), 'base_velas': len(df), 'hasta': str(df.fecha.max()),
                              'desde': str(df.fecha.min()), 'nuevas': 0, 'columnas': COLS, 'muerta': False, 'fuente': f'Yahoo ({sim})'}
                informe['acciones_nuevas'] += 1; informe['velas'] += len(df)
            else:
                hasta = pd.Timestamp(e['hasta'])
                df = yahoo(sim, hasta)
                n = df[df.fecha.dt.normalize() > hasta.normalize()] if df is not None else None
                if n is not None and len(n):
                    A.escribir(CARPETA, sim, {'1d': n[COLS]})
                    e['hasta'] = str(n.fecha.max()); e['nuevas'] = e.get('nuevas', 0) + len(n)
                    informe['velas'] += len(n)
            informe['acciones_ok'] += 1
        except Exception as ex:
            informe['fallos'].append(f'{sim}: {ex.__class__.__name__}: {str(ex)[:120]}')
    indice(est)
    return informe


def indice(est):
    idx = pd.read_csv(A.INDICE)
    idx = idx[idx.carpeta != CARPETA]
    filas = []
    for k, e in est.items():
        c, act, tf = k.split('|')
        if c != CARPETA: continue
        filas.append({'carpeta': c, 'activo': act, 'tf': tf, 'velas': int(e['base_velas']) + int(e.get('nuevas', 0)),
                      'desde': e.get('desde', ''), 'hasta': str(pd.Timestamp(e['hasta'])), 'fuente': e.get('fuente', f'Yahoo ({act})')})
    if filas:
        idx = pd.concat([idx, pd.DataFrame(filas).sort_values('activo')], ignore_index=True)
    idx.to_csv(A.INDICE, index=False)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--solo', default=''); a = ap.parse_args()
    est = A.leer_estado()
    inf = actualizar_acciones(est, set(a.solo.split(',')) if a.solo else None)
    A.guardar_estado(est)
    print(json.dumps(inf, ensure_ascii=False, indent=1))
