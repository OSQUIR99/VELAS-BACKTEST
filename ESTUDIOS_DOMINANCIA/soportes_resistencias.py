# -*- coding: utf-8 -*-
"""¿Rebotan las dominancias en soportes y resistencias? (15-oct-2026)

Dos tipos de niveles:
  OBJETIVOS: giros semanales (máximo/mínimo con 3 semanas a cada lado), agrupados si están a menos
             de 'tol'. Solo cuentan giros ya confirmados en esa fecha (sin mirar el futuro).
  DIBUJADOS: las líneas del gráfico de Óscar (15-oct-2026), leídas a ojo. Ojo: se dibujaron
             conociendo el pasado, así que su resultado está inflado.

1) Estudio de eventos: cada vez que la vela semanal toca un nivel viniendo de lejos,
   ¿cuántas veces rebota y cuántas lo rompe en las 8 semanas siguientes?
2) Estrategia de rotación: toque de soporte/resistencia -> rotar; si se rompe el nivel -> volver a 50/50.
"""
import sys, os, json
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from rotacion_dominancia import simular, metricas, tramos

DIBUJADOS = {
    'ETH_BTC': [0.0337, 0.0287, 0.0262, 0.0178],
    'dominancia_btc': [69.0, 65.3, 61.0, 58.5, 55.0],
    'dominancia_usdt': [8.25, 7.1, 6.75, 4.55, 3.85, 3.6],
    'others_fuera_top10': [345e9, 330e9, 290e9, 190e9, 175e9, 165e9],
}

def giros(w, n=3):
    """Lista (fecha_confirmación, precio) de máximos y mínimos locales."""
    hi, lo, out = w.maximo.values, w.minimo.values, []
    for i in range(n, len(w) - n):
        if hi[i] == hi[i - n:i + n + 1].max(): out.append((w.index[i + n], hi[i]))
        if lo[i] == lo[i - n:i + n + 1].min(): out.append((w.index[i + n], lo[i]))
    return out

def niveles_en(fecha, piv, tol, min_toques):
    p = sorted(np.log([x for d, x in piv if d <= fecha]))
    grupos, g = [], []
    for v in p:
        if g and v - g[0] > tol: grupos.append(g); g = []
        g.append(v)
    if g: grupos.append(g)
    return [float(np.exp(np.mean(g))) for g in grupos if len(g) >= min_toques]

def eventos(w, tipo, tol=0.02, min_toques=2, fijos=None):
    """Toque 'fresco': la semana anterior estaba a más de 3·tol del nivel."""
    piv = giros(w); ev = []
    for i in range(10, len(w) - 1):
        d = w.index[i]
        lv = fijos if tipo == 'dibujados' else niveles_en(d, piv, tol, min_toques)
        c, lo, hi, pc = w.cierre.iloc[i], w.minimo.iloc[i], w.maximo.iloc[i], w.cierre.iloc[i - 1]
        for L in lv:
            if pc > L * (1 + 3 * tol) and lo <= L * (1 + tol) and c > L * (1 - tol):
                ev.append((d, 'soporte', L))
            if pc < L * (1 - 3 * tol) and hi >= L * (1 - tol) and c < L * (1 + tol):
                ev.append((d, 'resistencia', L))
    return ev

def resultado_evento(w, d, lado, L, tol, h=8):
    fut = w.loc[w.index > d].iloc[:h]
    if len(fut) < h: return None
    s = 1 if lado == 'soporte' else -1
    roto = ((fut.cierre - L) * s < -2 * tol * L).any()
    mov = (fut.cierre.iloc[-1] / w.cierre.loc[d] - 1) * s     # >0 = se movió a favor del rebote
    return dict(rebote=mov > 0, mov=mov, roto=roto)

def azar(w, h=8):
    """Referencia: cualquier semana, ¿con qué frecuencia sube / baja en h semanas?"""
    r = w.cierre.shift(-h) / w.cierre - 1
    r = r['2018':].dropna()
    return float((r > 0).mean())

# ---- estrategia
# Mapa: qué activo comprar en soporte (A) y cuál en resistencia (B)
PARES = {
    'ETH_BTC': ('ETH', 'BTC', 'soporte de ETH/BTC -> ETH'),
    'dominancia_btc': ('BTC', 'ALTS', 'soporte de BTC.D -> BTC (espera que suba)'),
    'dominancia_usdt': ('LIQ', 'BTC', 'soporte de USDT.D (euforia) -> liquidez; resistencia (miedo) -> BTC'),
    'others_fuera_top10': ('ALTS', 'BTC', 'soporte de OTHERS -> alts; resistencia -> BTC'),
}

def rentab():
    c = lambda a: velas(a, '1d')['cierre']
    r = {'BTC': c('BTC').pct_change(), 'ETH': c('ETH').pct_change()}
    r['ALTS'] = pd.concat([c(a).pct_change() for a in ['ETH', 'BNB', 'XRP', 'ADA', 'LINK', 'SOL']], axis=1).mean(axis=1)
    r['LIQ'] = pd.Series(0.0, r['BTC'].index)
    return r

def estrategia(w, evs, tol, A, B, R, cortar_al_romper=True):
    idx = R['BTC'].dropna().index; idx = idx[idx >= '2018-01-01']
    peso = pd.Series(np.nan, idx); cur, nivel, lado = 0.5, None, None
    porfecha = {}
    for d, l, L in evs: porfecha.setdefault(d, []).append((l, L))
    for d in w.index:
        cierre_sem = d + pd.Timedelta(days=6)
        if d in porfecha:
            l, L = porfecha[d][-1]; lado, nivel = l, L
            cur = 1.0 if l == 'soporte' else 0.0
        elif nivel is not None and cortar_al_romper:
            s = 1 if lado == 'soporte' else -1
            if (w.cierre.loc[d] - nivel) * s < -2 * tol * nivel: cur, nivel = 0.5, None
        if cierre_sem in peso.index: peso.loc[cierre_sem] = cur
    peso = peso.ffill().fillna(0.5)
    rA, rB = R[A].reindex(idx).fillna(0), R[B].reindex(idx).fillna(0)
    eq, turn = simular(rA, rB, peso)
    base, _ = simular(rA, rB, pd.Series(0.5, idx))
    return eq, base, turn

if __name__ == '__main__':
    R = rentab(); filas, estr = [], []
    for activo, fijos in DIBUJADOS.items():
        w = velas(activo, '1w'); w = w[w.index >= '2016-01-01']
        base_sube = azar(w)
        configs = [('objetivos', t, m) for t in (0.015, 0.025) for m in (2, 3)] + [('dibujados', 0.015, 0)]
        A, B, txt = PARES[activo]
        for tipo, tol, mt in configs:
            evs = [e for e in eventos(w, tipo, tol, mt, fijos) if e[0] >= pd.Timestamp('2018-01-01')]
            res = [dict(lado=l, **r) for d, l, L in evs if (r := resultado_evento(w, d, l, L, tol))]
            df = pd.DataFrame(res)
            for lado in ('soporte', 'resistencia'):
                x = df[df.lado == lado] if len(df) else df
                ref = base_sube if lado == 'soporte' else 1 - base_sube
                filas.append(dict(activo=activo, niveles=tipo, tol=tol, min_toques=mt, lado=lado, n=len(x),
                                  rebota=float(x.rebote.mean()) if len(x) else np.nan, azar=ref,
                                  rompe=float(x.roto.mean()) if len(x) else np.nan,
                                  mov_mediano=float(x.mov.median()) if len(x) else np.nan))
            eq, base, turn = estrategia(w, evs, tol, A, B, R)
            m, mb = metricas(eq), metricas(base); t, tb = tramos(eq), tramos(base)
            estr.append(dict(activo=activo, regla=txt, niveles=tipo, tol=tol, min_toques=mt, eventos=len(evs),
                             total=m['total'], mdd=m['mdd'], ratio=m['ratio'],
                             base_total=mb['total'], base_mdd=mb['mdd'], base_ratio=mb['ratio'],
                             gana_2018_21=t.get('2018-21', 0) > tb.get('2018-21', 0),
                             gana_2022_26=t.get('2022-26', 0) > tb.get('2022-26', 0)))
    ev, es = pd.DataFrame(filas), pd.DataFrame(estr)
    ev.to_csv(os.path.join(AQUI, 'sr_eventos.csv'), index=False); es.to_csv(os.path.join(AQUI, 'sr_estrategia.csv'), index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 20)
    print(ev.round(2).to_string(index=False)); print(); print(es.round(2).to_string(index=False))
