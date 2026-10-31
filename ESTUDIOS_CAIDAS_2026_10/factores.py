# -*- coding: utf-8 -*-
"""Factores (métricas) que se conocen ANTES de cada entrada, para buscar qué acompaña a las pérdidas.
F.loc[d] = valor conocido al empezar el día d (calculado con cierres hasta d−1; datos de la Reserva Federal con su
retraso de publicación). Además, métricas propias de la cartera en el momento de cada entrada."""
import sys, json, io, pickle
sys.path.insert(0, '/home/claude/velas-backtest')
import numpy as np, pandas as pd
from cargar import velas, financiacion
from linea import fred

DIAS = pd.date_range('1988-01-01', '2026-10-31', freq='D')


def cierre(n, perp=False):
    """Cierre diario fechado por su SESIÓN: TradingView fecha algunas velas (oro, cobre, dólar, Brent) por su apertura
    de la tarde anterior (21-23 UTC); sumando 6 h antes de quitar la hora, cada vela queda en el día en que cierra.
    (Corrección de la verificación independiente del 28-oct.)"""
    s = velas(n, '1d', perpetuo=perp).cierre.astype(float)
    s.index = (pd.to_datetime(s.index) + pd.Timedelta(hours=6)).normalize(); return s[~s.index.duplicated(keep='last')]


def conocido(s, lag=1):
    """Serie en fechas de cierre → valor conocido al empezar cada día (desde el día siguiente al cierre + lag-1)."""
    s = s.dropna(); s = s[~s.index.duplicated(keep='last')]
    s.index = s.index + pd.Timedelta(days=lag)
    return s.reindex(DIAS.union(s.index)).ffill().reindex(DIAS)


def mm(s, n): return s.rolling(n, min_periods=n).mean()


def construir():
    spx = cierre('sp500'); vix = cierre('vix'); hyg = cierre('hyg'); ief = cierre('ief'); dxy = cierre('dolar_dxy')
    semi = cierre('semiconductores'); amp = cierre('sp500_pct_sobre_media200'); btc = cierre('BTC'); oro = cierre('oro')
    brent = cierre('petroleo_brent'); cobre = cierre('cobre'); ndx = cierre('nasdaq100')
    F = {}
    F['spx_bajo200'] = conocido((spx < mm(spx, 200)).astype(float))
    F['spx_dist200'] = conocido(spx / mm(spx, 200) - 1)
    F['spx_cae5'] = conocido((spx / spx.shift(5) - 1 < -0.03).astype(float))
    F['vix'] = conocido(vix)
    F['vix_alto'] = conocido((vix > 20).astype(float))
    F['vix_salto'] = conocido((vix / vix.shift(5) > 1.3).astype(float))
    vxv = fred('VXVCLS', '2007-01-01')
    F['vix_invertido'] = conocido((vix / vxv.reindex(vix.index).ffill() > 1).astype(float).where(vix.index >= vxv.index[0]), 1)
    hi = hyg / ief.reindex(hyg.index).ffill()
    F['credito_flojo'] = conocido((hi < mm(hi, 50)).astype(float))
    F['dolar_sube'] = conocido((dxy / dxy.shift(20) - 1 > 0.02).astype(float))
    y10 = fred('DGS10', '1985-01-01')
    F['tipos_suben'] = conocido((y10 - y10.shift(20) > 0.30).astype(float), 2)
    rs = semi / spx.reindex(semi.index).ffill()
    F['B21_semis_flojos'] = conocido((rs < mm(rs, 50)).astype(float))
    F['amplitud_baja'] = conocido((amp < 50).astype(float))
    F['btc_bajo200'] = conocido((btc < mm(btc, 200)).astype(float))
    F['btc_cae7'] = conocido((btc / btc.shift(7) - 1 < -0.10).astype(float))
    fd = financiacion('BTC').tasa.astype(float); fd.index = pd.to_datetime(fd.index); fd = fd.resample('D').sum()
    F['financiacion_alta'] = conocido((fd.rolling(7).mean() > 0.0009).astype(float))
    F['oro_bajo200'] = conocido((oro < mm(oro, 200)).astype(float))
    F['petroleo_bajo200'] = conocido((brent < mm(brent, 200)).astype(float))
    cg = cobre / oro.reindex(cobre.index).ffill()
    F['cobre_oro_flojo'] = conocido((cg < mm(cg, 100)).astype(float))
    # línea de liquidez (viernes): vale desde el sábado
    L = pd.read_parquet('/home/claude/caidas/linea.parquet')
    F['liquidez_baja'] = conocido((L.linea < 33).astype(float), 1)
    F['liquidez_cae13'] = conocido((L.linea < L.linea.shift(13)).astype(float), 1)
    F['liquidez_impulso_bajo50'] = conocido((L.impulso < 50).astype(float), 1)
    # calendario: FOMC, IPC (CPI) y empleo (NFP) hoy o en los 2 días siguientes
    ev = json.load(open('/home/claude/velas-backtest/RENTA_FIJA/brutos/bonos_fechas_eventos.json'))
    for k in ('FOMC', 'CPI', 'NFP'):
        fechas = pd.to_datetime(ev[k])
        s = pd.Series(0.0, index=DIAS)
        for f in fechas:
            s.loc[f - pd.Timedelta(days=2): f] = 1.0
        s[DIAS < fechas.min()] = np.nan
        F[f'{k}_cerca'] = s
    F = pd.DataFrame(F)
    return F


def propias(C, s, eq, fam):
    """Métricas de la propia cartera en cada entrada tomada (s > 0)."""
    O = C.O; M = C.M
    k_all = np.flatnonzero(s > 0)
    te = M.t_ent[k_all]; ts = M.t_sal[k_all]
    orden = np.argsort(te)
    k_all = k_all[orden]
    e = eq.copy()
    pico = e.cummax(); dd = (pico - e)
    dd_prev = dd.shift(1).fillna(0)
    filas = {}
    for k in k_all:
        t = M.t_ent[k]; d = pd.Timestamp(t).normalize()
        ab = k_all[(M.t_ent[k_all] < t) & (M.t_sal[k_all] > t)]
        r_ab = sum(s[j] * M.riesgo(j, M.ent_dia[k]) for j in ab)
        mismo = [j for j in ab if fam[j] == fam[k]]
        cerr = k_all[(M.t_sal[k_all] <= t) & (fam[k_all] == fam[k])]
        ult = cerr[np.argsort(M.t_sal[cerr])][-3:] if len(cerr) else []
        racha3 = len(ult) == 3 and all(M.rf[j] < 0 for j in ult)
        rec = k_all[(M.t_ent[k_all] < t) & (M.t_ent[k_all] >= t - np.timedelta64(3, 'D')) & (fam[k_all] == fam[k])]
        filas[k] = dict(caida_cartera=float(dd_prev.get(d, 0.0)), riesgo_abierto=r_ab, n_abiertas=len(ab),
                        abiertas_misma_familia=len(mismo), racha3_perdedora=float(racha3), entradas_3d_familia=len(rec))
    return pd.DataFrame.from_dict(filas, orient='index')


if __name__ == '__main__':
    F = construir()
    F.to_parquet('/home/claude/caidas/factores.parquet')
    print(F.loc['2018-05-01':].mean().round(3).to_string())
