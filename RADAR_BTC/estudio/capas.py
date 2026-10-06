# -*- coding: utf-8 -*-
"""Clima macro (lento) x detonante (rápido) x estructura: ¿se potencian?"""
import numpy as np, pandas as pd
from robustez import S, pct_expandido, auc, LBL

P = pd.read_parquet('panel_diario.parquet')
# --- clima macro: solo tipos, dólar, condiciones financieras y crédito (elegidas en 2017-21, todas con lógica económica) ---
CLIMA = {'m_2a_menos_fed': 1, 'm_2a_chg60': 1, 'm_10a_chg60': 1, 'm_real_chg60': 1, 'm_dxy_dist200': 1, 'm_nfci_chg': 1, 'm_credito_chg30': 1}
clima = pd.DataFrame({v: pct_expandido(S[v] * s) for v, s in CLIMA.items()}).mean(axis=1) * 100
S['clima'] = clima
for e, (a, b) in {'2017-21': ('2017-08-17', '2021-12-31'), '2022-26': ('2022-01-01', '2026-08-28')}.items():
    s = S.loc[a:b]
    print(f'Clima macro {e}: AUC {auc(s.clima, s[LBL]):.2f}; tasa desplome por tramo:',
          s.groupby(pd.cut(s.clima, [0, 35, 50, 65, 101]))[LBL].agg(['mean', 'size']).round(2).to_dict('index'))

# --- detonante macro en curso (sorpresas): movimientos anómalos del día en tipos, dólar, bolsa, volatilidad, yen ---
def z(s, n=250):
    d = s.diff()
    return d / d.rolling(n, min_periods=120).std()
qqq_r = np.log(P['y_QQQ']).diff()
sh = pd.DataFrame({
    'bolsa': (qqq_r / qqq_r.rolling(250, min_periods=120).std()) <= -2.0,
    'vix': z(P['y_VIX']) >= 2.5,
    'tipos2a': z(P['DGS2']).abs() >= 2.5,
    'dolar': z(np.log(P['y_DXY'])) >= 2.0,
    'yen': z(np.log(P['DEXJPUS'])) <= -2.5,     # el yen se aprecia de golpe (deshacer carry)
    'credito': z(P['BAA10Y']) >= 2.5,
})
# solo cuenta días hábiles en que se movió el dato (el ffill crea ceros los fines de semana)
S['shock'] = sh.any(axis=1).astype(float)
S['shock_5d'] = S['shock'].rolling(5).max()
print('\nDías con detonante macro en los 5 días previos:', round(S.shock_5d.mean() * 100), '% del tiempo')
for e, (a, b) in {'2017-21': ('2017-08-17', '2021-12-31'), '2022-26': ('2022-01-01', '2026-08-28')}.items():
    s = S.loc[a:b].copy()
    s['clima_alto'] = s.clima >= 60
    t = s.groupby(['clima_alto', 'shock_5d'])[LBL].agg(['mean', 'size']).round(2)
    print(f'\nTasa de desplome {e} según clima (alto>=60) y detonante en 5 días:'); print(t.to_string())

# --- estructura tipo Wyckoff: cierre bajo el mínimo de 60 días y reintento fallido ---
c = P['c']; lo60 = P['l'].rolling(60).min().shift(1)
rompe = (c < lo60)
primer = rompe & ~rompe.shift(1, fill_value=False).rolling(10).max().astype(bool)
# reintento fallido: en los 10 días tras la ruptura, el precio vuelve a ±2 % del nivel roto pero no cierra por encima 2 días seguidos
fallo = pd.Series(False, index=c.index)
for d in primer[primer].index:
    nivel = lo60.loc[d]
    tramo = c.loc[d + pd.Timedelta(days=1): d + pd.Timedelta(days=10)]
    if len(tramo) < 3: continue
    toca = (P['h'].loc[tramo.index] >= nivel * 0.98)
    recupera = ((tramo > nivel) & (tramo.shift(1) > nivel)).any()
    if toca.any() and not recupera:
        dia = toca[toca].index[0]
        fallo.loc[dia] = True
S['ruptura'] = primer.astype(float); S['reintento_fallido'] = fallo.astype(float)
base = S[LBL].mean()
for k in ['ruptura', 'reintento_fallido']:
    m = S[k] == 1
    print(f'\n{k}: {m.sum()} casos; desplome posterior {S.loc[m, LBL].mean():.2f} (base {base:.2f}); caída media siguiente 30 d {S.loc[m, "dd_fut"].mean()*100:.1f} %  vs {S["dd_fut"].mean()*100:.1f} %')
    for e, (a, b) in {'2017-21': ('2017', '2021'), '2022-26': ('2022', '2026')}.items():
        mm = m.loc[a:b]
        print(f'   {e}: n={mm.sum()}  desplome {S.loc[a:b].loc[mm, LBL].mean():.2f}  base {S.loc[a:b, LBL].mean():.2f}')
    # ¿con clima alto?
    mm = m & (S.clima >= 60)
    print(f'   con clima macro alto: n={mm.sum()} desplome {S.loc[mm, LBL].mean():.2f}')
    mm = m & (S.clima < 60)
    print(f'   con clima macro bajo: n={mm.sum()} desplome {S.loc[mm, LBL].mean():.2f}')
S[['clima', 'shock', 'shock_5d', 'ruptura', 'reintento_fallido']].to_parquet('capas.parquet')
