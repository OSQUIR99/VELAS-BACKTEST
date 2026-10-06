# -*- coding: utf-8 -*-
"""Estudio 1: qué pasa después de un mínimo (o máximo) según cómo se relaciona con el anterior.
Categorías (para mínimos; los máximos se tratan en espejo):
  ruptura    : el nuevo mínimo perfora el anterior más de 1/3 del rango (caída fuerte que luego gira)
  barrido    : perfora el anterior (>0,2 ATR) pero menos de 1/3 del rango
  doble      : rebota en el mismo punto (±0,2 ATR)
  ml_extremo : mínimo más alto, pero en el tercio inferior del rango (compresión, deja liquidez debajo)
  ml_alto    : mínimo más alto en la mitad/tercio superior (retroceso corto en tendencia)
"""
import numpy as np, pandas as pd, sys
from core import *

TOL = 0.2


def eventos(df, k=2.5, lado='largo'):
    h, l, c = df.h.values, df.l.values, df.c.values
    if lado == 'corto':  # espejo: un máximo pasa a ser un mínimo
        h, l, c = -df.l.values, -df.h.values, -df.c.values
    a = df.atr.values; ema = df.ema200.values
    if lado == 'corto':
        ema = -ema
    z = zigzag(pd.DataFrame({'h': h, 'l': l, 'atr': a}), k)
    zi, zp, zt, zc = z.i.values, z.p.values, z.t.values, z.cf.values
    n = len(c); out = []
    for p in range(2, len(z) - 1):
        if zt[p] != -1:
            continue
        Lp, H1, Ln, H2 = zp[p - 2], zp[p - 1], zp[p], zp[p + 1]
        j, cf, jh = zi[p], zc[p], zi[p + 1]
        A = a[j]
        if A <= 0 or H1 <= Lp:
            continue
        rng = H1 - Lp
        pos = (Ln - Lp) / rng
        if abs(Ln - Lp) <= TOL * A:
            cat = 'doble'
        elif Ln < Lp:
            cat = 'barrido' if pos >= -1/3 else 'ruptura'
        else:
            cat = 'ml_extremo' if pos <= 1/3 else 'ml_alto'
        # --- tramo siguiente (descriptivo, mirando el giro siguiente) ---
        leg_atr = (H2 - Ln) / A
        leg_pct = abs(H2 - Ln) / abs(Ln)
        leg_bars = jh - j
        rompe = H2 > H1
        ext = (H2 - Ln) / (H1 - Ln) if H1 > Ln else np.nan
        er = eficiencia(c, j, jh)
        hl_sig = (zp[p + 2] > Ln) if p + 2 < len(z) else np.nan
        # máximos crecientes consecutivos (estructura alcista sana)
        s = 0; q = p + 1
        while q < len(z):
            if zp[q] > zp[q - 2]:
                s += 1
            else:
                break
            if q + 1 < len(z) and zp[q + 1] > zp[q - 1]:
                q += 2
            else:
                break
        # tendencia completa: hasta el primer mínimo más bajo (rotura de estructura)
        q = p + 2; mx = H2; mx_i = jh; fin_ok = False
        while q < len(z):
            if zp[q] < zp[q - 2]:
                fin_ok = True; break
            if q + 1 < len(z) and zp[q + 1] > mx:
                mx = zp[q + 1]; mx_i = zi[q + 1]
            q += 2
        tend_atr = (mx - Ln) / A; tend_pct = abs(mx - Ln) / abs(Ln); tend_bars = mx_i - j
        # --- operable: entrada al confirmarse el giro ---
        ent = c[cf]; stop = Ln - 0.1 * A
        if H1 > ent and ent > stop:
            res, jj = carrera(h, l, cf + 1, H1, stop, 2000)
            R_obj = (H1 - ent) / (ent - stop)
        else:
            res, jj, R_obj = np.nan, -1, np.nan
        f = {}
        for hz in (10, 20, 50, 100):
            f[f'f{hz}'] = (c[cf + hz] - ent) / A if cf + hz < n else np.nan
        W = 100
        if j >= W:
            mxw, mnw = h[j - W:j + 1].max(), l[j - W:j + 1].min()
            lateral = abs(c[j] - c[j - W]) / (mxw - mnw)
            posw = (Ln - mnw) / (mxw - mnw)
        else:
            lateral = posw = np.nan
        out.append(dict(
            fecha=df.fecha.iloc[j], j=j, cf=cf, cat=cat, d_atr=(Ln - Lp) / A, pos=pos,
            rango_atr=rng / A, mecha=(c[j] > Lp) if cat == 'barrido' else np.nan,
            leg_atr=leg_atr, leg_pct=leg_pct, leg_bars=leg_bars, rompe=rompe, ext=ext, er=er,
            hl_sig=hl_sig, hh_seguidos=s, tend_atr=tend_atr, tend_pct=tend_pct, tend_bars=tend_bars,
            tend_cerrada=fin_ok, res=res, R_obj=R_obj, ent=ent, stop_pct=abs(ent - stop) / abs(ent),
            obj_pct=abs(H1 - ent) / abs(ent), conf_atr=(ent - Ln) / A,
            tendencia=np.sign(c[j] - ema[j]), lateral=lateral, posw=posw, **f))
    return pd.DataFrame(out)


if __name__ == '__main__':
    filas = []
    for a in ACTIVOS:
        for tf in ['1h', '4h', '1d']:
            df = cargar(a, tf)
            for k in [1.5, 2.5, 4.0]:
                for lado in ['largo', 'corto']:
                    e = eventos(df, k, lado)
                    e['activo'] = a; e['tf'] = tf; e['k'] = k; e['lado'] = lado
                    filas.append(e)
            print(a, tf, flush=True)
    ev = pd.concat(filas, ignore_index=True)
    ev.to_parquet('ev1.parquet')
    print(len(ev))
