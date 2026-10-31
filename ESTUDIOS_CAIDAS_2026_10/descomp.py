# -*- coding: utf-8 -*-
"""Reparto correcto de cada caída (corrección de la verificación del 28-oct):
  ganancia abierta en el máximo = latente de lo que estaba abierto ese día;
  devuelto por lo ya abierto     = Σ (valor al final del tramo − latente en el máximo) de esas operaciones
                                   (si se cerró dentro del tramo, su valor es su resultado final);
  operaciones nuevas             = Σ valor al final del tramo de las abiertas durante la caída;
  cobrado                        = resultado final de las que estaban abiertas en el máximo y se cerraron en el tramo.
  Comprobación: caída = devuelto + nuevas."""
import pickle, numpy as np, pandas as pd
from comun import Cartera, HOY

C = Cartera(); O = C.O; M = C.M
base = C.bases['a · con S1 (listas originales)']
rr, eq = C.sim(base); s = rr.s
d0 = pd.Timestamp(M.dia0)
e = eq[(eq.index >= C.desde) & (eq.index <= HOY)]
dd = e - e.cummax()
eps, i, v, idx = [], 0, dd.values, dd.index
while i < len(v):
    if v[i] < 0:
        j = i
        while j < len(v) and v[j] < 0: j += 1
        seg = dd.iloc[i:j]; eps.append((idx[i - 1], seg.idxmin(), idx[j] if j < len(v) else None, -seg.min())); i = j
    else:
        i += 1
eps = sorted(eps, key=lambda x: -x[3])[:8]


def valor(k, dia):
    """Valor de la operación k (en R de la cartera, × s) al cierre del día `dia` (índice de días desde dia0)."""
    if dia >= M.sal_dia[k]:
        return s[k] * M.rf[k]
    if dia < M.ent_dia[k]:
        return 0.0
    if k not in M.lat:
        return 0.0
    d, vv, _ = M.lat[k]
    m = (d <= dia) & (d < M.sal_dia[k])
    return s[k] * float(vv[m][-1]) if m.any() else 0.0


filas = []
tom = np.flatnonzero(s > 0)
for a, b, c, prof in eps:
    ia = int((a - d0) / pd.Timedelta(days=1)); ib = int((b - d0) / pd.Timedelta(days=1))
    abiertas = [k for k in tom if M.ent_dia[k] <= ia and M.sal_dia[k] > ia]
    nuevas = [k for k in tom if ia < M.ent_dia[k] <= ib]
    g_a = sum(valor(k, ia) for k in abiertas)
    dev = sum(valor(k, ib) - valor(k, ia) for k in abiertas)
    nue = sum(valor(k, ib) for k in nuevas)
    cobr = sum(s[k] * M.rf[k] for k in abiertas if M.sal_dia[k] <= ib)
    filas.append(dict(desde=a.date(), hasta=b.date(), caida=-prof, ganancia_abierta_en_maximo=g_a, devuelto_por_lo_abierto=dev,
                      operaciones_nuevas=nue, cobrado_de_lo_abierto=cobr, comprobacion=dev + nue + prof))
T = pd.DataFrame(filas)
pd.set_option('display.width', 200)
print(T.round(1).to_string(index=False))
T.to_csv('/home/claude/caidas/descomposicion.csv', index=False)
pickle.dump(dict(eq=eq, s=s, eps=eps), open('/home/claude/caidas/epis_a.pkl', 'wb'))
