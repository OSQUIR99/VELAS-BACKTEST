# -*- coding: utf-8 -*-
"""Dos pruebas de mejora (18-oct-2026), sobre lo encontrado en el estudio de dominancias.

A) ¿La pendiente de la media de ETH/BTC está sobreajustada? Rejilla de vecinos: media de 10-40 días y
   pendiente medida a 3, 5 o 10 días. Rotación diaria ETH↔BTC (señal al cierre t, se opera al cierre t+1,
   comisión 0,1 %). Se compara con 50/50 por tramos: 2018-21, 2022-26 y 2024-26.

B) ¿Sirve para repartir la compra semanal al contado entre BTC y ETH (documento 09)?
   Regla del 09: 200 $ a la semana repartidos en proporción al multiplicador de cada moneda (el menor de:
   precio frente a la media de 200 semanas y caída desde el máximo). Variantes: inclinar el reparto hacia la
   moneda que favorece la pendiente (×1,25/×0,75, ×1,5/×0,5, todo a la favorecida). Mismo total de dólares.
   Se mide el valor final de lo comprado (BTC + ETH al precio final) por dólar aportado, por ciclo y empezando
   cada ciclo de cero, y la peor caída de la cartera.
"""
import sys, os, itertools
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas
from rotacion_dominancia import simular, metricas, tramos

btc, eth, eb = velas('BTC', '1d').cierre, velas('ETH', '1d').cierre, velas('ETH_BTC', '1d').cierre
idx = btc.index.intersection(eth.index); idx = idx[idx >= '2018-01-01']
rB, rE = btc.pct_change().reindex(idx), eth.pct_change().reindex(idx)

def tramo(eq, a, b):
    e = eq[a:b]; return e.iloc[-1] / e.iloc[0] - 1

# ------------------------------------------------------------------ A
base, _ = simular(rE, rB, pd.Series(0.5, idx))
filas = []
for n, k in itertools.product((10, 15, 20, 30, 40), (3, 5, 10)):
    m = eb.rolling(n).mean(); s = np.sign(m - m.shift(k)).reindex(idx).fillna(0)
    eq, turn = simular(rE, rB, 0.5 + 0.5 * s)
    met = metricas(eq); f = {'media': n, 'pendiente_dias': k, 'total_%': met['total'] * 100, 'caida_%': met['mdd'] * 100,
                             'ratio': met['ratio'], 'rotaciones': turn}
    for nom, a, b in (('2018-21', '2018', '2021'), ('2022-26', '2022', '2026'), ('2024-26', '2024', '2026')):
        f[nom] = (tramo(eq, a, b) - tramo(base, a, b)) * 100
    filas.append(f)
A = pd.DataFrame(filas)
A['gana_los_3'] = (A[['2018-21', '2022-26', '2024-26']] > 0).all(axis=1)
mb = metricas(base)
print(f"A) 50/50: total {mb['total']*100:.0f} %, caída {mb['mdd']*100:.0f} %, ratio {mb['ratio']:.2f}")
print(A.round(2).to_string(index=False))
print('Ganan a 50/50 en los tres tramos:', int(A.gana_los_3.sum()), 'de', len(A))

# ------------------------------------------------------------------ B
w_b, w_e = velas('BTC', '1w').cierre, velas('ETH', '1w').cierre
def mult(w):
    ma = w.rolling(200, min_periods=100).mean().shift(0)
    r = w / ma; dd = 1 - w / w.cummax()
    m1 = pd.cut(r, [-np.inf, 1, 1.5, 2.5, 3.5, np.inf], labels=[3, 2, 1, .5, 0]).astype(float)
    m2 = pd.cut(dd, [-np.inf, .2, .4, .6, np.inf], labels=[.5, 1, 2, 3], right=False).astype(float)
    return np.minimum(m1, m2)
mB, mE = mult(w_b), mult(w_e)
m20 = eb.rolling(20).mean(); pend = np.sign(m20 - m20.shift(5))
semanas = w_b.index.intersection(w_e.index)
ciclos = [('2020-24', '2020-05-11', '2024-04-19'), ('2024-26', '2024-04-22', '2026-10-12'), ('2021-26', '2021-01-04', '2026-10-12')]
variantes = {'09 tal cual': None, 'inclinar ×1,25/×0,75': .25, 'inclinar ×1,5/×0,5': .5, 'todo a la favorecida': 1.0}
filasB = []
for cnom, a, b in ciclos:
    sem = semanas[(semanas >= a) & (semanas <= b)]
    for vnom, t in variantes.items():
        qb = qe = aport = 0.0; valores = []
        for d in sem:
            pb, pe = mB.get(d, np.nan), mE.get(d, np.nan)
            if np.isnan(pb) or np.isnan(pe): continue
            if t is not None:
                p = pend[:d - pd.Timedelta(days=1)].iloc[-1] if len(pend[:d]) else 0   # señal del cierre anterior
                fb, fe = (1 - t, 1 + t) if p > 0 else (1 + t, 1 - t) if p < 0 else (1, 1)
                pb, pe = pb * fb, pe * fe
            if pb + pe == 0: continue
            gasto = 200
            qb += gasto * pb / (pb + pe) / w_b[d]; qe += gasto * pe / (pb + pe) / w_e[d]; aport += gasto
            valores.append((qb * w_b[d] + qe * w_e[d], aport))
        v = pd.DataFrame(valores, columns=['valor', 'aport'])
        caida = ((v.valor - v.aport) / v.aport).min() if len(v) else np.nan
        filasB.append({'ciclo': cnom, 'variante': vnom, 'valor_por_dolar': v.valor.iloc[-1] / v.aport.iloc[-1],
                       'peor_momento_%': caida * 100, 'aportado': v.aport.iloc[-1]})
B = pd.DataFrame(filasB)
B['frente_al_09_%'] = B.groupby('ciclo').valor_por_dolar.transform(lambda x: (x / x.iloc[0] - 1) * 100)
print('\nB) Reparto de la compra semanal BTC/ETH')
print(B.round(3).to_string(index=False))
A.to_csv(os.path.join(AQUI, 'mejoras_A_vecinos.csv'), index=False); B.to_csv(os.path.join(AQUI, 'mejoras_B_contado.csv'), index=False)
