# -*- coding: utf-8 -*-
"""Análisis del motor de cartera (puntos 1 a 6 y 8 del encargo; el 7, horarios, en horario.py).

Uso: python3 analisis.py <carpeta_listas> <carpeta_salida> [rapido]
Escribe CSV en <salida>/ y devuelve un diccionario con las cifras clave (resultados.json).
"""
import os, sys, json, time, itertools
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from motor import (cargar, Motor, metricas, caida_max, HOY, ULT5, EPOCAS, HALVINGS, fase_ciclo_cripto,
                   TOPE_TOTAL, TOPE_BLOQUE)
from precios import Correlaciones, cierre_diario
import horario as HOR
import copy

SIN_TOPES = dict(tope_total=None, tope_bloque=None, freno=None, max_op=None)
VIGENTE = dict()
REDOND = 3


def r(x, n=2):
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else round(float(x), n)
    return x


def fila(m, **extra):
    d = dict(extra)
    for k in ('n', 'ops_mes_media', 'ops_mes_mediana', 'meses_sin', 'R_total', 'R_ano', 'caida', 'R_op', 'acierto',
              'R_caida', 'Rano_caida'):
        d[k] = r(m[k], 3 if k in ('R_op', 'acierto') else 2)
    return d


def inicio_ventana(O):
    c = O[O.lista == 'cripto']
    if len(c):
        t = (c.t_entrada.min().normalize() + pd.offsets.MonthBegin(1))
        return max(pd.Timestamp('2018-01-01'), t)
    return pd.Timestamp('2018-01-01')


# ------------------------------------------------------------------------------------- fases
def fases(O):
    """Fase de cada activo con la media de 200 (precio encima/debajo y media subiendo/bajando en 20 sesiones),
    medida el día anterior a la entrada; y la fase de hoy."""
    fase_ent = np.array([''] * len(O), dtype=object)
    hoy = {}
    for a, g in O.groupby('activo'):
        s = cierre_diario(str(a))
        if s is None or len(s) < 260:
            continue
        s = s.sort_index()
        sma = s.rolling(200).mean()
        sube = sma > sma.shift(20)
        enc = s > sma
        lab = np.where(enc & sube, 'alcista firme', np.where(~enc & sube, 'alcista que se debilita',
                       np.where(~enc & ~sube, 'bajista firme', 'bajista que se recupera')))
        lab = pd.Series(lab, index=s.index)
        lab[sma.isna()] = ''
        hoy[str(a)] = lab.iloc[-1]
        pos = np.searchsorted(s.index.values, g.t_entrada.dt.normalize().values, side='left') - 1
        ok = pos >= 0
        v = np.array([''] * len(g), dtype=object)
        v[ok] = lab.values[pos[ok]]
        fase_ent[g.index.values] = v
    return fase_ent, hoy


# ------------------------------------------------------------------------------------- tablas
def por_grupos(M, s, O, col, desde=None, hasta=None, min_n=1, base=None):
    filas = []
    Og = O if base is None else O[base]
    for v, g in Og.groupby(col):
        m = np.zeros(len(O), bool)
        m[g.index.values] = True
        if (s[m] > 0).sum() < min_n:
            continue
        d0 = desde if desde is not None else g.t_entrada.min().normalize()
        filas.append(fila(metricas(M, s, d0, hasta, mascara=m), **{col: v, 'desde': str(pd.Timestamp(d0).date())}))
    return pd.DataFrame(filas)


def epocas(M, s, desde, mascara=None):
    filas = []
    eq = M.curva(s, mascara)
    tramos = [('ventana', desde, None), ('ultimos 5 años', ULT5, None)] + \
             [(n, max(pd.Timestamp(a), desde), pd.Timestamp(b)) for n, a, b in EPOCAS if pd.Timestamp(b) > desde]
    for n, a, b in tramos:
        filas.append(fila(metricas(M, s, a, b, mascara=mascara, eq=eq), tramo=n))
    return pd.DataFrame(filas)


def resumen(M, s, desde, mascara=None):
    t = epocas(M, s, desde, mascara).set_index('tramo')
    return dict(R_ano=t.loc['ventana', 'R_ano'], caida=t.loc['ventana', 'caida'],
                Rano_caida=t.loc['ventana', 'Rano_caida'], R_total=t.loc['ventana', 'R_total'],
                Rano_caida_5a=t.loc['ultimos 5 años', 'Rano_caida'], caida_5a=t.loc['ultimos 5 años', 'caida'],
                R_ano_5a=t.loc['ultimos 5 años', 'R_ano'],
                epocas={k: t.loc[k, 'Rano_caida'] for k in t.index if k not in ('ventana', 'ultimos 5 años')},
                n=t.loc['ventana', 'n'])


def perdidas(res, O, W):
    rech = (res.motivo != '') & W
    d = {}
    for mot in ('tope 20 R', 'tope bloque'):
        m = rech & (res.motivo == mot)
        d[mot] = dict(n=int(m.sum()), R_lista=r(float(O.r_final.values[m].sum())))
    por = pd.DataFrame({'lista': O.lista.values[rech], 'motivo': res.motivo[rech], 'r': O.r_final.values[rech]})
    pl = por.groupby(['lista', 'motivo']).r.agg(['size', 'sum']).round(2).reset_index() if len(por) else pd.DataFrame()
    return d, pl


# ------------------------------------------------------------------------------------- 1
def punto1(M, O, desde, W, BASE, fase_ent, fase_hoy, sal):
    todas = M.simular(SIN_TOPES)
    s = todas.s
    out = {}
    tot_v = fila(metricas(M, s, desde, mascara=W), tramo='cartera (ventana)')
    tot_h = fila(metricas(M, s, O.t_entrada.min().normalize(), mascara=BASE), tramo='historia completa')
    ep = epocas(M, s, desde, W)
    fam = por_grupos(M, s, O, 'lista')
    fam_v = por_grupos(M, s, O, 'lista', desde=desde, base=W)
    O2 = O.copy()
    O2['lista_senal'] = O2.lista + ' · ' + O2.senal
    sen = por_grupos(M, s, O2, 'lista_senal', base=BASE)
    O2['lista_activo'] = O2.lista + ' · ' + O2.activo.astype(str)
    act = por_grupos(M, s, O2, 'lista_activo', min_n=5, base=BASE)
    # fase actual: operaciones en la misma fase que su activo hoy
    misma = np.array([fase_ent[i] != '' and fase_ent[i] == fase_hoy.get(str(a), '#') for i, a in enumerate(O.activo)])
    ciclo = np.array([fase_ciclo_cripto(t) for t in O.t_entrada])
    fase_rows = [fila(metricas(M, s, desde, mascara=W & misma), tramo='misma fase que hoy (su activo, media de 200)'),
                 fila(metricas(M, s, desde, mascara=W & ~misma), tramo='otra fase'),
                 fila(metricas(M, s, desde, mascara=W & ciclo), tramo='24-36 meses tras el halving (cripto, todas las familias)')]
    fase_fam = []
    for l, g in O[W & misma].groupby('lista'):
        m = np.zeros(len(O), bool)
        m[g.index.values] = True
        fase_fam.append(fila(metricas(M, s, desde, mascara=m), lista=l, tramo='misma fase que hoy'))
    for l, g in O[W & ULT5_mask(O)].groupby('lista'):
        m = np.zeros(len(O), bool)
        m[g.index.values] = True
        fase_fam.append(fila(metricas(M, s, ULT5, mascara=m), lista=l, tramo='últimos 5 años'))
    pd.DataFrame([tot_v, tot_h]).to_csv(f'{sal}/p1_total.csv', index=False)
    ep.to_csv(f'{sal}/p1_epocas.csv', index=False)
    fam.to_csv(f'{sal}/p1_por_familia_historia.csv', index=False)
    fam_v.to_csv(f'{sal}/p1_por_familia_ventana.csv', index=False)
    sen.to_csv(f'{sal}/p1_por_senal.csv', index=False)
    act.to_csv(f'{sal}/p1_por_activo.csv', index=False)
    pd.DataFrame(fase_rows + fase_fam).to_csv(f'{sal}/p1_fase_actual.csv', index=False)
    out['total_ventana'] = tot_v
    out['total_historia'] = tot_h
    out['epocas'] = ep.to_dict('records')
    out['por_familia_ventana'] = fam_v.to_dict('records')
    out['fase'] = fase_rows
    out['fase_hoy'] = fase_hoy
    return out, todas


def ULT5_mask(O):
    return (O.t_entrada >= ULT5).values


# ------------------------------------------------------------------------------------- 2 y 3
def punto2(M, O, desde, W, sal):
    cfgs = {
        'A · todas, sin topes ni freno': SIN_TOPES,
        'B · sin topes, con freno de racha': dict(tope_total=None, tope_bloque=None),
        'C · solo 20 R abiertos (+ freno, 5 R/op)': dict(tope_bloque=None),
        'D · solo bloque 10 R (+ freno, 5 R/op)': dict(tope_total=None),
        'E · VIGENTE: 20 R + bloque 10 R + freno + 5 R/op': VIGENTE,
        'F · vigente sin freno': dict(freno=None),
        'G · vigente, recortando el tamaño para que quepa': dict(modo_tope='recortar'),
    }
    filas, res, pls = [], {}, []
    for n, c in cfgs.items():
        rr = M.simular(c, mascara=W)
        res[n] = rr
        rs = resumen(M, rr.s, desde, W)
        d, pl = perdidas(rr, O, W)
        if len(pl):
            pl.insert(0, 'config', n)
            pls.append(pl)
        filas.append(dict(config=n, R_ano=rs['R_ano'], caida=rs['caida'], Rano_caida=rs['Rano_caida'],
                          R_total=rs['R_total'], Rano_caida_5a=rs['Rano_caida_5a'], caida_5a=rs['caida_5a'],
                          **{f'ep_{k}': v for k, v in rs['epocas'].items()}, n=rs['n'],
                          perdidas_20R=d['tope 20 R']['n'], R_perdido_20R=d['tope 20 R']['R_lista'],
                          perdidas_bloque=d['tope bloque']['n'], R_perdido_bloque=d['tope bloque']['R_lista']))
    T = pd.DataFrame(filas)
    T.to_csv(f'{sal}/p2_topes.csv', index=False)
    if pls:
        pd.concat(pls).to_csv(f'{sal}/p2_perdidas_por_familia.csv', index=False)
    # riesgo abierto máximo con y sin topes (diario, aproximado)
    return T, res


def riesgo_abierto(M, s, desde):
    dias = pd.date_range(desde, HOY, freq='D')
    di = ((dias.values - M.dia0) / np.timedelta64(1, 'D')).astype(int)
    tot = np.zeros(len(di))
    sel = np.flatnonzero(s > 0)
    for k in sel:
        a, b = M.ent_dia[k], M.sal_dia[k]
        i0 = np.searchsorted(di, a)
        i1 = np.searchsorted(di, b)
        for i in range(i0, i1):
            tot[i] += s[k] * M.riesgo(k, di[i] + 1)
    return pd.Series(tot, index=dias)


def punto3(M, O, desde, W, sal):
    filas = []
    res = {}
    for agr in ('hora', 'dia'):
        for pr in ('llegada', 'calidad', 'descorr', 'inversa'):
            n = f'prioridad {pr} · simultáneas por {agr}'
            rr = M.simular(dict(prioridad=pr, agrupar=agr), mascara=W)
            res[n] = rr
            rs = resumen(M, rr.s, desde, W)
            d, _ = perdidas(rr, O, W)
            filas.append(dict(config=n, R_ano=rs['R_ano'], caida=rs['caida'], Rano_caida=rs['Rano_caida'],
                              Rano_caida_5a=rs['Rano_caida_5a'], **{f'ep_{k}': v for k, v in rs['epocas'].items()},
                              perdidas=d['tope 20 R']['n'] + d['tope bloque']['n']))
    for aj in ('raiz', 'lineal'):
        for tope in (True, False):
            n = f'tamaño ajustado por correlación ({aj})' + ('' if tope else ' · sin topes')
            c = dict(ajuste_corr=aj)
            if not tope:
                c.update(tope_total=None, tope_bloque=None)
            rr = M.simular(c, mascara=W)
            res[n] = rr
            rs = resumen(M, rr.s, desde, W)
            d, _ = perdidas(rr, O, W)
            filas.append(dict(config=n, R_ano=rs['R_ano'], caida=rs['caida'], Rano_caida=rs['Rano_caida'],
                              Rano_caida_5a=rs['Rano_caida_5a'], **{f'ep_{k}': v for k, v in rs['epocas'].items()},
                              perdidas=d['tope 20 R']['n'] + d['tope bloque']['n']))
    # grupos con conflicto: varias entradas a la misma hora y alguna rechazada (con llegada)
    base = res['prioridad llegada · simultáneas por hora']
    T = pd.DataFrame(filas)
    T.to_csv(f'{sal}/p3_prioridad.csv', index=False)
    return T, res


# ------------------------------------------------------------------------------------- 4 selección (walk-forward)
def variantes_de(listas):
    """Una lista es variante de otra si su nombre es «<familia>_<algo>» y <familia> también existe."""
    v = {}
    for l in listas:
        for f in listas:
            if l != f and l.startswith(f + '_'):
                v[l] = f
    return v


def marcar_variantes(O):
    v = variantes_de(set(O.lista))
    return (~O.lista.isin(list(v)) & O.operable).values


def en_cartera(O):
    return O['en_cartera'] if 'en_cartera' in O.columns else ((O.lista != 'cripto_24h') & O.operable)


def punto_variantes(M, O, desde, W, sal):
    """La cartera vigente cambiando una familia por su variante (p. ej. cripto_propuesta en lugar de cripto)."""
    v = variantes_de(set(O.lista))
    t_ok = (O.t_entrada >= desde).values
    filas = []
    base = M.simular(VIGENTE, mascara=W)
    rs = resumen(M, base.s, desde, W)
    filas.append(dict(cartera='vigente', R_ano=rs['R_ano'], caida=rs['caida'], Rano_caida=rs['Rano_caida'],
                      Rano_caida_5a=rs['Rano_caida_5a'], **{f'ep_{k}': x for k, x in rs['epocas'].items()}))
    for var, fam in sorted(v.items()):
        cand = [(var, (O.lista.values == var) & O.operable.values & t_ok)]
        if 'sin_revision' in O.columns and var != 'cripto_24h':
            sr = O['sin_revision'].fillna(False).astype(bool).values
            cand.append((var + ' sin las velas que no ve nadie', (O.lista.values == var) & ~sr & t_ok))
        for nombre, mv in cand:
            m = (W & (O.lista.values != fam)) | mv
            rr = M.simular(VIGENTE, mascara=m)
            rs = resumen(M, rr.s, desde, m)
            filas.append(dict(cartera=f'{fam} → {nombre}', R_ano=rs['R_ano'], caida=rs['caida'], Rano_caida=rs['Rano_caida'],
                              Rano_caida_5a=rs['Rano_caida_5a'], **{f'ep_{k}': x for k, x in rs['epocas'].items()}))
    T = pd.DataFrame(filas)
    T.to_csv(f'{sal}/p2b_variantes.csv', index=False)
    return T


def stats_is(O, hasta, por):
    """R por operación y número, con las operaciones CERRADAS antes de `hasta` (sin mirar el futuro)."""
    g = O[(O.t_salida < hasta) & en_cartera(O)].groupby(por).r_final.agg(['mean', 'size'])
    return g


def regla_mascara(O, nombre, hasta, M=None):
    n = len(O)
    if nombre == 'todo':
        return np.ones(n, bool)
    if nombre.startswith('calidad_top'):
        p = int(nombre[len('calidad_top'):]) / 100
        m = np.ones(n, bool)
        pasado = O[(O.t_salida < hasta) & en_cartera(O)]
        for l, g in pasado.groupby('lista'):
            if g.calidad.nunique() <= 1:
                continue
            umbral = g.calidad.quantile(1 - p)
            m &= ~((O.lista.values == l) & (O.calidad.values < umbral))
        return m
    if nombre in ('excluir_listas_negativas', 'excluir_senales_negativas', 'excluir_activos_negativos'):
        por = {'excluir_listas_negativas': ['lista'], 'excluir_senales_negativas': ['lista', 'senal'],
               'excluir_activos_negativos': ['lista', 'activo']}[nombre]
        st = stats_is(O, hasta, por)
        malos = set(st[(st['size'] >= 20) & (st['mean'] <= 0)].index)
        claves = list(zip(*[O[c].astype(str).values for c in por])) if len(por) > 1 else list(O[por[0]].astype(str).values)
        malos = {tuple(map(str, x)) if isinstance(x, tuple) else str(x) for x in malos}
        return np.array([c not in malos for c in claves])
    if nombre == 'excluir_peor_lista':
        pasado = O[(O.t_salida < hasta) & en_cartera(O)]
        peor, val = None, np.inf
        for l, g in pasado.groupby('lista'):
            if len(g) < 30:
                continue
            e = g.sort_values('t_salida').r_final.cumsum()
            dd = caida_max(e)
            anos = max((g.t_salida.max() - g.t_entrada.min()).days / 365.25, 0.5)
            v = (e.iloc[-1] / anos) / dd if dd > 0 else np.inf
            if v < val:
                peor, val = l, v
        return O.lista.values != peor
    if nombre.startswith('sin_'):
        return O.lista.values != nombre[4:]
    raise ValueError(nombre)


REGLAS_SEL = ['todo', 'calidad_top75', 'calidad_top50', 'excluir_listas_negativas', 'excluir_senales_negativas',
              'excluir_activos_negativos', 'excluir_peor_lista']


def walk_forward(M, O, desde, W, reglas, mascara_de, sal, nombre, cfg_base=None, primer_ano=None):
    """Cada año Y: con datos hasta el 1-ene de Y se elige la regla con mejor R/año ÷ caída de la cartera (vigente)
    desde el inicio de la ventana hasta Y, y se aplica al año Y. Devuelve la máscara compuesta y la tabla."""
    cfg_base = cfg_base or {}
    anos = list(range(primer_ano or desde.year + 2, HOY.year + 1))
    ent = O.t_entrada.values
    comp = W.copy()
    tam_comp = np.ones(len(O))
    elegidas = []
    for Y in anos:
        ini = pd.Timestamp(f'{Y}-01-01')
        fin = pd.Timestamp(f'{Y + 1}-01-01')
        mejor, val = None, -np.inf
        detalle = {}
        for rg in reglas:
            msk, tm = mascara_de(rg, ini)
            m_is = W & (ent < np.datetime64(ini)) & msk
            c = dict(cfg_base)
            if tm is not None:
                c['tam_mult'] = tm
            rr = M.simular(c, mascara=m_is)
            mt = metricas(M, rr.s, desde, ini, mascara=m_is)
            v = mt['Rano_caida'] if np.isfinite(mt['Rano_caida']) else -np.inf
            detalle[rg] = r(v)
            if v > val + 1e-9:
                mejor, val = rg, v
        msk, tm = mascara_de(mejor, ini)
        en_ano = (ent >= np.datetime64(ini)) & (ent < np.datetime64(fin))
        comp[en_ano] = W[en_ano] & msk[en_ano]
        if tm is not None:
            tam_comp[en_ano] = tm[en_ano]
        elegidas.append(dict(ano=Y, elegida=mejor, **{f'IS_{k}': v for k, v in detalle.items()}))
    E = pd.DataFrame(elegidas)
    E.to_csv(f'{sal}/{nombre}_elecciones.csv', index=False)
    return comp, tam_comp, E, pd.Timestamp(f'{anos[0]}-01-01')


def punto4(M, O, desde, W, sal):
    def mde(rg, ini):
        return regla_mascara(O, rg, ini), None
    comp, _, E, oos0 = walk_forward(M, O, desde, W, REGLAS_SEL, mde, sal, 'p4_seleccion')
    base = M.simular(VIGENTE, mascara=W)
    wf = M.simular(VIGENTE, mascara=comp)
    filas = []
    for n, rr, msk in (('vigente (todo)', base, W), ('selección walk-forward', wf, comp)):
        mo = metricas(M, rr.s, oos0, mascara=msk)
        m5 = metricas(M, rr.s, ULT5, mascara=msk)
        filas.append(dict(config=n, OOS_desde=str(oos0.date()), R_ano_OOS=r(mo['R_ano']), caida_OOS=r(mo['caida']),
                          Rano_caida_OOS=r(mo['Rano_caida']), Rano_caida_5a=r(m5['Rano_caida']), n_OOS=mo['n']))
    # cada regla aplicada sola año a año (sin meta-elección), solo para el catálogo
    for rg in REGLAS_SEL[1:] + ['sin_petroleo', 'sin_mensuales', 'sin_x_petroleo', 'sin_acciones_v2', 'sin_metales',
                               'sin_bolsa_e1', 'sin_c10', 'sin_shy', 'sin_cripto']:
        if rg.startswith('sin_') and rg[4:] not in set(O.lista):
            continue
        m = W.copy()
        for Y in range(oos0.year, HOY.year + 1):
            ini = pd.Timestamp(f'{Y}-01-01')
            en = (O.t_entrada >= ini).values & (O.t_entrada < pd.Timestamp(f'{Y + 1}-01-01')).values
            m[en] = W[en] & regla_mascara(O, rg, ini)[en]
        rr = M.simular(VIGENTE, mascara=m)
        mo = metricas(M, rr.s, oos0, mascara=m)
        m5 = metricas(M, rr.s, ULT5, mascara=m)
        rs = resumen(M, rr.s, desde, m)
        filas.append(dict(config=f'regla fija: {rg}', OOS_desde=str(oos0.date()), R_ano_OOS=r(mo['R_ano']),
                          caida_OOS=r(mo['caida']), Rano_caida_OOS=r(mo['Rano_caida']), Rano_caida_5a=r(m5['Rano_caida']),
                          n_OOS=mo['n'], **{f'ep_{k}': v for k, v in rs['epocas'].items()}))
    T = pd.DataFrame(filas)
    T.to_csv(f'{sal}/p4_seleccion.csv', index=False)
    return T, E, comp, wf


# ------------------------------------------------------------------------------------- 5 tamaños por estrellas
ESQUEMAS = {
    'actual': None,
    'P1 ★★×0,5 ★★★×1 ★★★★×1,5 ★★★★★×2': {1: 0.0, 2: 0.5, 3: 1.0, 4: 1.5, 5: 2.0},
    'P2 ★★×0,75 ★★★×1 ★★★★×1,25 ★★★★★×1,5': {1: 0.0, 2: 0.75, 3: 1.0, 4: 1.25, 5: 1.5},
    'P3 ★★×0,5 resto ×1': {1: 0.0, 2: 0.5, 3: 1.0, 4: 1.0, 5: 1.0},
    'P4 ★★★★ o más ×1,5': {1: 0.0, 2: 1.0, 3: 1.0, 4: 1.5, 5: 1.5},
}


def tam_esquema(O, esq, normalizar_con=None):
    if esq is None:
        return np.ones(len(O))
    est = O.estrellas.values.astype(float)
    tm = np.ones(len(O))
    ok = ~np.isnan(est)
    q = np.clip(np.round(est[ok]), 1, 5).astype(int)
    tm[ok] = np.array([esq[x] for x in q])
    if normalizar_con is not None:
        m = normalizar_con & ok
        if m.sum():
            f = (O.tam_R.values[m]).sum() / max((O.tam_R.values[m] * tm[m]).sum(), 1e-9)
            tm[ok] *= f
    tm[~ok] = 1.0
    return tm


def punto5(M, O, desde, W, sal, semillas=20):
    filas = []
    con_est = O.estrellas.notna().values
    for n, esq in ESQUEMAS.items():
        for norm in ((False, True) if esq else (False,)):
            tm = tam_esquema(O, esq, W if norm else None)
            rr = M.simular(dict(tam_mult=tm), mascara=W)
            rs = resumen(M, rr.s, desde, W)
            filas.append(dict(config=n + (' · mismo riesgo medio' if norm else ''), R_ano=rs['R_ano'], caida=rs['caida'],
                              Rano_caida=rs['Rano_caida'], Rano_caida_5a=rs['Rano_caida_5a'],
                              **{f'ep_{k}': v for k, v in rs['epocas'].items()}))
    T = pd.DataFrame(filas)
    # walk-forward entre esquemas (normalizados)
    def mde(rg, ini):
        return np.ones(len(O), bool), tam_esquema(O, ESQUEMAS[rg], W & (O.t_entrada < ini).values)
    comp, tamc, E, oos0 = walk_forward(M, O, desde, W, list(ESQUEMAS), mde, sal, 'p5_tamanos')
    wf = M.simular(dict(tam_mult=tamc), mascara=W)
    base = M.simular(VIGENTE, mascara=W)
    mo_b = metricas(M, base.s, oos0, mascara=W)
    mo_w = metricas(M, wf.s, oos0, mascara=W)
    extra = [dict(config='vigente (tamaños actuales) · fuera de muestra', Rano_caida_OOS=r(mo_b['Rano_caida']),
                  R_ano_OOS=r(mo_b['R_ano']), caida_OOS=r(mo_b['caida'])),
             dict(config='esquema elegido año a año (walk-forward)', Rano_caida_OOS=r(mo_w['Rano_caida']),
                  R_ano_OOS=r(mo_w['R_ano']), caida_OOS=r(mo_w['caida']))]
    # placebo para el mejor esquema fijo: estrellas barajadas dentro de lista y año
    mejor = T.iloc[1:].sort_values('Rano_caida', ascending=False).iloc[0]['config'] if len(T) > 1 else None
    plac = []
    if mejor:
        esq = ESQUEMAS[mejor.split(' · ')[0]]
        norm = ' · mismo riesgo medio' in mejor
        rng = np.random.default_rng(20)
        O2 = O.copy()
        for sd in range(semillas):
            est = O.estrellas.values.copy()
            for _, g in O[con_est].groupby([O.lista[con_est], O.t_entrada[con_est].dt.year]):
                idx = g.index.values
                est[idx] = rng.permutation(est[idx])
            O2['estrellas'] = est
            tm = tam_esquema(O2, esq, W if norm else None)
            rr = M.simular(dict(tam_mult=tm), mascara=W)
            plac.append(resumen(M, rr.s, desde, W)['Rano_caida'])
        real = T.set_index('config').loc[mejor, 'Rano_caida']
        extra.append(dict(config=f'placebo de «{mejor}» (estrellas barajadas, {semillas} veces)',
                          Rano_caida=r(float(np.median(plac))), pct_placebo_ge_real=r(float(np.mean(np.array(plac) >= real)))))
    T = pd.concat([T, pd.DataFrame(extra)], ignore_index=True)
    T.to_csv(f'{sal}/p5_tamanos.csv', index=False)
    return T, E


# ------------------------------------------------------------------------------------- 6 apalancamiento
GRID = [0.2, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]


def m_para(caidas, rs, objetivo):
    """Interpola el multiplicador con el que la peor caída llega a `objetivo` R."""
    g = np.array(GRID)
    c = np.array(caidas)
    if c[0] >= objetivo:
        m = g[0] * objetivo / c[0]
        return m, rs[0] * m / g[0]
    for i in range(1, len(g)):
        if c[i] >= objetivo:
            f = (objetivo - c[i - 1]) / (c[i] - c[i - 1]) if c[i] > c[i - 1] else 0
            m = g[i - 1] + f * (g[i] - g[i - 1])
            return m, rs[i - 1] + f * (rs[i] - rs[i - 1])
    return float('inf'), rs[-1]


def punto6(M, O, desde, W, sal, candidatas):
    # (a) combinaciones de familias, sin topes ni freno: la caída escala con el multiplicador
    listas = sorted(O[W].lista.unique())
    curvas = {}
    for l in listas:
        m = W & (O.lista.values == l)
        todas = np.where(m, 1.0, 0.0)
        curvas[l] = M.curva(todas)
    filas = []
    for k in range(1, len(listas) + 1):
        for comb in itertools.combinations(listas, k):
            e = sum(curvas[l] for l in comb)
            e = e[(e.index >= desde - pd.Timedelta(days=1)) & (e.index <= HOY)]
            anos = (HOY - desde).days / 365.25
            dd = caida_max(e)
            ra = (e.iloc[-1] - e.iloc[0]) / anos
            e1 = e[e.index < pd.Timestamp('2022-01-01')]
            e2 = e[e.index >= pd.Timestamp('2021-12-31')]
            e5 = e[e.index >= ULT5 - pd.Timedelta(days=1)]
            def rc(x, a):
                d = caida_max(x)
                return ((x.iloc[-1] - x.iloc[0]) / a) / d if d > 0 else np.nan
            filas.append(dict(combinacion=' + '.join(comb), n_familias=k, R_ano=r(ra), caida=r(dd),
                              Rano_caida=r(ra / dd if dd > 0 else np.nan),
                              m_20R=r(20 / dd if dd > 0 else np.nan), R_ano_a_20R=r(ra * 20 / dd if dd > 0 else np.nan),
                              m_30R=r(30 / dd if dd > 0 else np.nan), R_ano_a_30R=r(ra * 30 / dd if dd > 0 else np.nan),
                              Rano_caida_hasta2021=r(rc(e1, (pd.Timestamp('2022-01-01') - desde).days / 365.25)),
                              Rano_caida_2022_26=r(rc(e2, (HOY - pd.Timestamp('2022-01-01')).days / 365.25)),
                              Rano_caida_5a=r(rc(e5, 5.0))))
    C = pd.DataFrame(filas).sort_values('Rano_caida', ascending=False)
    C.to_csv(f'{sal}/p6_combinaciones_sin_topes.csv', index=False)
    # elegir la mejor combinación con datos hasta 2021 y comprobarla en 2022-26
    mejor_is = C.sort_values('Rano_caida_hasta2021', ascending=False).iloc[0]
    todo = C[C.n_familias == len(listas)].iloc[0]
    oos = dict(elegida_hasta_2021=mejor_is['combinacion'], su_2022_26=mejor_is['Rano_caida_2022_26'],
               todas_2022_26=todo['Rano_caida_2022_26'],
               posicion_de_la_elegida_en_2022_26=int((C.Rano_caida_2022_26 > mejor_is['Rano_caida_2022_26']).sum()) + 1,
               de=len(C))
    # (b) con topes: rejilla de multiplicadores para las carteras candidatas
    filas = []
    for n, (cfg, msk) in candidatas.items():
        cs, rs_ = [], []
        for g in GRID:
            c = dict(cfg)
            c['mult'] = g * cfg.get('mult', 1.0)
            rr = M.simular(c, mascara=msk)
            mt = metricas(M, rr.s, desde, mascara=msk)
            cs.append(mt['caida'])
            rs_.append(mt['R_ano'])
            filas.append(dict(cartera=n, mult=g, R_ano=r(mt['R_ano']), caida=r(mt['caida']), Rano_caida=r(mt['Rano_caida']),
                              perdidas=int(((rr.motivo == 'tope 20 R') | (rr.motivo == 'tope bloque')).sum())))
        m20, r20 = m_para(cs, rs_, 20)
        m30, r30 = m_para(cs, rs_, 30)
        filas.append(dict(cartera=n, mult='→20R', R_ano=r(r20), caida=20, Rano_caida=None, perdidas=None, m=r(m20)))
        filas.append(dict(cartera=n, mult='→30R', R_ano=r(r30), caida=30, Rano_caida=None, perdidas=None, m=r(m30)))
    G = pd.DataFrame(filas)
    G.to_csv(f'{sal}/p6_apalancamiento_con_topes.csv', index=False)
    return C, oos, G


# ------------------------------------------------------------------------------------- 8 ideas de cartera
def comparar_is_oos(M, O, desde, W, variantes, corte, sal, nombre):
    filas = []
    for n, c in variantes.items():
        rr = M.simular(c, mascara=W)
        mi = metricas(M, rr.s, desde, corte, mascara=W)
        eq = rr.eq
        mo = metricas(M, rr.s, corte, mascara=W, eq=eq)
        m5 = metricas(M, rr.s, ULT5, mascara=W, eq=eq)
        rs = resumen(M, rr.s, desde, W)
        filas.append(dict(variante=n, Rano_caida_IS=r(mi['Rano_caida']), R_ano_IS=r(mi['R_ano']), caida_IS=r(mi['caida']),
                          Rano_caida_OOS=r(mo['Rano_caida']), R_ano_OOS=r(mo['R_ano']), caida_OOS=r(mo['caida']),
                          Rano_caida_5a=r(m5['Rano_caida']), Rano_caida_todo=rs['Rano_caida'],
                          **{f'ep_{k}': v for k, v in rs['epocas'].items()}))
    T = pd.DataFrame(filas)
    T.to_csv(f'{sal}/{nombre}.csv', index=False)
    return T


def pesos_bloque_wf(M, O, desde, W, base_s):
    """Pesos por bloque = 1 / caída del bloque en los 3 años anteriores (normalizados a media 1 por operación).
    Se recalculan el 1 de enero de cada año con datos anteriores."""
    tabla = {}
    for Y in range(desde.year, HOY.year + 1):
        ini = pd.Timestamp(f'{Y}-01-01')
        a = ini - pd.DateOffset(years=3)
        pes = {}
        for b in set(O.bloque):
            m = W & (O.bloque.values == b)
            e = M.curva(base_s, m)
            e = e[(e.index >= a) & (e.index < ini)]
            dd = caida_max(e) if len(e) else 0
            pes[b] = 1.0 / max(dd, 2.0)
        cnt = O[W & (O.t_entrada >= ini).values & (O.t_entrada < pd.Timestamp(f'{Y + 1}-01-01')).values].bloque.value_counts()
        tot = sum(pes[b] * cnt.get(b, 0) for b in pes)
        n = cnt.sum()
        f = n / tot if tot > 0 else 1
        tabla[Y] = {b: pes[b] * f for b in pes}
    dia0 = pd.Timestamp(M.dia0)
    return lambda dia: tabla.get((dia0 + pd.Timedelta(days=int(dia))).year, {}), tabla


def punto8(M, O, desde, W, sal):
    corte = pd.Timestamp('2022-01-01')
    var = {'vigente (freno 4 R → × 0,5)': VIGENTE}
    for u in (3, 6, 8):
        var[f'freno {u} R → × 0,5'] = dict(freno=(u, 0.5))
    for u in (4, 6):
        var[f'freno {u} R → × 0,75'] = dict(freno=(u, 0.75))
    var['sin freno'] = dict(freno=None)
    for obj in (5, 8, 12):
        var[f'objetivo de riesgo abierto {obj} R (nuevas ×{obj}/abierto, 0,5-1)'] = dict(vol_obj=dict(obj=obj, lim=(0.5, 1.0), max=1.0))
        var[f'objetivo de riesgo abierto {obj} R (con poco abierto ×1,25)'] = dict(vol_obj=dict(obj=obj, lim=(0.5, 1.25), max=1.25))
    var['SHY fuera del tope de 20 R'] = dict(shy_fuera_tope=True)
    var['tamaño ajustado por correlación (raíz)'] = dict(ajuste_corr='raiz')
    base = M.simular(SIN_TOPES, mascara=W)
    fpes, tabla = pesos_bloque_wf(M, O, desde, W, base.s)
    var['reparto de riesgo entre bloques (1/caída de 3 años, año a año)'] = dict(pesos_bloque=fpes)
    T = comparar_is_oos(M, O, desde, W, var, corte, sal, 'p8_ideas')
    pd.DataFrame(tabla).T.round(3).to_csv(f'{sal}/p8_pesos_bloque.csv')
    return T


# ------------------------------------------------------------------------------------- 7 horario
def motor_modificado(M, O2):
    M2 = copy.copy(M)
    M2.rf = O2.r_final.values.astype(float)
    M2.t_ent = O2.t_entrada.values
    M2.t_sal = O2.t_salida.values
    M2.ent_dia = ((O2.t_entrada.dt.normalize().values - M.dia0) / np.timedelta64(1, 'D')).astype(int)
    M2.sal_dia = ((O2.t_salida.dt.normalize().values - M.dia0) / np.timedelta64(1, 'D')).astype(int)
    return M2


def punto7(M, O, desde, W, sal):
    filas = []
    dets = {}
    nombres = {'a-opt': 'a · actual (la ligera ve la señal si está en vigilancia)',
               'a-pes': 'a · actual (señales nuevas de 4 h solo a las 6, 10, 14, 18 y 22)',
               'b': 'b · revisión de todo cada hora de 6 a 22', 'd': 'd · 24 horas'}
    tiene24 = 'cripto_24h' in set(O.lista)
    t_ok = (O.t_entrada >= desde).values
    BASEm = en_cartera(O).values if hasattr(en_cartera(O), 'values') else en_cartera(O)
    cr = (O.lista.values == 'cripto')
    hl = HOR.local(O.t_senal.values)
    invierno_fuera = cr & np.isin(hl.hour, [9, 13, 17, 21])
    for h in ('a-opt', 'a-pes', 'b', 'd'):
        O2, keep, det = HOR.aplicar(O, h, cripto_por_lista=tiene24)
        M2 = motor_modificado(M, O2)
        if tiene24:
            if h == 'd':
                keep = (keep & ~cr & BASEm) | ((O.lista.values == 'cripto_24h') & O.operable.values)
                c24 = (O.lista.values == 'cripto_24h') & t_ok
                det['cripto_24h_vs_horario_actual'] = dict(n_24h=int(c24.sum()), n_actual=int((cr & t_ok).sum()),
                                                           R_24h=r(float(O.r_final.values[c24].sum())),
                                                           R_actual=r(float(O.r_final.values[cr & t_ok].sum())))
            elif h == 'a-pes':
                det['cripto_perdidas_invierno'] = int((invierno_fuera & t_ok).sum())
                det['R_cripto_perdidas_invierno'] = r(float(O.r_final.values[invierno_fuera & t_ok].sum()))
                keep = keep & ~invierno_fuera
        dets[h] = det
        for topes in (True, False):
            c = VIGENTE if topes else dict(tope_total=None, tope_bloque=None)
            mk = (W & keep) if not (tiene24 and h == 'd') else (keep & t_ok)
            rr = M2.simular(c, mascara=mk)
            rs = resumen(M2, rr.s, desde, mk)
            filas.append(dict(horario=nombres[h] + ('' if topes else ' · SIN TOPES (solo freno)'), R_ano=rs['R_ano'],
                              caida=rs['caida'], Rano_caida=rs['Rano_caida'], Rano_caida_5a=rs['Rano_caida_5a'],
                              n=rs['n'], **{f'ep_{k}': v for k, v in rs['epocas'].items()},
                              entradas_perdidas=det['perdidas'], R_lista_perdidas=det['R_perdidas'],
                              entradas_retrasadas=det['retrasadas'], dR_entradas_retrasadas=det['dR_retrasos_entrada'],
                              salidas_retrasadas=det['salidas_retrasadas'], dR_salidas=det['dR_salidas']))
    T = pd.DataFrame(filas)
    T.to_csv(f'{sal}/p7_horario.csv', index=False)
    S = HOR.estimar_stops()
    S.to_csv(f'{sal}/p7_simulador_rebote4h_horario.csv', index=False)
    ctx = HOR.contexto_horario(O)
    return T, S, ctx, dets


# ------------------------------------------------------------------------------------- principal
def main(carpeta, sal, rapido=False):
    os.makedirs(sal, exist_ok=True)
    t0 = time.time()
    O, D = cargar(carpeta)
    if 'cripto_realista' in set(O.lista):
        # la lista «realista» es la del horario actual (sin las velas que no ve nadie): es la cripto de la cartera;
        # la de 24 h queda aparte para el punto 7
        O['lista'] = O['lista'].replace({'cripto': 'cripto_24h', 'cripto_realista': 'cripto'})
    O['en_cartera'] = marcar_variantes(O)
    BASE = O['en_cartera'].values
    blo = dict(zip(O.activo.astype(str), O.bloque.astype(str)))
    C = Correlaciones(O.activo.astype(str).unique(),
                      defecto=lambda a, b: 0.6 if blo.get(a) == blo.get(b) else 0.1)
    M = Motor(O, D, C)
    desde = inicio_ventana(O)
    W = BASE & (O.t_entrada >= desde).values
    log = lambda *a: print(f'[{time.time() - t0:6.0f}s]', *a, flush=True)
    log('cargado', len(O), 'operaciones;', 'ventana desde', desde.date(), '; sin precios:', C.sin_datos)
    R = dict(ventana_desde=str(desde.date()), n_operaciones=len(O), listas=O.lista.value_counts().to_dict(),
             sin_precios_para_correlacion=C.sin_datos,
             escala_diario=O.groupby('lista').escala_diario.first().to_dict())
    fase_ent, fase_hoy = fases(O)
    R['p1'], todas = punto1(M, O, desde, W, BASE, fase_ent, fase_hoy, sal)
    log('punto 1')
    T2, res2 = punto2(M, O, desde, W, sal)
    R['p2'] = T2.to_dict('records')
    vig = res2['E · VIGENTE: 20 R + bloque 10 R + freno + 5 R/op']
    ra_v = riesgo_abierto(M, vig.s, desde)
    ra_t = riesgo_abierto(M, res2['A · todas, sin topes ni freno'].s, desde)
    R['riesgo_abierto'] = dict(vigente_max=r(ra_v.max()), vigente_p95=r(ra_v.quantile(0.95)),
                               vigente_medio=r(ra_v.mean()), sin_topes_max=r(ra_t.max()),
                               sin_topes_p95=r(ra_t.quantile(0.95)), dias_sin_topes_sobre_20R=int((ra_t > 20).sum()))
    pd.DataFrame({'vigente': ra_v, 'sin_topes': ra_t}).to_csv(f'{sal}/riesgo_abierto_diario.csv')
    log('punto 2')
    TV = punto_variantes(M, O, desde, W, sal)
    R['variantes'] = TV.to_dict('records')
    log('variantes')
    T3, res3 = punto3(M, O, desde, W, sal)
    R['p3'] = T3.to_dict('records')
    log('punto 3')
    T4, E4, comp4, wf4 = punto4(M, O, desde, W, sal)
    R['p4'] = dict(tabla=T4.to_dict('records'), elecciones=E4[['ano', 'elegida']].to_dict('records'))
    log('punto 4')
    T5, E5 = punto5(M, O, desde, W, sal, semillas=8 if rapido else 20)
    R['p5'] = dict(tabla=T5.to_dict('records'), elecciones=E5[['ano', 'elegida']].to_dict('records'))
    log('punto 5')
    T7, S7, ctx7, det7 = punto7(M, O, desde, W, sal)
    R['p7'] = dict(tabla=T7.to_dict('records'), simulador=S7.to_dict('records'), contexto_c=ctx7, detalle=det7)
    log('punto 7')
    T8 = punto8(M, O, desde, W, sal)
    R['p8'] = T8.to_dict('records')
    log('punto 8')
    cand = {'vigente': (VIGENTE, W), 'vigente sin topes (solo freno)': (dict(tope_total=None, tope_bloque=None), W),
            'selección walk-forward': (VIGENTE, comp4)}
    for l in ('petroleo', 'acciones_v2', 'mensuales'):
        if l in set(O.lista):
            cand[f'sin {l}'] = (VIGENTE, W & (O.lista.values != l))
    C6, oos6, G6 = punto6(M, O, desde, W, sal, cand)
    R['p6'] = dict(top_combinaciones=C6.head(10).to_dict('records'), todas=C6[C6.n_familias == C6.n_familias.max()].to_dict('records'),
                   eleccion_fuera_de_muestra=oos6, rejilla=G6[G6.mult.astype(str).str.startswith('→')].to_dict('records'))
    log('punto 6')
    R['segundos'] = round(time.time() - t0)
    json.dump(R, open(f'{sal}/resultados_analisis.json', 'w'), ensure_ascii=False, indent=1, default=str)
    return R, M, O, D, W, desde


if __name__ == '__main__':
    carpeta = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/motor/listas'
    sal = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/motor/salida'
    main(carpeta, sal, rapido=len(sys.argv) > 3)
