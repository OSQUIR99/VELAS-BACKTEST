# -*- coding: utf-8 -*-
"""Reglas candidatas para bajar la caída, fijadas ANTES de medirlas (28-oct-2026), sobre las tres versiones de la base.
Cada una se juzga con la regla del documento 23 (sube R/año ÷ caída Y sube R/año en todo, 2018-21 y 2022-26),
la media de las 5 peores caídas, el remuestreo por meses y el R/año escalado a la misma caída que la base."""
import sys, copy, time
import numpy as np, pandas as pd
from comun import Cartera, FL, HOY
from b21 import serie_b21, afectadas

C = Cartera(); O = C.O; M = C.M
F = pd.read_parquet('/home/claude/caidas/factores.parquet')
L = C.L; largo = O.direccion.values == 1
dia_ent = O.t_entrada.dt.normalize()
PET_L = (L == 'petroleo') & largo
CRI = L == 'cripto'
E1 = C.e1


def on_at_entry(col):
    return F[col].reindex(dia_ent).fillna(0).values.astype(bool)


def tm(mask, f):
    return np.where(mask, f, 1.0)


# ---------------------------------------------------------------- E1: varias a la vez
def e1_por_dia(raiz=False):
    g = pd.Series(dia_ent.values[E1]).value_counts()
    n = dia_ent.map(g).fillna(1).values
    f = 1 / np.sqrt(n) if raiz else 1 / n
    return np.where(E1, f, 1.0)


def e1_una_a_la_vez(base):
    k = np.flatnonzero(E1 & base); k = k[np.argsort(M.t_ent[k])]
    ok = np.ones(len(O), bool); fin = np.datetime64('1900-01-01')
    for j in k:
        if M.t_ent[j] < fin:
            ok[j] = False
        else:
            fin = M.t_sal[j]
    return ok


# ---------------------------------------------------------------- cripto: racimos
def cripto_max_24h(base, nmax=2):
    k = np.flatnonzero(CRI & base); k = k[np.argsort(M.t_ent[k])]
    ok = np.ones(len(O), bool); tomadas = []
    for j in k:
        t = M.t_ent[j]
        rec = [x for x in tomadas if t - x < np.timedelta64(24, 'h')]
        if len(rec) >= nmax:
            ok[j] = False
        else:
            tomadas.append(t)
    return ok


def cripto_raiz_simultaneas():
    h = O.t_entrada.dt.floor('h')
    g = pd.Series(h.values[CRI]).value_counts()
    n = h.map(g).fillna(1).values
    return np.where(CRI, 1 / np.sqrt(n), 1.0)


# ---------------------------------------------------------------- devolver ganancias: protección y venta parcial
def motor_protegido(sel, X, g=None, parcial=False):
    M2 = copy.copy(M)
    M2.rf = M.rf.copy(); M2.sal_dia = M.sal_dia.copy(); M2.t_sal = M.t_sal.copy(); M2.lat = dict(M.lat)
    M2.mfe_run = dict(M.mfe_run)
    d0 = pd.Timestamp(M.dia0)
    cambios = 0
    for k in np.flatnonzero(sel):
        if k not in M.lat:
            continue
        d, v, r = M.lat[k]
        m = d < M.sal_dia[k]
        if m.sum() < 2:
            continue
        d, v = d[m], v[m]
        u = v / max(M.tam[k], 1e-9)
        mx = np.maximum.accumulate(u)
        if not parcial:
            hit = np.flatnonzero((mx >= X) & (u <= (1 - g) * mx))
            if not len(hit):
                continue
            i = hit[0]
            M2.sal_dia[k] = d[i]; M2.rf[k] = v[i]
            M2.t_sal[k] = np.datetime64(d0 + pd.Timedelta(days=int(d[i]), hours=23))
            cambios += 1
        else:
            hit = np.flatnonzero(u >= X)
            if not len(hit):
                continue
            i = hit[0]
            vi = v[i]
            v2 = v.copy(); v2[i + 1:] = 0.5 * vi + 0.5 * v[i + 1:]
            M2.lat[k] = (d, v2, None)
            M2.rf[k] = 0.5 * vi + 0.5 * M.rf[k]
            uu = v2 / max(M.tam[k], 1e-9)
            M2.mfe_run[k] = np.maximum.accumulate(np.maximum(uu, 0))
            cambios += 1
    return M2, cambios


def variantes(base):
    V = {}
    # petróleo largo
    V['P1 petróleo largo × 0,5 si el dólar sube +2 % en 20 sesiones'] = dict(tam=tm(PET_L & on_at_entry('dolar_sube'), 0.5))
    V['P2 petróleo largo NO entrar si el dólar sube +2 %'] = dict(mask=base & ~(PET_L & on_at_entry('dolar_sube')))
    V['P3 petróleo largo × 0,5 con la línea de liquidez < 33'] = dict(tam=tm(PET_L & on_at_entry('liquidez_baja'), 0.5))
    V['P4 petróleo largo NO entrar con la línea < 33'] = dict(mask=base & ~(PET_L & on_at_entry('liquidez_baja')))
    V['P5 petróleo largo × 0,5 si el bono a 10 años sube +0,30 en 20 días'] = dict(tam=tm(PET_L & on_at_entry('tipos_suben'), 0.5))
    # E1
    V['E1a E1 × 0,5 con la línea con impulso < 50'] = dict(tam=tm(E1 & on_at_entry('liquidez_impulso_bajo50'), 0.5))
    V['E1b E1 NO entrar con la línea con impulso < 50'] = dict(mask=base & ~(E1 & on_at_entry('liquidez_impulso_bajo50')))
    V['E1c E1 del mismo día repartidas (1 R entre todas)'] = dict(tam=e1_por_dia(False))
    V['E1d E1 del mismo día × 1/raíz(n)'] = dict(tam=e1_por_dia(True))
    V['E1e E1 una sola abierta a la vez (de los 3 índices)'] = dict(mask=base & e1_una_a_la_vez(base))
    # cripto: racimos y topes
    V['K1 tope por bloque 6 R (en vez de 10)'] = dict(cfg=dict(FL, tope_bloque=6.0))
    V['K2 tope por bloque 4 R'] = dict(cfg=dict(FL, tope_bloque=4.0))
    V['K3 cripto: máximo 2 entradas en 24 h'] = dict(mask=base & cripto_max_24h(base))
    V['K4 cripto simultáneas × 1/raíz(n)'] = dict(tam=cripto_raiz_simultaneas())
    # devolver ganancias abiertas (aprox. con el cierre diario)
    for X, g in ((3, 0.5), (5, 0.5), (3, 0.33), (5, 0.33)):
        V[f'G cripto: tras +{X} R no devolver más del {int(g*100)} % de lo ganado'] = dict(prot=(CRI & base, X, g, False))
    for X in (3, 5):
        V[f'G cripto: vender la mitad al llegar a +{X} R'] = dict(prot=(CRI & base, X, None, True))
    V['G todas: tras +3 R no devolver más del 50 %'] = dict(prot=(base & ~np.isin(L, ['shy']), 3, 0.5, False))
    # freno de racha
    V['F1 freno a 3 R (en vez de 4)'] = dict(cfg=dict(FL, freno=(3, 0.5)))
    V['F2 freno a 6 R'] = dict(cfg=dict(FL, freno=(6, 0.5)))
    # B21 (referencia: lo que se aplicó ayer)
    b21 = serie_b21()
    resto = largo & ~np.isin(L, ['cripto', 'shy', 'corto_sector', 'corto_indices_credito'])
    V['B21 mitad (vigente desde el 27-oct)'] = dict(tam=tm(afectadas(C, b21, resto & base), 0.5))
    return V


if __name__ == '__main__':
    t0 = time.time(); filas = []
    for nb, base in C.bases.items():
        rb, eqb = C.sim(base); qb = C.met3(eqb); m5b, _ = C.media5(eqb)
        filas.append(dict(base=nb, regla='BASE', r=qb[0]['ratio'], r1821=qb[1]['ratio'], r2226=qb[2]['ratio'], Ra=qb[0]['R_ano'],
                          Ra1821=qb[1]['R_ano'], Ra2226=qb[2]['R_ano'], caida=qb[0]['caida'], media5=m5b))
        print(f'\n{nb} BASE', C.fmt(qb), '| media5', round(m5b, 1), flush=True)
        for nr, v in variantes(base).items():
            MM = M; extra = ''
            if 'prot' in v:
                sel, X, g, par = v['prot']; MM, nc = motor_protegido(sel, X, g, par); extra = f' ({nc} cambiadas)'
            rr, eq = C.sim(v.get('mask', base), cfg=v.get('cfg'), tam_mult=v.get('tam'), M=MM)
            q = C.met3(eq); m5, _ = C.media5(eq); ok = C.pasa(q, qb); bt = C.bootstrap(eqb, eq, n=500)
            esc = q[0]['R_ano'] * qb[0]['caida'] / q[0]['caida']
            filas.append(dict(base=nb, regla=nr, r=q[0]['ratio'], r1821=q[1]['ratio'], r2226=q[2]['ratio'], Ra=q[0]['R_ano'],
                              Ra1821=q[1]['R_ano'], Ra2226=q[2]['R_ano'], caida=q[0]['caida'], media5=m5, pasa=ok, boot=bt,
                              Ra_misma_caida=esc))
            print(f'  {nr[:62]:62s}', C.fmt(q), f'| media5 {m5:.1f} | escalada {esc:.1f}', '| PASA' if ok else '| no', f'| boot {bt:.2f}{extra}', flush=True)
        pd.DataFrame(filas).to_csv('/home/claude/caidas/reglas.csv', index=False)
    print('tiempo', round(time.time() - t0))
