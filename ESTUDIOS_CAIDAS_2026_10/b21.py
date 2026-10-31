# -*- coding: utf-8 -*-
"""B21 (semiconductores peor que el S&P 500 en 50 sesiones) sobre la cartera base vigente con cortos.
B21 al cierre del día t (SMH ÷ S&P bajo su media de 50) vale para las entradas desde el día t+1."""
import sys, pickle, time
sys.path.insert(0, '/home/claude/velas-backtest')
import numpy as np, pandas as pd
from cargar import velas
from comun import Cartera, CORTE, HOY


def cierre(n):
    s = velas(n, '1d').cierre.astype(float); s.index = (pd.to_datetime(s.index) + pd.Timedelta(hours=6)).normalize()
    return s[~s.index.duplicated(keep='last')]


def serie_b21(n=50):
    semi = cierre('semiconductores'); spx = cierre('sp500')
    rs = semi / spx.reindex(semi.index).ffill()
    on = rs < rs.rolling(n).mean()
    dias = pd.date_range('2000-01-01', '2026-10-31', freq='D')
    b = on.astype(float).reindex(dias.union(on.index)).ffill()
    b = b.shift(1, freq='D').reindex(dias).ffill().fillna(0).astype(bool)   # vale desde el día siguiente
    return b


def afectadas(C, serie, ambito):
    dia = C.O.t_entrada.dt.normalize()
    on = serie.reindex(dia).fillna(False).values.astype(bool)
    return ambito & on


def ambitos(C):
    largo = C.O.direccion.values == 1
    L = C.L
    no_cri = (L != 'cripto') & (L != 'shy') & ~np.isin(L, ['corto_sector', 'corto_indices_credito'])
    return {'resto (todo menos cripto, SHY y cortos)': no_cri & largo,
            'solo E1': C.e1 & largo,
            'E1 + C10': (C.e1 | (L == 'c10')) & largo,
            'resto sin oro': no_cri & largo & ~((L == 'metales')),
            'resto sin petróleo': no_cri & largo & ~np.isin(L, ['petroleo', 'x_petroleo'])}


if __name__ == '__main__':
    t0 = time.time()
    C = Cartera()
    B21 = serie_b21()
    AMB = ambitos(C)
    filas = []
    for nb, base in C.bases.items():
        rr, eqb = C.sim(base); qb = C.met3(eqb); m5b, _ = C.media5(eqb)
        filas.append(dict(base=nb, variante='BASE', **{f'r{i}': qb[i]['ratio'] for i in range(3)},
                          Ra=qb[0]['R_ano'], caida=qb[0]['caida'], media5=m5b, pasa=None, boot=None))
        print(nb, 'BASE', C.fmt(qb), flush=True)
        for na, amb in AMB.items():
            af = afectadas(C, B21, amb & base)
            for modo in ('mitad', 'bloquear'):
                if modo == 'mitad':
                    rr, eq = C.sim(base, tam_mult=np.where(af, 0.5, 1.0))
                else:
                    rr, eq = C.sim(base & ~af)
                q = C.met3(eq); m5, _ = C.media5(eq)
                ok = C.pasa(q, qb); bt = C.bootstrap(eqb, eq, n=500)
                filas.append(dict(base=nb, variante=f'B21 {modo} · {na}', **{f'r{i}': q[i]['ratio'] for i in range(3)},
                                  Ra=q[0]['R_ano'], caida=q[0]['caida'], media5=m5, pasa=ok, boot=bt))
                print('   ', f'{modo:8s} {na:42s}', C.fmt(q), '| media5', round(m5, 1), '| PASA' if ok else '| no', '| boot', bt, flush=True)
    T = pd.DataFrame(filas); T.to_csv('b21_bases.csv', index=False)
    print('tiempo', round(time.time() - t0))
