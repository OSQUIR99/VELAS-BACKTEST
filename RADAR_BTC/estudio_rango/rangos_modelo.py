# -*- coding: utf-8 -*-
"""Modelo simple (regresión logística) ajustado con 2017-2021 y probado con 2022-2026."""
import json
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

Z = pd.read_parquet('rangos_senales.parquet')
F1 = ['posicion', 'rsi4h', 'ret_24v', 'pend_minimos', 'pend_maximos', 'dist_ema50d', 'vol_velas_bajistas', 'compresion_12v']
F2 = ['radar_macro', 'toques_techo', 'posicion', 'ret_24v']

def ajustar(df, feats, y, a='2017', b='2021'):
    tr = df.loc[a:b].dropna(subset=feats + [y])
    mu, sd = tr[feats].mean(), tr[feats].std()
    m = LogisticRegression(C=0.5, max_iter=1000).fit((tr[feats] - mu) / sd, tr[y])
    return m, mu, sd

def prob(df, m, mu, sd, feats):
    ok = df[feats].notna().all(axis=1)
    p = pd.Series(np.nan, index=df.index)
    p[ok] = m.predict_proba((df.loc[ok, feats] - mu) / sd)[:, 1]
    return p

# --- 1) ¿rompe antes por abajo? ---
m1, mu1, sd1 = ajustar(Z, F1, 'rompe_abajo')
Z['p_abajo'] = prob(Z, m1, mu1, sd1, F1)
print('Modelo 1: ¿rompe antes por abajo? (10 días)')
for e, (a, b) in {'2017-21 (ajuste)': ('2017', '2021'), '2022-26 (fuera)': ('2022', '2026'), '2024-26 (fuera)': ('2024', '2026')}.items():
    s = Z.loc[a:b].dropna(subset=['p_abajo'])
    q = pd.cut(s.p_abajo, [0, .25, .4, .55, .7, 1])
    print(f'  {e}: AUC {roc_auc_score(s.rompe_abajo, s.p_abajo):.2f} | real por tramo:',
          {str(k): (round(v, 2), int(n)) for k, v, n in zip(s.groupby(q, observed=False).rompe_abajo.mean().index,
                                                            s.groupby(q, observed=False).rompe_abajo.mean().values,
                                                            s.groupby(q, observed=False).size().values)})
print('  pesos:', dict(zip(F1, np.round(m1.coef_[0], 2))))

# solo con la posición (para ver cuánto añade lo demás)
s = Z.loc['2022':'2026'].dropna(subset=['p_abajo'])
print('  AUC fuera de muestra solo con la posición:', round(roc_auc_score(s.rompe_abajo, -s.posicion), 2))

# --- 2) si rompe por abajo, ¿es real? ---
B = Z[Z.lado == -1].copy()
B['real'] = ((B['falsa'] == 0) & (B['sigue_abajo_anchos'] >= 0.5)).astype(float)
m2, mu2, sd2 = ajustar(B, F2, 'real')
B['p_real'] = prob(B, m2, mu2, sd2, F2)
Z['p_real'] = prob(Z, m2, mu2, sd2, F2)
print('\nModelo 2: si rompe por abajo, ¿es real?')
for e, (a, b) in {'2017-21 (ajuste)': ('2017', '2021'), '2022-26 (fuera)': ('2022', '2026')}.items():
    s = B.loc[a:b].dropna(subset=['p_real'])
    q = pd.qcut(s.p_real, 3, labels=['baja', 'media', 'alta'])
    print(f'  {e}: AUC {roc_auc_score(s.real, s.p_real):.2f} | ruptura real por tercio:', s.groupby(q, observed=False).real.mean().round(2).to_dict(),
          '| caída mediana tras romper:', s.groupby(q, observed=False).caida_tras_ruptura.median().mul(100).round(1).to_dict())
print('  pesos:', dict(zip(F2, np.round(m2.coef_[0], 2))))

# --- 3) riesgo combinado: rompe por abajo Y de verdad ---
Z['p_ruptura_real'] = Z['p_abajo'] * Z['p_real']
Z['ruptura_real'] = ((Z.lado == -1) & (Z.falsa == 0) & (Z.sigue_abajo_anchos >= 0.5)).astype(float)
for e, (a, b) in {'2017-21': ('2017', '2021'), '2022-26': ('2022', '2026')}.items():
    s = Z.loc[a:b].dropna(subset=['p_ruptura_real'])
    q = pd.qcut(s.p_ruptura_real, 5, labels=[1, 2, 3, 4, 5])
    print(f'\nRiesgo combinado {e}: AUC {roc_auc_score(s.ruptura_real, s.p_ruptura_real):.2f}; ruptura bajista real por quintil:',
          s.groupby(q, observed=False).ruptura_real.mean().round(2).to_dict(), ' base', round(s.ruptura_real.mean(), 2))

json.dump({'m1': {'feats': F1, 'coef': m1.coef_[0].tolist(), 'inter': float(m1.intercept_[0]), 'mu': mu1.tolist(), 'sd': sd1.tolist()},
           'm2': {'feats': F2, 'coef': m2.coef_[0].tolist(), 'inter': float(m2.intercept_[0]), 'mu': mu2.tolist(), 'sd': sd2.tolist()}},
          open('rangos_modelo.json', 'w'), indent=1)
Z.to_parquet('rangos_con_prob.parquet')
