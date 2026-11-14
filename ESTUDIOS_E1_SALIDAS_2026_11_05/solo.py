# -*- coding: utf-8 -*-
"""Paso 1 del documento 23: la E1 de índices (S&P, Nasdaq 100, Dow) SOLA, con cada salida, con el tamaño del motor
(puntos + tope de 3 R al día) y la curva diaria valorada (latente de la lista _diario). Uso: python3 solo.py <carpeta_listas>"""
import sys, numpy as np, pandas as pd
LIS = sys.argv[1] if len(sys.argv) > 1 else 'listas'
IDX = ['SPX', 'NDX', 'DJI']
SAL = ['base', 'seguir5', 'rsi90', 'minant', 'seguir5_max10', 'mitad']
TRAMOS = {'1990-2026': ('1990-01-01', '2026-12-31'), 'P1 ≤2023': ('1990-01-01', '2023-12-31'),
          'P2 2024-26': ('2024-01-01', '2026-12-31'), 'cartera may-18→': ('2018-05-01', '2026-12-31'),
          '2018-21': ('2018-05-01', '2021-12-31'), '2022-26': ('2022-01-01', '2026-12-31')}


def curva(L, Dd):
    Dd = Dd[Dd.id.isin(set(L.id))].sort_values(['id', 'fecha'])
    Dd = Dd.assign(inc=Dd.groupby('id').r_latente.diff().fillna(Dd.r_latente))
    return Dd.groupby('fecha').inc.sum().cumsum()


def met(L, Dd, a, b):
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    S = L[(L.t_entrada >= a) & (L.t_entrada <= b + pd.Timedelta(days=1))]
    if not len(S):
        return {}
    e = curva(S, Dd)
    dd = float((np.maximum.accumulate(np.r_[0, e.values])[1:] - e.values).max())
    yrs = max((min(b, e.index[-1]) - max(a, e.index[0])).days / 365.25, 0.5)
    ses = np.array([np.busday_count(x.date(), y.date()) for x, y in zip(S.t_entrada, S.t_salida)])
    anual = S.groupby(S.t_entrada.dt.year).r_final.sum()
    return dict(ops=len(S), R_op=S.r_final.mean(), R_bruto_op=S.r_bruto.mean(), acierto=(S.r_final > 0).mean() * 100,
                R=S.r_final.sum(), R_ano=S.r_final.sum() / yrs, caida=dd, ratio=S.r_final.sum() / yrs / dd if dd > 0 else np.nan,
                peor_ano=anual.min(), sesiones=ses.mean())


filas = []
LL = {}
for s in SAL:
    L = pd.read_parquet(f'{LIS}/bolsa_e1_{s}.parquet'); Dd = pd.read_parquet(f'{LIS}/bolsa_e1_{s}_diario.parquet')
    L = L[L.activo.isin(IDX)].copy(); LL[s] = L
    for act in ['3 índices'] + IDX:
        S = L if act == '3 índices' else L[L.activo == act]
        for t, (a, b) in TRAMOS.items():
            m = met(S, Dd, a, b)
            filas.append(dict(salida=s, activo=act, tramo=t, **m))
T = pd.DataFrame(filas)
T.to_csv('solo.csv', index=False)
pd.set_option('display.width', 250)
print(T[T.activo == '3 índices'].round(3).to_string(index=False))
print(T[T.activo != '3 índices'].pivot_table(index=['activo', 'salida'], columns='tramo', values='R_op').round(3).to_string())

# diferencia emparejada por señal (misma señal en las dos listas), en R finales y en R por unidad
B = LL['base'].set_index(['activo', 't_senal'])
pares = []
for s in SAL[1:]:
    V = LL[s].set_index(['activo', 't_senal'])
    j = B[['r_final', 'r_bruto']].join(V[['r_final', 'r_bruto']], rsuffix='_v', how='inner')
    for t, (a, b) in TRAMOS.items():
        k = j[(j.index.get_level_values(1) >= a) & (j.index.get_level_values(1) <= pd.Timestamp(b) + pd.Timedelta(days=1))]
        d = k.r_bruto_v - k.r_bruto
        pares.append(dict(salida=s, tramo=t, n_comunes=len(k), solo_base=len(B.loc[B.index.difference(V.index)].query('t_senal>=@a and t_senal<=@b')),
                          solo_variante=len(V.loc[V.index.difference(B.index)].query('t_senal>=@a and t_senal<=@b')),
                          dif_R_unidad=d.mean(), z=d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))))
P = pd.DataFrame(pares); P.to_csv('solo_pares.csv', index=False)
print(P.round(3).to_string(index=False))
