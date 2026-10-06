# -*- coding: utf-8 -*-
"""
PUNTUACIÓN DE BONOS (0-100) — Óscar, octubre 2026
==================================================

Calcula dos puntuaciones con datos públicos (Reserva Federal de San Luis y Yahoo):

  1) Puntuación de PLAZO (duración): ¿compensa estar en bonos largos (TLT) o cortos (SHY)?
       65 o más  -> largo (TLT)      35-65 -> medio (IEF)      menos de 35 -> corto (SHY o BIL)
  2) Puntuación BONOS frente a ACCIONES: ¿qué parte de la cartera en acciones?
       % en acciones = 60 % + 20 % x (50 - puntuación) / 50, entre 40 % y 80 %

Uso en tu Mac (con internet):
    python3 score_bonos.py            -> descarga todo y escribe la lectura de hoy
    python3 score_bonos.py --offline  -> usa los ficheros de la carpeta brutos/ (sin internet)

Necesita pandas y numpy (python3 -m pip install pandas numpy).
Revisión recomendada: una vez al mes (el estudio se probó con cambios mensuales).
"""
import io, json, math, os, sys, time, urllib.request
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
BRUTOS = os.path.join(AQUI, 'brutos')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36'}
SERIES_FRED = ['DGS10', 'DGS2', 'DGS3MO', 'DTB3', 'DFF', 'THREEFYTP10', 'CPILFESL', 'NFCI']
VENTANA = 520        # 10 años de semanas para decidir qué es "alto" o "bajo"
MINIMO = 156         # al menos 3 años de historia

# ---------------------------------------------------------------- descarga
def _get(url, intentos=3):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read().decode('utf-8')
        except Exception as e:
            if i == intentos - 1:
                raise
            time.sleep(2)

def fred(id_):
    t = _get('https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + id_)
    s = pd.read_csv(io.StringIO(t), na_values=['.'], parse_dates=['observation_date'])
    return s.set_index('observation_date').iloc[:, 0].dropna()

def yahoo_cierre(simbolo):
    url = ('https://query2.finance.yahoo.com/v8/finance/chart/%s?period1=0&period2=%d&interval=1d'
           % (urllib.request.quote(simbolo), int(time.time())))
    j = json.loads(_get(url))['chart']['result'][0]
    off = j['meta'].get('gmtoffset', 0) or 0
    idx = pd.to_datetime([t + off for t in j['timestamp']], unit='s').normalize()
    return pd.Series(j['indicators']['quote'][0]['close'], index=idx).dropna()

def cargar_datos(offline=False):
    if offline:
        f = json.load(open(os.path.join(BRUTOS, 'bonos_fred_macro.json')))
        F = {k: pd.read_csv(io.StringIO(f[k]), na_values=['.'], parse_dates=['observation_date'])
                .set_index('observation_date').iloc[:, 0].dropna() for k in SERIES_FRED if k in f}
        if 'DTB3' not in F:
            g = json.load(open(os.path.join(BRUTOS, 'bonos_fred_extra.json')))
            F['DTB3'] = pd.read_csv(io.StringIO(g['DTB3']), na_values=['.'], parse_dates=['observation_date']).set_index('observation_date').iloc[:, 0].dropna()
        raw = open(os.path.join(BRUTOS, 'bonos_yahoo_precios.csv')).read().split('#DIVIDENDOS\n')[0]
        px = pd.read_csv(io.StringIO(raw), parse_dates=['fecha'])
        dxy = px[px.simbolo == 'DX-Y.NYB'].set_index('fecha').cierre.dropna()
    else:
        F = {k: fred(k) for k in SERIES_FRED}
        dxy = yahoo_cierre('DX-Y.NYB')
    return F, dxy

# ---------------------------------------------------------------- preparación sin mirar al futuro
SEMANAS = None
def semanal(s):
    s = s[~s.index.duplicated(keep='last')].sort_index()
    return s.reindex(s.index.union(SEMANAS)).ffill().reindex(SEMANAS)

def con_retraso(s, dias=None, habiles=None):
    s = s.copy()
    s.index = s.index + (pd.offsets.BDay(habiles) if habiles else pd.Timedelta(days=dias))
    return s

def mensual_publicado(s, fechas_pub=None):
    """El dato del mes M se conoce cuando se publica (IPC: hacia el día 10-15 del mes siguiente)."""
    out = {}
    for d, v in s.items():
        fin = d + pd.offsets.MonthEnd(0)
        if fechas_pub is not None:
            r = fechas_pub[fechas_pub > fin]
            if len(r) and (r[0] - fin).days < 50:
                out[r[0]] = v
                continue
        out[fin + pd.Timedelta(days=45 if fechas_pub is not None else 16)] = v
    return pd.Series(out).sort_index()

def z(s):
    m = s.rolling(VENTANA, min_periods=MINIMO).mean()
    sd = s.rolling(VENTANA, min_periods=MINIMO).std()
    return ((s - m) / sd).clip(-3, 3)

def a_0_100(x):
    return 100 * 0.5 * (1 + np.vectorize(math.erf)(x / math.sqrt(2)))

def calcular(F, dxy):
    global SEMANAS
    hoy = pd.Timestamp.today().normalize()
    SEMANAS = pd.date_range('1962-01-05', hoy + pd.offsets.Week(weekday=4), freq='W-FRI')
    fechas_ipc = None
    p = os.path.join(BRUTOS, 'bonos_fechas_eventos.json')
    if os.path.exists(p):
        fechas_ipc = pd.to_datetime(sorted(set(json.load(open(p))['CPI'])))
    y10 = semanal(con_retraso(F['DGS10'], habiles=1))
    y2 = semanal(con_retraso(F['DGS2'], habiles=1))
    y3m = semanal(con_retraso(F['DGS3MO'], habiles=1)).fillna(semanal(con_retraso(F['DTB3'], habiles=1)))
    ff = semanal(con_retraso(F['DFF'], habiles=1))
    tp = semanal(con_retraso(F['THREEFYTP10'], dias=7))
    sub = semanal(mensual_publicado(F['CPILFESL'], fechas_ipc))
    nfci = semanal(con_retraso(F['NFCI'], dias=5))
    dol = semanal(dxy)
    sub_anual = (sub / sub.shift(52) - 1) * 100
    C = pd.DataFrame({
        'prima_plazo': z(tp),                               # prima por plazo alta = bonos largos pagan más
        'tipo_real': z(y10 - sub_anual),                     # 10 años menos inflación subyacente
        'pendiente_10a_3m': z(y10 - y3m),                    # curva: largo frente a letras
        'carry_10a_fed': z(y10 - ff),                        # lo que ganas por alargar plazo frente al tipo Fed
        'tramo_corto_2a_fed': z(y2 - ff),                    # 2 años por encima del tipo Fed
        'condiciones_financieras': z(-nfci),                 # condiciones holgadas
        'y10_vs_media5a': z(y10 - y10.rolling(260).mean()),  # 10 años frente a su media de 5 años
        'dolar_13s': z(dol / dol.shift(13) - 1),             # dólar subiendo en 3 meses
    })
    BLOQ_D = {'Valoración': (['prima_plazo', 'tipo_real'], 0.40),
              'Pendiente y carry': (['pendiente_10a_3m', 'carry_10a_fed', 'tramo_corto_2a_fed'], 0.45),
              'Condiciones financieras': (['condiciones_financieras'], 0.15)}
    BLOQ_B = {'Valoración bonos': (['y10_vs_media5a', 'prima_plazo'], 0.45),
              'Pendiente': (['pendiente_10a_3m'], 0.30),
              'Dólar': (['dolar_13s'], 0.25)}
    def montar(bloques):
        tot, peso, partes = 0, 0, {}
        for b, (cols, w) in bloques.items():
            v = C[cols].mean(axis=1, skipna=True); partes[b] = v
            tot = tot + v.fillna(0) * w; peso = peso + v.notna() * w
        comp = tot / peso.replace(0, np.nan)
        return pd.Series(a_0_100(comp / comp.expanding(MINIMO).std()), index=comp.index), pd.DataFrame(partes)
    D, bD = montar(BLOQ_D)
    B, bB = montar(BLOQ_B)
    out = pd.DataFrame({'puntuacion_plazo': D, 'puntuacion_bonos_vs_acciones': B,
                        'rend_10a': y10, 'media10s_rend_10a': y10.rolling(10).mean()}).join(C)
    out = out[out.index <= hoy + pd.Timedelta(days=6)].dropna(subset=['puntuacion_plazo'])
    return out, bD, bB

def tramo(d):
    return 'LARGO (TLT)' if d >= 65 else ('MEDIO (IEF)' if d >= 35 else 'CORTO (SHY o BIL)')

def main():
    offline = '--offline' in sys.argv
    F, dxy = cargar_datos(offline)
    out, bD, bB = calcular(F, dxy)
    u = out.iloc[-1]; fecha = out.index[-1].date()
    d, b = u.puntuacion_plazo, u.puntuacion_bonos_vs_acciones
    acc = min(0.8, max(0.4, 0.6 + 0.2 * (50 - b) / 50))
    conf = u.rend_10a < u.media10s_rend_10a
    hace4 = out.puntuacion_plazo.iloc[-5] if len(out) > 5 else float('nan')
    print('=' * 64)
    print('LECTURA DE BONOS  —  semana del %s' % fecha)
    print('=' * 64)
    print('Puntuación de PLAZO ........... %5.1f / 100  (hace 4 semanas: %.1f)' % (d, hace4))
    print('  -> tramo sugerido: %s' % tramo(d))
    print('  -> confirmación (10 años por debajo de su media de 10 semanas): %s' % ('SÍ' if conf else 'NO todavía'))
    print('Puntuación BONOS vs ACCIONES .. %5.1f / 100' % b)
    print('  -> reparto sugerido: %.0f %% acciones / %.0f %% bonos' % (acc * 100, (1 - acc) * 100))
    print('-' * 64)
    print('Rendimiento del bono a 10 años: %.2f %%' % u.rend_10a)
    print('Piezas (en desviaciones respecto a los últimos 10 años; + = a favor de bonos):')
    for c in ['prima_plazo', 'tipo_real', 'pendiente_10a_3m', 'carry_10a_fed', 'tramo_corto_2a_fed',
              'condiciones_financieras', 'y10_vs_media5a', 'dolar_13s']:
        print('   %-26s %+.2f' % (c, u[c]))
    destino = os.path.join(AQUI, 'historial_puntuaciones.csv')
    out.round(4).to_csv(destino, index_label='viernes')
    print('-' * 64)
    print('Historial guardado en: %s' % destino)

if __name__ == '__main__':
    main()
