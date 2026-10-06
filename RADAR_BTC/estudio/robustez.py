# -*- coding: utf-8 -*-
"""Robustez: AUC año a año, colas por deciles y puntuación compuesta elegida SOLO con 2017-2021 y probada en 2022-2026."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

S = pd.read_parquet('estudio_diario.parquet')
c = pd.read_parquet('panel_diario.parquet')['c']
# variables estructurales extra (tipo Wyckoff: ruptura de rango)
lo60 = pd.read_parquet('panel_diario.parquet')['l'].rolling(60).min().shift(1)
hi60 = pd.read_parquet('panel_diario.parquet')['h'].rolling(60).max().shift(1)
S['t_bajo_min60'] = (c < lo60).astype(float)
S['t_dist_min60'] = c / lo60 - 1
S['t_rango60'] = hi60 / lo60 - 1
S['t_cierres_bajo_min60_5d'] = (c < lo60).astype(float).rolling(5).sum()
LBL = 'desplome_relvol'

def auc(x, y):
    m = x.notna() & y.notna()
    if m.sum() < 100 or y[m].nunique() < 2: return np.nan
    return roc_auc_score(y[m], x[m])

top = ['m_2a_menos_fed', 'm_2a_chg60', 'm_10a_chg60', 'm_real_chg60', 'm_dxy_dist200', 'm_prima_plazo', 'm_nfci_chg', 't_rsi14', 't_ret20',
       't_bajo_min60', 't_dist_min60', 't_vol30', 'd_funding7', 'm_dolar_chg60']
print('AUC AÑO A AÑO (desplome relativo a la volatilidad)')
Y = pd.DataFrame({v: S.groupby(S.index.year).apply(lambda g: auc(g[v], g[LBL])) for v in top}).T.round(2)
Y['años_>0,5'] = (Y > 0.5).sum(axis=1); Y['años_<0,5'] = (Y.drop(columns='años_>0,5') < 0.5).sum(axis=1)
print(Y.to_string())

print('\nTASA DE DESPLOME A 30 DÍAS POR QUINTIL (1 = valores más bajos) — 2017-2026 completo')
for v in ['m_2a_menos_fed', 'm_2a_chg60', 'm_dxy_dist200', 'm_nfci_chg', 't_ret20', 'd_funding7', 't_vol30']:
    q = pd.qcut(S[v].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    print(f'{v:18s}', S.groupby(q)[LBL].mean().round(2).to_dict())

# ---------- compuesto walk-forward ----------
def pct_expandido(s, minp=365):
    """Percentil de cada día respecto a TODO su pasado (sin mirar el futuro)."""
    vals = s.values; out = np.full(len(s), np.nan)
    hist = []
    import bisect
    for i, v in enumerate(vals):
        if not np.isnan(v):
            if len(hist) >= minp:
                out[i] = bisect.bisect_left(hist, v) / len(hist)
            bisect.insort(hist, v)
    return pd.Series(out, index=s.index)

A = S.loc['2017-08-17':'2021-12-31']
cand = [v for v in S.columns if v[:2] in ('t_', 'm_') and S[v].notna().mean() > 0.9]
elegidas = {}
for v in cand:
    a = auc(A[v], A[LBL])
    if not np.isnan(a) and abs(a - 0.5) >= 0.06:
        elegidas[v] = 1 if a > 0.5 else -1
print('\nElegidas SOLO con 2017-2021:', elegidas)
PC = pd.DataFrame({v: pct_expandido(S[v] * sg) for v, sg in elegidas.items()})
comp = PC.mean(axis=1, skipna=True) * 100
for nombre, (a, b) in {'2017-21 (dentro)': ('2017-08-17', '2021-12-31'), '2022-26 (fuera)': ('2022-01-01', '2026-08-28')}.items():
    s = comp.loc[a:b]; y = S[LBL].loc[a:b]
    print(f'Compuesto técnico+macro {nombre}: AUC {auc(s, y):.2f}')
    q = pd.cut(s, [0, 30, 50, 70, 101])
    print('   tasa de desplome por tramo de puntuación:', y.groupby(q).mean().round(2).to_dict(), ' base', round(y.mean(), 2))

# solo macro elegidas en A
mac = {v: sg for v, sg in elegidas.items() if v.startswith('m_')}
compm = pd.DataFrame({v: pct_expandido(S[v] * sg) for v, sg in mac.items()}).mean(axis=1) * 100
tec = {v: sg for v, sg in elegidas.items() if v.startswith('t_')}
compt = pd.DataFrame({v: pct_expandido(S[v] * sg) for v, sg in tec.items()}).mean(axis=1) * 100
for nombre, s in [('solo macro', compm), ('solo técnico', compt)]:
    print(f'{nombre} fuera de muestra 2022-26: AUC {auc(s.loc["2022":"2026-08-28"], S[LBL].loc["2022":"2026-08-28"]):.2f}')
S[['t_bajo_min60', 't_dist_min60', 't_rango60', 't_cierres_bajo_min60_5d']].to_parquet('extra_estructura.parquet')
