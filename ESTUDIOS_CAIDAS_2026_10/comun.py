# -*- coding: utf-8 -*-
"""Herramientas comunes del estudio «causas de las caídas» (28-oct-2026).
Monta el motor real (velas-backtest/MOTOR) con las listas de GitHub + los cortos reconstruidos, y define la cartera base
vigente (documentos 23 y 25):
  base 5,49 = REBOTE 4H cripto + petróleo + X1/X3 + C10 + SHY + E1 de S&P, Nasdaq y Dow + oro (sin plata, T1/T2,
              E1 sectores ni E1 Russell); freno de racha con la cartera valorada (4 R → × 0,5) y prioridad por descorrelación.
  + CORTO SECTOR y CORTO ÍNDICES CRÉDITO, los dos FUERA del freno (como SHY).
  + CORTO PETRÓLEO en el sitio de la S1: NO se puede rehacer aquí (la nota de escasez necesita la curva de futuros e
    inventarios que no están en esta sesión). Se usan tres versiones de la parte de petróleo para comprobar que las
    conclusiones no dependen de ella: (a) listas originales con la S1, (b) sin la S1, (c) sin nada de petróleo.
OJO: las listas de petróleo corregidas del 27-oct (contrato real) tampoco están aquí: se usan las originales.
"""
import sys, os, glob, tempfile
sys.path.insert(0, '/home/claude/velas-backtest/MOTOR')
import numpy as np
import pandas as pd
import recomendacion as RC
import analisis as A
from motor import metricas

LISTAS_GH = '/home/claude/velas-backtest/MOTOR/listas'
LISTAS_CORTOS = '/home/claude/caidas/listas_cortos'
CORTE = pd.Timestamp('2022-01-01')
HOY = pd.Timestamp('2026-10-20')
FL = dict(freno=(4, 0.5), freno_modo='latente', prioridad='descorr')
IDX = ['SPX', 'DJI', 'NDX']


def mezclar(*carpetas):
    tmp = tempfile.mkdtemp(prefix='caidas_')
    for car in carpetas:
        for p in glob.glob(os.path.join(car, '*.parquet')):
            dst = os.path.join(tmp, os.path.basename(p))
            if not os.path.exists(dst):
                os.symlink(os.path.abspath(p), dst)
    return tmp


def met_eq(eq, a, b=None):
    e = eq[(eq.index >= a) & ((eq.index < b) if b is not None else (eq.index <= HOY + pd.Timedelta(days=1)))]
    e = e - e.iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e.cummax() - e).max())
    ra = float(e.iloc[-1] / yrs)
    return dict(R_ano=ra, caida=dd, ratio=ra / dd if dd > 0 else np.nan)


class Cartera:
    def __init__(self, extra=(LISTAS_CORTOS,)):
        self.tmp = mezclar(LISTAS_GH, *extra)
        O, D, M = RC.preparar(self.tmp)
        self.O, self.D, self.M = O, D, M
        L = O.lista.values; act = O.activo.astype(str).values
        self.L, self.act = L, act
        self.desde = A.inicio_ventana(O)
        self.W = O.en_cartera.values & (O.t_entrada >= self.desde).values & (L != 'acciones_v2')
        E1 = (L == 'bolsa_e1') & np.isin(act, IDX)
        self.e1 = E1 & self.W
        self.base549 = (np.isin(L, ['cripto', 'petroleo', 'x_petroleo', 'c10', 'shy']) | E1 | ((L == 'metales') & (act == 'oro'))) & self.W
        sen = O['senal'].astype(str).values if 'senal' in O.columns else np.array([''] * len(O))
        self.senal = sen
        self.s1 = (L == 'petroleo') & (sen == 'S1')
        self.pet = (L == 'petroleo') & self.W
        self.c_sector = (L == 'corto_sector') & (O.t_entrada >= self.desde).values
        self.c_indices = (L == 'corto_indices_credito') & (O.t_entrada >= self.desde).values
        self.cortos_exentos = self.c_sector | self.c_indices
        self.sf0 = self.M.sin_freno.copy()
        # 31-oct: tope de 10.000 $ por fondo de renta fija (SHY en tres tercios de 3.333 $, 1 R = 301 $; la distancia
        # al stop incluye el hueco, como su regla de tamaño) y cortos de bolsa a doble tamaño (instrucción «cortos x2»).
        self.tam_base = np.ones(len(O))
        shy = (L == 'shy')
        dist = ((O.entrada - O.sl_inicial) / O.entrada).values + (O['hueco'].fillna(0).values if 'hueco' in O.columns else 0)
        r_cap = 3333.0 * dist / 301.0
        self.tam_base[shy] = np.minimum(1.0, r_cap[shy] / O.tam_R.values[shy])
        self.tam_base[self.c_sector | self.c_indices] = 2.0
        self.usar_base_31oct = True
        # tres versiones de la cartera base vigente
        self.bases = {
            'a · con S1 (listas originales)': self.base549 | self.cortos_exentos,
            'b · sin S1': (self.base549 & ~self.s1) | self.cortos_exentos,
            'c · sin petróleo': (self.base549 & ~self.pet) | self.cortos_exentos,
        }

    def sim(self, mascara, cfg=None, exentas=None, tam_mult=None, mult=1.0, M=None):
        M = M or self.M
        c = dict(FL if cfg is None else cfg)
        c['mult'] = mult
        tb = self.tam_base if getattr(self, 'usar_base_31oct', False) else None
        if tam_mult is not None or tb is not None:
            c['tam_mult'] = (tam_mult if tam_mult is not None else 1.0) * (tb if tb is not None else 1.0)
        ex = self.cortos_exentos if exentas is None else exentas
        sf = M.sin_freno.copy()
        M.sin_freno = sf | ex
        try:
            rr = M.simular(c, mascara=mascara)
            eq = M.curva(rr.s)
        finally:
            M.sin_freno = sf
        return rr, eq

    def met3(self, eq):
        return [met_eq(eq, self.desde), met_eq(eq, self.desde, CORTE), met_eq(eq, CORTE)]

    @staticmethod
    def fmt(q):
        return (' / '.join(f"{x['ratio']:.2f}" for x in q) +
                f" | R/año {q[0]['R_ano']:.1f} ({q[1]['R_ano']:.1f}/{q[2]['R_ano']:.1f}) | caída {q[0]['caida']:.1f} ({q[1]['caida']:.1f}/{q[2]['caida']:.1f})")

    @staticmethod
    def pasa(q, ref):
        return all(q[i]['ratio'] > ref[i]['ratio'] and q[i]['R_ano'] > ref[i]['R_ano'] for i in range(3))

    def mensual(self, eq):
        return eq[(eq.index >= self.desde) & (eq.index <= HOY)].resample('ME').last().diff().dropna()

    def bootstrap(self, eq_ref, eq_new, n=1000, semilla=7):
        mb = self.mensual(eq_ref); mn = self.mensual(eq_new).reindex(mb.index).fillna(0)
        rng = np.random.default_rng(semilla); g = 0
        def rt(x):
            cc = np.cumsum(x); dd = np.max(np.maximum.accumulate(np.r_[0, cc])[1:] - cc); return cc[-1] / max(dd, 1e-9)
        for _ in range(n):
            i = rng.integers(0, len(mb), len(mb)); g += rt(mn.values[i]) > rt(mb.values[i])
        return g / n

    def media5(self, eq):
        e = eq[(eq.index >= self.desde) & (eq.index <= HOY)].values
        pk = np.maximum.accumulate(e); dd = pk - e
        res, i = [], 0
        while i < len(e):
            if dd[i] > 0:
                j = i
                while j < len(e) and dd[j] > 0:
                    j += 1
                res.append(dd[i:j].max()); i = j
            else:
                i += 1
        res = sorted(res, reverse=True)
        return float(np.mean(res[:5])), res[:5]
