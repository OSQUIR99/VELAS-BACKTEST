#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TERMÓMETRO DE ACUMULACIÓN — Óscar, octubre 2026
================================================
Da una PUNTUACIÓN de 0 a 100 para Bitcoin, S&P 500, Nasdaq 100, oro y plata. Cada activo tiene sus propios ingredientes
(los que se relacionaron con lo que pasó después en las dos mitades de su historia):
  - Bitcoin: liquidez (7 luces), reloj del halving, tendencia + liquidez, sobrecalentamiento y zona de valor.
  - S&P 500: liquidez (6 luces), tendencia, recesión y miedo aprovechable.
  - Nasdaq 100: dólar, bono a 10 años, miedo aprovechable, sobrecalentamiento y recesión.
  - Oro: tendencia, media subiendo, sin caída del 10 %, dólar, subida parabólica y volatilidad.
  - Plata: tendencia propia y del oro, sin caída del 10 %, subida parabólica y ratio oro/plata.

Cómo se usa (ver LEEME.md):
  - Bitcoin: 25 o menos, vender por tramos y recomprar al volver a 50; 25-40, sin dinero extra; 75 o más, dinero extra.
  - Nasdaq 100: 25 o menos es un aviso serio (no una regla de venta); 75 o más, dinero extra.
  - S&P 500: solo destaca 75 o más (miedo aprovechable).
  - Oro y plata: 75 o más, tendencia a favor; por debajo, sin dinero extra. No se vende por puntuación.
  - Las compras periódicas no se retrasan nunca.
  - Todo está elegido mirando la historia completa: no hay prueba con datos nuevos. Úsalo como lectura ordenada, no como oráculo.

Uso:
    python3 termometro.py              -> lectura con los datos guardados en datos/
    python3 termometro.py --descargar  -> primero actualiza datos desde internet (solo desde la Terminal normal del Mac)
Necesita pandas y numpy.
"""
import io, json, os, sys, time, urllib.request
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, 'datos')
SERIES = os.path.join(DATOS, 'series')
ACTIVOS = ['BTC', 'sp500', 'nasdaq100', 'oro', 'plata']
NOMBRE = {'BTC': 'Bitcoin', 'sp500': 'S&P 500', 'nasdaq100': 'Nasdaq 100', 'oro': 'Oro', 'plata': 'Plata'}
BPY = {'BTC': 365, 'sp500': 252, 'nasdaq100': 252, 'oro': 252, 'plata': 252}
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36'}

# parámetros de las reglas (los del estudio; no tocar sin repetir las pruebas)
LIQ_FUERA, LIQ_DENTRO, BANDA_VUELTA, DIAS_TRAMO2 = 33, 50, 0.05, 7
Z_PARABOLICA = 1.7
PARO_UMBRAL, BANDA_BOLSA = 0.20, 0.03

# antigüedad máxima admitida de cada dato (días naturales) antes de avisar de que está caducado
CADUCA = {'DXY': 6, 'VIX': 6, 'DGS10': 8, 'BAA10Y': 8, 'DFII10': 8, 'NFCI': 16, 'ICSA': 16, 'WALCL': 12, 'WTREGEN': 12, 'RRPONTSYD': 12,
          'ECBASSETSW': 16, 'JPNASSETS': 100, 'DEXUSEU': 14, 'DEXJPUS': 14, 'ESTABLES': 10, 'FNG_CRIPTO': 4, 'FNG_CNN': 6}
CADUCA_PRECIO = {'BTC': 3, 'sp500': 5, 'nasdaq100': 5, 'oro': 5, 'plata': 5}
LUZ_SERIES = {'dolar': ['DXY'], 'condfin': ['NFCI'], 'tipos': ['DGS10'], 'credito': ['BAA10Y'], 'liq_neta': ['WALCL', 'WTREGEN', 'RRPONTSYD'],
              'bancos_c': ['WALCL', 'ECBASSETSW', 'JPNASSETS', 'DEXUSEU', 'DEXJPUS'], 'estables': ['ESTABLES']}
LUZ_NOMBRE = {'dolar': 'Dólar (índice DXY, cambio en 13 semanas, %; verde si baja)',
              'condfin': 'Condiciones financieras (índice de la Fed de Chicago, cambio en 13 semanas; verde si baja)',
              'tipos': 'Tipo del bono de EE. UU. a 10 años (cambio en 13 semanas, puntos; verde si baja)',
              'credito': 'Prima de riesgo del crédito de empresas (cambio en 13 semanas, puntos; verde si baja)',
              'bancos_c': 'Balance de los bancos centrales: Fed + BCE + Banco de Japón, en dólares (cambio en 13 semanas, %; verde si sube)',
              'liq_neta': 'Liquidez neta de la Fed: balance menos cuenta del Tesoro menos repos inversos (cambio en 13 semanas, %; verde si sube)',
              'estables': 'Monedas estables en circulación (cambio en 13 semanas, %; verde si crece más del 2 %)'}


# ------------------------------------------------------------------ lectura de ficheros
def leer_precios():
    p = pd.read_csv(os.path.join(DATOS, 'precios_diarios.csv'), parse_dates=['fecha']).set_index('fecha')
    return {a: p[a].dropna() for a in ACTIVOS}


def serie(nombre):
    f = os.path.join(SERIES, nombre + '.csv')
    s = pd.read_csv(f, parse_dates=['fecha']).set_index('fecha')['valor']
    return s[~s.index.duplicated(keep='last')].sort_index().dropna()


def guardar_serie(nombre, s):
    s = s[~s.index.duplicated(keep='last')].sort_index().dropna()
    s.rename('valor').rename_axis('fecha').to_csv(os.path.join(SERIES, nombre + '.csv'))


# ------------------------------------------------------------------ utilidades (todo sin mirar al futuro)
def sma(s, n):
    return s.rolling(n, min_periods=n).mean()


def rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def con_retraso(s, dias, idx):
    """Serie tal y como se conocía cada día: el dato fechado en t se puede usar desde t + 'dias'."""
    s = s.copy(); s.index = s.index + pd.Timedelta(days=dias)
    s = s[~s.index.duplicated(keep='last')]
    return s.reindex(idx.union(s.index)).ffill().reindex(idx)


def semanal(c, activo):
    """Cierres semanales con la etiqueta del último día de la semana. OJO: la última puede estar sin terminar;
    por eso se usa siempre a través de a_diario(), que solo deja ver cada semana a partir del día siguiente a su fin."""
    return c.resample('W-SUN' if activo == 'BTC' else 'W-FRI').last().dropna()


def a_diario(wser, idx):
    s = wser.copy(); s.index = s.index + pd.Timedelta(days=1)
    return s.reindex(idx.union(s.index)).ffill().reindex(idx)


def extension_z(c, bpy, n=200):
    """Distancia a la media de 200 sesiones medida en 'volatilidades': cuánto se ha alejado el precio para lo que suele moverse."""
    r = np.log(c).diff(); sd = r.ewm(span=bpy, min_periods=bpy // 2).std()
    return np.log(c / sma(c, n)) / (sd * np.sqrt(n))


# ------------------------------------------------------------------ liquidez: 7 luces
def luces_liquidez(hasta=None):
    hasta = hasta or pd.Timestamp.today().normalize()
    idx = pd.date_range('1971-01-01', hasta, freq='D')
    L = pd.DataFrame(index=idx); V = pd.DataFrame(index=idx)
    dxy = serie('DXY').reindex(idx).ffill(limit=4)
    V['dolar'] = 100 * (dxy / dxy.shift(91) - 1); L['dolar'] = V['dolar'] < 0
    nf = serie('NFCI'); V['condfin'] = con_retraso(nf - nf.shift(13), 5, idx); L['condfin'] = V['condfin'] < 0
    t10 = con_retraso(serie('DGS10'), 1, idx); V['tipos'] = t10 - t10.shift(91); L['tipos'] = V['tipos'] < 0
    baa = con_retraso(serie('BAA10Y'), 1, idx); V['credito'] = baa - baa.shift(91); L['credito'] = V['credito'] < 0
    wal = serie('WALCL'); tga = serie('WTREGEN').reindex(wal.index).ffill(); rrp = serie('RRPONTSYD')
    rrp = rrp[rrp.index.dayofweek == 2]
    rrpw = rrp.reindex(wal.index.union(rrp.index)).ffill().reindex(wal.index).fillna(0)
    netliq = wal - tga - rrpw
    V['liq_neta'] = con_retraso(100 * (netliq / netliq.shift(13) - 1), 2, idx); L['liq_neta'] = V['liq_neta'] > 0
    wk = pd.date_range('1999-01-08', hasta, freq='W-FRI')
    g = pd.DataFrame({'fed': con_retraso(wal, 2, wk), 'ecb': con_retraso(serie('ECBASSETSW'), 5, wk) * con_retraso(serie('DEXUSEU'), 1, wk),
                      'boj': con_retraso(serie('JPNASSETS'), 45, wk) * 100 / con_retraso(serie('DEXJPUS'), 1, wk)})
    gcb = g.sum(axis=1, min_count=3)
    V['bancos_c'] = con_retraso(100 * (gcb / gcb.shift(13) - 1), 0, idx); L['bancos_c'] = V['bancos_c'] > 0
    st = serie('ESTABLES')
    st13 = (100 * (st / st.shift(13) - 1)).replace([np.inf, -np.inf], np.nan)
    V['estables'] = con_retraso(st13, 0, idx); V.loc[V.index < '2019-01-01', 'estables'] = np.nan; L['estables'] = V['estables'] > 2
    L = L.astype(float).where(V.notna())
    info = {'netliq': con_retraso(netliq, 2, idx), 'gcb': con_retraso(gcb, 0, idx), 'estables': con_retraso(st, 0, idx)}
    return L, V, info


def liquidez(L, activo, idx):
    cols = ['dolar', 'condfin', 'tipos', 'credito', 'bancos_c', 'liq_neta'] + (['estables'] if activo == 'BTC' else [])
    return (100 * L[cols].mean(axis=1, skipna=True)).reindex(idx)


# ------------------------------------------------------------------ reglas de venta (devuelven % invertido objetivo: 1, 0.5 o 0)
def regla_btc(c, liq):
    """Tramo 1 (mitad) al saltar; tramo 2 (resto) si a los 7 días sigue fuera. Recompra todo con liquidez >= 50 o precio > media*1,05."""
    s = sma(c, 200); dist = c / s - 1
    fuera = (liq <= LIQ_FUERA) & (dist < 0); vuelta = (liq >= LIQ_DENTRO) | (dist > BANDA_VUELTA)
    st = pd.Series(np.where(vuelta, 1.0, np.where(fuera, 0.5, np.nan)), index=c.index).ffill().fillna(1.0)
    todo = (st < 1).rolling(DIAS_TRAMO2 + 1).sum() == DIAS_TRAMO2 + 1
    return st.where(~todo, 0.0)


def regla_parabolica(c, bpy, tope_barras=None):
    """Fuera desde que la extensión z >= 1,7 hasta que el precio vuelve a su media de 200 sesiones (o pasan 2 años)."""
    z = extension_z(c, bpy); s = sma(c, 200); tope = tope_barras or 2 * bpy
    zz = z.values; p = c.values; m = s.values; out = np.ones(len(p)); dentro = True; k = 0
    for i in range(len(p)):
        if dentro:
            if not np.isnan(zz[i]) and zz[i] >= Z_PARABOLICA: dentro = False; k = i
        else:
            if p[i] <= m[i] or i - k >= tope: dentro = True
        out[i] = 1.0 if dentro else 0.0
    return pd.Series(out, index=c.index)


def bandera_paro(idx):
    ic = serie('ICSA'); ic4 = ic.rolling(4).mean()
    ratio = ic4 / ic4.rolling(52).min()
    return con_retraso((ratio > 1 + PARO_UMBRAL).astype(float), 6, idx), con_retraso(ratio, 6, idx)


def regla_bolsa(c, paro):
    s = sma(c, 200); dist = c / s - 1
    fuera = (paro == 1) & (dist < -BANDA_BOLSA); vuelta = (paro == 0) | (dist > BANDA_BOLSA)
    return pd.Series(np.where(vuelta, 1.0, np.where(fuera, 0.0, np.nan)), index=c.index).ffill().fillna(1.0)


def simular(c, w, coste):
    """Unidades equivalentes partiendo de 1 unidad. El objetivo decidido al cierre t se ejecuta al cierre t+1."""
    wx = w.shift(1).fillna(1.0).values; p = c.values; u, cash, prev = 1.0, 0.0, 1.0; ue = np.empty(len(p)); ops = []
    for i in range(len(p)):
        tw = wx[i]
        if tw != prev and not np.isnan(tw):
            tot = u * p[i] + cash; d = tw * tot - u * p[i]
            if d > 0:
                d = min(d, cash); u += d * (1 - coste) / p[i]; cash -= d
            else:
                u += d / p[i]; cash += (-d) * (1 - coste)
            ops.append((c.index[i], p[i], prev, tw)); prev = tw
        ue[i] = u + cash / p[i]
    return pd.Series(ue, index=c.index), ops


# ------------------------------------------------------------------ señales de compra
def senales_compra(a, c, L, V):
    """Señales que en el estudio dieron mejor resultado posterior que un día cualquiera. Sirven para dinero EXTRA y para recomprar;
    no para retrasar las compras periódicas."""
    idx = c.index; bpy = BPY[a]; S = {}
    w = semanal(c, a)
    rsiw = a_diario(rsi(w, 14), idx); rsid = rsi(c, 14)
    hi52 = c.rolling(bpy, min_periods=bpy // 2).max(); dd52 = c / hi52 - 1
    r = np.log(c).diff(); rv = r.rolling(20).std() * np.sqrt(bpy); rvp = rv.expanding(min_periods=750).rank(pct=True) * 100
    if a == 'BTC':
        m200w = a_diario(sma(w, 200), idx)
        S['Zona de valor (precio hasta un 10 % sobre la media de 200 semanas)'] = c <= 1.10 * m200w
        S['RSI semanal por debajo de 35'] = rsiw < 35
        liq = liquidez(L, a, idx)
        S['Liquidez favorable (67 o más) con precio sobre la media de 200 días'] = (liq >= 67) & (c > sma(c, 200))
    if a in ('sp500', 'nasdaq100'):
        vix = serie('VIX').reindex(idx).ffill(limit=4)
        S['VIX en 40 o más (pánico)'] = vix >= 40
        S['Volatilidad extrema (percentil 95 o más de su historia)'] = rvp >= 95
        S['RSI diario por debajo de 25'] = rsid < 25
        fng = serie('FNG_CNN').reindex(idx).ffill(limit=4)
        S['Miedo en bolsa (índice de CNN en 25 o menos)'] = fng <= 25
        if a == 'nasdaq100': S['Caída del 10 % o más desde el máximo de 52 semanas'] = dd52 <= -0.10
    if a in ('oro', 'plata'):
        ry = con_retraso(serie('DFII10'), 1, pd.date_range(idx[0], idx[-1], freq='D'))
        S['Tipos reales bajando 0,5 puntos o más en 13 semanas'] = (ry - ry.shift(91)).reindex(idx) <= -0.5
        S['Volatilidad extrema (percentil 95 o más de su historia)'] = rvp >= 95
    return {k: v.reindex(idx).fillna(False).astype(bool) for k, v in S.items()}


def estado_senal(cond, bpy):
    """activa hoy, desde cuándo, y si es reciente (empezó hace un mes o menos: es cuando el estudio midió su efecto)."""
    if not bool(cond.iloc[-1]): return {'activa': False}
    racha = cond[::-1].cumprod()[::-1]; ini = racha[racha == 1].index[0]
    barras = int((cond.index >= ini).sum())
    return {'activa': True, 'desde': str(ini.date()), 'reciente': barras <= bpy // 12}


# ------------------------------------------------------------------ PUNTUACIÓN 0-100, distinta para cada activo
HALVINGS = [pd.Timestamp(x) for x in ('2012-11-28', '2016-07-09', '2020-05-11', '2024-04-20')]
HALVING_PREVISTO = pd.Timestamp('2028-04-15')   # estimación del siguiente; cambiar por la fecha real cuando ocurra


def meses_desde_halving(idx):
    out = pd.Series(np.nan, index=idx)
    for h in HALVINGS + [HALVING_PREVISTO]:
        m = idx >= h; out[m] = (idx[m] - h).days / 30.44
    return out


def puntuacion(a, P, L, V, paro=None):
    """Devuelve (tabla de puntos por ingrediente, máximos por ingrediente, puntuación 0-100).
    Cada activo tiene sus propios ingredientes: los que se relacionaron con la rentabilidad posterior en las dos mitades de su historia.
    Un ingrediente sin dato ese día no cuenta ni a favor ni en contra (la puntuación se calcula sobre los puntos disponibles)."""
    c = P[a]; idx = c.index; bpy = BPY[a]
    s200 = sma(c, 200); z = extension_z(c, bpy); liq = liquidez(L, a, idx) / 100.0
    hi52 = c.rolling(bpy, min_periods=bpy // 2).max(); lo52 = c.rolling(bpy, min_periods=bpy // 2).min(); dd52 = c / hi52 - 1
    w = semanal(c, a); rsiw = a_diario(rsi(w, 14), idx); rsid = rsi(c, 14)
    r = np.log(c).diff(); rvp = (r.rolling(20).std() * np.sqrt(bpy)).expanding(min_periods=750).rank(pct=True) * 100
    dl = L.reindex(idx)
    pts = pd.DataFrame(index=idx); mx = {}
    def pone(nombre, maximo, serie, valido=None):
        x = pd.Series(serie, index=idx).astype(float)
        if valido is not None: x = x.where(valido)
        pts[nombre] = x; mx[nombre] = maximo
    if a == 'BTC':
        mh = meses_desde_halving(idx)
        fase = pd.Series(np.where(mh < 12, 3.0, np.where(mh < 24, 0.0, np.where(mh < 30, 1.5, 3.0))), index=idx)
        pone('Liquidez (7 luces)', 3, 3 * liq, liq.notna())
        pone('Reloj del halving (fase del ciclo)', 3, fase, mh.notna())
        pone('Regla de venta apagada (tendencia + liquidez)', 2, 2 * regla_btc(c, liquidez(L, a, idx)), s200.notna())
        pone('Sin sobrecalentamiento (extensión por debajo de 1,2)', 1, (z < 1.2), z.notna())
        m200w = a_diario(sma(w, 200), idx)
        pone('Zona de valor (cerca de la media de 200 semanas)', 1, (c <= 1.10 * m200w), m200w.notna())
    elif a in ('sp500', 'nasdaq100'):
        vix = serie('VIX').reindex(idx).ffill(limit=4)
        if paro is None: paro = bandera_paro(pd.date_range('1967-01-01', idx[-1], freq='D'))[0]
        pr = paro.reindex(idx).ffill()
        motor = regla_bolsa(c, pr)
        if a == 'sp500':
            miedo = (vix >= 30) | (rvp >= 95) | (rsiw < 35)
            pone('Liquidez (6 luces)', 3, 3 * liq, liq.notna())
            pone('Tendencia (precio sobre su media de 200)', 2, 2 * (c > s200), s200.notna())
            pone('Sin recesión con tendencia rota', 2, 2 * motor, pr.notna() & s200.notna())
            pone('Miedo aprovechable (VIX 30+, volatilidad extrema o RSI semanal bajo 35)', 3, 3 * miedo, rsiw.notna())
        else:
            miedo = (vix >= 30) | (rsid < 30) | (rsiw < 35)
            dol = V['dolar'].reindex(idx); bono = V['tipos'].reindex(idx)
            pone('Dólar bajando (13 semanas)', 1.5, 1.5 * (dol < 0), dol.notna())
            pone('Bono a 10 años bajando (13 semanas)', 1.5, 1.5 * (bono < 0), bono.notna())
            pone('Dólar sin dispararse (no sube más del 3 %)', 1, (dol <= 3), dol.notna())
            pone('Miedo aprovechable (VIX 30+ o RSI bajo)', 3, 3 * miedo, rsiw.notna())
            pone('Sin sobrecalentamiento (extensión por debajo de 1,2)', 1, (z < 1.2), z.notna())
            pone('Sin recesión con tendencia rota', 2, 2 * motor, pr.notna() & s200.notna())
    elif a == 'oro':
        dol = V['dolar'].reindex(idx)
        pone('Tendencia (precio sobre su media de 200)', 3, 3 * (c > s200), s200.notna())
        pone('Media de 200 subiendo', 2, 2 * (s200 > s200.shift(20)), s200.shift(20).notna())
        pone('Sin caída del 10 % desde el máximo de 52 semanas', 2, 2 * (dd52 > -0.10), dd52.notna())
        pone('Dólar bajando (13 semanas)', 1, (dol < 0), dol.notna())
        pone('Sin subida parabólica (extensión por debajo de 1,7)', 1, (z < 1.7), z.notna())
        pone('Volatilidad extrema (suele preceder a subidas)', 1, (rvp >= 95), rvp.notna())
    else:   # plata
        g = P['oro']; gt = (g > sma(g, 200)).astype(float).where(sma(g, 200).notna()).reindex(idx).ffill(limit=5)
        ratio = (g.reindex(idx).ffill(limit=5) / c); rp = ratio.rolling(2520, min_periods=750).rank(pct=True) * 100
        pone('Tendencia (precio sobre su media de 200)', 2, 2 * (c > s200), s200.notna())
        pone('Media de 200 subiendo', 1, (s200 > s200.shift(20)), s200.shift(20).notna())
        pone('Oro en tendencia alcista', 2, 2 * gt, gt.notna())
        pone('Sin caída del 10 % desde el máximo de 52 semanas', 2, 2 * (dd52 > -0.10), dd52.notna())
        pone('Sin subida parabólica (extensión por debajo de 1,7)', 2, 2 * (z < 1.7), z.notna())
        pone('Plata no cara frente al oro (ratio oro/plata fuera de su 20 % más bajo)', 1, (rp > 20), rp.notna())
    maxs = pd.Series(mx)
    disp = pts.notna().mul(maxs, axis=1).sum(axis=1)
    score = (100 * pts.sum(axis=1, skipna=True) / disp).where(disp >= 0.6 * maxs.sum()).round(1)
    return pts, maxs, score


# ------------------------------------------------------------------ control de datos caducados
def avisos_datos(P, hoy):
    av = []; caducadas = set()
    for n, dias in CADUCA.items():
        try:
            u = serie(n).index[-1]
            if (hoy - u).days > dias: av.append(f"{n}: último dato del {u.date()} (hace {(hoy - u).days} días)"); caducadas.add(n)
        except Exception:
            av.append(f"{n}: no se puede leer"); caducadas.add(n)
    for a, dias in CADUCA_PRECIO.items():
        u = P[a].index[-1]
        if (hoy - u).days > dias: av.append(f"precio de {NOMBRE[a]}: último cierre del {u.date()} (hace {(hoy - u).days} días)")
    return av, caducadas


# ------------------------------------------------------------------ lectura de hoy
PUNT_ROJA, PUNT_VUELTA, PUNT_VERDE = 25, 50, 75
# series de las que depende la puntuación de cada activo (si alguna está caducada, esa puntuación no es fiable)
SERIES_PUNT = {'BTC': ['DXY', 'NFCI', 'DGS10', 'BAA10Y', 'WALCL', 'WTREGEN', 'RRPONTSYD', 'ECBASSETSW', 'JPNASSETS', 'DEXUSEU', 'DEXJPUS', 'ESTABLES'],
               'sp500': ['DXY', 'NFCI', 'DGS10', 'BAA10Y', 'WALCL', 'WTREGEN', 'RRPONTSYD', 'ECBASSETSW', 'JPNASSETS', 'DEXUSEU', 'DEXJPUS', 'VIX', 'ICSA'],
               'nasdaq100': ['DXY', 'DGS10', 'VIX', 'ICSA'], 'oro': ['DXY'], 'plata': []}


def regla_puntuacion(sc, tramos=True):
    """Venta según la puntuación (solo se usa en Bitcoin): fuera al bajar a 25 o menos; dentro al volver a 50 o más.
    Con tramos: mitad al saltar y el resto si 7 días después no ha vuelto a 50."""
    st = pd.Series(np.where(sc >= PUNT_VUELTA, 1.0, np.where(sc <= PUNT_ROJA, 0.5 if tramos else 0.0, np.nan)), index=sc.index).ffill().fillna(1.0)
    if tramos:
        todo = (st < 1).rolling(DIAS_TRAMO2 + 1).sum() == DIAS_TRAMO2 + 1
        st = st.where(~todo, 0.0)
    return st


def zona(a, p, obj=1.0):
    """Qué significa la puntuación en CADA activo (sale de lo que pasó después en su historia; no es igual en todos):
    Bitcoin: 25 o menos 'venta' · 25-40 'sin extra' · 40-75 'normal' · 75 o más 'extra'.
    Nasdaq 100: 25 o menos 'aviso' (precedió a caídas fuertes, pero con muy pocos casos: no es regla de venta) · 75 o más 'extra'.
    S&P 500: solo destaca 75 o más ('extra'); por debajo, 'normal'.
    Oro y plata: 75 o más 'extra' (tendencia a favor); por debajo, 'sin extra'."""
    if p is None or pd.isna(p): return 'sin dato'
    if a == 'BTC' and obj < 1.0: return 'venta activa'
    if p >= PUNT_VERDE: return 'extra'
    if a == 'BTC': return 'venta' if p <= PUNT_ROJA else ('sin extra' if p < 40 else 'normal')
    if a == 'nasdaq100': return 'aviso' if p <= PUNT_ROJA else 'normal'
    if a == 'sp500': return 'normal'
    return 'sin extra'


def accion(a, p, obj=1.0, obj_ayer=1.0):
    z = zona(a, p, obj)
    if z == 'sin dato': return 'Sin puntuación: faltan datos. Actualiza antes de decidir nada.'
    if a == 'BTC':
        if obj < obj_ayer:
            return ('HOY SALTA LA VENTA: vender la mitad de lo que rotas al próximo cierre.' if obj == 0.5 else 'HOY TOCA EL SEGUNDO TRAMO: vender el resto al próximo cierre.') + f' Recomprar todo cuando la puntuación vuelva a {PUNT_VUELTA}.'
        if obj > obj_ayer: return f'HOY TOCA RECOMPRAR: la puntuación ha vuelto a {PUNT_VUELTA} o más. Recomprar todo al próximo cierre.'
        if obj < 1.0:
            return ('Tramo 1 vendido (mitad); el resto se vende si a los 7 días de la primera venta no ha vuelto a 50.' if obj == 0.5 else 'Los dos tramos vendidos.') + f' Recomprar todo cuando la puntuación vuelva a {PUNT_VUELTA} o más.'
        if z == 'sin extra': return f'Compras periódicas de siempre, sin dinero extra. La venta por tramos salta si baja a {PUNT_ROJA} o menos.'
        if z == 'extra': return 'Buen momento para dinero extra, además de las compras periódicas.'
        return f'Compras periódicas de siempre. La venta por tramos salta si la puntuación baja a {PUNT_ROJA} o menos.'
    if z == 'aviso': return 'Aviso serio: sin dinero extra. Las otras veces (sobre todo en 2001 y 2008) hubo caídas fuertes después, pero son muy pocos casos y no hay regla de venta fiable.'
    if z == 'sin extra': return 'Compras periódicas de siempre, sin dinero extra. No se vende por puntuación en este activo.'
    if z == 'extra': return 'Buen momento para dinero extra, además de las compras periódicas.'
    return 'Compras periódicas de siempre. No se vende por puntuación en este activo.'


# ------------------------------------------------------------------ cambio oro <-> plata (ratio oro/plata)
RATIO_VENTANA = 260              # semanas: 5 años
RATIO_Z1, RATIO_Z2 = 1.5, 2.0    # medio tramo en cada umbral


def cambio_metales(P):
    """Ratio oro/plata con cierres semanales (viernes). z = distancia del ratio a su media de 5 años, medida en desviaciones típicas.
    Quien tiene PLATA: cambia medio tramo a oro con z por debajo de -1,5 y el otro medio por debajo de -2; vuelve a plata con z en 0 o más.
    Quien tiene ORO: cambia a plata con z por encima de +1,5 / +2; vuelve a oro con z en 0 o menos (este lado tiene mucho menos respaldo).
    Se decide con la semana cerrada. En la prueba (1975-2026) el lado de la plata dio entre x2 y x3 en unidades, con pocas operaciones
    (unas 7 independientes) y rachas de hasta un tercio por detrás antes de recuperarse."""
    d = pd.concat([P['oro'], P['plata']], axis=1, keys=['g', 's'], sort=True).dropna()
    w = d.resample('W-FRI').last().dropna()
    if w.index[-1] > d.index[-1]: w = w.iloc[:-1]            # la semana en curso no cuenta hasta que cierra
    lr = np.log(w.g / w.s); mp = RATIO_VENTANA // 2
    mu = lr.rolling(RATIO_VENTANA, min_periods=mp).mean(); sd = lr.rolling(RATIO_VENTANA, min_periods=mp).std()
    z = ((lr - mu) / sd).dropna()

    def tramos(lado):   # lado -1: plata cara (z muy bajo); +1: plata barata (z muy alto)
        est = {RATIO_Z1: None, RATIO_Z2: None}
        for t, v in z.items():
            for k in est:
                if est[k] is None and lado * v > k: est[k] = t
                elif est[k] is not None and lado * v <= 0: est[k] = None
        return est

    ep, eo = tramos(-1), tramos(+1)
    m, s = float(mu.iloc[-1]), float(sd.iloc[-1]); r = float(d.g.iloc[-1] / d.s.iloc[-1])
    niv = lambda k: float(np.exp(m + k * s))
    o = {'ratio': r, 'fecha': str(d.index[-1].date()), 'semana_cerrada': str(w.index[-1].date()), 'ratio_semana': float(w.g.iloc[-1] / w.s.iloc[-1]),
         'media_5a': niv(0), 'z': float((np.log(r) - m) / s), 'z_semana': float(z.iloc[-1]),
         'plata_cara_1': niv(-RATIO_Z1), 'plata_cara_2': niv(-RATIO_Z2), 'plata_barata_1': niv(RATIO_Z1), 'plata_barata_2': niv(RATIO_Z2),
         'plata_tramos_en_oro': sum(v is not None for v in ep.values()), 'oro_tramos_en_plata': sum(v is not None for v in eo.values()),
         'plata_desde': [None if v is None else str(v.date()) for v in ep.values()], 'oro_desde': [None if v is None else str(v.date()) for v in eo.values()],
         'plata_ratio_entrada': [None if v is None else float(np.exp(lr[v])) for v in ep.values()],
         'oro_ratio_entrada': [None if v is None else float(np.exp(lr[v])) for v in eo.values()]}
    n = o['plata_tramos_en_oro']; k = o['oro_tramos_en_plata']
    if n:
        o['estado'] = 'plata cara frente al oro'
        o['accion'] = (f"PLATA CARA FRENTE AL ORO: {n} de 2 medios tramos de la regla están cambiados a oro (desde {o['plata_desde'][0]}). "
                       + (f"El segundo medio tramo, si el ratio cierra una semana por debajo de {o['plata_cara_2']:.1f}. " if n == 1 else '')
                       + f"Vuelta a plata cuando el ratio cierre una semana en {o['media_5a']:.1f} o más (ese nivel se mueve un poco cada semana).")
    elif k:
        o['estado'] = 'plata barata frente al oro'
        o['accion'] = (f"PLATA BARATA FRENTE AL ORO: {k} de 2 medios tramos de la regla están cambiados de oro a plata (desde {o['oro_desde'][0]}). "
                       + (f"El segundo medio tramo, si el ratio cierra una semana por encima de {o['plata_barata_2']:.1f}. " if k == 1 else '')
                       + f"Vuelta a oro cuando el ratio cierre una semana en {o['media_5a']:.1f} o menos. Ojo: este lado tiene poco respaldo.")
    else:
        o['estado'] = 'normal'
        o['accion'] = (f"Ratio en zona normal: no se cambia nada. Plata a oro si cierra una semana por debajo de {o['plata_cara_1']:.1f}; "
                       f"oro a plata si cierra por encima de {o['plata_barata_1']:.1f}.")
    return o


def lectura(hoy=None):
    P = leer_precios()
    hasta = max(s.index[-1] for s in P.values())
    hoy = pd.Timestamp(hoy) if hoy is not None else max(hasta, pd.Timestamp.today().normalize())
    av, caducadas = avisos_datos(P, hoy)
    if hoy >= HALVING_PREVISTO: av.append(f'Reloj del halving: la fecha del siguiente halving ({HALVING_PREVISTO.date()}) es una estimación. Comprueba la fecha real y cámbiala en el programa.')
    L, V, info = luces_liquidez(hasta)
    out = {'fecha': str(hasta.date()), 'avisos': av, 'activos': {}, 'liquidez': {}}
    for k in LUZ_NOMBRE:
        val = V[k].iloc[-1]; cad = any(s in caducadas for s in LUZ_SERIES[k])
        estado = 'sin dato' if pd.isna(val) else ('caducada' if cad else ('verde' if L[k].iloc[-1] == 1 else 'roja'))
        out['liquidez'][k] = {'nombre': LUZ_NOMBRE[k], 'valor': None if pd.isna(val) else round(float(val), 2), 'estado': estado, 'verde': estado == 'verde'}
    fiable = all(x['estado'] in ('verde', 'roja') for x in out['liquidez'].values())
    out['liquidez_fiable'] = fiable
    if not fiable: out['avisos'].append('Faltan luces de liquidez o están caducadas: las puntuaciones que usan la liquidez NO son fiables hasta actualizar los datos.')
    paro_s, ratio_s = bandera_paro(pd.date_range('1967-01-01', hasta, freq='D'))
    for a in ACTIVOS:
        c = P[a]; bpy = BPY[a]; idx = c.index
        s200 = sma(c, 200); z = extension_z(c, bpy); liq = liquidez(L, a, idx)
        w = semanal(c, a); m = float(s200.iloc[-1]); px = float(c.iloc[-1])
        pts, mx, sc = puntuacion(a, P, L, V, paro_s)
        p_hoy = sc.iloc[-1]; atras = 28 if a == 'BTC' else 20; p_antes = sc.iloc[-1 - atras]
        malas = [n for n in SERIES_PUNT[a] if n in caducadas] + ([f'precio de {NOMBRE[a]}'] if (hoy - idx[-1]).days > CADUCA_PRECIO[a] else [])
        d = {'nombre': NOMBRE[a], 'fecha_precio': str(idx[-1].date()), 'precio': px, 'media200': m, 'dist_media200_pct': 100 * (px / m - 1),
             'extension_z': float(z.iloc[-1]), 'rsi_diario': float(rsi(c).iloc[-1]), 'rsi_semanal': float(a_diario(rsi(w, 14), idx).iloc[-1]),
             'caida_desde_max_historico_pct': 100 * (px / float(c.max()) - 1), 'caida_desde_max_52s_pct': 100 * (px / float(c.iloc[-bpy:].max()) - 1),
             'liquidez': float(liq.iloc[-1]),
             'puntuacion': None if pd.isna(p_hoy) else int(round(float(p_hoy))), 'puntuacion_hace_4_semanas': None if pd.isna(p_antes) else int(round(float(p_antes))),
             'puntuacion_fiable': len(malas) == 0, 'datos_caducados': malas,
             'ingredientes': [{'nombre': k, 'puntos': (None if pd.isna(pts[k].iloc[-1]) else round(float(pts[k].iloc[-1]), 1)), 'max': float(mx[k])} for k in pts.columns]}
        obj, obj_ayer = 1.0, 1.0
        if a == 'BTC':
            st = regla_puntuacion(sc, True); obj, obj_ayer = float(st.iloc[-1]), float(st.iloc[-2])
            d['meses_desde_halving'] = round(float(meses_desde_halving(idx).iloc[-1]), 1)
            d['media200semanas'] = float(a_diario(sma(w, 200), idx).iloc[-1])
            d['regla_sin_reloj_tendencia_liquidez'] = float(regla_btc(c, liq).iloc[-1])
        if a in ('sp500', 'nasdaq100'):
            d['paro_sobre_minimo_pct'] = float(100 * (ratio_s.reindex(idx).ffill().iloc[-1] - 1))
        if a in ('oro', 'plata'):
            par = float(regla_parabolica(c, bpy).iloc[-1]); d['aviso_parabolico'] = par < 1.0
            r = np.log(c).diff(); sd = float(r.ewm(span=bpy, min_periods=bpy // 2).std().iloc[-1])
            d['nivel_parabolico'] = float(m * np.exp(Z_PARABOLICA * sd * np.sqrt(200)))
        d['invertido_objetivo'] = obj
        d['zona'] = zona(a, p_hoy, obj)
        d['accion'] = accion(a, p_hoy, obj, obj_ayer)
        sc_ = senales_compra(a, c, L, V)
        d['compra'] = {k: estado_senal(v, bpy) for k, v in sc_.items()}
        d['compra_activas'] = [k for k, v in d['compra'].items() if v['activa'] and v['reciente']]
        d['compra_viejas'] = [k + ' (desde ' + v['desde'] + ')' for k, v in d['compra'].items() if v['activa'] and not v['reciente']]
        out['activos'][a] = d
    try:
        out['metales'] = cambio_metales(P)
        if (hoy - P['plata'].index[-1]).days > CADUCA_PRECIO['plata'] or (hoy - P['oro'].index[-1]).days > CADUCA_PRECIO['oro']:
            out['metales']['accion'] = 'NO FIABLE (precios de oro o plata caducados). ' + out['metales']['accion']
    except Exception as e:
        out['metales'] = None; out['avisos'].append(f'No se pudo calcular el ratio oro/plata: {e}')
    return out


def imprimir(o):
    print(f"\nTERMÓMETRO DE ACUMULACIÓN — datos hasta {o['fecha']}\n" + '=' * 60)
    if o['avisos']:
        print('\n*** ATENCIÓN: DATOS CADUCADOS O INCOMPLETOS ***')
        for x in o['avisos']: print('   -', x)
        print('   Actualiza con:  python3 termometro.py --descargar  (desde la Terminal normal del Mac)')
    print('\nPUNTUACIONES (0 = peor momento, 100 = mejor)')
    for a, d in o['activos'].items():
        print(f"  {d['nombre']:<11} {str(d['puntuacion']):>4}  {d['zona']:<12} (hace 4 semanas: {d['puntuacion_hace_4_semanas']})" + ('' if d['puntuacion_fiable'] else '   NO FIABLE: datos caducados (' + ', '.join(d['datos_caducados']) + ')'))
    disp = [x for x in o['liquidez'].values() if x['estado'] in ('verde', 'roja')]
    print(f"\nLIQUIDEZ: {sum(x['verde'] for x in disp)} luces verdes de {len(disp)} con dato válido" + ('' if o['liquidez_fiable'] else '  (LECTURA NO FIABLE)'))
    for k, x in o['liquidez'].items():
        print(f"  [{x['estado'].upper():<8}] {x['nombre']}: {x['valor']}")
    for a, d in o['activos'].items():
        print(f"\n{d['nombre'].upper()} — PUNTUACIÓN {d['puntuacion']} ({d['zona']})   precio {d['precio']:,.2f} (cierre del {d['fecha_precio']})")
        print(f"  {d['accion']}")
        if not d['puntuacion_fiable']: print('  *** PUNTUACIÓN NO FIABLE: datos caducados: ' + ', '.join(d['datos_caducados']) + ' ***')
        for g in d['ingredientes']:
            print(f"    {'sin dato' if g['puntos'] is None else format(g['puntos'], '.1f'):>8} de {g['max']:.1f}  {g['nombre']}")
        print(f"  Media de 200: {d['media200']:,.2f} ({d['dist_media200_pct']:+.1f} %) | extensión {d['extension_z']:.2f} | RSI diario {d['rsi_diario']:.0f}, semanal (última semana cerrada) {d['rsi_semanal']:.0f} | desde máximo histórico {d['caida_desde_max_historico_pct']:.0f} %")
        if a in ('oro', 'plata'):
            print('  Aviso de subida parabólica: ' + ('ACTIVO (no ha vuelto a su media de 200)' if d['aviso_parabolico'] else f"no (saltaría hacia {d['nivel_parabolico']:,.2f}, orientativo)"))
        print("  Señales de compra nuevas: " + ('; '.join(d['compra_activas']) if d['compra_activas'] else 'ninguna'))
        if d['compra_viejas']: print("    Siguen encendidas desde hace más de un mes: " + '; '.join(d['compra_viejas']))
    g = o.get('metales')
    if g:
        print(f"\nCAMBIO ORO <-> PLATA — ratio oro/plata {g['ratio']:.1f} (media de 5 años {g['media_5a']:.1f}; distancia {g['z']:+.2f} desviaciones; semana cerrada el {g['semana_cerrada']}: {g['z_semana']:+.2f})")
        print(f"  {g['accion']}")
        print(f"  Niveles de esta semana: plata cara por debajo de {g['plata_cara_1']:.1f} (medio tramo) y {g['plata_cara_2']:.1f} (el otro medio); plata barata por encima de {g['plata_barata_1']:.1f} y {g['plata_barata_2']:.1f}.")
        print("  Solo sirve con productos cotizados (no con metal físico) y es lenta: una operación cada cinco años de media.")


def guardar(o):
    json.dump(o, open(os.path.join(AQUI, 'lectura_actual.json'), 'w'), ensure_ascii=False, indent=1)
    f = os.path.join(AQUI, 'historial_lecturas.csv')
    fila = {'fecha': o['fecha'], 'luces_verdes': sum(x['verde'] for x in o['liquidez'].values()), 'liquidez_fiable': o['liquidez_fiable']}
    for a, d in o['activos'].items():
        fila.update({a + '_precio': round(d['precio'], 2), a + '_puntuacion': d['puntuacion'], a + '_objetivo': d['invertido_objetivo'], a + '_z': round(d['extension_z'], 2), a + '_compras_nuevas': len(d['compra_activas'])})
    if o.get('metales'):
        g = o['metales']; fila.update({'ratio_oro_plata': round(g['ratio'], 2), 'ratio_z': round(g['z'], 2), 'plata_tramos_en_oro': g['plata_tramos_en_oro'], 'oro_tramos_en_plata': g['oro_tramos_en_plata']})
    h = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
    h = pd.concat([h[h['fecha'] != o['fecha']] if len(h) else h, pd.DataFrame([fila])])
    h.to_csv(f, index=False)


# ------------------------------------------------------------------ descarga (solo funciona desde la Terminal normal del Mac)
def _get(url, intentos=3):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode('utf-8')
        except Exception:
            if i == intentos - 1: raise
            time.sleep(2)


def _fred(id_):
    s = pd.read_csv(io.StringIO(_get('https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + id_)), na_values=['.'], parse_dates=['observation_date'])
    return s.set_index('observation_date').iloc[:, 0].dropna()


def _yahoo(simbolo):
    """Cierres diarios del último año. Se descarta la vela de hoy: puede estar sin terminar."""
    url = 'https://query2.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d&interval=1d' % (urllib.request.quote(simbolo), int(time.time()) - 400 * 86400, int(time.time()))
    j = json.loads(_get(url))['chart']['result'][0]; off = j['meta'].get('gmtoffset', 0) or 0
    idx = pd.to_datetime([t + off for t in j['timestamp']], unit='s').normalize()
    s = pd.Series(j['indicators']['quote'][0]['close'], index=idx).dropna()
    return s[s.index < pd.Timestamp.utcnow().tz_localize(None).normalize()]


def _empalmar(viejo, nuevo, por_ratio=False):
    """Añade los días nuevos y corrige los últimos 7 guardados. por_ratio: reescala la fuente nueva para que case con la guardada (plata)."""
    nuevo = nuevo[~nuevo.index.duplicated(keep='last')].sort_index()
    corte = viejo.index[-1] - pd.Timedelta(days=7)
    if por_ratio:
        com = viejo.index.intersection(nuevo.index); com = com[com <= corte]
        if len(com): nuevo = nuevo * float((viejo[com] / nuevo[com]).iloc[-10:].mean())
    return pd.concat([viejo[viejo.index <= corte], nuevo[nuevo.index > corte]])


def descargar():
    fallos = []
    P = pd.read_csv(os.path.join(DATOS, 'precios_diarios.csv'), parse_dates=['fecha']).set_index('fecha')
    def intenta(nombre, fn):
        try: fn(); print('  ok   ', nombre)
        except Exception as e: fallos.append(nombre); print('  FALLO', nombre, '->', str(e)[:90])
    cols = {a: P[a].dropna() for a in ACTIVOS}
    def btc():
        t0 = int((cols['BTC'].index[-1] - pd.Timedelta(days=7)).timestamp() * 1000)
        k = json.loads(_get('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=%d&limit=1000' % t0))
        ahora = time.time() * 1000
        s = pd.Series({pd.Timestamp(x[0], unit='ms').normalize(): float(x[4]) for x in k if x[6] < ahora})   # solo velas cerradas
        cols['BTC'] = pd.concat([cols['BTC'][cols['BTC'].index < s.index[0]], s])
    intenta('precio Bitcoin (Binance)', btc)
    for a, sym, ratio in (('sp500', '^GSPC', False), ('nasdaq100', '^NDX', False), ('oro', 'GC=F', False), ('plata', 'SI=F', True)):
        def f(a=a, sym=sym, ratio=ratio): cols[a] = _empalmar(cols[a], _yahoo(sym), ratio)
        intenta('precio ' + NOMBRE[a] + ' (Yahoo)', f)
    pd.DataFrame(cols).rename_axis('fecha').to_csv(os.path.join(DATOS, 'precios_diarios.csv'))
    for nombre, sym in (('DXY', 'DX-Y.NYB'), ('VIX', '^VIX')):
        def f(nombre=nombre, sym=sym): guardar_serie(nombre, _empalmar(serie(nombre), _yahoo(sym)))
        intenta(nombre + ' (Yahoo)', f)
    for nombre, mult in (('NFCI', 1), ('DGS10', 1), ('BAA10Y', 1), ('DFII10', 1), ('ICSA', 1), ('DEXUSEU', 1), ('DEXJPUS', 1), ('RRPONTSYD', 1),
                         ('WALCL', 0.001), ('WTREGEN', 0.001), ('ECBASSETSW', 0.001), ('JPNASSETS', 0.001)):
        def f(nombre=nombre, mult=mult): guardar_serie(nombre, _fred(nombre) * mult)
        intenta(nombre + ' (FRED)', f)
    def fng():
        j = json.loads(_get('https://api.alternative.me/fng/?limit=0&format=json'))['data']
        guardar_serie('FNG_CRIPTO', pd.Series({pd.Timestamp(int(x['timestamp']), unit='s').normalize(): float(x['value']) for x in j}))
    intenta('miedo y codicia cripto (alternative.me)', fng)
    def cnn():
        j = json.loads(_get('https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2021-02-10'))['fear_and_greed_historical']['data']
        s = pd.Series({pd.Timestamp(int(x['x']), unit='ms').normalize(): round(float(x['y'])) for x in j})
        v = serie('FNG_CNN'); guardar_serie('FNG_CNN', pd.concat([v[v.index < s.index[0]], s]))
    intenta('miedo y codicia bolsa (CNN)', cnn)
    def est():
        j = json.loads(_get('https://stablecoins.llama.fi/stablecoincharts/all'))
        s = pd.Series({pd.Timestamp(int(x['date']), unit='s').normalize(): float(x['totalCirculatingUSD']['peggedUSD']) / 1e9 for x in j if x.get('totalCirculatingUSD', {}).get('peggedUSD')})
        s = s.sort_index(); s = s[s.index.dayofweek == 4]     # siempre viernes: la rejilla semanal no cambia de un día para otro
        v = serie('ESTABLES'); guardar_serie('ESTABLES', pd.concat([v[v.index < s.index[-60]], s[s.index >= s.index[-60]]]))
    intenta('monedas estables (DefiLlama)', est)
    if fallos: print('\nNo se han podido actualizar:', ', '.join(fallos), '\nSe usa el último dato guardado de esas series (si está caducado, la lectura lo avisará).')
    return fallos


if __name__ == '__main__':
    if '--descargar' in sys.argv:
        print('Descargando datos...'); descargar()
    o = lectura(); imprimir(o); guardar(o)
    print('\nGuardado: lectura_actual.json e historial_lecturas.csv')
