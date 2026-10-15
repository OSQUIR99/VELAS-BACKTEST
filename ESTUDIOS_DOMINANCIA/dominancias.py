# -*- coding: utf-8 -*-
"""Vigilancia de dominancias para el apartado 6.1 del panel (16-oct-2026, petición de Óscar).

  python3 dominancias.py [carpeta_velas] [salida.json]
  (por defecto /home/claude/velas-backtest y dominancias.json)

Qué hace
  1. Zonas de pivote DIARIAS (giro con 5 días a cada lado, agrupados a menos de un 2 %, 2 giros o más),
     calculadas solo con lo que se sabía en cada fecha.
  2. SESGO OPERATIVO (probado, ESTUDIOS_DOMINANCIA): rotura de resistencia confirmada con 2 cierres
     diarios en ETH/BTC (-> ETH sobre BTC) y en OTHERS y TOTAL3 (-> altcoins sobre BTC), 4 semanas.
     Y la pendiente de la media de 20 días de ETH/BTC (la regla más robusta, auditada).
  3. CONTEXTO: dominancia de BTC y de USDT. Cuando el precio se acerca a una zona, qué pasó las otras veces.
  4. Para cada caso: estadística (todo desde 2018, últimos 5 años, misma fase de BTC) frente a un día
     cualquiera, y las 5 últimas veces con sus circunstancias.
Datos: velas diarias del repositorio + vela de hoy del escáner público de TradingView (si responde).
La vela de hoy NO está cerrada: solo se usa para la distancia a los niveles, nunca para confirmar.
"""
import sys, os, json, itertools, datetime as dt
import numpy as np, pandas as pd

CARPETA = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/velas-backtest'
SALIDA = sys.argv[2] if len(sys.argv) > 2 else 'dominancias.json'
sys.path.insert(0, CARPETA)
from cargar import velas as _velas_repo
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

_RECIENTES = None
def _recientes():
    """Velas cerradas posteriores al repositorio: el registro diario de GitHub + lo que dé hoy el escáner."""
    global _RECIENTES
    if _RECIENTES is None:
        filas = []
        p = os.path.join(AQUI, 'velas_recientes.csv')
        if os.path.exists(p): filas += pd.read_csv(p).to_dict('records')
        try:
            from registrar_velas import leer
            filas += leer()
        except Exception as e:
            print('Aviso: sin velas recientes del escáner:', e)
        df = pd.DataFrame(filas)
        if len(df):
            df['fecha'] = pd.to_datetime(df.fecha)
            for c in ('apertura', 'maximo', 'minimo', 'cierre'): df[c] = df[c].astype(float)
            df = df.drop_duplicates(['serie', 'fecha'], keep='last')
        _RECIENTES = df
    return _RECIENTES

def velas(archivo, tf='1d'):
    """Velas del repositorio + las cerradas que falten (solo diario)."""
    v = _velas_repo(archivo, tf)
    r = _recientes()
    if tf != '1d' or not len(r): return v
    r = r[(r.serie == archivo) & (r.fecha > v.index[-1])].set_index('fecha')[['apertura', 'maximo', 'minimo', 'cierre']]
    return pd.concat([v[['apertura', 'maximo', 'minimo', 'cierre']], r]).sort_index() if len(r) else v

N, TOL, MT, K, H_SESGO = 5, 0.02, 2, 2, 28       # parámetros del centro de la rejilla probada
CERCA = 0.03                                       # "cerca" = a menos de un 3 % de la zona
# La dominancia de BTC se mueve 4 veces menos que el resto (0,31 % al día frente a 0,9-1,8 %): su zona es más estrecha.
TOLS = {'BTC.D': 0.005}
FUERTE = 4                                         # zona principal: 4 giros o más (los avisos solo saltan con estas)
CERCAS = {'BTC.D': 0.0075}
HOR = [1, 2, 7, 28]                                # días de los resultados
DESDE = pd.Timestamp('2018-01-01')

SERIES = {   # clave: (archivo, símbolo TradingView, papel, qué se compara)
    'ETH_BTC': ('ETH_BTC', 'BINANCE:ETHBTC', 'sesgo', 'ETH frente a BTC'),
    'OTHERS': ('others_fuera_top10', 'CRYPTOCAP:OTHERS', 'sesgo', 'altcoins pequeñas (OTHERS) frente a BTC'),
    'TOTAL3': ('total3_sin_btc_eth', 'CRYPTOCAP:TOTAL3', 'sesgo', 'altcoins sin BTC ni ETH (TOTAL3) frente a BTC'),
    'BTC.D': ('dominancia_btc', 'CRYPTOCAP:BTC.D', 'contexto', 'dominancia de BTC'),
    'USDT.D': ('dominancia_usdt', 'CRYPTOCAP:USDT.D', 'contexto', 'dominancia de USDT'),
}

# ---------------------------------------------------------------- niveles
def zonas_por_dia(dd):
    hi, lo = dd.maximo.values, dd.minimo.values
    nuevos = {}
    for i in range(N, len(dd) - N):
        for v, es in ((hi[i], hi[i] == hi[i - N:i + N + 1].max()), (lo[i], lo[i] == lo[i - N:i + N + 1].min())):
            if es: nuevos.setdefault(i + N, []).append(np.log(v))
    piv, zonas, out = [], [], []
    for i in range(len(dd)):
        if i in nuevos:
            piv = sorted(piv + nuevos[i]); grupos, g = [], []
            for v in piv:
                if g and v - g[0] > TOL: grupos.append(g); g = []
                g.append(v)
            if g: grupos.append(g)
            zonas = [(float(np.exp(np.mean(x))), len(x)) for x in grupos if len(x) >= MT]
        out.append(zonas)
    return out

def roturas(dd, zonas):
    """Rotura de resistencia: venía al menos un 6 % por debajo y en 10 días cierra 2 veces seguidas >2 % por encima."""
    c = dd.cierre.values; out, i = [], 25
    while i < len(dd) - 1:
        hecho = False
        for L, f in zonas[i]:
            if not ((L - c[i - 5:i]) > 3 * TOL * L).all(): continue
            for j in range(i, min(i + 11, len(dd) - K)):
                if all(c[j + q] > L * (1 + TOL) for q in range(K)):
                    out.append((dd.index[j + K - 1], L, f)); hecho = True; break
            if hecho: break
        i += 10 if hecho else 1
    return out

def acercamientos(dd, zonas, lado):
    """Llega a una zona viniendo de lejos (5 cierres previos a más de un 6 %). Resultado: ¿la rompe en 20 días?"""
    c, hi, lo = dd.cierre.values, dd.maximo.values, dd.minimo.values
    s = 1 if lado == 'soporte' else -1
    out, i = [], 25
    while i < len(dd) - 1:
        hecho = False
        for L, f in zonas[i]:
            if not ((c[i - 5:i] - L) * s > 3 * TOL * L).all(): continue
            toca = lo[i] <= L * (1 + TOL) if s == 1 else hi[i] >= L * (1 - TOL)
            if not toca: continue
            fut = c[i + 1:i + 21]
            rota = bool(((fut - L) * s < -2 * TOL * L).any()) if len(fut) == 20 else None
            out.append((dd.index[i], L, f, rota)); hecho = True; break
        i += 10 if hecho else 1
    return out

# ---------------------------------------------------------------- datos de hoy
def hoy_tradingview():
    import urllib.request
    body = json.dumps({'symbols': {'tickers': [v[1] for v in SERIES.values()] + ['BINANCE:BTCUSDT']},
                       'columns': ['close', 'high', 'low', 'open']}).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request('https://scanner.tradingview.com/global/scan', body,
                                   {'Content-Type': 'application/json'}), timeout=15)
        return {x['s']: x['d'] for x in json.load(r)['data']}
    except Exception as e:
        return {'_error': str(e)}

# ---------------------------------------------------------------- estadística
def relativo(nombre, btc):
    """Serie cuyo cambio es 'lo que se gana rotando': ETH/BTC tal cual; OTHERS y TOTAL3 divididos por BTC."""
    s = velas(SERIES[nombre][0], '1d').cierre
    return s if nombre == 'ETH_BTC' else (s / btc).dropna()

def fwd(s, d, h):
    if d not in s.index: return None
    i = s.index.get_loc(d)
    return float(s.iloc[i + h] / s.iloc[i] - 1) if i + h < len(s) else None

def circunstancias(d, btc):
    b = btc[:d]
    if len(b) < 200: return {}
    return {'btc_sobre_media200': bool(b.iloc[-1] > b.iloc[-200:].mean()),
            'btc_30d_%': round(float(b.iloc[-1] / b.iloc[-31] - 1) * 100, 1)}

def resumen(fechas, serie, btc, signo=1):
    """Media y % a favor a cada horizonte, en 3 ventanas, frente a un día cualquiera."""
    hoy = btc.index[-1]; fase_hoy = btc.iloc[-1] > btc.iloc[-200:].mean()
    sobre = btc > btc.rolling(200).mean()
    out = {}
    for ventana, filtro in (('misma_fase', lambda d: bool(sobre.get(d, False)) == fase_hoy),
                            ('ultimos_5_anos', lambda d: d >= hoy - pd.Timedelta(days=5 * 365)),
                            ('todo_desde_2018', lambda d: True)):
        fs = [d for d in fechas if filtro(d)]
        base = [d for d in serie.index if d >= DESDE and filtro(d)]
        fila = {'casos': len(fs)}
        for h in HOR:
            r = [x * signo for d in fs if (x := fwd(serie, d, h)) is not None]
            rb = (serie.shift(-h) / serie - 1).reindex(base).dropna() * signo
            fila[f'{h}d'] = {'media_%': round(np.mean(r) * 100, 2) if r else None,
                             'a_favor_%': round(np.mean(np.array(r) > 0) * 100) if r else None,
                             'dia_cualquiera_media_%': round(float(rb.mean()) * 100, 2),
                             'dia_cualquiera_a_favor_%': round(float((rb > 0).mean()) * 100)}
        out[ventana] = fila
    return out

def ultimos(eventos, serie, btc, signo=1, extra=None):
    res = []
    for e in eventos[-5:]:
        d = e[0]
        r = {f'{h}d_%': (round(x * signo * 100, 1) if (x := fwd(serie, d, h)) is not None else None) for h in HOR}
        res.append({'fecha': str(d.date()), 'nivel': round(e[1], 6 if e[1] < 1 else 2), 'fuerza': e[2],
                    **r, **circunstancias(d, btc), **(extra(e) if extra else {})})
    return res

# ---------------------------------------------------------------- principal
def main():
    global TOL, CERCA
    btc = velas('BTC', '1d').cierre
    tv = hoy_tradingview(); out = {'generado': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
                                   'parametros': dict(pivote_dias=N, tolerancia=TOL, giros_minimos=MT,
                                                      cierres_confirmacion=K, dias_sesgo=H_SESGO, cerca=CERCA),
                                   'fallos': [], 'series': {}}
    if '_error' in tv: out['fallos'].append('TradingView: ' + tv['_error']); tv = {}
    alts_btc = relativo('TOTAL3', btc)          # para el contexto: altcoins frente a BTC
    for nombre, (archivo, simbolo, papel, que) in SERIES.items():
        TOL, CERCA = TOLS.get(nombre, 0.02), CERCAS.get(nombre, 0.03)
        dd = velas(archivo, '1d'); dd = dd[dd.index >= '2016-01-01']
        zonas = zonas_por_dia(dd)
        ultimo_cierre = float(dd.cierre.iloc[-1]); ultima_fecha = str(dd.index[-1].date())
        actual = tv.get(simbolo, [None])[0]
        precio = float(actual) if actual else ultimo_cierre
        if not actual: out['fallos'].append(f'{nombre}: sin dato de hoy, se usa el cierre del {ultima_fecha}')
        z = sorted(zonas[-1])
        res = [(L, f) for L, f in z if L > precio][:3]; sop = [(L, f) for L, f in z if L <= precio][::-1][:3]
        fila = {'que': que, 'papel': papel, 'tolerancia_zona': TOL, 'precio_hoy': precio, 'ultimo_cierre': ultimo_cierre,
                'ultima_vela_cerrada': ultima_fecha,
                'resistencias': [{'nivel': L, 'fuerza_giros': f, 'distancia_%': round((L / precio - 1) * 100, 2),
                                  'cerca': (L / precio - 1) < CERCA, 'principal': f >= FUERTE} for L, f in res],
                'soportes': [{'nivel': L, 'fuerza_giros': f, 'distancia_%': round((L / precio - 1) * 100, 2),
                              'cerca': (1 - L / precio) < CERCA, 'principal': f >= FUERTE} for L, f in sop]}
        fila['aviso'] = [f"{'resistencia' if r in fila['resistencias'] else 'soporte'} principal a {r['distancia_%']} %"
                         for r in fila['resistencias'] + fila['soportes'] if r['cerca'] and r['principal']]
        if papel == 'sesgo':
            serie = relativo(nombre, btc)
            ev = [e for e in roturas(dd, zonas) if e[0] >= DESDE]
            fila['roturas_resistencia'] = {'evento': f'rotura de resistencia diaria de {nombre} confirmada con {K} cierres',
                                           'que_se_mide': f'{que}: ganancia de rotar (positivo = a favor de la rotura)',
                                           'estadistica': resumen([e[0] for e in ev], serie, btc),
                                           'ultimas_5': ultimos(ev, serie, btc)}
            ac = [e for e in acercamientos(dd, zonas, 'resistencia') if e[0] >= DESDE and e[3] is not None]
            fila['al_llegar_a_resistencia'] = {'casos': len(ac),
                                               'la_rompe_en_20d_%': round(np.mean([e[3] for e in ac]) * 100) if ac else None}
            hoy_d = pd.Timestamp(dt.datetime.now(dt.timezone.utc).date())
            # vivo: menos de 28 días desde la rotura (contados hasta hoy) y sin un cierre más de un 2 % bajo la zona rota
            activo = [e for e in ev if (hoy_d - e[0]).days <= H_SESGO
                      and not (dd.cierre[dd.index > e[0]] < e[1] * (1 - 2 * TOL)).any()]
            fila['sesgo_activo'] = ({'desde': str(activo[-1][0].date()), 'nivel_roto': activo[-1][1],
                                     'invalida_si_cierra_bajo': activo[-1][1] * (1 - 2 * TOL),
                                     'hasta': str((activo[-1][0] + pd.Timedelta(days=H_SESGO)).date()),
                                     'favorece': 'ETH' if nombre == 'ETH_BTC' else 'altcoins'} if activo else None)
            # niveles concretos: las veces que ESA zona se rompió antes
            for r in fila['resistencias']:
                prev = [e for e in ev if abs(np.log(e[1] / r['nivel'])) < TOL]
                r['roturas_previas_de_esta_zona'] = ultimos(prev, serie, btc)
            if nombre == 'ETH_BTC':
                m = dd.cierre.rolling(20).mean(); p = m - m.shift(5)
                fila['pendiente_media20'] = {'sube': bool(p.iloc[-1] > 0), 'media20': float(m.iloc[-1]),
                                             'favorece': 'ETH' if p.iloc[-1] > 0 else 'BTC',
                                             'desde': str(dd.index[(np.sign(p) != np.sign(p.iloc[-1]))].max().date())}
        else:
            for lado, signo_alts in (('resistencia', 1), ('soporte', -1)):
                ac = [e for e in acercamientos(dd, zonas, lado) if e[0] >= DESDE]
                hechos = [e for e in ac if e[3] is not None]
                bloque = {'evento': f'{nombre} llega a una zona de {lado} diaria viniendo de lejos',
                          'casos': len(hechos),
                          'aguanta_20d_%': round(np.mean([not e[3] for e in hechos]) * 100) if hechos else None,
                          'btc': resumen([e[0] for e in hechos], btc, btc),
                          'zonas_fuertes': {'giros_minimos': FUERTE, 'casos': len(fu := [e for e in hechos if e[2] >= FUERTE]),
                                            'aguanta_20d_%': round(np.mean([not e[3] for e in fu]) * 100) if fu else None,
                                            'altcoins_frente_a_btc_TOTAL3': resumen([e[0] for e in fu], alts_btc, btc),
                                            'btc': resumen([e[0] for e in fu], btc, btc)},
                          'altcoins_frente_a_btc_TOTAL3': resumen([e[0] for e in hechos], alts_btc, btc),
                          'ultimas_5': ultimos(hechos, btc, btc, extra=lambda e: {
                              'aguanto': (None if e[3] is None else not e[3]),
                              'alts_vs_btc_28d_%': (round(x * 100, 1) if (x := fwd(alts_btc, e[0], 28)) is not None else None)})}
                fila[f'al_llegar_a_{lado}'] = bloque
        out['series'][nombre] = fila
    json.dump(out, open(SALIDA, 'w'), indent=1, ensure_ascii=False, default=float)
    print(json.dumps({k: {'precio': v['precio_hoy'], 'R': [(round(r['nivel'], 5), r['distancia_%']) for r in v['resistencias']],
                          'S': [(round(r['nivel'], 5), r['distancia_%']) for r in v['soportes']],
                          'sesgo': v.get('sesgo_activo')} for k, v in out['series'].items()}, indent=1, default=str))
    if out['fallos']: print('FALLOS:', out['fallos'])

if __name__ == '__main__':
    main()
