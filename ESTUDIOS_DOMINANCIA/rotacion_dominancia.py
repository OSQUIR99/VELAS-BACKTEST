# -*- coding: utf-8 -*-
"""Rotación por extremos de dominancia (15-oct-2026).

Hipótesis de Óscar: cuando una dominancia está muy estirada respecto a su media,
tiende a volver. Se prueba:
  A) ETH contra BTC   (señal: ETH/BTC o ETH.D/BTC.D)
  B) BTC contra cesta de altcoins grandes (señal: BTC.D, y OTHERS/TOTAL)
  C) Dominancia de USDT: entrar/salir de BTC (señal: USDT.D)

Reglas comunes: decisión con el cierre diario, se ejecuta al cierre del día siguiente
(sin mirar el futuro). Comisión 0,1 % por lado sobre lo que se mueve.
"Estirado" = z (distancia a la media móvil en desviaciones típicas, en logaritmos).
Se prueba una rejilla de parámetros y se mira la mediana, no el mejor caso.
"""
import sys, os, itertools, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from cargar import velas

FEE = 0.001
c = lambda a: velas(a, '1d')['cierre']

def zscore(s, w):
    l = np.log(s)
    return (l - l.rolling(w).mean()) / l.rolling(w).std()

def pesos_rotacion(z, k, salida):
    """Peso en el activo 'A' (el que se compra cuando la señal está BAJA).
    salida='opuesto': se mantiene hasta el extremo contrario.
    salida='media': vuelve a 50/50 al cruzar la media."""
    w = np.full(len(z), 0.5); cur = 0.5
    for i, v in enumerate(z.values):
        if np.isnan(v): w[i] = 0.5; continue
        if v > k: cur = 0.0
        elif v < -k: cur = 1.0
        elif salida == 'media' and ((cur == 1.0 and v > 0) or (cur == 0.0 and v < 0)): cur = 0.5
        w[i] = cur
    return pd.Series(w, z.index)

def simular(rA, rB, wA, reb_semanal=True):
    """rA, rB rentabilidades diarias; wA peso objetivo en A (decidido ayer)."""
    wA = wA.shift(2).fillna(0.5)  # señal al cierre t, se opera al cierre t+1, gana desde t+2
    eq, cur, out, turn = 1.0, None, [], 0.0
    for d, a, b, t in zip(rA.index, rA.values, rB.values, wA.values):
        if cur is None: cur = t
        if t != cur or (reb_semanal and d.weekday() == 0):
            cost = abs(t - cur) * FEE * 2
            eq *= 1 - cost; turn += abs(t - cur); cur = t
        g = cur * (1 + a) + (1 - cur) * (1 + b)
        eq *= g
        cur = cur * (1 + a) / g if g else cur  # el peso deriva hasta el siguiente ajuste
        out.append(eq)
    return pd.Series(out, rA.index), turn

def metricas(eq):
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    mdd = (eq / eq.cummax() - 1).min()
    return dict(total=eq.iloc[-1] - 1, cagr=cagr, mdd=mdd, ratio=cagr / abs(mdd))

def tramos(eq):
    r = {}
    for nombre, a, b in [('2018-21', '2018', '2021'), ('2022-26', '2022', '2026')]:
        e = eq[a:b]
        if len(e) > 200: r[nombre] = (e.iloc[-1] / e.iloc[0] - 1)
    return r

RES = []

def probar(nombre, A, B, rA, rB, senal, invertir=False):
    idx = rA.dropna().index.intersection(rB.dropna().index).intersection(senal.dropna().index)
    idx = idx[idx >= '2018-01-01']
    senal_full = senal.dropna()
    rA, rB = rA[idx], rB[idx]
    base, _ = simular(rA, rB, pd.Series(0.5, idx))
    sA, _ = simular(rA, rB, pd.Series(1.0, idx)); sB, _ = simular(rA, rB, pd.Series(0.0, idx))
    mb = metricas(base)
    filas = []
    for w, k, sal in itertools.product([90, 180, 365], [1.0, 1.5, 2.0], ['opuesto', 'media']):
        z = zscore(senal_full, w).reindex(idx)
        if invertir: z = -z
        eq, turn = simular(rA, rB, pesos_rotacion(z, k, sal))
        m = metricas(eq); t = tramos(eq); tb = tramos(base)
        filas.append(dict(prueba=nombre, ventana=w, umbral=k, salida=sal, **m,
                          vs_base_total=(eq.iloc[-1] / base.iloc[-1]) - 1,
                          gana_tramos=sum(t[x] > tb[x] for x in t), rotaciones=round(turn, 1)))
    df = pd.DataFrame(filas)
    RES.append(dict(prueba=nombre, A=A, B=B, desde=str(idx[0].date()), hasta=str(idx[-1].date()),
                    base_50_50=mb, solo_A=metricas(sA), solo_B=metricas(sB),
                    mediana_rejilla=df[['total', 'cagr', 'mdd', 'ratio', 'vs_base_total']].median().to_dict(),
                    pct_rejilla_mejor_ratio_que_base=float((df.ratio > mb['ratio']).mean()),
                    pct_rejilla_gana_ambos_tramos=float((df.gana_tramos == 2).mean()),
                    mejor=df.sort_values('ratio').iloc[-1].to_dict()))
    return df

if __name__ == '__main__':
    btc, eth = c('BTC'), c('ETH')
    rb, re = btc.pct_change(), eth.pct_change()
    tablas = []
    # A) ETH (A) contra BTC (B): señal baja -> comprar ETH
    tablas.append(probar('A1 ETH/BTC precio', 'ETH', 'BTC', re, rb, c('ETH_BTC')))
    tablas.append(probar('A2 ETH.D/BTC.D', 'ETH', 'BTC', re, rb, c('dominancia_eth') / c('dominancia_btc')))
    tablas.append(probar('A3 ETH/BTC IMPULSO (al revés)', 'ETH', 'BTC', re, rb, c('ETH_BTC'), invertir=True))
    # B) BTC (A) contra cesta de alts (B): BTC.D baja -> comprar BTC; alta -> alts
    alts = ['ETH', 'BNB', 'XRP', 'ADA', 'LINK', 'SOL']
    ra = pd.concat([c(a).pct_change() for a in alts], axis=1).mean(axis=1, skipna=True)
    tablas.append(probar('B1 BTC.D -> BTC vs cesta alts', 'BTC', 'ALTS', rb, ra, c('dominancia_btc')))
    tablas.append(probar('B2 OTHERS/TOTAL -> BTC vs cesta', 'BTC', 'ALTS', rb, ra,
                         1 / (c('others_fuera_top10') / c('capitalizacion_total'))))
    tablas.append(probar('B3 BTC.D IMPULSO (al revés)', 'BTC', 'ALTS', rb, ra, c('dominancia_btc'), invertir=True))
    # C) USDT.D: A = BTC, B = efectivo (0 %). USDT.D alta -> BTC (señal invertida: alta = comprar A)
    cash = pd.Series(0.0, rb.index)
    tablas.append(probar('C1 USDT.D -> BTC o liquidez', 'BTC', 'LIQUIDEZ', rb, cash, c('dominancia_usdt'), invertir=True))
    tablas.append(probar('C2 USDT.D -> ETH o liquidez', 'ETH', 'LIQUIDEZ', re, cash, c('dominancia_usdt'), invertir=True))
    out = os.path.dirname(os.path.abspath(__file__))
    pd.concat(tablas).to_csv(os.path.join(out, 'rejilla_resultados.csv'), index=False)
    json.dump(RES, open(os.path.join(out, 'resumen.json'), 'w'), indent=1, default=float)
    for r in RES:
        print(f"\n== {r['prueba']}  ({r['desde']} a {r['hasta']})")
        for k in ['base_50_50', 'solo_A', 'solo_B']:
            m = r[k]; print(f"  {k:11s} total {m['total']*100:8.0f}%  cagr {m['cagr']*100:5.1f}%  mdd {m['mdd']*100:5.1f}%  ratio {m['ratio']:.2f}")
        m = r['mediana_rejilla']
        print(f"  MEDIANA    total {m['total']*100:8.0f}%  cagr {m['cagr']*100:5.1f}%  mdd {m['mdd']*100:5.1f}%  ratio {m['ratio']:.2f}  vs50/50 {m['vs_base_total']*100:+.0f}%")
        print(f"  % rejilla mejor ratio que 50/50: {r['pct_rejilla_mejor_ratio_que_base']*100:.0f}%  | gana en ambos tramos: {r['pct_rejilla_gana_ambos_tramos']*100:.0f}%")
        b = r['mejor']; print(f"  mejor: v{b['ventana']} k{b['umbral']} {b['salida']} ratio {b['ratio']:.2f} total {b['total']*100:.0f}%")
