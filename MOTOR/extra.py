# -*- coding: utf-8 -*-
"""Punto 8 (segunda tanda): más ideas de cartera, con la misma regla de juego: se elige con datos hasta 2021
(dentro de muestra) y se comprueba en 2022-26 (fuera de muestra), y además por épocas y últimos 5 años.
Uso: python3 extra.py <carpeta_listas> <carpeta_salida>"""
import os, sys, json
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from motor import cargar, Motor, metricas, caida_max, HOY, ULT5
from precios import Correlaciones
import analisis as A


def pesos_lista_wf(M, O, desde, W, base_s, lim=(0.5, 2.0)):
    """Peso de cada familia ∝ su R/año ÷ caída de los 3 años anteriores (con su propia curva, sin topes),
    recortado a 0,5-2 y normalizado a media 1 por operación. Se rehace cada 1 de enero."""
    tabla = {}
    for Y in range(desde.year, HOY.year + 1):
        ini = pd.Timestamp(f'{Y}-01-01')
        a = ini - pd.DateOffset(years=3)
        rat = {}
        for l in set(O.lista[W]):
            m = W & (O.lista.values == l)
            e = M.curva(base_s, m)
            e = e[(e.index >= a) & (e.index < ini)]
            if len(e) < 200:
                continue
            dd = caida_max(e)
            ra = (e.iloc[-1] - e.iloc[0]) / 3
            rat[l] = ra / max(dd, 1.0)
        if not rat:
            tabla[Y] = {}
            continue
        med = np.median(list(rat.values())) or 1.0
        pes = {l: float(np.clip(v / med if med > 0 else 1.0, *lim)) for l, v in rat.items()}
        cnt = O[W & (O.t_entrada >= ini).values & (O.t_entrada < pd.Timestamp(f'{Y + 1}-01-01')).values].lista.value_counts()
        tot = sum(pes.get(l, 1.0) * c for l, c in cnt.items())
        f = cnt.sum() / tot if tot > 0 else 1.0
        tabla[Y] = {l: pes.get(l, 1.0) * f for l in cnt.index}
    dia0 = pd.Timestamp(M.dia0)
    return tabla


def main(carpeta, sal):
    O, D = cargar(carpeta)
    if 'cripto_realista' in set(O.lista):
        O['lista'] = O['lista'].replace({'cripto': 'cripto_24h', 'cripto_realista': 'cripto'})
    O['en_cartera'] = A.marcar_variantes(O)
    BASE = O['en_cartera'].values
    blo = dict(zip(O.activo.astype(str), O.bloque.astype(str)))
    C = Correlaciones(O.activo.astype(str).unique(), defecto=lambda a, b: 0.6 if blo.get(a) == blo.get(b) else 0.1)
    M = Motor(O, D, C)
    desde = A.inicio_ventana(O)
    W = BASE & (O.t_entrada >= desde).values
    corte = pd.Timestamp('2022-01-01')
    var = {'vigente': {}}
    for tb in (7, 15):
        var[f'tope por bloque {tb} R'] = dict(tope_bloque=tb)
    var['sin tope por bloque'] = dict(tope_bloque=None)
    for tt in (15, 25):
        var[f'tope total {tt} R'] = dict(tope_total=tt)
    for u in (4, 6, 8):
        var[f'freno con la cartera valorada (cerrado + abierto) {u} R → × 0,5'] = dict(freno=(u, 0.5), freno_modo='latente')
    base = M.simular(A.SIN_TOPES, mascara=W)
    tabla = pesos_lista_wf(M, O, desde, W, base.s)
    dia0 = pd.Timestamp(M.dia0)
    lista_k = O.lista.values
    yrs = O.t_entrada.dt.year.values
    tm = np.array([tabla.get(int(y), {}).get(l, 1.0) for y, l in zip(yrs, lista_k)])
    var['peso por familia ∝ su R/año ÷ caída de 3 años (0,5-2, año a año)'] = dict(tam_mult=tm)
    pd.DataFrame(tabla).T.round(3).to_csv(f'{sal}/p8b_pesos_familia.csv')
    T = A.comparar_is_oos(M, O, desde, W, var, corte, sal, 'p8b_ideas')
    print(T.to_string())
    # placebo del peso por familia: pesos barajados entre familias cada año (20 veces)
    rng = np.random.default_rng(8)
    plac = []
    for sd in range(20):
        tb2 = {}
        for Y, d in tabla.items():
            ks = list(d)
            vs = rng.permutation([d[k] for k in ks])
            tb2[Y] = dict(zip(ks, vs))
        tm2 = np.array([tb2.get(int(y), {}).get(l, 1.0) for y, l in zip(yrs, lista_k)])
        rr = M.simular(dict(tam_mult=tm2), mascara=W)
        plac.append(metricas(M, rr.s, corte, mascara=W)['Rano_caida'])
    real = T.set_index('variante').loc['peso por familia ∝ su R/año ÷ caída de 3 años (0,5-2, año a año)', 'Rano_caida_OOS']
    res = dict(placebo_pesos_familia_OOS_mediana=float(np.median(plac)), real=float(real),
               pct_placebo_ge_real=float(np.mean(np.array(plac) >= real)))
    json.dump(res, open(f'{sal}/p8b_placebo.json', 'w'), indent=1)
    print(res)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
