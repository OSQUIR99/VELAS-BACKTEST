# -*- coding: utf-8 -*-
"""Velas DIARIAS de las acciones de la lista de seguimiento (ACTUALIZACION/acciones_lista.csv), desde TradingView (tv.py, como TRADICIONAL); <simbolo> = nombre de Yahoo de la lista.

  python3 ACTUALIZACION/acciones.py              # todas las de la lista
  python3 ACTUALIZACION/acciones.py --solo HST,RACE.MI

  - Primera vez de cada acción: toda su historia -> CARPETA_DE_BACKTEST/ACCIONES/<simbolo>/1d.parquet (no se vuelve a tocar).
  - Después: solo lo nuevo, en ACTUALIZACION/velas/CARPETA_DE_BACKTEST/ACCIONES/<simbolo>/... (igual que el resto de series).
  - Columnas como TRADICIONAL: fecha (apertura de la sesión, UTC), apertura, maximo, minimo, cierre, volumen.
    Precios ajustados por splits (no por dividendos). Solo velas cerradas.
  - De una en una, con pausa y reintentos (TradingView corta con 429). Un fallo en una acción no para las demás.
"""
import os, sys, json, time, random, argparse, urllib.request, urllib.error, urllib.parse
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import actualizar as A
from tv import velas_tv

TV = {}

CARPETA = 'CARPETA_DE_BACKTEST/ACCIONES'
LISTA = os.path.join(AQUI, 'acciones_lista.csv')
COLS = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'


def descargar(simbolo, desde=None):
    """Velas 1d desde TradingView con tv.py (el mismo método que TRADICIONAL), con el símbolo de TradingView de la lista."""
    tv = TV[simbolo]
    n = 5000 if desde is None else int(min(5000, max(30, (A.AHORA - desde).days + 30)))
    ultimo = None
    for espera in (0, 15, 45, 120):
        time.sleep(espera or 1.0)
        try:
            df = velas_tv(tv, '1d', n=n, ajuste='splits')
            break
        except Exception as ex:
            ultimo = ex
            if '429' not in str(ex) and espera >= 15: raise
    else:
        raise ultimo
    if df is None or not len(df): return None
    df = df.sort_values('fecha')
    df['fecha'] = df.fecha.astype('datetime64[ms]')
    df = df[~df.fecha.dt.normalize().duplicated(keep='last')].astype({c: float for c in COLS[1:]})
    # vela de hoy sin cerrar: Europa cierra hacia las 16:40 UTC, EE. UU. hacia las 21:00 UTC
    cierre_h = 21.25 if tv.split(':')[0] in ('NYSE', 'NASDAQ', 'AMEX') else 17.0
    hoy = A.AHORA.normalize()
    if len(df) and df.fecha.iloc[-1].normalize() >= hoy and A.AHORA < hoy + pd.Timedelta(hours=cierre_h):
        df = df.iloc[:-1]
    return df[COLS].reset_index(drop=True)


def lista():
    t = pd.read_csv(LISTA).dropna()
    TV.update(dict(zip(t.yahoo.astype(str), t.tradingview.astype(str))))
    return list(TV)


PRESUPUESTO_S = 30 * 60   # como mucho 30 min por ejecución; lo que falte se hace mañana (se guarda lo hecho)


def actualizar_acciones(est, solo=None):
    informe = {'acciones_ok': 0, 'acciones_nuevas': 0, 'velas': 0, 'fallos': [], 'pendientes': 0}
    t0, seguidos = time.time(), 0
    for i, sim in enumerate(lista()):
        if solo and sim not in solo: continue
        if time.time() - t0 > PRESUPUESTO_S or seguidos >= 8:   # 8 fallos seguidos = nos están cortando: parar
            informe['pendientes'] += 1; continue
        if i % 25 == 0:
            print(f'{i} {sim} {time.time() - t0:.0f}s ok={informe["acciones_ok"]} fallos={len(informe["fallos"])}', flush=True)
            A.guardar_estado(est)
        clave = f'{CARPETA}|{sim}|1d'
        e = est.get(clave)
        try:
            if e is None:
                df = descargar(sim)
                if df is None or not len(df): raise ValueError('sin velas')
                d = os.path.join(A.RAIZ, CARPETA, sim); os.makedirs(d, exist_ok=True)
                df[COLS].to_parquet(os.path.join(d, '1d.parquet'), index=False, compression='zstd')
                est[clave] = {'base_hasta': str(df.fecha.max()), 'base_velas': len(df), 'hasta': str(df.fecha.max()),
                              'desde': str(df.fecha.min()), 'nuevas': 0, 'columnas': COLS, 'muerta': False, 'fuente': f'TradingView ({TV[sim]})'}
                informe['acciones_nuevas'] += 1; informe['velas'] += len(df)
            else:
                hasta = pd.Timestamp(e['hasta'])
                df = descargar(sim, hasta)
                n = df[df.fecha.dt.normalize() > hasta.normalize()] if df is not None else None
                if n is not None and len(n):
                    A.escribir(CARPETA, sim, {'1d': n[COLS]})
                    e['hasta'] = str(n.fecha.max()); e['nuevas'] = e.get('nuevas', 0) + len(n)
                    informe['velas'] += len(n)
            informe['acciones_ok'] += 1; seguidos = 0
        except Exception as ex:
            seguidos += 1
            print('FALLO', sim, ex, flush=True)
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
                      'desde': e.get('desde', ''), 'hasta': str(pd.Timestamp(e['hasta'])), 'fuente': e.get('fuente', f'TradingView ({TV.get(act, act)})')})
    if filas:
        idx = pd.concat([idx, pd.DataFrame(filas).sort_values('activo')], ignore_index=True)
    idx.to_csv(A.INDICE, index=False)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--solo', default=''); a = ap.parse_args()
    est = A.leer_estado()
    inf = actualizar_acciones(est, set(a.solo.split(',')) if a.solo else None)
    A.guardar_estado(est)
    print(json.dumps(inf, ensure_ascii=False, indent=1))
