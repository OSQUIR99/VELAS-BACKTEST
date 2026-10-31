# -*- coding: utf-8 -*-
"""Señales nuevas candidatas (31-oct-2026), fijadas ANTES de medir. Todas en futuros (sin el tope de 10.000 $):
  N1 VIX/VXV (YouTube): el VIX vuelve a quedar por debajo del VIX a 3 meses tras estar por encima → largo S&P en la
     apertura siguiente, 9 sesiones. 1 R = 2,5 ATR(14). Stop de seguridad 20 %.
  N2 Martillo 60/5 S&P (YouTube): mecha inferior > 60 % del rango y cuerpo > 5 % → largo en la apertura siguiente; sale en
     la apertura siguiente al primer cierre por encima del máximo del día anterior. 1 R.
  N3 Fin de mes Russell 2000 (YouTube): largo al cierre de la 5.ª sesión antes de la última del mes; sale al cierre de la
     primera sesión del mes siguiente. 0,5 R.
  N4 Fin de mes S&P (misma regla en el S&P). 0,5 R.
  N5 Bono a 10 años (futuro; precios de IEF): E1 en bonos. Precio sobre su media de 200 que sube (20 sesiones), RSI(2) < 10
     → largo al cierre; sale al primer cierre sobre la media de 5 o a las 10 sesiones; stop 2,5 ATR. 1 R.
  N6 Bono a 30 años (futuro; precios de TLT): la misma regla. 1 R.
Datos: velas del repositorio (TradingView) y VIX a 3 meses de la Reserva Federal (VXVCLS, desde dic-2007).
Coste 0,02 % ida y vuelta. Una posición a la vez por señal."""
import sys, os
sys.path.insert(0, '/home/claude/caidas')
import numpy as np, pandas as pd
from cortos import diario, atr_wilder, rsi_wilder
from linea import fred

COSTE = 0.0002
CIERRE_H, APERT_H = 20, 13.5


def run(d, ent, salida, entrada='open', salida_modo='open', stop_fn=None, nombre='', activo='SPX', tam=1.0, bloque='bolsa_eeuu',
        desde='1990-01-01'):
    A = atr_wilder(d).values; O = d.apertura.values; H = d.maximo.values; L = d.minimo.values; C = d.cierre.values; idx = d.index; n = len(d)
    ent = np.asarray(ent, bool) & (idx >= pd.Timestamp(desde))
    ops, dia = [], []; i = 0
    while i < n - 1:
        if ent[i] and A[i] > 0:
            if entrada == 'close': e, ei = C[i], i
            else: e, ei = O[i + 1], i + 1
            risk = 2.5 * A[i]; stop = stop_fn(e, A[i]) if stop_fn else None
            j = ei; lat = []; xp = None
            while j < n:
                if stop is not None and (j > ei or entrada == 'open') and L[j] <= stop:
                    xp = min(stop, O[j]); xd = j; mot = 'stop'; xh = 17; break
                if salida(j, ei):
                    if salida_modo == 'close' or j == n - 1: xp = C[j]; xd = j; xh = CIERRE_H
                    else: xp = O[j + 1]; xd = j + 1; xh = APERT_H
                    mot = 'regla'; break
                lat.append((idx[j], (C[j] - e) / risk)); j += 1
            if xp is None: break
            r = (xp - e - COSTE * e) / risk
            oid = f'{nombre}-{idx[i].strftime("%Y%m%d")}'
            te = idx[ei] + pd.Timedelta(hours=CIERRE_H if entrada == 'close' else APERT_H)
            ops.append(dict(id=oid, familia=nombre, activo=activo, direccion=1, t_senal=idx[i] + pd.Timedelta(hours=CIERRE_H),
                            t_entrada=te, t_salida=idx[xd] + pd.Timedelta(hours=xh), entrada=e, sl_inicial=e - risk, salida=xp,
                            r_bruto=r, tam_R=tam, r_final=r * tam, estrellas=np.nan,
                            mae_R=min([v for _, v in lat] + [r, 0]), mfe_R=max([v for _, v in lat] + [r, 0]), motivo_salida=mot, bloque=bloque))
            for f, v in lat:
                if f < idx[xd]: dia.append(dict(id=oid, fecha=f, r_latente=v * tam))
            dia.append(dict(id=oid, fecha=idx[xd], r_latente=r * tam))
            i = xd if xd > i else i + 1
            continue
        i += 1
    return pd.DataFrame(ops), pd.DataFrame(dia)


def construir(car='/home/claude/caidas/listas_nuevas'):
    os.makedirs(car, exist_ok=True)
    out = {}
    spx = diario('sp500'); rut = diario('russell2000'); ief = diario('ief'); tlt = diario('tlt'); vix = diario('vix').cierre
    vxv = fred('VXVCLS', '2007-01-01'); vxv.index = vxv.index.normalize()
    # N1
    r = (vix / vxv.reindex(vix.index).ffill()).reindex(spx.index)
    ent = ((r < 1) & (r.shift(1) > 1)).fillna(False).values
    out['n1_vixvxv'] = run(spx, ent, lambda j, ei: j - ei >= 8, stop_fn=lambda e, a: e * 0.8, nombre='n1_vixvxv', desde='2008-01-01')
    # N2
    d = spx; rng = (d.maximo - d.minimo).replace(0, np.nan); cuerpo = (d.cierre - d.apertura).abs() / rng
    mecha = (d[['apertura', 'cierre']].min(axis=1) - d.minimo) / rng
    ent = ((mecha > 0.6) & (cuerpo > 0.05)).fillna(False).values; C = d.cierre.values; H = d.maximo.values
    out['n2_martillo'] = run(d, ent, lambda j, ei: j > ei and C[j] > H[j - 1], nombre='n2_martillo')
    # N3 / N4
    for nom, d_, act in (('n3_finmes_rut', rut, 'RUT'), ('n4_finmes_spx', spx, 'SPX')):
        idx = d_.index; per = idx.to_period('M'); s = pd.Series(range(len(idx)), index=idx)
        last = s.groupby(per).max().values; first = s.groupby(per).min().values
        en = np.zeros(len(idx), bool); ex = np.zeros(len(idx), bool)
        for L_ in last:
            if L_ - 5 >= 0: en[L_ - 5] = True
        for F_ in first: ex[F_] = True
        out[nom] = run(d_, en, lambda j, ei, ex=ex: j > ei and ex[j], entrada='close', salida_modo='close', nombre=nom, activo=act, tam=0.5)
    # N5 / N6
    for nom, d_, act in (('n5_bono10', ief, 'IEF'), ('n6_bono30', tlt, 'TLT')):
        c = d_.cierre; m200 = c.rolling(200).mean(); perm = (c > m200) & (m200 > m200.shift(20)); r2 = rsi_wilder(c)
        m5 = c.rolling(5).mean().values; Cc = c.values
        en = (perm & (r2 < 10)).fillna(False).values
        out[nom] = run(d_, en, lambda j, ei, Cc=Cc, m5=m5: (j > ei and Cc[j] > m5[j]) or (j - ei >= 10), entrada='close', salida_modo='close',
                       stop_fn=lambda e, a: e - 2.5 * a, nombre=nom, activo=act, bloque='bonos')
    for nom, (O, D) in out.items():
        O.to_parquet(f'{car}/{nom}.parquet'); D.to_parquet(f'{car}/{nom}_diario.parquet')
    return out


if __name__ == '__main__':
    out = construir()
    eps = [('1990-99', '1990', '2000'), ('2000-09', '2000', '2010'), ('2010-17', '2010', '2018-05-01'), ('2018-26', '2018-05-01', '2027')]
    for nom, (O, D) in out.items():
        u = O.r_bruto; t = O.t_entrada
        txt = ' | '.join(f'{a}: {u[(t >= b) & (t < c)].mean():+.3f} ({((t >= b) & (t < c)).sum()})' for a, b, c in eps)
        w = O[t >= '2018-05-01']
        print(f'{nom:16s} ops {len(O)} · R/op {u.mean():+.3f} · acierto {(u > 0).mean()*100:.0f} % · R/año 2018-26 {w.r_final.sum()/8.47:+.2f} | {txt}')
