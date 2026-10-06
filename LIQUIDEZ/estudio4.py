# -*- coding: utf-8 -*-
"""Estudio 4: entrada tipo SMC idéntica para todos los casos, para comparar en igualdad de condiciones.
Giro menor (ZigZag 1,5 ATR) que se forma junto a un mínimo mayor pendiente (ZigZag 2,5 ATR):
  barrido  : el giro menor perfora el mínimo mayor (hasta 1,5 ATR)
  doble    : se queda a ±0,2 ATR
  ml_cerca : se queda por encima, a 0,2–1,0 ATR (deja la liquidez debajo)
  sin_nivel: giro menor sin mínimo mayor cerca (referencia)
Entrada: cuando el giro menor se confirma (rotura de estructura menor), orden límite al 50 % del
impulso; stop 0,1 ATR bajo el mínimo; objetivos 2R, 3R o la liquidez opuesta (máximo mayor pendiente).
"""
import numpy as np, pandas as pd
from core import *
from estudio2 import salida, resultado, COM, LEV

ESPERA = 10


def analizar(df, lado='largo', kmen=1.5, kmay=2.5):
    if lado == 'largo':
        h, l, c, o = df.h.values, df.l.values, df.c.values, df.o.values
    else:
        h, l, c, o = -df.l.values, -df.h.values, -df.c.values, -df.o.values
    a = df.atr.values; n = len(c)
    ema = df.ema200.values * (1 if lado == 'largo' else -1)
    base = pd.DataFrame({'h': h, 'l': l, 'atr': a})
    zm = zigzag(base, kmen); zM = zigzag(base, kmay)
    brM = np.array([primer_cruce(l if t == -1 else h, cf + 1, p, t == -1) for p, t, cf in zip(zM.p, zM.t, zM.cf)])
    brM = np.where(brM < 0, n + 10, brM)
    Mi, Mp, Mt, Mc = zM.i.values, zM.p.values, zM.t.values, zM.cf.values
    lowsM = Mt == -1; highsM = Mt == 1
    mi, mp, mt, mc = zm.i.values, zm.p.values, zm.t.values, zm.cf.values
    out = []
    for q in range(1, len(zm)):
        if mt[q] != -1:
            continue
        js, ps, cs = mi[q], mp[q], mc[q]
        jh = mi[q - 1]                       # máximo menor previo: inicio de la aproximación
        A = a[js]
        if cs + 2 >= n or A <= 0:
            continue
        pend = lowsM & (Mc < jh) & (brM >= jh)
        cat = 'sin_nivel'; L = np.nan
        if pend.any():
            Ls = Mp[pend]
            d = (ps - Ls) / A
            ok = (d >= -1.5) & (d <= 1.0)
            if ok.any():
                L = Ls[ok][np.argmin(np.abs(d[ok]))]
                dd = (ps - L) / A
                cat = 'doble' if abs(dd) <= 0.2 else ('barrido' if dd < 0 else 'ml_cerca')
        Hc = h[js:cs + 1].max()
        E = ps + 0.5 * (Hc - ps)
        stop = ps - 0.1 * A
        if E <= stop:
            continue
        R1 = E - stop
        # liquidez opuesta: máximo mayor pendiente más cercano por encima de la entrada
        ph = highsM & (Mc < cs) & (brM > cs) & (Mp > E)
        obj_op = Mp[ph].min() if ph.any() else np.nan
        rec = dict(fecha=df.fecha.iloc[js], js=js, cat=cat, d=(ps - L) / A if not np.isnan(L) else np.nan,
                   tend=np.sign(c[js] - ema[js]), riesgo_pct=R1 / abs(E), R_op=(obj_op - E) / R1 if not np.isnan(obj_op) else np.nan)
        for nom, tp in [('2R', E + 2 * R1), ('3R', E + 3 * R1), ('op', obj_op)]:
            if np.isnan(tp) or tp <= E:
                rec[nom] = np.nan; continue
            fill = -1; pe = E
            for b in range(cs + 1, min(n, cs + 1 + ESPERA)):
                if l[b] <= E:
                    fill = b; pe = min(E, o[b]); break
                if h[b] >= tp:
                    break
            if fill < 0:
                rec[nom] = np.nan; rec['lleno'] = False; continue
            rec['lleno'] = True
            if pe <= stop:
                rec[nom], rec[nom + '_m'] = resultado(pe, stop, stop); continue
            if l[fill] <= stop:
                sal = stop
            else:
                sal, js2, mot = salida(h, l, c, fill + 1, pe, stop, tp, 300)
            rec[nom], rec[nom + '_m'] = resultado(pe, sal, stop)
        out.append(rec)
    return pd.DataFrame(out)


if __name__ == '__main__':
    R = []
    for a_ in ACTIVOS:
        for tf in ['1h', '4h', '1d']:
            df = cargar(a_, tf)
            for lado in ['largo', 'corto']:
                e = analizar(df, lado)
                e['activo'] = a_; e['tf'] = tf; e['lado'] = lado
                R.append(e)
            print(a_, tf, flush=True)
    pd.concat(R, ignore_index=True).to_parquet('ev4.parquet')
