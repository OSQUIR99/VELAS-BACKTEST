# -*- coding: utf-8 -*-
"""Cómo cambia el entorno macro la lectura técnica: ¿aguantan los soportes? ¿siguen las rupturas al alza?"""
import numpy as np, pandas as pd
P = pd.read_parquet('panel_diario.parquet')
K = pd.read_parquet('capas.parquet')
c, h, l = P['c'], P['h'], P['l']

def resultado(d, sube=0.10, baja=0.08, maxd=45):
    """Desde el cierre del día d: ¿qué llega antes, +10 % o -8 %?"""
    p0 = c.loc[d]
    fut = P.loc[d + pd.Timedelta(days=1): d + pd.Timedelta(days=maxd)]
    for i, r in fut.iterrows():
        if r['l'] <= p0 * (1 - baja): return 'falla'
        if r['h'] >= p0 * (1 + sube): return 'aguanta'
    return 'nada'

# régimen macro de cada día
ciclo = P['FEDTGT'] - P['FEDTGT'].shift(180)
bal = P['WALCL'].pct_change(91)
reg = pd.DataFrame(index=P.index)
reg['Fed'] = np.where(ciclo > 0.2, 'subiendo tipos', np.where(ciclo < -0.2, 'bajando tipos', 'quieta'))
reg['Balance Fed'] = np.where(bal > 0.01, 'creciendo', np.where(bal < -0.005, 'menguando', 'plano'))
reg['Clima macro'] = np.where(K['clima'] >= 60, 'hostil (>=60)', np.where(K['clima'] <= 40, 'favorable (<=40)', 'neutro'))
reg['Dólar'] = np.where(P['y_DXY'] > P['y_DXY'].rolling(200).mean(), 'sobre su media 200', 'bajo su media 200')

# toques de soporte: el mínimo del día entra en el 3 % sobre el mínimo de 90 días previo (primer toque en 10 días)
VENT = int(__import__("os").environ.get("VENT", 90))
lo90 = l.rolling(VENT).min().shift(1)
toque = (l <= lo90 * 1.03) & (c >= lo90 * 0.97)
toque = toque & ~toque.shift(1, fill_value=False).rolling(10).max().astype(bool)
# rupturas alcistas: cierre sobre el máximo de 90 días previo (primera en 10 días)
hi90 = h.rolling(VENT).max().shift(1)
rup = (c > hi90); rup = rup & ~rup.shift(1, fill_value=False).rolling(10).max().astype(bool)

filas = []
for tipo, serie in [('toque de soporte', toque), ('ruptura al alza', rup)]:
    for d in serie[serie].index:
        if d > P.index.max() - pd.Timedelta(days=45) or pd.isna(lo90.loc[d]): continue
        r = resultado(d) if tipo == 'toque de soporte' else resultado(d)
        filas.append(dict(fecha=d, tipo=tipo, resultado=r, **reg.loc[d].to_dict()))
T = pd.DataFrame(filas)
T.to_csv('lectura_tecnica_por_regimen.csv', index=False)
print('Casos:', T.groupby('tipo').size().to_dict())
for col in ['Fed', 'Balance Fed', 'Clima macro', 'Dólar']:
    print(f'\n--- según {col} ---')
    t = T.groupby(['tipo', col])['resultado'].value_counts(normalize=True).unstack().fillna(0).round(2)
    t['n'] = T.groupby(['tipo', col]).size()
    print(t.to_string())
