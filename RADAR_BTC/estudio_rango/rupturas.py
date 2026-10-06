# -*- coding: utf-8 -*-
"""Cada ruptura bajista de un rango (cierre de 4 h bajo el suelo): qué la acompañaba y qué pasó después."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

def episodios(D, etiqueta):
    c, l, h, v = D.c.values, D.l.values, D.h.values, D.v.values
    tb = D.taker_buy_v.values
    T, S = D.techo.values, D.suelo.values
    n = len(D); vistos = set(); filas = []
    vmed = pd.Series(v).rolling(60).median().values
    for i in np.where(~np.isnan(T))[0]:
        a, b = S[i], T[i]
        for j in range(i + 1, min(i + 61, n)):
            if c[j] > b: break
            if c[j] < a:
                if j in vistos: break
                vistos.add(j); w = b - a
                fin = min(j + 31, n); mn = l[j:fin].min()
                recupera = bool((c[j + 1:min(j + 7, n)] > a).any())
                dos = bool(j + 1 < n and c[j + 1] < a)
                filas.append(dict(fecha=D.index[j], rango=etiqueta, suelo=a, techo=b, ancho=w / ((a + b) / 2),
                                  prof=(a - c[j]) / w, delta_vela=(2 * tb[j] - v[j]) / v[j],
                                  delta_3v=(2 * tb[j - 2:j + 1].sum() - v[j - 2:j + 1].sum()) / v[j - 2:j + 1].sum(),
                                  vol_rel=v[j] / vmed[j] if vmed[j] else np.nan, dos_cierres=dos,
                                  recupera_24h=recupera, sigue_anchos=(a - mn) / w, caida_5d=mn / a - 1,
                                  caida_10d=l[j:min(j + 61, n)].min() / a - 1))
                break
    R = pd.DataFrame(filas).set_index('fecha').sort_index()
    R['real'] = (~R.recupera_24h) & (R.sigue_anchos >= 0.5)
    return R

def auc(x, y):
    m = x.notna() & y.notna()
    return roc_auc_score(y[m], x[m]) if m.sum() > 40 and y[m].nunique() > 1 else np.nan

if __name__ == '__main__':
    RH = pd.read_parquet('radar_historico.parquet')[['total', 'macro']].shift(1)
    out = []
    for fn, et in [('rangos_4h.parquet', 'mayor'), ('rangos_menores_4h.parquet', 'menor')]:
        D = pd.read_parquet(fn)
        R = episodios(D, et)
        R = R.join(RH.reindex(R.index.normalize()).set_index(R.index))
        out.append(R)
        print(f'\n=== RANGO {et.upper()}: {len(R)} rupturas bajistas; reales {R.real.mean()*100:.0f} %; caída mediana a 5 días {R.caida_5d.median()*100:.1f} %, a 10 días {R.caida_10d.median()*100:.1f} %')
        for k in ['delta_vela', 'delta_3v', 'vol_rel', 'prof', 'total', 'macro']:
            q = pd.qcut(R[k], 3, labels=['bajo', 'medio', 'alto'], duplicates='drop')
            g = R.groupby(q, observed=False)
            print(f'  {k:10s} AUC {auc(R[k], R.real.astype(float)):.2f} | 17-21 {auc(R.loc[:"2021", k], R.loc[:"2021", "real"].astype(float)):.2f} · 22-26 {auc(R.loc["2022":, k], R.loc["2022":, "real"].astype(float)):.2f} | real por tercio',
                  g.real.mean().round(2).to_dict(), '| caída 5 d', (g.caida_5d.median() * 100).round(1).to_dict())
        m = R.dos_cierres
        print(f'  Dos cierres de 4 h seguidos bajo el suelo: {m.mean()*100:.0f} % de las rupturas -> caída mediana 5 d {R.loc[m,"caida_5d"].median()*100:.1f} % y 10 d {R.loc[m,"caida_10d"].median()*100:.1f} %; recupera después {R.loc[m,"recupera_24h"].mean()*100:.0f} %')
        print(f'  Sin el segundo cierre: caída mediana 5 d {R.loc[~m,"caida_5d"].median()*100:.1f} %')
        fuerte = (R.delta_vela < -0.10) & (R.vol_rel > 1.5)
        print(f'  Vela de ruptura con ventas agresivas fuertes (delta < -10 % y volumen > 1,5x): n {fuerte.sum()}, real {R.loc[fuerte,"real"].mean()*100:.0f} % vs {R.loc[~fuerte,"real"].mean()*100:.0f} %')
        hostil = R.total >= 52
        print(f'  Con el radar diario en naranja o rojo: n {hostil.sum()}, real {R.loc[hostil,"real"].mean()*100:.0f} % vs {R.loc[~hostil,"real"].mean()*100:.0f} %; caída 10 d {R.loc[hostil,"caida_10d"].median()*100:.1f} % vs {R.loc[~hostil,"caida_10d"].median()*100:.1f} %')
    pd.concat(out).to_csv('rupturas_bajistas_4h.csv')
