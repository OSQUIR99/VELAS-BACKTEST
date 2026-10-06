# -*- coding: utf-8 -*-
"""Estudio de desequilibrio de liquidez pendiente y prueba del 'imán'.
Cada N velas: niveles pendientes por encima (máximos sin barrer) y por debajo (mínimos sin barrer).
- ¿Se toca antes el lado con más liquidez acumulada de lo que diría el azar (paseo aleatorio)?
- ¿El desequilibrio predice la dirección de las 50 velas siguientes?
También: tras un mínimo más alto en el extremo, ¿barren antes el mínimo pendiente o llegan al techo?
"""
import numpy as np, pandas as pd
from core import *

PASO = 10


def niveles(df, k=2.5):
    z = zigzag(df, k)
    n = len(df); h, l = df.h.values, df.l.values
    br = np.array([primer_cruce(l if t == -1 else h, cf + 1, p, t == -1) for p, t, cf in zip(z.p, z.t, z.cf)])
    z['br'] = np.where(br < 0, n + 10, br)
    return z


def muestreo(df, k=2.5):
    z = niveles(df, k)
    h, l, c, a, ema = df.h.values, df.l.values, df.c.values, df.atr.values, df.ema200.values
    n = len(c)
    Hz = z[z.t == 1]; Lz = z[z.t == -1]
    hp, hcf, hbr = Hz.p.values, Hz.cf.values, Hz.br.values
    lp, lcf, lbr = Lz.p.values, Lz.cf.values, Lz.br.values
    out = []
    for s in range(300, n - 60, PASO):
        A = a[s]
        mh = (hcf < s) & (hbr > s) & (hp > c[s]); ml = (lcf < s) & (lbr > s) & (lp < c[s])
        if not mh.any() or not ml.any():
            continue
        up = hp[mh]; dn = lp[ml]
        du = (up.min() - c[s]) / A; dd = (c[s] - dn.max()) / A
        nu5 = int(((up - c[s]) / A <= 5).sum()); nd5 = int(((c[s] - dn) / A <= 5).sum())
        nu10 = int(((up - c[s]) / A <= 10).sum()); nd10 = int(((c[s] - dn) / A <= 10).sum())
        # racimo junto al nivel más cercano (niveles a menos de 0,5 ATR del más cercano)
        cu = int(((up - up.min()) / A <= 0.5).sum()); cd = int(((dn.max() - dn) / A <= 0.5).sum())
        res, jr = carrera(h, l, s + 1, up.min(), dn.max(), 3000)
        f50 = (c[s + 50] - c[s]) / A
        out.append(dict(s=s, du=du, dd=dd, nu5=nu5, nd5=nd5, nu10=nu10, nd10=nd10, cu=cu, cd=cd,
                        res=res, barras=jr - s, f50=f50, tend=np.sign(c[s] - ema[s]),
                        p_azar=dd / (du + dd)))
    return pd.DataFrame(out)


if __name__ == '__main__':
    R = []
    for a_ in ACTIVOS:
        for tf in ['1h', '4h', '1d']:
            df = cargar(a_, tf)
            m = muestreo(df)
            m['activo'] = a_; m['tf'] = tf
            R.append(m); print(a_, tf, len(m), flush=True)
    pd.concat(R, ignore_index=True).to_parquet('ev3.parquet')
