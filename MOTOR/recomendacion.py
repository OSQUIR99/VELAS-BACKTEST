# -*- coding: utf-8 -*-
"""Combinaciones finales del motor de cartera, apalancamiento que aguanta cada una, horario (punto 7 corregido) y
robustez (remuestreo por meses). Uso: python3 recomendacion.py <carpeta_listas> <carpeta_salida>"""
import os, sys, json
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from motor import cargar, Motor, metricas, caida_max, HOY, ULT5
from precios import Correlaciones
import analisis as A
import extra as X

CORTE = pd.Timestamp('2022-01-01')
GRID = [0.3, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]


def preparar(carpeta):
    O, D = cargar(carpeta)
    if 'cripto_realista' in set(O.lista):
        O['lista'] = O['lista'].replace({'cripto': 'cripto_24h', 'cripto_realista': 'cripto'})
    O['en_cartera'] = A.marcar_variantes(O)
    blo = dict(zip(O.activo.astype(str), O.bloque.astype(str)))
    C = Correlaciones(O.activo.astype(str).unique(), defecto=lambda a, b: 0.6 if blo.get(a) == blo.get(b) else 0.1)
    M = Motor(O, D, C)
    return O, D, M


def pesos_familia(M, O, desde, W):
    base = M.simular(A.SIN_TOPES, mascara=W)
    tabla = X.pesos_lista_wf(M, O, desde, W, base.s)
    yrs = O.t_entrada.dt.year.values
    tm = np.array([tabla.get(int(y), {}).get(l, 1.0) for y, l in zip(yrs, O.lista.values)])
    return tm, tabla


def evaluar(M, O, desde, W, cfg, nombre, apal=True):
    rr = M.simular(cfg, mascara=W)
    eq = rr.eq
    mi = metricas(M, rr.s, desde, CORTE, mascara=W, eq=eq)
    mo = metricas(M, rr.s, CORTE, mascara=W, eq=eq)
    m5 = metricas(M, rr.s, ULT5, mascara=W, eq=eq)
    mt = metricas(M, rr.s, desde, mascara=W, eq=eq)
    rs = A.resumen(M, rr.s, desde, W)
    f = dict(combinacion=nombre, R_ano=A.r(mt['R_ano']), caida=A.r(mt['caida']), Rano_caida=A.r(mt['Rano_caida']),
             R_total=A.r(mt['R_total']), R_op=A.r(mt['R_op'], 3), acierto=A.r(mt['acierto'], 3), n=mt['n'],
             Rano_caida_IS=A.r(mi['Rano_caida']), Rano_caida_OOS=A.r(mo['Rano_caida']), R_ano_OOS=A.r(mo['R_ano']),
             caida_OOS=A.r(mo['caida']), Rano_caida_5a=A.r(m5['Rano_caida']), R_ano_5a=A.r(m5['R_ano']),
             caida_5a=A.r(m5['caida']), **{f'ep_{k}': v for k, v in rs['epocas'].items()},
             perdidas_topes=int(((rr.motivo == 'tope 20 R') | (rr.motivo == 'tope bloque'))[W].sum()))
    if apal:
        cs, ra = [], []
        for g in GRID:
            c = dict(cfg)
            c['mult'] = g * cfg.get('mult', 1.0)
            r2 = M.simular(c, mascara=W)
            m2 = metricas(M, r2.s, desde, mascara=W)
            cs.append(m2['caida'])
            ra.append(m2['R_ano'])
        # multiplicador con la peor caída ≤ objetivo (el mayor de la rejilla que cumple, interpolando)
        for obj in (20, 30):
            mejor_m, mejor_r = 0.0, 0.0
            for i, g in enumerate(GRID):
                if cs[i] <= obj:
                    mejor_m, mejor_r = g, ra[i]
                elif i > 0 and cs[i - 1] <= obj:
                    fr = (obj - cs[i - 1]) / (cs[i] - cs[i - 1])
                    mm, rr_ = GRID[i - 1] + fr * (g - GRID[i - 1]), ra[i - 1] + fr * (ra[i] - ra[i - 1])
                    if mm > mejor_m:
                        mejor_m, mejor_r = mm, rr_
                    break
                else:
                    break
            f[f'mult_{obj}R'] = A.r(mejor_m)
            f[f'R_ano_a_{obj}R'] = A.r(mejor_r)
        f['rejilla'] = ';'.join(f'{g}:{A.r(c)}/{A.r(r)}' for g, c, r in zip(GRID, cs, ra))
    return f, rr


def bootstrap(M, ra, rb, desde, n=500, semilla=7):
    """Remuestreo por meses (los mismos meses para las dos carteras): % de veces que B supera a A en R/año ÷ caída."""
    ea = ra.eq[(ra.eq.index >= desde) & (ra.eq.index <= HOY)].diff().fillna(0)
    eb = rb.eq[(rb.eq.index >= desde) & (rb.eq.index <= HOY)].diff().fillna(0)
    meses = ea.index.to_period('M')
    grupos = {m: (ea[meses == m].values, eb[meses == m].values) for m in meses.unique()}
    claves = list(grupos)
    rng = np.random.default_rng(semilla)
    gana = 0
    difs = []
    for _ in range(n):
        sel = rng.choice(len(claves), len(claves), replace=True)
        xa = np.concatenate([grupos[claves[i]][0] for i in sel])
        xb = np.concatenate([grupos[claves[i]][1] for i in sel])
        ca, cb = np.cumsum(xa), np.cumsum(xb)
        da, db = caida_max(pd.Series(ca)), caida_max(pd.Series(cb))
        qa = ca[-1] / da if da > 0 else np.nan
        qb = cb[-1] / db if db > 0 else np.nan
        gana += qb > qa
        difs.append(qb - qa)
    return dict(pct_gana=A.r(gana / n, 3), dif_mediana=A.r(float(np.nanmedian(difs))),
                dif_p5=A.r(float(np.nanpercentile(difs, 5))))


def main(carpeta, sal):
    O, D, M = preparar(carpeta)
    BASE = O.en_cartera.values
    desde = A.inicio_ventana(O)
    W = BASE & (O.t_entrada >= desde).values
    tm_pf, tabla = pesos_familia(M, O, desde, W)
    acc = (O.lista.values == 'acciones_v2')
    FL = dict(freno=(4, 0.5), freno_modo='latente')
    DC = dict(prioridad='descorr')
    combos = {
        'R0 · todas, sin topes ni freno (referencia)': (A.SIN_TOPES, W),
        'V · VIGENTE (20 R + bloque 10 R + freno de lo cerrado 4 R + 5 R/op)': ({}, W),
        'V + freno con la cartera valorada (FL)': (FL, W),
        'V + prioridad por descorrelación (DC)': (DC, W),
        'V + peso por familia de 3 años (PF)': (dict(tam_mult=tm_pf), W),
        'V + SHY fuera del tope de 20 R': (dict(shy_fuera_tope=True), W),
        'FL + DC': ({**FL, **DC}, W),
        'FL + DC + PF': ({**FL, **DC, 'tam_mult': tm_pf}, W),
        'FL + DC + acciones_v2 a × 0,5': ({**FL, **DC, 'tam_mult': np.where(acc, 0.5, 1.0)}, W),
        'FL + DC sin acciones_v2': ({**FL, **DC}, W & ~acc),
        'V sin acciones_v2': ({}, W & ~acc),
    }
    filas, res = [], {}
    for n, (c, m) in combos.items():
        f, rr = evaluar(M, O, desde, m, c, n, apal=not n.startswith('R0'))
        filas.append(f)
        res[n] = rr
        print(n, f['Rano_caida'], f['Rano_caida_IS'], f['Rano_caida_OOS'], f['Rano_caida_5a'], f.get('mult_20R'), flush=True)
    # variante cripto_propuesta (sin las velas que no ve nadie) encima de FL + DC + PF
    if 'cripto_propuesta' in set(O.lista):
        sr = O['sin_revision'].fillna(False).astype(bool).values if 'sin_revision' in O.columns else np.zeros(len(O), bool)
        Wp = (W & (O.lista.values != 'cripto')) | ((O.lista.values == 'cripto_propuesta') & ~sr & (O.t_entrada >= desde).values)
        O2 = O.copy()
        tm2, _ = pesos_familia(M, O2.assign(lista=O2.lista.replace({'cripto_propuesta': 'cripto'})), desde, Wp)
        for n, c in (('V con cripto_propuesta (horario actual)', {}),
                     ('FL + DC + PF con cripto_propuesta (horario actual)', {**FL, **DC, 'tam_mult': tm2})):
            f, rr = evaluar(M, O, desde, Wp, c, n)
            filas.append(f)
            res[n] = rr
            print(n, f['Rano_caida'], f['Rano_caida_OOS'], flush=True)
    T = pd.DataFrame(filas)
    T.to_csv(f'{sal}/p9_combinaciones_finales.csv', index=False)
    vig = res['V · VIGENTE (20 R + bloque 10 R + freno de lo cerrado 4 R + 5 R/op)']
    boot = {}
    for n in ('V + freno con la cartera valorada (FL)', 'V + prioridad por descorrelación (DC)', 'FL + DC',
              'FL + DC + PF', 'V + peso por familia de 3 años (PF)', 'FL + DC sin acciones_v2'):
        boot[n] = bootstrap(M, vig, res[n], desde)
        print('bootstrap', n, boot[n], flush=True)
    json.dump(boot, open(f'{sal}/p9_bootstrap.json', 'w'), ensure_ascii=False, indent=1)
    # punto 7 corregido
    T7, S7, ctx7, det7 = A.punto7(M, O, desde, W, sal)
    print(T7[['horario', 'R_ano', 'caida', 'Rano_caida', 'Rano_caida_5a', 'n']].to_string(), flush=True)
    json.dump(dict(det=det7, ctx=ctx7), open(f'{sal}/p7_detalle.json', 'w'), ensure_ascii=False, indent=1, default=str)
    return T, boot, T7


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
