# -*- coding: utf-8 -*-
"""RADAR DE RANGO BTC (4 h) — riesgo de perder el suelo de un lateral, aunque sea estrecho.

Uso:  python3 radar_rango.py      (lee hoy_4h.json si existe; actualiza velas_4h.csv, rango_estado.json y rango.json)
Ficheros (misma carpeta):
    velas_4h.csv       velas de 4 h de Binance BTCUSDT con volumen comprador agresivo (últimas ~700)
    hoy_4h.json        {"velas_4h": [[t_ms, o, h, l, c, v, t_cierre, qv, n, taker_buy_v, ...], ...]} tal cual las da Binance
    rango_modelo.json  modelos ajustados con 2017-2026 (riesgo de romper antes por abajo) y umbrales de ruptura fuerte
    estado.csv         estado diario del radar (para la media de 50 días)
    historial.json     radar diario (para dar contexto: nivel de hoy)
    rango_estado.json  memoria entre revisiones (rangos vigentes, rupturas en curso, avisos dados)
    rango.json         lo que lee la página: rangos, riesgo, velas recientes, historial y avisos
"""
import json, os, datetime as dt
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(AQUI, n)
CAPAS = {'mayor': dict(ventanas=[24, 36, 48, 72, 96, 120], ancho_max=0.12, ancho_min=0.02, er_max=0.30, texto='rango mayor (4-20 días)'),
         'menor': dict(ventanas=[12, 18, 24, 36], ancho_max=0.07, ancho_min=0.015, er_max=0.35, texto='rango menor (2-6 días)')}
UMBRAL_RIESGO = 0.70


def fmt(x):
    return f'{x:,.0f}'.replace(',', '.')


def dec(x, n=1):
    return f'{x:.{n}f}'.replace('.', ',')


def cargar_velas():
    d = pd.read_csv(F('velas_4h.csv'))
    if os.path.exists(F('hoy_4h.json')):
        H = json.load(open(F('hoy_4h.json')))
        nuevas = pd.DataFrame([[int(x[0]), *[float(x[k]) for k in (1, 2, 3, 4, 5)], float(x[7]), int(x[8]), float(x[9])]
                               for x in H.get('velas_4h', [])], columns=['t', 'o', 'h', 'l', 'c', 'v', 'qv', 'n', 'taker_buy_v'])
        ahora = dt.datetime.now(dt.timezone.utc).timestamp() * 1000
        nuevas = nuevas[nuevas.t + 4 * 3600000 <= ahora]  # solo velas cerradas
        d = pd.concat([d, nuevas]).drop_duplicates('t', keep='last').sort_values('t')
    if not os.environ.get('RANGO_REPLAY'):
        d = d.tail(700).reset_index(drop=True)
        d.to_csv(F('velas_4h.csv'), index=False, float_format='%.8g')
    else:
        d = d.reset_index(drop=True)
    d['fecha'] = pd.to_datetime(d['t'], unit='ms')
    return d.set_index('fecha')


def detectar(d, ventanas, ancho_max, ancho_min, er_max, **_):
    """Rango definido con las N velas anteriores; se queda la ventana más larga que cumple."""
    h, l, c = d['h'].values, d['l'].values, d['c'].values
    n = len(d); cs = np.cumsum(np.abs(np.diff(c, prepend=c[0])))
    out = {k: np.full(n, np.nan) for k in ['N', 'techo', 'suelo', 'ancho']}
    for N in ventanas:
        H = pd.Series(h).rolling(N).max().shift(1).values; L = pd.Series(l).rolling(N).min().shift(1).values
        ancho = (H - L) / ((H + L) / 2)
        er = np.abs(pd.Series(c).shift(1).values - pd.Series(c).shift(N).values) / pd.Series(cs - np.roll(cs, N)).shift(1).values
        ok = (ancho <= ancho_max) & (ancho >= ancho_min) & (er <= er_max)
        for k, v in [('N', N), ('techo', H), ('suelo', L), ('ancho', ancho)]:
            out[k] = np.where(ok, v, out[k])
    R = pd.DataFrame(out, index=d.index)
    for i in np.where(~np.isnan(R['N'].values))[0]:
        N = int(R['N'].values[i]); a, b = R['suelo'].values[i], R['techo'].values[i]; w = c[i - N:i]
        if np.sum(w >= b - 0.25 * (b - a)) < 2 or np.sum(w <= a + 0.25 * (b - a)) < 2:
            R.iloc[i] = np.nan
    return R


def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)


def senales(d, i, N, a, b, dist_ema50d):
    c, h, l, o, v = d['c'].values, d['h'].values, d['l'].values, d['o'].values, d['v'].values
    w = b - a; N = int(N)
    hw, lw, cw, ow, vw = h[i - N:i], l[i - N:i], c[i - N:i], o[i - N:i], v[i - N:i]
    bh = [hw[j:j + 6].max() for j in range(0, N - 5, 6)]; bl = [lw[j:j + 6].min() for j in range(0, N - 5, 6)]
    x = np.arange(len(bh))
    return {'posicion': (c[i] - a) / w, 'rsi4h': float(rsi(d['c']).values[i]), 'ret_24v': c[i] / c[i - 24] - 1,
            'pend_minimos': np.polyfit(x, bl, 1)[0] * len(bl) / w, 'pend_maximos': np.polyfit(x, bh, 1)[0] * len(bh) / w,
            'dist_ema50d': dist_ema50d, 'vol_velas_bajistas': vw[cw < ow].sum() / vw.sum(),
            'compresion_12v': (hw[-12:].max() - lw[-12:].min()) / w}


def probabilidad(m, s):
    z = sum(cf * (s[f] - mu) / sd for f, cf, mu, sd in zip(m['feats'], m['coef'], m['mu'], m['sd']))
    return 1 / (1 + np.exp(-(z + m['inter'])))


def contexto_diario():
    try:
        E = pd.read_csv(F('estado.csv'), parse_dates=['fecha']).set_index('fecha')['c'].dropna()
        ema = E.ewm(span=50).mean(); dist = float(E.iloc[-1] / ema.iloc[-1] - 1)
    except Exception:
        dist = 0.0
    try:
        hz = json.load(open(F('historial.json'))).get('hoy', {})
        radar = {'nivel': hz.get('nivel'), 'total': hz.get('total'), 'fecha': hz.get('fecha')}
    except Exception:
        radar = {}
    return dist, radar


def main():
    d = cargar_velas()
    M = json.load(open(F('rango_modelo.json')))
    est = json.load(open(F('rango_estado.json'))) if os.path.exists(F('rango_estado.json')) else {'capas': {}, 'historial': [], 'avisos': [], 'ultima_vela': 0}
    dist50, radar = contexto_diario()
    vmed = d['v'].rolling(60).median().values
    c, v, tb = d['c'].values, d['v'].values, d['taker_buy_v'].values
    tms = d['t'].values
    avisos_nuevos = []
    detec = {k: detectar(d, **p) for k, p in CAPAS.items()}
    pendientes = [i for i in range(len(d)) if tms[i] > est.get('ultima_vela', 0) and i >= 130]
    if est.get('ultima_vela', 0) == 0 and not os.environ.get('RANGO_REPLAY'):
        pendientes = pendientes[-1:]  # primera ejecución: solo la última vela
    for i in pendientes:
        fecha = d.index[i]
        for capa, p in CAPAS.items():
            R = detec[capa]; st = est['capas'].setdefault(capa, {'estado': 'sin rango'})
            r = R.iloc[i]
            if not np.isnan(r['techo']):
                # dentro de un rango válido
                nuevo = st.get('suelo') is None or abs(r['suelo'] - st.get('suelo', 0)) / r['suelo'] > 0.02 or st['estado'] in ('sin rango', 'roto al alza', 'confirmada')
                if nuevo:
                    st.update({'desde': fecha.strftime('%Y-%m-%d %H:%M'), 'aviso_riesgo': False})
                if st['estado'] in ('ruptura', 'confirmada') and c[i] >= st['suelo']:
                    avisos_nuevos.append(dict(tipo='BARRIDO', capa=capa, fecha=fecha.strftime('%Y-%m-%d %H:%M'), precio=float(c[i]),
                                              texto=f"Barrido del suelo del {p['texto']}: el precio vuelve a {fmt(c[i])} $, dentro del rango. La ruptura era falsa. Tras un barrido, 3 días después el precio estaba más arriba {M['ruptura']['barrido_3d']['p_sube']*100:.0f} de cada 100 veces."))
                st.update({'estado': 'dentro', 'techo': float(r['techo']), 'suelo': float(r['suelo']), 'ancho': float(r['ancho']), 'N': int(r['N'])})
                s = senales(d, i, r['N'], r['suelo'], r['techo'], dist50)
                st['senales'] = {k: round(float(x), 4) for k, x in s.items()}
                st['prob_abajo'] = round(float(probabilidad(M[capa], s)), 3)
                st['velas_ruptura'] = 0
                ult_aviso = st.get('ultimo_aviso_riesgo_t', 0)
                lejos = abs(st['suelo'] - st.get('ultimo_aviso_riesgo_suelo', 0)) / st['suelo'] > 0.01
                if (st['prob_abajo'] >= UMBRAL_RIESGO and s['posicion'] <= 0.25 and not st.get('aviso_riesgo')
                        and tms[i] - ult_aviso >= 48 * 3600000 and lejos):
                    st['aviso_riesgo'] = True; st['ultimo_aviso_riesgo_t'] = int(tms[i]); st['ultimo_aviso_riesgo_suelo'] = st['suelo']
                    avisos_nuevos.append(dict(tipo='RIESGO', capa=capa, fecha=fecha.strftime('%Y-%m-%d %H:%M'), precio=float(c[i]),
                                              texto=(f"Riesgo de perder el suelo del {p['texto']} ({fmt(st['suelo'])} $; techo {fmt(st['techo'])} $, ancho {dec(st['ancho']*100)} %). "
                                                    f"Probabilidad de que se rompa antes por abajo que por arriba: {st['prob_abajo']*100:.0f} %. "
                                                    f"Cuidado con los stops justo debajo del suelo: la mitad de las rupturas son barridos.")))
            elif st.get('suelo') is not None and st['estado'] in ('dentro', 'ruptura', 'confirmada'):
                a, b = st['suelo'], st['techo']; w = b - a
                if c[i] > b:
                    st['estado'] = 'roto al alza'
                elif c[i] >= a and st['estado'] in ('ruptura', 'confirmada'):
                    if st.get('velas_ruptura', 0) <= 6:
                        avisos_nuevos.append(dict(tipo='BARRIDO', capa=capa, fecha=fecha.strftime('%Y-%m-%d %H:%M'), precio=float(c[i]),
                                                  texto=f"Barrido del suelo del {p['texto']}: el precio vuelve a {fmt(c[i])} $, por encima de {fmt(a)} $. La ruptura era falsa. Tras un barrido, 3 días después el precio estaba más arriba {M['ruptura']['barrido_3d']['p_sube']*100:.0f} de cada 100 veces."))
                    st['estado'] = 'dentro'; st['velas_ruptura'] = 0
                elif c[i] < a:
                    st['velas_ruptura'] = st.get('velas_ruptura', 0) + 1
                    if st['estado'] == 'dentro':
                        prof = (a - c[i]) / w; vr = v[i] / vmed[i] if vmed[i] else np.nan; dl = (2 * tb[i] - v[i]) / v[i]
                        U = M['ruptura'][capa]
                        fuerte_p, fuerte_v = prof >= U['prof_fuerte'], vr >= U['vol_fuerte']
                        calidad = 'FUERTE' if (fuerte_p and fuerte_v) else 'MEDIA' if (fuerte_p or fuerte_v) else 'FLOJA'
                        p_real = M['ruptura']['real_si_ambos' if calidad == 'FUERTE' else 'real_si_uno' if calidad == 'MEDIA' else 'real_si_ninguno'][capa]
                        st.update({'estado': 'ruptura', 'ruptura': {'fecha': fecha.strftime('%Y-%m-%d %H:%M'), 'cierre': float(c[i]), 'profundidad_anchos': round(float(prof), 3),
                                                                    'volumen_relativo': round(float(vr), 2), 'delta': round(float(dl), 3), 'calidad': calidad, 'prob_real': p_real}})
                        T3 = M['ruptura']['tras_ruptura_3d'][calidad]
                        hostil = (radar.get('total') or 0) >= 52
                        if calidad == 'FUERTE':
                            lectura = (f"Ruptura FUERTE: cierre lejos del suelo y con mucho volumen. Así, {p_real*100:.0f} de cada 100 no recuperaron el suelo y siguieron cayendo. "
                                       + (f"Con el radar diario en naranja o rojo, como ahora, la caída mediana a 3 días fue del {abs(M['ruptura']['fuerte_con_radar_hostil']['ret3d']):.0f} % (pocos casos)." if hostil
                                          else f"Con el radar diario tranquilo, 3 días después el precio estaba más abajo el {T3['p_baja']*100:.0f} % de las veces."))
                        elif calidad == 'FLOJA':
                            lectura = (f"Ruptura FLOJA: cierre justo debajo y sin volumen excepcional. Suele ser un barrido: 3 días después el precio estaba más arriba "
                                       f"{(1-T3['p_baja'])*100:.0f} de cada 100 veces. Ojo a la recuperación del suelo.")
                        else:
                            lectura = "Ruptura MEDIA: sin ventaja clara. Decide el siguiente cierre de 4 h: otro cierre debajo la confirma; volver dentro la convierte en barrido."
                        avisos_nuevos.append(dict(tipo='RUPTURA', capa=capa, calidad=calidad, fecha=fecha.strftime('%Y-%m-%d %H:%M'), precio=float(c[i]),
                                                  texto=(f"Ruptura bajista del {p['texto']}: cierre de 4 h en {fmt(c[i])} $, bajo el suelo de {fmt(a)} $ "
                                                         f"({dec(prof*100, 0 if prof >= 0.1 else 1)} % del ancho por debajo, volumen {dec(vr)} veces lo normal). " + lectura)))
                    elif st['estado'] == 'ruptura' and st['velas_ruptura'] >= 2:
                        st['estado'] = 'confirmada'
                        caida = M['ruptura']['caida5d_dos_cierres'][capa]
                        avisos_nuevos.append(dict(tipo='CONFIRMADA', capa=capa, fecha=fecha.strftime('%Y-%m-%d %H:%M'), precio=float(c[i]),
                                                  texto=f"Ruptura confirmada del {p['texto']}: segundo cierre de 4 h bajo {fmt(a)} $ ({fmt(c[i])} $). Con dos cierres debajo, la caída mediana en los 5 días siguientes fue del {dec(abs(caida))} %."))
                    if st['estado'] == 'confirmada' and (c[i] < a - 1.5 * w or st['velas_ruptura'] > 30):
                        st['estado'] = 'sin rango'
                else:
                    st['estado'] = 'sin rango'
            else:
                st['estado'] = 'sin rango' if st.get('estado') not in ('roto al alza',) else st['estado']
        est['ultima_vela'] = int(tms[i])
        est['historial'].append({'t': fecha.strftime('%Y-%m-%d %H:%M'), 'precio': float(c[i]),
                                 **{f'p_{k}': est['capas'].get(k, {}).get('prob_abajo') if est['capas'].get(k, {}).get('estado') == 'dentro' else None for k in CAPAS},
                                 **{f'estado_{k}': est['capas'].get(k, {}).get('estado') for k in CAPAS}})
    est['historial'] = est['historial'][-540:]
    for a in avisos_nuevos:
        a['radar_diario'] = radar
    est['avisos'] = (est.get('avisos', []) + avisos_nuevos)[-40:]
    if os.environ.get('RANGO_REPLAY'): json.dump(avisos_nuevos, open(F('avisos_replay.json'), 'w'), ensure_ascii=False)
    est['actualizado'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    json.dump(est, open(F('rango_estado.json'), 'w'), ensure_ascii=False, indent=1)
    # fichero para la página
    ult = d.tail(120)
    pag = {'actualizado': est['actualizado'], 'ultima_vela': d.index[-1].strftime('%Y-%m-%d %H:%M'), 'precio': float(c[-1]),
           'capas': {k: {kk: vv for kk, vv in est['capas'].get(k, {}).items()} for k in CAPAS},
           'textos': {k: p['texto'] for k, p in CAPAS.items()}, 'radar_diario': radar,
           'velas': [[x.strftime('%Y-%m-%d %H:%M'), round(o_, 1), round(h_, 1), round(l_, 1), round(c_, 1)] for x, o_, h_, l_, c_ in zip(ult.index, ult.o, ult.h, ult.l, ult.c)],
           'historial': est['historial'][-180:], 'avisos': est['avisos'][-12:],
           'referencia': {'falsas': M['ruptura']['falsas'], 'caida5d_dos_cierres': M['ruptura']['caida5d_dos_cierres']}}
    json.dump(pag, open(F('rango.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    # mensaje de Telegram (solo si hay avisos nuevos)
    msg = ''
    if avisos_nuevos:
        emo = {'RIESGO': '🟡', 'RUPTURA': '🟠', 'CONFIRMADA': '🔴', 'BARRIDO': '🟢'}
        lineas = ['<b>📦 RANGO BTC · 4 horas</b>']
        for a in avisos_nuevos:
            lineas += ['', f"{emo[a['tipo']]} <b>{a['tipo']}</b> · {a['fecha']} UTC", a['texto']]
        if radar.get('nivel'):
            lineas += ['', f"Radar diario: {radar['nivel']} ({radar.get('total', 0):.0f}/100)"]
        msg = '\n'.join(lineas)
    res = {'avisar': bool(avisos_nuevos), 'mensaje_telegram': msg, 'avisos': avisos_nuevos,
           'capas': {k: {kk: est['capas'].get(k, {}).get(kk) for kk in ('estado', 'techo', 'suelo', 'ancho', 'prob_abajo')} for k in CAPAS},
           'ultima_vela': pag['ultima_vela'], 'precio': pag['precio']}
    json.dump(res, open(F('resumen_rango.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ('ultima_vela', 'precio', 'capas', 'avisar')}, ensure_ascii=False, indent=1))
    for a in avisos_nuevos: print('AVISO', a['tipo'], a['capa'], a['fecha'])


if __name__ == '__main__':
    main()
