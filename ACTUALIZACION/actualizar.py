# -*- coding: utf-8 -*-
"""Actualización diaria de TODAS las velas del repositorio (todas las series de INDICE.csv, todas las temporalidades).

  python3 ACTUALIZACION/actualizar.py                 # añade las velas cerradas que falten hasta ahora
  python3 ACTUALIZACION/actualizar.py --iniciar       # (una vez, con el repositorio entero) crea estado.json
  python3 ACTUALIZACION/actualizar.py --solo BTC,oro  # solo esos activos (pruebas)

Cómo se guarda (para no reescribir los parquet grandes cada día, que engordaría el repositorio):
  - Los archivos originales (<tf>.parquet) NO se tocan.
  - Las velas nuevas van a ACTUALIZACION/velas/<carpeta>/<activo>/<AAAA-MM>/<AAAA-MM-DD>.parquet:
    un archivo por activo y día (según la fecha de apertura de la vela), con todas sus temporalidades (columna `tf`).
  - cargar.py junta original + nuevas solo. `velas(..., actualizado=False)` da la copia fija de siempre.
  - ACTUALIZACION/estado.json guarda, por serie, hasta dónde está guardada. Así GitHub no necesita bajarse los 1,7 GB.

Fuentes (las mismas que el original de cada serie, según INDICE.csv):
  - Binance contado y futuros: archivo oficial diario (data.binance.vision), el mismo que se usó para el histórico.
    Si el archivo del día aún no está publicado: contado → API pública data-api.binance.vision; futuros → se espera.
    1w de Binance: se construye con las velas de 1d (semana de lunes a domingo, hora UTC), como hace Binance.
    Financiación: archivo mensual (se publica a principios del mes siguiente).
  - HYPE al contado: OKX (5m, 15m, 1h) y Hyperliquid (4h, 1d, 1w); si OKX no responde, Hyperliquid.
  - TradingView (índices, tradicionales, dominancias): conexión pública, mismo símbolo que el original.
Solo se guardan velas CERRADAS.
"""
import os, sys, io, json, re, time, zipfile, argparse, datetime as dt, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DIR_VELAS = os.path.join(AQUI, 'velas')
ESTADO = os.path.join(AQUI, 'estado.json')
INDICE = os.path.join(RAIZ, 'INDICE.csv')
sys.path.insert(0, AQUI)

DUR = {'5m': 300, '15m': 900, '1h': 3600, '4h': 14400, '1d': 86400, '1w': 604800}
TV_SIN_PARENTESIS = {'oro': 'COMEX:GC1!', 'plata': 'COMEX:SI1!', 'petroleo_brent': 'TVC:UKOIL',
                     'nasdaq100': 'NASDAQ:NDX', 'sp500': 'SP:SPX', 'dax': 'XETR:DAX'}
AHORA = pd.Timestamp(dt.datetime.now(dt.timezone.utc)).tz_localize(None)
COLS = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen', 'volumen_comprador']


# ------------------------------------------------------------------ utilidades de red
def _get(url, timeout=30, datos=None, cabeceras=None):
    req = urllib.request.Request(url, data=datos, headers={'User-Agent': 'velas-backtest/1.0', **(cabeceras or {})})
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 451, 400): raise
            time.sleep(2 * (intento + 1))
        except Exception:
            if intento == 2: raise
            time.sleep(2 * (intento + 1))


def _ms(x):
    x = pd.to_numeric(x)
    return pd.to_datetime(x // 1000 if x.max() > 1e14 else x, unit='ms')  # el contado de Binance usa microsegundos desde 2025


# ------------------------------------------------------------------ catálogo de series
def catalogo():
    idx = pd.read_csv(INDICE)
    idx['hasta'] = pd.to_datetime(idx.hasta, format='mixed')
    ref = idx.groupby('carpeta').hasta.transform('max')
    out = []
    for r in idx.itertuples():
        f = r.fuente
        s = {'clave': f'{r.carpeta}|{r.activo}|{r.tf}', 'carpeta': r.carpeta, 'activo': r.activo, 'tf': r.tf}
        if r.tf == 'financiacion':
            s.update(tipo='financiacion', simbolo=f'{r.activo}USDT')
        elif f.startswith('TradingView'):
            m = re.search(r'\((.+)\)', f)
            s.update(tipo='tv', simbolo=m.group(1) if m else TV_SIN_PARENTESIS.get(r.activo),
                     tf_base=r.tf.split('_')[0], ajuste='dividends' if 'ajustado' in r.tf else 'splits')
        elif f.startswith('Binance'):
            s.update(tipo='binance', mercado='um' if 'futuros' in f else 'spot',
                     simbolo=('ETHBTC' if r.activo == 'ETH_BTC' else f'{r.activo}USDT'))
        elif f.startswith('Okx'):
            s.update(tipo='okx', simbolo='HYPE-USDT')
        elif f.startswith('Hyperliquid'):
            s.update(tipo='hyperliquid', simbolo='HYPE')
        else:
            continue
        # serie muerta: lleva más de 30 días sin datos respecto al resto de su carpeta (p. ej. TON contado, retirado)
        s['muerta'] = bool((ref[r.Index] - r.hasta).days > 30)
        out.append(s)
    return out


# ------------------------------------------------------------------ estado
def leer_estado():
    return json.load(open(ESTADO)) if os.path.exists(ESTADO) else {}


def guardar_estado(e):
    json.dump(e, open(ESTADO, 'w'), indent=0, ensure_ascii=False, sort_keys=True)


def calibrar(est):
    """Comprueba cada serie de Binance contra su último día guardado y fija el mercado (contado o futuros) que coincide.
    INDICE.csv dice «Binance futuros» en algunas series de 15 min que en realidad son de contado (p. ej. ALGO)."""
    import pyarrow.parquet as pq
    def una(s):
        e = est[s['clave']]
        p = os.path.join(RAIZ, s['carpeta'], s['activo'], s['tf'] + '.parquet')
        base = pq.read_table(p).to_pandas().sort_values('fecha')
        dia = pd.Timestamp(e['base_hasta']).normalize()
        base = base[base.fecha >= dia].set_index('fecha')
        res = {}
        for m in ([s['mercado']] + [x for x in ('spot', 'um') if x != s['mercado']]):
            try:
                n = binance_dia(m, s['simbolo'], s['tf'], dia.strftime('%Y-%m-%d'))
            except Exception:
                n = None
            if n is None: continue
            j = base.join(n.set_index('fecha'), rsuffix='_n', how='inner')
            if len(j):
                dif = float(((j.cierre_n - j.cierre).abs() / j.cierre).max())
                res[m] = (dif, len(j))
                if dif < 1e-9: break
        ok = [m for m, (d, n) in res.items() if d < 1e-9]
        return s['clave'], (ok[0] if ok else None), res
    series = [s for s in catalogo() if s.get('tipo') == 'binance' and s['tf'] != '1w' and not est[s['clave']].get('muerta')]
    with ThreadPoolExecutor(12) as ex:
        for clave, m, res in ex.map(una, series):
            if m: est[clave]['mercado'] = m
            else:
                est[clave]['muerta'] = True
                print('SIN COINCIDENCIA, no se actualiza:', clave, res)
    # el 1w sigue al 1d de su misma moneda
    for s in catalogo():
        if s.get('tipo') == 'binance' and s['tf'] == '1w':
            k1 = s['clave'].rsplit('|', 1)[0] + '|1d'
            if est.get(k1, {}).get('muerta'): est[s['clave']]['muerta'] = True
    cambios = [(s['clave'], s['mercado'], est[s['clave']].get('mercado')) for s in series if est[s['clave']].get('mercado') not in (None, s['mercado'])]
    print('Mercado corregido respecto a INDICE.csv:', cambios)


def iniciar():
    """Con el repositorio completo: lee el último dato real de cada parquet y las columnas."""
    import pyarrow.parquet as pq
    est = {}
    for s in catalogo():
        p = os.path.join(RAIZ, s['carpeta'], s['activo'], s['tf'] + '.parquet')
        t = pq.read_table(p)
        df = t.select(['fecha']).to_pandas()
        e = {'base_hasta': str(df.fecha.max()), 'base_velas': len(df), 'hasta': str(df.fecha.max()), 'nuevas': 0,
             'columnas': t.schema.names, 'muerta': s['muerta']}
        if s['tf'] == '1d' and s.get('tipo') in ('binance', 'hyperliquid'):
            cola = t.to_pandas().sort_values('fecha').tail(7)
            e['semilla_1d'] = json.loads(cola.to_json(orient='records', date_format='iso'))
        est[s['clave']] = e
    calibrar(est)
    guardar_estado(est)
    print(f'estado.json creado con {len(est)} series')


# ------------------------------------------------------------------ fuentes
def binance_dia(mercado, simbolo, tf, dia):
    base = 'https://data.binance.vision/data/' + ('spot' if mercado == 'spot' else 'futures/um')
    url = f'{base}/daily/klines/{simbolo}/{tf}/{simbolo}-{tf}-{dia}.zip'
    try:
        z = zipfile.ZipFile(io.BytesIO(_get(url)))
    except urllib.error.HTTPError as e:
        if e.code != 404: raise
        if mercado != 'spot': return None
        return binance_api_dia(simbolo, tf, dia)
    raw = z.read(z.namelist()[0]).decode()
    lineas = [l for l in raw.splitlines() if l and l[0].isdigit()]          # futuros traen cabecera
    df = pd.read_csv(io.StringIO('\n'.join(lineas)), header=None)
    return _binance_df(df)


def binance_api_dia(simbolo, tf, dia):
    """Respaldo para el contado si el archivo del día aún no está publicado (solo si el día ya ha terminado)."""
    ini = pd.Timestamp(dia); fin = ini + pd.Timedelta(days=1)
    if fin > AHORA: return None
    filas, t0 = [], int(ini.timestamp() * 1000)
    while True:
        u = (f'https://data-api.binance.vision/api/v3/klines?symbol={simbolo}&interval={tf}'
             f'&startTime={t0}&endTime={int(fin.timestamp() * 1000) - 1}&limit=1000')
        try:
            d = json.loads(_get(u))
        except urllib.error.HTTPError:
            return None
        if not d: break
        filas += d
        if len(d) < 1000: break
        t0 = d[-1][0] + 1
    return _binance_df(pd.DataFrame(filas)) if filas else None


def _binance_df(df):
    out = pd.DataFrame({'fecha': _ms(df[0]), 'apertura': df[1].astype(float), 'maximo': df[2].astype(float),
                        'minimo': df[3].astype(float), 'cierre': df[4].astype(float), 'volumen': df[5].astype(float),
                        'volumen_comprador': df[9].astype(float)})
    return out


def binance_financiacion_mes(simbolo, mes):
    url = f'https://data.binance.vision/data/futures/um/monthly/fundingRate/{simbolo}/{simbolo}-fundingRate-{mes}.zip'
    try:
        z = zipfile.ZipFile(io.BytesIO(_get(url)))
    except urllib.error.HTTPError:
        return None
    df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
    return pd.DataFrame({'fecha': pd.to_datetime(df.iloc[:, 0], unit='ms'), 'tasa': df.iloc[:, 2].astype(float)})


def okx(tf, desde):
    bar = {'5m': '5m', '15m': '15m', '1h': '1H'}[tf]
    filas, despues = [], ''
    for _ in range(200):
        u = f'https://www.okx.com/api/v5/market/history-candles?instId=HYPE-USDT&bar={bar}&limit=100' + (f'&after={despues}' if despues else '')
        d = json.loads(_get(u))['data']
        if not d: break
        filas += d
        despues = d[-1][0]
        if pd.to_datetime(int(despues), unit='ms') <= desde: break
    df = pd.DataFrame(filas)
    out = pd.DataFrame({'fecha': pd.to_datetime(df[0].astype('int64'), unit='ms'), 'apertura': df[1].astype(float),
                        'maximo': df[2].astype(float), 'minimo': df[3].astype(float), 'cierre': df[4].astype(float),
                        'volumen': df[5].astype(float), 'confirmada': df[8].astype(int)})
    out = out[out.confirmada == 1].drop(columns='confirmada')
    return out


def hyperliquid(tf, desde):
    ini = int((desde - pd.Timedelta(days=1)).timestamp() * 1000)
    body = json.dumps({'type': 'candleSnapshot', 'req': {'coin': '@107', 'interval': tf, 'startTime': ini}}).encode()  # @107 = HYPE/USDC al contado
    d = json.loads(_get('https://api.hyperliquid.xyz/info', datos=body, cabeceras={'Content-Type': 'application/json'}))
    df = pd.DataFrame(d)
    return pd.DataFrame({'fecha': pd.to_datetime(df.t, unit='ms'), 'apertura': df.o.astype(float), 'maximo': df.h.astype(float),
                         'minimo': df.l.astype(float), 'cierre': df.c.astype(float), 'volumen': df.v.astype(float)})


def tradingview(simbolo, tf, ajuste, desde):
    from tv import velas_tv
    n = 5000 if tf in ('5m', '15m', '1h', '4h') else int(min(5000, max(30, (AHORA - desde).days * 1.2 + 20)))
    return velas_tv(simbolo, tf, n=n, ajuste=ajuste)


# ------------------------------------------------------------------ una serie
def cerradas(df, tf, parado=False):
    """Quita la vela en curso. Cerrada = hay otra posterior, o ya pasó su duración, o el mercado está parado."""
    if df is None or not len(df): return df
    df = df.sort_values('fecha').drop_duplicates('fecha', keep='last')
    ultima = df.fecha.iloc[-1]
    fin = ultima + pd.Timedelta(seconds=DUR[tf])
    if fin <= AHORA: return df
    if parado and tf != '1w': return df
    if parado and tf == '1w' and AHORA.weekday() >= 5: return df
    return df.iloc[:-1]


def actualizar_serie(s, e, leer_nuevas_1d):
    """Devuelve (DataFrame de velas nuevas cerradas, aviso)."""
    hasta = pd.Timestamp(e['hasta'])
    tipo, tf = s['tipo'], s['tf']
    if tipo == 'financiacion':
        meses = pd.period_range(hasta.to_period('M'), (AHORA - pd.Timedelta(days=1)).to_period('M') - 1, freq='M')
        partes = [x for m in meses if (x := binance_financiacion_mes(s['simbolo'], str(m))) is not None]
        df = pd.concat(partes) if partes else None
        return (df[df.fecha > hasta] if df is not None else None), None
    if tipo == 'binance':
        s = {**s, 'mercado': e.get('mercado', s['mercado'])}
        if tf == '1w':
            return semanas_binance(s, e, leer_nuevas_1d), None
        dias = pd.date_range(hasta.normalize(), (AHORA - pd.Timedelta(days=1)).normalize(), freq='D')
        partes = []
        for d in dias:
            x = binance_dia(s['mercado'], s['simbolo'], tf, d.strftime('%Y-%m-%d'))
            if x is None:            # aún no publicado: se para aquí y se sigue mañana (sin huecos)
                if (AHORA - d).days >= 4:
                    return (pd.concat(partes) if partes else None), f'sin datos de {d.date()} en Binance'
                break
            partes.append(x)
        df = pd.concat(partes) if partes else None
        return (df[df.fecha > hasta] if df is not None else None), None
    if tipo == 'okx':
        try:
            df = okx(tf, hasta)
        except Exception as ex:      # OKX puede no responder desde EE. UU.: respaldo en Hyperliquid
            df = hyperliquid(tf, hasta); aviso = f'OKX falló ({ex.__class__.__name__}); usado Hyperliquid'
            return cerradas(df[df.fecha > hasta], tf), aviso
        return df[df.fecha > hasta], None
    if tipo == 'hyperliquid':
        if tf == '1w':   # las semanas de Hyperliquid empiezan en jueves: se construye con el 1d (lunes a domingo)
            return semanas_binance(s, e, leer_nuevas_1d), None
        df = hyperliquid(tf, hasta)
        return cerradas(df[df.fecha > hasta], tf), None
    if tipo == 'tv':
        df = tradingview(s['simbolo'], s['tf_base'], s['ajuste'], hasta)
        return df, None   # el cierre se decide fuera (necesita saber si el mercado está parado)
    return None, f'tipo desconocido {tipo}'


def semanas_binance(s, e, leer_nuevas_1d):
    clave_1d = s['clave'].rsplit('|', 1)[0] + '|1d'
    d = leer_nuevas_1d(clave_1d)
    if d is None or not len(d): return None
    d = d.set_index('fecha').sort_index()
    sem = d.resample('W-MON', label='left', closed='left').agg(
        {'apertura': 'first', 'maximo': 'max', 'minimo': 'min', 'cierre': 'last', 'volumen': 'sum',
         **({'volumen_comprador': 'sum'} if 'volumen_comprador' in d else {})})
    cuenta = d.cierre.resample('W-MON', label='left', closed='left').count()
    sem = sem[cuenta == 7].reset_index()                                   # solo semanas completas
    return sem[sem.fecha > pd.Timestamp(e['hasta'])]


# ------------------------------------------------------------------ escritura
def ruta_dia(carpeta, activo, dia):
    return os.path.join(DIR_VELAS, carpeta, activo, dia.strftime('%Y-%m'), dia.strftime('%Y-%m-%d') + '.parquet')


def leer_nuevas(carpeta, activo, tf):
    d = os.path.join(DIR_VELAS, carpeta, activo)
    if not os.path.isdir(d): return None
    partes = []
    for raiz, _, archivos in os.walk(d):
        for a in archivos:
            if a.endswith('.parquet'):
                x = pd.read_parquet(os.path.join(raiz, a))
                partes.append(x[x.tf == tf])
    if not partes: return None
    return pd.concat(partes).drop(columns='tf').drop_duplicates('fecha', keep='last').sort_values('fecha')


def escribir(carpeta, activo, filas_por_tf):
    """filas_por_tf: {tf: DataFrame}. Agrupa por día de apertura y fusiona con lo que ya hubiera."""
    todo = []
    for tf, df in filas_por_tf.items():
        if df is None or not len(df): continue
        x = df.copy(); x['tf'] = tf; todo.append(x)
    if not todo: return 0
    todo = pd.concat(todo)
    n = 0
    for dia, g in todo.groupby(todo.fecha.dt.normalize()):
        p = ruta_dia(carpeta, activo, dia)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            g = pd.concat([pd.read_parquet(p), g]).drop_duplicates(['tf', 'fecha'], keep='last')
        g.sort_values(['tf', 'fecha']).reset_index(drop=True).to_parquet(p, index=False, compression='zstd')
        n += 1
    return n


# ------------------------------------------------------------------ principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iniciar', action='store_true')
    ap.add_argument('--solo', default='')
    ap.add_argument('--hilos', type=int, default=12)
    a = ap.parse_args()
    if a.iniciar:
        return iniciar()
    est = leer_estado()
    series = [s for s in catalogo() if s['clave'] in est and not est[s['clave']].get('muerta')]
    if a.solo:
        quiero = set(a.solo.split(','))
        series = [s for s in series if s['activo'] in quiero]
    informe = {'hora': str(AHORA), 'nuevas': 0, 'avisos': [], 'errores': []}

    # 1) TradingView: primero el 5m de cada símbolo para saber si su mercado está parado
    parado = {}
    def leer_serie(s):
        try:
            return s, *actualizar_serie(s, est[s['clave']], _nuevas_1d)
        except Exception as ex:
            return s, None, f'ERROR {ex.__class__.__name__}: {str(ex)[:150]}'

    nuevas_1d = {}
    def _nuevas_1d(clave_1d):
        c, act, _ = clave_1d.split('|')
        base = pd.DataFrame(est[clave_1d].get('semilla_1d', []))
        if len(base): base['fecha'] = pd.to_datetime(base.fecha).dt.tz_localize(None)
        partes = [base, leer_nuevas(c, act, '1d'), nuevas_1d.get(clave_1d)]
        partes = [p for p in partes if p is not None and len(p)]
        return pd.concat(partes).drop_duplicates('fecha', keep='last').sort_values('fecha') if partes else None

    semanal_de_1d = lambda s: s['tf'] == '1w' and s.get('tipo') in ('binance', 'hyperliquid')
    primero = [s for s in series if not semanal_de_1d(s)]
    despues = [s for s in series if semanal_de_1d(s)]
    resultados = []
    with ThreadPoolExecutor(a.hilos) as ex:
        resultados += list(ex.map(leer_serie, primero))
    for s, df, aviso in resultados:
        if s['tf'] == '1d' and s.get('tipo') in ('binance', 'hyperliquid') and df is not None:
            nuevas_1d[s['clave']] = df
    with ThreadPoolExecutor(a.hilos) as ex:
        resultados += list(ex.map(leer_serie, despues))

    # mercado parado por símbolo de TradingView (última vela de 5 min hace más de 45 min)
    for s, df, aviso in resultados:
        if s.get('tipo') == 'tv' and s['tf_base'] == '5m' and df is not None and len(df):
            parado[s['simbolo']] = (AHORA - (df.fecha.max() + pd.Timedelta(minutes=5))) > pd.Timedelta(minutes=45)

    from tv import velas_tv
    for sim in {s['simbolo'] for s in series if s.get('tipo') == 'tv'} - set(parado):
        try:
            x = velas_tv(sim, '5m', 3)
            parado[sim] = (AHORA - (x.fecha.max() + pd.Timedelta(minutes=5))) > pd.Timedelta(minutes=45)
        except Exception:
            pass

    por_activo = {}
    for s, df, aviso in resultados:
        e = est[s['clave']]
        if aviso: (informe['errores'] if aviso.startswith('ERROR') else informe['avisos']).append(f"{s['clave']}: {aviso}")
        if aviso and aviso.startswith('sin datos') and (AHORA - pd.Timestamp(e['hasta'])).days > 30:
            e['muerta'] = True   # p. ej. moneda retirada de Binance: se deja de pedir y se avisa
            informe['avisos'].append(f"{s['clave']}: sin datos desde hace más de 30 días; se deja de actualizar")
        if df is None or not len(df): continue
        if s.get('tipo') == 'tv':
            # sin 5 min para saberlo (p. ej. % de acciones sobre su media de 200): en bolsa, la ejecución de las 03:30 UTC cae con el mercado cerrado
            df = cerradas(df, s['tf_base'], parado.get(s['simbolo'], s['carpeta'].endswith('TRADICIONAL')))
        df = df[df.fecha > pd.Timestamp(e['hasta'])]
        if not len(df): continue
        cols = [c for c in e['columnas'] if c in df.columns]
        df = df[cols]
        por_activo.setdefault((s['carpeta'], s['activo']), {})[s['tf']] = df
        e['hasta'] = str(df.fecha.max()); e['nuevas'] = e.get('nuevas', 0) + len(df)
        informe['nuevas'] += len(df)
    archivos = sum(escribir(c, act, d) for (c, act), d in por_activo.items())
    guardar_estado(est)
    actualizar_indice(est)
    informe['archivos_dia'] = archivos
    json.dump(informe, open(os.path.join(AQUI, 'ultimo_informe.json'), 'w'), indent=1, ensure_ascii=False)
    print(f"{informe['nuevas']} velas nuevas en {archivos} archivos; {len(informe['avisos'])} avisos; {len(informe['errores'])} errores")
    for x in informe['errores'][:30]: print('  ', x)


def actualizar_indice(est):
    idx = pd.read_csv(INDICE)
    for i, r in idx.iterrows():
        e = est.get(f'{r.carpeta}|{r.activo}|{r.tf}')
        if e and e.get('nuevas'):
            idx.at[i, 'hasta'] = str(pd.Timestamp(e['hasta']))
            idx.at[i, 'velas'] = int(e['base_velas']) + int(e['nuevas'])
    idx.to_csv(INDICE, index=False)


if __name__ == '__main__':
    main()
