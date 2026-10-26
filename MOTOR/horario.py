# -*- coding: utf-8 -*-
"""Punto 7 del motor de cartera: horario de revisiones.

Horarios (hora de España, Europe/Madrid, con cambio de hora):
  a  ACTUAL: COMPLETA 6:00 + barrido de 4 h a las 10, 14, 18 y 22 + ligeras cada hora de 7 a 22 que miran la lista
     de vigilancia y lo abierto; nada de 22:01 a 5:59. En cripto no se persigue la entrada perdida.
       a-opt: la ligera ve la señal de 4 h si el activo estaba en vigilancia (se supone que sí).
       a-pes: las señales nuevas de 4 h solo las ven la COMPLETA y el barrido (6, 10, 14, 18, 22).
     Las salidas (retroceso fallido, cierre de 4 h bajo la media) y los stops que suben sí se miran cada hora de 6 a 22.
  b  revisión de todo cada hora de 6 a 22.
  c  como b, con el contexto recalculado cada hora (se estima aparte si cambia el tamaño de alguna señal).
  d  24 h.
Las órdenes de stop y de venta parcial (+1 R) quedan puestas en el bróker y se ejecutan a cualquier hora.
Lo que depende del horario: (1) entrar en la vela de 4 h (cripto: si no se ve el cierre, se pierde; oro y plata de
4 h y 1 h: se entra en la siguiente revisión, al precio de entonces), (2) las salidas por cierre de vela de 4 h
(se ejecutan en la siguiente revisión, al precio de entonces, salvo que antes toque el stop) y (3) subir el stop
(se estima con el simulador provisional del REBOTE 4H, porque las listas no traen la trayectoria del stop).
"""
import os, sys
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, '/home/claude/velas-backtest')
from cargar import velas
from precios import activo_base

TZ = 'Europe/Madrid'
H_DIA = set(range(6, 23))
HORARIOS = {
    'a-opt': dict(entrada=H_DIA, salida=H_DIA),
    'a-pes': dict(entrada={6, 10, 14, 18, 22}, salida=H_DIA),
    'b': dict(entrada=H_DIA, salida=H_DIA),
    'd': dict(entrada=set(range(24)), salida=set(range(24))),
}
ALIAS_VELAS = {'ORO': 'oro', 'PLATA': 'plata', 'GOLD': 'oro', 'SILVER': 'plata'}


def local(t):
    t = pd.DatetimeIndex(pd.to_datetime(t))
    return t.tz_localize('UTC').tz_convert(TZ)


def siguiente_revision(t_utc, horas):
    """Primera hora en punto (UTC) >= t_utc cuya hora local está en `horas`."""
    t = pd.Timestamp(t_utc).ceil('h')
    for _ in range(48):
        if local([t])[0].hour in horas:
            return t
        t += pd.Timedelta(hours=1)
    return t


_cache = {}


def velas_intradia(activo):
    a = activo_base(activo)
    a = ALIAS_VELAS.get(a.upper(), a)
    if a in _cache:
        return _cache[a]
    df = None
    for tf in ('1h', '4h'):
        try:
            d = velas(a, tf)
            d.index = pd.to_datetime(d.index)
            d = d.rename(columns={'apertura': 'o', 'maximo': 'h', 'minimo': 'l', 'cierre': 'c'})[['o', 'h', 'l', 'c']]
            df = d if df is None else pd.concat([d[d.index < df.index[0]], df]).sort_index() if tf == '4h' else d
            if tf == '1h':
                continue
        except Exception:
            pass
    _cache[a] = df
    return df


def precio_en(df, t):
    if df is None or len(df) == 0 or t < df.index[0] or t > df.index[-1] + pd.Timedelta(hours=4):
        return None
    i = df.index.searchsorted(t)
    if i >= len(df):
        return None
    return float(df.o.iloc[i])


def toca_stop(df, t0, t1, sl, d):
    if df is None:
        return False
    x = df[(df.index >= t0.floor('h')) & (df.index < t1)]
    if not len(x):
        return False
    return bool((x.l <= sl).any()) if d == 1 else bool((x.h >= sl).any())


def es_intradia(O):
    """Señales de 4 h o 1 h: la familia cripto y las señales de oro/plata con «4h» o «1h» en su nombre."""
    s = O.senal.astype(str).str.lower()
    return np.isin(O.lista.values, ['cripto', 'cripto_24h']) | s.str.contains('4h').values | s.str.contains('1h').values | \
        s.str.contains('4 h').values | s.str.contains('1 h').values


def es_salida_por_cierre(O):
    m = O.motivo_salida.astype(str).str.lower()
    return (m.str.contains('retroceso').values | m.str.contains('4h').values | m.str.contains('ema').values |
            m.str.contains('fallid').values) & es_intradia(O)


def aplicar(O, nombre, cripto_por_lista=False):
    """Devuelve una copia de O con el efecto del horario: entradas perdidas (máscara), entradas retrasadas y salidas
    retrasadas con su nuevo R. También el detalle de qué cambió."""
    h = HORARIOS[nombre]
    O2 = O.copy()
    intr = es_intradia(O)
    cripto = np.isin(O.lista.values, ['cripto', 'cripto_24h'])
    if cripto_por_lista:
        # la cripto ya viene simulada con cada horario en su propia lista (cripto_realista / cripto de 24 h)
        intr = intr & ~cripto
    hora_ent = local(O.t_senal.values).hour
    vista = np.isin(hora_ent, list(h['entrada']))
    perdida = intr & cripto & ~vista
    retrasar = intr & ~cripto & ~vista
    det = dict(entradas_intradia=int(intr.sum()), perdidas=int(perdida.sum()), R_perdidas=float(O.r_final.values[perdida].sum()),
               retrasadas=int(retrasar.sum()), salidas_retrasadas=0, dR_retrasos_entrada=0.0, dR_salidas=0.0,
               salidas_sin_precio=0)
    # entradas retrasadas (oro y plata de 4 h / 1 h): se entra en la siguiente revisión
    for i in np.flatnonzero(retrasar):
        o = O.iloc[i]
        t = siguiente_revision(o.t_senal, h['entrada'])
        df = velas_intradia(o.activo)
        p = precio_en(df, t)
        if p is None or not np.isfinite(o.entrada) or not np.isfinite(o.sl_inicial):
            continue
        d = int(o.direccion)
        riesgo = d * (o.entrada - o.sl_inicial)
        if riesgo <= 0:
            continue
        # tarde y casi en el stop: con el mismo stop el tamaño se dispararía; se da por perdida
        if t >= o.t_salida or d * (p - o.sl_inicial) < 0.25 * riesgo:
            perdida[i] = True
            det['perdidas'] += 1
            det['R_perdidas'] += float(o.r_final)
            continue
        X = o.entrada + d * o.r_bruto * riesgo           # precio de salida equivalente
        rb = d * (X - p) / (d * (p - o.sl_inicial))
        nf = rb * o.tam_R
        det['dR_retrasos_entrada'] += float(nf - o.r_final)
        O2.iat[i, O2.columns.get_loc('r_final')] = nf
        O2.iat[i, O2.columns.get_loc('t_entrada')] = t
    # salidas por cierre de vela no vistas: se ejecutan en la siguiente revisión
    sal = es_salida_por_cierre(O)
    if cripto_por_lista:
        sal = sal & ~cripto
    hora_sal = local(O.t_salida.values).hour
    vista_sal = np.isin(hora_sal, list(h['salida'])) | np.isin((hora_sal + 1) % 24, list(h['salida']))
    for i in np.flatnonzero(sal & ~vista_sal & ~perdida):
        o = O.iloc[i]
        t = siguiente_revision(o.t_salida, h['salida'])
        df = velas_intradia(o.activo)
        p = precio_en(df, t)
        d = int(o.direccion)
        riesgo = d * (o.entrada - o.sl_inicial)
        if p is None or riesgo <= 0 or not np.isfinite(o.salida):
            det['salidas_sin_precio'] += 1
            continue
        if toca_stop(df, o.t_salida, t, o.sl_inicial, d):
            p = o.sl_inicial
        rb = o.r_bruto + d * (p - o.salida) / riesgo
        nf = rb * o.tam_R
        det['salidas_retrasadas'] += 1
        det['dR_salidas'] += float(nf - o.r_final)
        O2.iat[i, O2.columns.get_loc('r_final')] = nf
        O2.iat[i, O2.columns.get_loc('t_salida')] = t
    det = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in det.items()}
    return O2, ~perdida, det


# ------------------------------------------------------------------ simulador provisional del REBOTE 4H con horario
def cripto_con_horario(horas_ent, horas_sal, actualiza_stop=True, activos=('BTC', 'ETH', 'SOL', 'ADA', 'LINK', 'ZEC')):
    """Versión del REBOTE 4H provisional (provisional/gen.py) en la que solo se entra en cierres vistos, la salida
    por retroceso fallido y la subida del stop (y el paso del stop a la entrada tras vender 1/3) se hacen en la
    siguiente revisión. Devuelve R total (con tamaño de la lista provisional) y número de operaciones."""
    sys.path.insert(0, os.path.join(AQUI, 'provisional'))
    import gen
    T2 = gen.total2()
    tot, nops = 0.0, 0
    for a in activos:
        h4 = gen.ohlc(a, '4h')
        dd = gen.ohlc(a, '1d')
        atr4 = gen.wilder(h4)
        ema20 = h4.c.ewm(span=20, adjust=False).mean().values
        atrd = pd.Series(gen.wilder(dd), index=dd.index)
        sma200 = dd.c.rolling(200).mean()
        e20 = dd.c.ewm(span=20, adjust=False).mean()
        e50 = dd.c.ewm(span=50, adjust=False).mean()
        tend = ((dd.c > sma200) & (e20 > e50)).shift(1)
        dia_idx = h4.index.normalize()
        tend4 = tend.reindex(dia_idx).fillna(False).values.astype(bool)
        atrd4 = atrd.shift(1).reindex(dia_idx).values
        t2r = (T2.t2 / T2.s20 - 1).shift(1).reindex(dia_idx).values
        o, hh, l, c = h4.o.values, h4.h.values, h4.l.values, h4.c.values
        idx = h4.index
        cierre_local = local(idx + pd.Timedelta(hours=4)).hour
        ve_ent = np.isin(cierre_local, list(horas_ent))
        # salidas y stop: se pueden hacer tarde; un cierre se ve si hay revisión a esa hora o a la siguiente
        ve_sal = np.isin(cierre_local, list(horas_sal)) | np.isin((cierre_local + 1) % 24, list(horas_sal))
        n = len(c)
        rf_ok = a in ('BTC', 'ETH', 'ADA', 'ZEC')
        i = 60
        while i < n - 1:
            ok = (ve_ent[i] and tend4[i] and not np.isnan(atr4[i]) and not np.isnan(atrd4[i])
                  and min(l[i], l[i - 1]) <= ema20[i] * 1.002 and c[i] > ema20[i] and c[i] > o[i]
                  and c[i] - ema20[i] <= 1.0 * atr4[i])
            if not ok:
                i += 1
                continue
            e = i + 1
            ent = o[e]
            sl = ent - 2 * atr4[i]
            rp = ent - sl
            ad = atrd4[i]
            x = t2r[i]
            tam = 1.0 if np.isnan(x) else (1.5 if x < 0 else (0.5 if x <= 0.06 else 1.0))
            parcial = False
            stop = sl
            stop_obj = sl
            maxh = ent
            res = None
            j = e
            while j < n:
                if j > e and o[j] <= stop:
                    u = (o[j] - ent) / rp
                    res = (1 / 3 + 2 / 3 * u) if parcial else u
                    break
                if l[j] <= stop:
                    u = (stop - ent) / rp
                    res = (1 / 3 + 2 / 3 * u) if parcial else u
                    break
                if not parcial and hh[j] >= ent + rp:
                    parcial = True
                    stop_obj = max(stop_obj, ent)
                maxh = max(maxh, hh[j])
                stop_obj = max(stop_obj, maxh - 2.5 * ad)
                visto = ve_sal[j] or not actualiza_stop
                if visto:
                    stop = max(stop, stop_obj)
                if rf_ok and not parcial and c[j] < ema20[j] - 0.75 * atr4[j]:
                    if ve_sal[j]:
                        res = (c[j] - ent) / rp
                        break
                    # cierre no visto: se sale al cierre de la primera vela vista, salvo que antes toque el stop
                    m = j + 1
                    while m < n:
                        if o[m] <= stop or l[m] <= stop:
                            break
                        if ve_sal[m]:
                            break
                        m += 1
                    if m >= n:
                        res = (c[n - 1] - ent) / rp
                    elif o[m] <= stop:
                        res = (o[m] - ent) / rp
                    elif l[m] <= stop:
                        res = (stop - ent) / rp
                    else:
                        res = (c[m] - ent) / rp
                    j = m
                    break
                j += 1
            if res is None:
                break
            coste = 0.0016 * ent / rp
            tot += (res - coste) * tam
            nops += 1
            i = max(i + 1, j)
    return round(float(tot), 2), nops


def estimar_stops():
    """Efecto de cada parte del horario en el REBOTE 4H provisional (R total 2018-2026, tamaño provisional)."""
    filas = []
    todo = set(range(24))
    casos = [('d · 24 h (todo visto)', todo, todo, True),
             ('a/b · entradas 6-22, salidas y stop 6-22', H_DIA, H_DIA, True),
             ('a-pes · entradas 6,10,14,18,22; salidas y stop 6-22', {6, 10, 14, 18, 22}, H_DIA, True),
             ('solo entradas 6-22 (salidas y stop 24 h)', H_DIA, todo, True),
             ('solo salidas y stop 6-22 (entradas 24 h)', todo, H_DIA, True)]
    for n, he, hs, st in casos:
        R, k = cripto_con_horario(he, hs, st)
        filas.append(dict(caso=n, R_total=R, operaciones=k))
    return pd.DataFrame(filas)


def contexto_horario(O):
    """(c) ¿Cambia el tamaño si TOTAL2 se mide con la vela de 4 h más reciente en vez del cierre diario anterior?
    Desde 2024 (hay capitalización total de 4 h); dominancia de BTC del día anterior."""
    try:
        cap4 = velas('capitalizacion_total', '4h')
        cap4.index = pd.to_datetime(cap4.index)
        capd = velas('capitalizacion_total', '1d')
        capd.index = pd.to_datetime(capd.index).normalize()
        dom = velas('dominancia_btc', '1d')
        dom.index = pd.to_datetime(dom.index).normalize()
    except Exception as e:
        return dict(error=str(e))
    t2d = (capd.cierre * (1 - dom.cierre.reindex(capd.index).ffill() / 100)).dropna()
    s20 = t2d.rolling(20).mean()
    c = O[(O.lista == 'cripto') & (O.t_senal >= pd.Timestamp('2024-02-01'))]
    if not len(c):
        return dict(n=0)
    def zona(x):
        return 'bajo' if x < 0 else ('franja' if x <= 0.06 else 'encima')
    f = {'bajo': 1.5, 'franja': 0.5, 'encima': 1.0}
    cambios, dR = 0, 0.0
    for _, o in c.iterrows():
        dia = o.t_senal.normalize()
        prev = t2d.index[t2d.index < dia]
        if not len(prev):
            continue
        d0 = prev[-1]
        x0 = t2d[d0] / s20[d0] - 1
        k = cap4.index[cap4.index + pd.Timedelta(hours=4) <= o.t_senal]
        if not len(k):
            continue
        dm = dom.cierre[dom.index < dia]
        t2now = cap4.cierre[k[-1]] * (1 - dm.iloc[-1] / 100)
        x1 = t2now / s20[d0] - 1
        z0, z1 = zona(x0), zona(x1)
        if z0 != z1:
            cambios += 1
            dR += o.r_final * (f[z1] / f[z0] - 1)
    return dict(senales=len(c), cambian_de_zona=cambios, pct=round(100 * cambios / len(c), 1), dR_aprox=round(dR, 1))
