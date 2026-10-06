# -*- coding: utf-8 -*-
"""RADAR DE RIESGO BTC — revisión diaria.

Uso:
    python3 radar_diario.py            (lee hoy.json si existe, actualiza estado.csv, historial.json y resumen.json)
Ficheros (misma carpeta):
    estado.csv        datos en bruto diarios desde 2017 (se va ampliando)
    calibracion.json  distribución histórica de cada variable (para convertir valores en percentiles)
    eventos.json      fechas de Fed / IPC / empleo
    historial.json    lectura diaria del radar (reconstruida 2018-2026 + en vivo desde oct-2026)
    hoy.json          datos nuevos que trae Claude cada día (ver PLANTILLA_HOY)
    resumen.json      lectura de hoy, qué ha cambiado y si hay que avisar
"""
import json, os, sys, datetime as dt
import numpy as np, pandas as pd
import radar_nucleo as R

AQUI = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(AQUI, n)

PLANTILLA_HOY = {
    "velas": {"AAAA-MM-DD": {"o": 0, "h": 0, "l": 0, "c": 0, "v": 0, "taker_buy_v": 0}},
    "coinbase_cierre": {"AAAA-MM-DD": 0},
    "funding_dia": {"AAAA-MM-DD": 0.0},
    "stables_usd": {"AAAA-MM-DD": 0},
    "etf_flujo_musd": {"AAAA-MM-DD": 0},
    "fred": {"DGS2": {"AAAA-MM-DD": 0}, "NASDAQCOM": {"AAAA-MM-DD": 0}},
    "noticias": {"puntos": 0, "resumen": "", "fuentes": []},
    "eventos_proximos": [{"fecha": "AAAA-MM-DD", "evento": "IPC de EE. UU."}],
    "oi_okx_usd": {"AAAA-MM-DD": 0},
}


def cargar_estado():
    E = pd.read_csv(F('estado.csv'), parse_dates=['fecha']).set_index('fecha')
    for c in R.COLUMNAS + ['NASDAQCOM', 'oi_okx_usd']:
        if c not in E: E[c] = np.nan
    return E


def fusionar(E, H):
    def poner(fecha, col, val):
        if val is None: return
        f = pd.Timestamp(fecha)
        if f not in E.index:
            E.loc[f] = np.nan
        E.loc[f, col] = float(val)
    hoy_utc = pd.Timestamp(dt.datetime.now(dt.timezone.utc).date())
    for f, v in H.get('velas', {}).items():
        if pd.Timestamp(f) >= hoy_utc: continue  # vela sin cerrar
        for k in ['o', 'h', 'l', 'c', 'v', 'taker_buy_v']: poner(f, k, v.get(k))
    for f, v in H.get('coinbase_cierre', {}).items():
        if pd.Timestamp(f) < hoy_utc: poner(f, 'cb_c', v)
    for f, v in H.get('funding_dia', {}).items(): poner(f, 'funding_dia', v)
    for f, v in H.get('stables_usd', {}).items(): poner(f, 'stables_usd', v)
    for f, v in H.get('etf_flujo_musd', {}).items(): poner(f, 'etf_flujo_musd', v)
    for f, v in H.get('oi_okx_usd', {}).items(): poner(f, 'oi_okx_usd', v)
    for serie, obs in H.get('fred', {}).items():
        for f, v in obs.items(): poner(f, serie, v)
    E = E.sort_index()
    E = E[~E.index.duplicated(keep='last')]
    # rellenar días que falten en el calendario
    E = E.reindex(pd.date_range(E.index.min(), E.index.max(), freq='D'))
    E.index.name = 'fecha'
    # rentabilidad del Nasdaq a partir de niveles NASDAQCOM consecutivos (solo días en vivo)
    n = E['NASDAQCOM'].dropna()
    if len(n) >= 2:
        r = np.log(n).diff().dropna()
        for f, v in r.items():
            if pd.isna(E.loc[f, 'nasdaq_ret']): E.loc[f, 'nasdaq_ret'] = v
    return E


def sensibilidad_eventos(E, ev):
    """Cuánto se mueve BTC en los últimos 8 días de cada evento frente a un día normal."""
    c = E['c'].dropna(); r = np.log(c).diff().abs()
    normal = r.rolling(60, min_periods=30).median().shift(1)
    out = {}
    for k, nombre in [('FOMC', 'Reunión de la Fed'), ('CPI', 'Inflación (IPC)'), ('NFP', 'Empleo')]:
        d = pd.DatetimeIndex(pd.to_datetime(ev.get(k, [])))
        d = d[(d <= c.index.max()) & (d >= c.index.min())]
        if k == 'FOMC': d = pd.DatetimeIndex(sorted(set(d + pd.Timedelta(days=1))))  # el comunicado sale de noche en Europa
        x = (r / normal).reindex(d).dropna().iloc[-8:]
        out[nombre] = round(float(x.median()), 2) if len(x) else None
    return out


def piezas(X, ref, fila):
    P = R.Percentil(ref)
    nombres = {
        'tipos_2a_menos_fed': ('Bono a 2 años menos tipo de la Fed', 'pp', 'El mercado descuenta más subidas de tipos'),
        'tipos_2a_60d': ('Cambio del bono a 2 años en 60 días', 'pp', 'Sube = la Fed se endurece'),
        'tipos_10a_60d': ('Cambio del bono a 10 años en 60 días', 'pp', 'Sube = dinero más caro'),
        'tipos_real_60d': ('Cambio del tipo real a 10 años en 60 días', 'pp', 'Sube = peor para activos sin renta'),
        'cond_nfci_6s': ('Condiciones financieras (cambio 6 semanas)', 'índice', 'Sube = crédito más difícil'),
        'cond_credito_30d': ('Diferencial de crédito (cambio 30 días)', 'pp', 'Sube = miedo en el crédito'),
        'dolar_vs_media200': ('Dólar frente a su media de 200 días', '%', 'Dólar fuerte = menos liquidez global'),
        'dolar_60d': ('Cambio del dólar en 60 días', '%', 'Sube = se encarece la liquidez'),
        'stables_aceleracion': ('Aceleración de las stablecoins', 'pp', 'Baja = entra menos dinero nuevo a cripto'),
        'etf_flujo_10d': ('Flujo de los fondos de BTC (10 días)', 'M$', 'Negativo = salen inversores'),
        'liq_neta_13s': ('Liquidez neta de la Fed (13 semanas)', '%', 'Baja = se retira dinero del sistema'),
        'prima_coinbase7': ('Prima de Coinbase (7 días)', '%', 'Negativa = EE. UU. vende más que el resto'),
    }
    out = []
    for k, (n, u, expl) in nombres.items():
        v = fila.get(k)
        if v is None or pd.isna(v): continue
        pct = P.serie(pd.Series([v], name=k)).iloc[0]
        d = R.VARS_MACRO.get(k, R.VARS_LIQ.get(k, -1))
        riesgo = pct if d > 0 else 1 - pct
        if k == 'prima_coinbase7': riesgo = 1 - pct
        mult = 100 if u == '%' and k in ('dolar_vs_media200',) else 1
        out.append(dict(clave=k, nombre=n, valor=round(float(v) * mult, 2), unidad=u, explicacion=expl,
                        riesgo_pct=None if pd.isna(riesgo) else round(float(riesgo) * 100)))
    return out


def mensaje(res):
    emo = {'VERDE': '🟢', 'AMARILLO': '🟡', 'NARANJA': '🟠', 'ROJO': '🔴'}[res['nivel']]
    b = res['bloques']
    cab = f"<b>⚠️ Aviso:</b> {res['motivo_aviso']}" if res.get('avisar') else '<b>Resumen diario:</b> sin cambios de nivel'
    ayer = res.get('total_ayer')
    l = [f"<b>{emo} RADAR BTC · {res['nivel']} ({res['total']:.0f}/100)</b>" + (f" · ayer {ayer:.0f}" if ayer is not None else ''),
         f"Precio {res['precio']:,.0f} $ · cierre del {res['fecha']}".replace(',', '.'),
         '', cab, '',
         f"Macro {b['macro']:.0f} · Liquidez {b['liquidez']:.0f} · Estructura {b['estructura']:.0f} · Catalizadores {b['catalizadores']:.0f}",
         f"Hace 7 días: {res['total_hace7']:.0f} → hoy {res['total']:.0f}"]
    if res['gatillos']:
        l += ['', '<b>Gatillos:</b> ' + '; '.join(res['gatillos'])]
    l += ['', f"Soporte 20 días: {res['niveles']['soporte_20d']:,.0f} $ · Soporte 60 días: {res['niveles']['soporte_60d']:,.0f} $".replace(',', '.')]
    return '\n'.join(l)


def main():
    E = cargar_estado()
    hoy_json = F('hoy.json')
    H = json.load(open(hoy_json)) if os.path.exists(hoy_json) else {}
    E = fusionar(E, H)
    calib = json.load(open(F('calibracion.json')))
    ev = json.load(open(F('eventos.json')))
    X = R.variables(E)
    B = R.bloques(X, ref=calib['ref'])
    # último día con vela cerrada
    ult = X['precio'].last_valid_index()
    fila = X.loc[ult]; bl = B.loc[ult].copy()
    # noticias (solo hoy): suman al bloque de catalizadores
    pts = float(H.get('noticias', {}).get('puntos', 0) or 0)
    if pts:
        B.loc[ult, 'catalizadores'] = min(100.0, B.loc[ult, 'catalizadores'] + pts)
        B = R.componer(B)
        bl = B.loc[ult].copy()
    nivel = R.nivel(bl['total'])
    # historial
    hist = json.load(open(F('historial.json')))
    filas = {r['fecha']: r for r in hist['filas']}
    clave = ult.strftime('%Y-%m-%d')
    filas[clave] = dict(fecha=clave, precio=round(float(fila['precio']), 1), total=round(float(bl['total']), 1),
                        macro=round(float(bl['macro']), 1), liquidez=round(float(bl['liquidez']), 1),
                        estructura=round(float(bl['estructura']), 1), catalizadores=round(float(bl['catalizadores']), 1),
                        nivel=nivel, origen='en vivo', nota=H.get('noticias', {}).get('resumen', ''))
    orden = sorted(filas)
    hist['filas'] = [filas[k] for k in orden]
    prev = [filas[k] for k in orden if k < clave]
    ayer = prev[-1] if prev else None
    hace7 = [filas[k] for k in orden if k <= (ult - pd.Timedelta(days=7)).strftime('%Y-%m-%d')]
    hace7 = hace7[-1] if hace7 else ayer
    # gatillos
    g = []
    if fila.get('ruptura20') == 1: g.append('cierre por debajo del soporte de 20 días')
    if fila.get('ruptura_con_delta_vendedor_5d') == 1: g.append('ruptura con ventas agresivas fuertes')
    if fila.get('bajo_min60') == 1: g.append('precio bajo el mínimo de 60 días')
    if fila.get('reintento_fallido_10d') == 1: g.append('intento de recuperar el soporte fallido')
    if fila.get('n_sobresaltos_5d', 0) >= 1:
        nombres = {'bolsa': 'caída fuerte del Nasdaq', 'vix': 'salto del miedo (VIX)', 'tipos2a': 'salto del bono a 2 años',
                   'dolar': 'subida brusca del dólar', 'yen': 'subida brusca del yen', 'credito': 'salto del diferencial de crédito'}
        g += [nombres[k.split('_')[1]] for k in X.columns if k.startswith('sobresalto_') and fila.get(k) == 1]
    if pts >= 50: g.append('noticia de alto impacto: ' + H['noticias'].get('resumen', '')[:120])
    # decisión de aviso (con histéresis de 4 puntos)
    meta = hist.setdefault('meta', {})
    avisado = meta.get('ultimo_nivel_avisado', 'VERDE')
    orden_niv = ['VERDE', 'AMARILLO', 'NARANJA', 'ROJO']
    umbral = {n: u for u, n in R.NIVELES}
    avisar, motivo = False, ''
    if orden_niv.index(nivel) > orden_niv.index(avisado) and nivel in ('NARANJA', 'ROJO'):
        avisar, motivo = True, f'el riesgo sube a {nivel}'
        meta['ultimo_nivel_avisado'] = nivel
    elif orden_niv.index(avisado) >= 2 and bl['total'] < umbral[avisado] - 4:
        nuevo = nivel
        avisar, motivo = True, f'el riesgo baja de {avisado} a {nuevo}'
        meta['ultimo_nivel_avisado'] = nuevo
    nuevos_gat = fila.get('ruptura20') == 1 or (ayer and fila.get('ruptura_con_delta_vendedor_5d') == 1 and X['ruptura_con_delta_vendedor_5d'].shift(1).loc[ult] != 1)
    if nuevos_gat and bl['total'] >= 40:
        avisar = True; motivo = (motivo + ' · ' if motivo else '') + 'gatillo técnico: ' + g[0]
    if pts >= 50:
        avisar = True; motivo = (motivo + ' · ' if motivo else '') + 'catalizador externo nuevo'
    meta['ultima_revision'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    res = dict(fecha=clave, precio=float(fila['precio']), total=round(float(bl['total']), 1), nivel=nivel,
               bloques={k: round(float(bl[k]), 1) for k in ['macro', 'liquidez', 'estructura', 'catalizadores']},
               peso_macro=round(float(bl['peso_macro']), 2),
               total_ayer=ayer['total'] if ayer else None, total_hace7=hace7['total'] if hace7 else bl['total'],
               gatillos=g, avisar=avisar, motivo_aviso=motivo or 'sin cambios relevantes',
               niveles=dict(soporte_20d=round(float(fila['soporte_20d']), 0), soporte_60d=round(float(fila['soporte_60d']), 0),
                            techo_60d=round(float(fila['techo_60d']), 0)),
               flujo=dict(delta_hoy=round(float(fila['delta_ratio']) * 100, 1), cvd30=round(float(fila['cvd30']) * 100, 2),
                          rsi14=round(float(fila['rsi14']), 1), divergencias={k: int(fila[k] == 1) for k in ['div_rsi', 'div_macd', 'div_mfi', 'div_cvd']},
                          funding_anual=None if pd.isna(fila['funding_7d_anual']) else round(float(fila['funding_7d_anual']), 1),
                          vol30=round(float(fila['vol30']), 1)),
               corr_nasdaq=None if pd.isna(fila['corr_nasdaq_90d']) else round(float(fila['corr_nasdaq_90d']), 2),
               sensibilidad_eventos=sensibilidad_eventos(E, ev),
               eventos_proximos=H.get('eventos_proximos', []),
               piezas=piezas(X, calib['ref'], fila.to_dict()),
               noticias=H.get('noticias', {}))
    res['mensaje_telegram'] = mensaje(res)
    hist['hoy'] = res
    json.dump(hist, open(F('historial.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump(res, open(F('resumen.json'), 'w'), ensure_ascii=False, indent=1)
    E.to_csv(F('estado.csv'), float_format='%.8g')
    print(json.dumps({k: res[k] for k in ['fecha', 'precio', 'total', 'nivel', 'bloques', 'gatillos', 'avisar', 'motivo_aviso']}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
