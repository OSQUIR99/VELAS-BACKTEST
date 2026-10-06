# -*- coding: utf-8 -*-
"""Detecta de forma objetiva los grandes movimientos de BTC (2017-2026)."""
import json
import numpy as np, pandas as pd

P = pd.read_parquet('panel_diario.parquet')
c = P['c']

def zigzag(s, umbral):
    """Puntos de giro: cada tramo recorre al menos `umbral` (0.25 = 25 %)."""
    piv = [(s.index[0], s.iloc[0], 0)]
    tend = 0; ext_i, ext_v = s.index[0], s.iloc[0]
    for i, v in s.items():
        if tend >= 0:
            if v > ext_v: ext_i, ext_v = i, v
            if tend == 1 and v <= ext_v * (1 - umbral):
                piv.append((ext_i, ext_v, 1)); tend = -1; ext_i, ext_v = i, v; continue
        if tend <= 0:
            if v < ext_v: ext_i, ext_v = i, v
            if tend == -1 and v >= ext_v * (1 + umbral):
                piv.append((ext_i, ext_v, -1)); tend = 1; ext_i, ext_v = i, v; continue
        if tend == 0:
            if v >= piv[0][1] * (1 + umbral): tend = 1; ext_i, ext_v = i, v
            elif v <= piv[0][1] * (1 - umbral): tend = -1; ext_i, ext_v = i, v
    piv.append((ext_i, ext_v, 0))
    return piv

piv = zigzag(c, 0.25)
tramos = []
for (i0, v0, _), (i1, v1, _) in zip(piv[:-1], piv[1:]):
    tramos.append(dict(inicio=i0.date(), fin=i1.date(), dias=(i1 - i0).days, desde=round(v0), hasta=round(v1),
                       cambio_pct=round((v1 / v0 - 1) * 100, 1)))
T = pd.DataFrame(tramos)
T['tipo'] = np.where(T.cambio_pct > 0, 'SUBIDA', 'CAIDA')
T.to_csv('tramos_zigzag25.csv', index=False)
print('TRAMOS >=25% (cierres diarios):', len(T))
print(T.to_string())

# movimientos rápidos: 7 días >= +-15 %, agrupados en episodios
r7 = c.pct_change(7)
ev = []
for signo, cond in [('CAIDA', r7 <= -0.15), ('SUBIDA', r7 >= 0.15)]:
    dias = cond[cond].index
    grupo = []
    for d in dias:
        if grupo and (d - grupo[-1]).days > 10:
            ev.append((signo, grupo)); grupo = []
        grupo.append(d)
    if grupo: ev.append((signo, grupo))
rows = []
for signo, g in ev:
    # día clave = día de mayor movimiento diario dentro de la ventana [primer día-7, último día]
    win = c.loc[g[0] - pd.Timedelta(days=7): g[-1]]
    rd = win.pct_change()
    clave = rd.idxmin() if signo == 'CAIDA' else rd.idxmax()
    ext = r7.loc[g].min() if signo == 'CAIDA' else r7.loc[g].max()
    rows.append(dict(tipo=signo, dia_clave=clave.date(), ret_dia_clave=round(rd.loc[clave] * 100, 1), ret_7d_extremo=round(ext * 100, 1),
                     precio=round(c.loc[clave])))
R = pd.DataFrame(rows).sort_values('dia_clave').reset_index(drop=True)
R.to_csv('movimientos_rapidos.csv', index=False)
print('\nMOVIMIENTOS RÁPIDOS (>=15 % en 7 días):', len(R), ' caídas', (R.tipo == 'CAIDA').sum(), ' subidas', (R.tipo == 'SUBIDA').sum())
print(R.to_string())
