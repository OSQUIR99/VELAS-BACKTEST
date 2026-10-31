# -*- coding: utf-8 -*-
"""Escaneo: ¿qué métricas, conocidas antes de entrar, acompañan a las operaciones perdedoras de cada familia?
Cartera base vigente (versión a). R por unidad = resultado de la operación por cada R arriesgado (sin el tamaño)."""
import pickle, numpy as np, pandas as pd
from comun import Cartera, HOY, CORTE
from factores import propias

C = Cartera()
O = C.O; M = C.M
F = pd.read_parquet('/home/claude/caidas/factores.parquet')


def familia(k):
    l = C.L[k]
    if l == 'bolsa_e1': return 'E1 índices'
    if l == 'metales': return 'oro'
    if l == 'petroleo':
        if C.senal[k] == 'S1': return 'petróleo S1'
        return 'petróleo corto noticia' if O.direccion.values[k] == -1 else 'petróleo largo'
    return {'cripto': 'cripto REBOTE 4H', 'x_petroleo': 'X1/X3', 'c10': 'C10', 'shy': 'SHY', 'corto_sector': 'CORTO SECTOR',
            'corto_indices_credito': 'CORTO ÍNDICES'}.get(l, l)


fam = np.array([familia(k) for k in range(len(O))])
base = C.bases['a · con S1 (listas originales)']
rr, eq = C.sim(base)
s = rr.s
P = propias(C, s, eq, fam)
tom = np.flatnonzero(s > 0)
T = pd.DataFrame({'k': tom, 'familia': fam[tom], 'activo': C.act[tom], 't': O.t_entrada.values[tom],
                  'u': O.r_final.values[tom] / O.tam_R.values[tom], 'R': s[tom] * O.r_final.values[tom]}).set_index('k')
T = T.join(P)
d0 = pd.to_datetime(T.t).dt.normalize()
for c in F.columns:
    T[c] = F[c].reindex(d0).values
T['freno_encendido'] = (T.caida_cartera >= 4).astype(float)
T['mucho_riesgo_abierto'] = (T.riesgo_abierto >= 8).astype(float)
T['3+_misma_familia_abiertas'] = (T.abiertas_misma_familia >= 3).astype(float)
T['3+_entradas_familia_3d'] = (T['entradas_3d_familia'] >= 3).astype(float)
T['racha3_perdedora'] = T['racha3_perdedora'].astype(float)
T.to_parquet('/home/claude/caidas/operaciones_factores.parquet')
FACT = [c for c in F.columns if c not in ('spx_dist200', 'vix')] + ['freno_encendido', 'mucho_riesgo_abierto', '3+_misma_familia_abiertas',
                                                                   '3+_entradas_familia_3d', 'racha3_perdedora']


def welch(a, b):
    if len(a) < 5 or len(b) < 5: return np.nan
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    return (a.mean() - b.mean()) / np.sqrt(va + vb) if va + vb > 0 else np.nan


filas = []
for f_, g in T.groupby('familia'):
    for c in FACT:
        x = g[c]
        ok = x.notna()
        on = g[ok & (x == 1)]; off = g[ok & (x == 0)]
        if len(on) < 8 or len(off) < 8:
            continue
        mitad = []
        for a, b in ((None, CORTE), (CORTE, None)):
            gg = g[ok]
            if a is not None: gg = gg[pd.to_datetime(gg.t) >= a]
            if b is not None: gg = gg[pd.to_datetime(gg.t) < b]
            o1 = gg[gg[c] == 1].u; o0 = gg[gg[c] == 0].u
            mitad.append((o1.mean() - o0.mean()) if len(o1) >= 4 and len(o0) >= 4 else np.nan)
        filas.append(dict(familia=f_, factor=c, n_on=len(on), pct_on=len(on) / ok.sum(), u_on=on.u.mean(), u_off=off.u.mean(),
                          dif=on.u.mean() - off.u.mean(), t=welch(on.u, off.u), dif_18_21=mitad[0], dif_22_26=mitad[1],
                          R_on=on.R.sum(), R_off=off.R.sum(), perdedoras_on=(on.u < 0).mean(), perdedoras_off=(off.u < 0).mean()))
E = pd.DataFrame(filas)
E['consistente'] = (np.sign(E.dif_18_21) == np.sign(E.dif_22_26)) & (np.sign(E.dif_18_21) == np.sign(E.dif))
E.to_csv('/home/claude/caidas/escaneo.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
print('Operaciones tomadas por familia:', T.familia.value_counts().to_dict())
print('R realizado por familia (ventana):', T.groupby('familia').R.sum().round(1).to_dict())
sel = E[(E.t.abs() >= 2) & E.consistente].sort_values('t')
print(sel[['familia', 'factor', 'n_on', 'pct_on', 'u_on', 'u_off', 'dif', 't', 'dif_18_21', 'dif_22_26', 'R_on', 'R_off']].round(3).to_string(index=False))
