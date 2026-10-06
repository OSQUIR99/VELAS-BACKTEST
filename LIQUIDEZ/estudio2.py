# -*- coding: utf-8 -*-
"""Estudio 2 y 3: vida de los niveles pendientes y qué pasa cuando el precio los toca.
Se trabaja con mínimos (liquidez de largos: stops y liquidaciones de largos debajo).
Los máximos se tratan en espejo (precios con signo cambiado), así que todo el código es para mínimos.
"""
import numpy as np, pandas as pd
from core import *

M = 1.5         # carrera de giro/continuación: ±1,5 ATR desde el nivel
TOQUE = 0.3     # niveles a menos de 0,3 ATR se consideran el mismo "suelo"
COM = 0.0005    # comisión por lado (0,05 %)
LEV = 20
LIQ = 1 / LEV - 0.005   # distancia aproximada al precio de liquidación con 20x


def rsi(c, n=14):
    d = np.diff(c, prepend=c[0])
    up = pd.Series(np.clip(d, 0, None)).ewm(alpha=1/n, adjust=False).mean()
    dn = pd.Series(np.clip(-d, 0, None)).ewm(alpha=1/n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).fillna(50).values


@njit(cache=True)
def salida(h, l, c, desde, ent, stop, tp, maxb):
    """Simula un largo desde la barra 'desde' (incluida). Devuelve (precio de salida, barra, motivo)."""
    n = len(h)
    fin = min(n - 1, desde + maxb)
    for j in range(desde, fin + 1):
        if l[j] <= stop:
            return stop, j, -1
        if h[j] >= tp:
            return tp, j, 1
    return c[fin], fin, 0


def resultado(ent, sal, stop):
    """R neto de comisiones y rentabilidad sobre margen con 20x (liquidación si el stop está más lejos)."""
    riesgo = ent - stop
    pnl = (sal - ent) / abs(ent)
    R = (sal - ent) / riesgo - 2 * COM * abs(ent) / riesgo
    if riesgo / abs(ent) > LIQ and sal <= stop:
        marg = -1.0
    else:
        marg = max(-1.0, LEV * (pnl - 2 * COM))
    return R, marg


def analizar(df, k=2.5, lado='largo', semilla=0):
    h0, l0, c0 = df.h.values, df.l.values, df.c.values
    sg = 1 if lado == 'largo' else -1
    if lado == 'largo':
        h, l, c, o = h0, l0, c0, df.o.values
    else:
        h, l, c, o = -l0, -h0, -c0, -df.o.values
    a = df.atr.values; a50 = df.atr50.values; ema = sg * df.ema200.values
    v = df.v.values.astype(float)
    rs = rsi(c)
    n = len(c)
    z = zigzag(pd.DataFrame({'h': h, 'l': l, 'atr': a}), k)
    zi, zp, zt, zc = z.i.values, z.p.values, z.t.values, z.cf.values
    # rotura de cada giro: mínimos se rompen por debajo, máximos por encima
    br = np.full(len(z), -1, np.int64)
    for q in range(len(z)):
        br[q] = primer_cruce(l if zt[q] == -1 else h, zc[q] + 1, zp[q], zt[q] == -1)
    brx = np.where(br < 0, n + 10, br)
    lows = np.where(zt == -1)[0]; highs = np.where(zt == 1)[0]
    rng = np.random.default_rng(semilla)
    ev = []
    for qi, q in enumerate(lows):
        L = zp[q]; j = zi[q]; cf = zc[q]; t = br[q]
        # ¿lo dejó pendiente un mínimo más alto? (el siguiente mínimo quedó por encima)
        sig = q + 2
        dejado = (sig < len(z)) and (zp[sig] > L + 0.2 * a[zi[sig]]) and (zc[sig] < brx[q])
        rec = dict(fecha=df.fecha.iloc[j], j=j, cf=cf, nivel=L, roto=t >= 0,
                   espera=(t - cf) if t >= 0 else (n - 1 - cf), edad=(t - j) if t >= 0 else np.nan,
                   dist_conf=(c[cf] - L) / a[cf], dejado=dejado, tendencia_conf=(c[cf] - ema[cf]) / a[cf])
        if t < 0 or t < 12:
            ev.append(rec); continue
        A = a[t - 1]
        # --- rasgos ANTES de la vela de rotura (información disponible para anticipar) ---
        pend_l = (zc[lows] < t) & (brx[lows] >= t)         # mínimos pendientes justo antes de t (incluye este)
        Ls = zp[lows][pend_l]
        n_toq = int((np.abs(Ls - L) <= TOQUE * A).sum())
        mas_alla = Ls[(Ls < L - TOQUE * A)]
        dist_sig = (L - mas_alla.max()) / A if len(mas_alla) else 50.0
        pend_h = (zc[highs] < t) & (brx[highs] > t)
        Hs = zp[highs][pend_h]
        Hs_arriba = Hs[Hs > c[t - 1]]
        dist_opuesto = (Hs_arriba.min() - L) / A if len(Hs_arriba) else np.nan
        obj_opuesto = Hs_arriba.min() if len(Hs_arriba) else np.nan
        # último máximo confirmado antes de t: tramo de aproximación
        hh = highs[(zc[highs] < t)]
        if len(hh):
            ultH = hh[-1]
            aprox_tramo = (zp[ultH] - L) / A; aprox_barras = t - zi[ultH]
            prev3 = zp[hh[-3:]]
            presion = int(np.sum(np.diff(prev3) < 0)) if len(prev3) >= 2 else 0  # máximos decrecientes hacia el nivel
        else:
            aprox_tramo = aprox_barras = np.nan; presion = 0
        # mínimos crecientes previos (cuántos mínimos más altos se apilaron sobre el nivel antes de volver)
        ll = lows[(zc[lows] < t) & (zi[lows] > j)]
        apilados = int(len(ll))
        vel = (c[t - 1] - c[t - 11]) / A
        compr = a[t - 1] / a50[t - 1]
        tend = (c[t - 1] - ema[t - 1]) / A
        vol = v[t - 1] / v[t - 21:t - 1].mean() if v[t - 21:t - 1].mean() > 0 else np.nan
        # --- lo que ocurre en la vela de rotura (confirmación al cierre) ---
        prof = (L - l[t]) / A
        cierra_dentro = c[t] > L
        gap = o[t] < L
        # --- carrera ±1,5 ATR desde el nivel ---
        if l[t] <= L - M * A:
            res, jr = -1, t
        elif c[t] >= L + M * A:
            res, jr = 1, t
        else:
            res, jr = carrera(h, l, t + 1, L + M * A, L - M * A, 500)
        # máximo recorrido a favor del giro en 50 velas tras la rotura (desde el nivel)
        fin = min(n, t + 51)
        mfe50 = (h[t:fin].max() - L) / A
        mae50 = (L - l[t:fin].min()) / A
        # ¿el giro llega a la liquidez opuesta antes de hacer nuevo mínimo por debajo del barrido?
        llega_opuesto = np.nan
        if not np.isnan(obj_opuesto):
            r2, _ = carrera(h, l, t + 1, obj_opuesto, l[t] - 0.1 * A, 2000)
            llega_opuesto = r2
        rec.update(dict(t=t, A=A, n_toques=n_toq, dist_sig=dist_sig, dist_opuesto=dist_opuesto,
                        aprox_tramo=aprox_tramo, aprox_barras=aprox_barras, presion=presion, apilados=apilados,
                        vel=vel, compr=compr, tend=tend, vol=vol, rsi=rs[t - 1], prof=prof,
                        cierra_dentro=cierra_dentro, gap=gap, res=res, barras_res=jr - t, mfe50=mfe50, mae50=mae50,
                        llega_opuesto=llega_opuesto))
        # --- estrategias ---
        # E1 anticipar: límite en el nivel, stop 1 ATR debajo, objetivo 2R
        ent = L; stop = L - A
        if gap:
            ent = o[t]
        if ent > stop:
            if l[t] <= stop:
                sal, js, mot = stop, t, -1
            else:
                sal, js, mot = salida(h, l, c, t + 1, ent, stop, ent + 2 * (ent - stop), 200)
            rec['E1_R'], rec['E1_m'] = resultado(ent, sal, stop)
        # E2 confirmar (barrido con cierre de vuelta dentro en ≤3 velas): stop bajo la mecha, objetivo 2R
        u = -1
        for x in range(t, min(n, t + 4)):
            if l[x] <= L - M * A and c[x] <= L:
                break
            if c[x] > L:
                u = x; break
        if u >= 0 and u + 1 < n:
            ent = c[u]; stop = l[t:u + 1].min() - 0.1 * A
            sal, js, mot = salida(h, l, c, u + 1, ent, stop, ent + 2 * (ent - stop), 200)
            rec['E2_R'], rec['E2_m'] = resultado(ent, sal, stop)
            rec['E2_stop_pct'] = (ent - stop) / abs(ent)
            rec['E2_u'] = u - t
            # E2b: mismo, pero objetivo la liquidez opuesta (máximo pendiente más cercano)
            if not np.isnan(obj_opuesto) and obj_opuesto > ent:
                sal, js, mot = salida(h, l, c, u + 1, ent, stop, obj_opuesto, 500)
                rec['E2b_R'], rec['E2b_m'] = resultado(ent, sal, stop)
                rec['E2b_Robj'] = (obj_opuesto - ent) / (ent - stop)
        # E3 ruptura: la vela cierra fuera (por debajo) -> corto al cierre, stop 0,5 ATR por encima del nivel, 2R
        if c[t] < L and t + 1 < n:
            # corto = largo en el espejo
            hh_, ll_, cc_ = -l, -h, -c
            ent = -c[t]; stop = -(L + 0.5 * A)
            if ent > stop:
                sal, js, mot = salida(hh_, ll_, cc_, t + 1, ent, stop, ent + 2 * (ent - stop), 200)
                rec['E3_R'], rec['E3_m'] = resultado(ent, sal, stop)
        ev.append(rec)
    out = pd.DataFrame(ev)
    # --- control: niveles al azar (misma lógica, sin giro detrás) ---
    ctrl = []
    for _ in range(len(lows)):
        s = int(rng.integers(250, n - 50))
        Lc = c[s] - rng.uniform(1.0, 6.0) * a[s]
        t = primer_cruce(l, s + 1, Lc, True)
        if t < 0 or t < 12:
            continue
        A = a[t - 1]
        if l[t] <= Lc - M * A:
            res = -1
        elif c[t] >= Lc + M * A:
            res = 1
        else:
            res, _ = carrera(h, l, t + 1, Lc + M * A, Lc - M * A, 500)
        fin = min(n, t + 51)
        # también la estrategia "confirmar" sobre niveles al azar
        u = -1
        for x in range(t, min(n, t + 4)):
            if l[x] <= Lc - M * A and c[x] <= Lc:
                break
            if c[x] > Lc:
                u = x; break
        e2 = np.nan
        if u >= 0 and u + 1 < n:
            ent = c[u]; stop = l[t:u + 1].min() - 0.1 * A
            sal, js, mot = salida(h, l, c, u + 1, ent, stop, ent + 2 * (ent - stop), 200)
            e2 = resultado(ent, sal, stop)[0]
        ctrl.append(dict(res=res, cierra_dentro=c[t] > Lc, prof=(Lc - l[t]) / A,
                         mfe50=(h[t:fin].max() - Lc) / A, E2_R=e2))
    return out, pd.DataFrame(ctrl)


if __name__ == '__main__':
    import sys
    E, C = [], []
    for a_ in ACTIVOS:
        for tf in ['1h', '4h', '1d']:
            df = cargar(a_, tf)
            for k in [1.5, 2.5, 4.0]:
                for lado in ['largo', 'corto']:
                    e, ct = analizar(df, k, lado, semilla=hash((a_, tf, k, lado)) % 2**31)
                    for x in (e, ct):
                        x['activo'] = a_; x['tf'] = tf; x['k'] = k; x['lado'] = lado
                    E.append(e); C.append(ct)
            print(a_, tf, flush=True)
    pd.concat(E, ignore_index=True).to_parquet('ev2.parquet')
    pd.concat(C, ignore_index=True).to_parquet('ctrl2.parquet')
