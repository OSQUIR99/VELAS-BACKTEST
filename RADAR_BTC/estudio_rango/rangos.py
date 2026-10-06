# -*- coding: utf-8 -*-
"""Rangos laterales en velas de 4 h: detección automática, ruptura y continuación (BTC 2017-2026)."""
import json, os
import numpy as np, pandas as pd

def cargar_4h():
    ruta = 'datos/RADAR_BTC/brutos/binance_btc_4h_taker.csv'
    if os.path.exists(ruta):
        d = pd.read_csv(ruta); d['fecha'] = pd.to_datetime(d['t'], unit='ms')
        d = d.set_index('fecha')[['o', 'h', 'l', 'c', 'v', 'taker_buy_v']].astype(float)
    else:
        d = pd.read_parquet('datos/CRIPTO/BTC/4h.parquet')
        d['fecha'] = pd.to_datetime(d['fecha'])
        d = d.set_index('fecha').rename(columns={'apertura': 'o', 'maximo': 'h', 'minimo': 'l', 'cierre': 'c', 'volumen': 'v'})
        d['taker_buy_v'] = np.nan
    return d[~d.index.duplicated()].sort_index()

VENTANAS = [24, 36, 48, 72, 96, 120]   # 4, 6, 8, 12, 16 y 20 días
ANCHO_MAX, ANCHO_MIN, ER_MAX = 0.12, 0.02, 0.30

def detectar(d, VENTANAS=VENTANAS, ANCHO_MAX=ANCHO_MAX, ANCHO_MIN=ANCHO_MIN, ER_MAX=ER_MAX):
    """Para cada vela t: el rango vigente definido con las N velas ANTERIORES (t-N..t-1).
    Se elige la ventana más larga que cumple: ancho 2-12 %, poca tendencia (eficiencia <= 0,30),
    y el precio ha visitado tanto el cuarto superior como el inferior (>= 2 cierres en cada uno)."""
    h, l, c = d['h'].values, d['l'].values, d['c'].values
    n = len(d)
    out = {k: np.full(n, np.nan) for k in ['N', 'techo', 'suelo', 'ancho', 'er']}
    absd = np.abs(np.diff(c, prepend=c[0]))
    cs = np.cumsum(absd)
    for N in VENTANAS:
        H = pd.Series(h).rolling(N).max().shift(1).values
        L = pd.Series(l).rolling(N).min().shift(1).values
        mid = (H + L) / 2
        ancho = (H - L) / mid
        mov = np.abs(pd.Series(c).shift(1).values - pd.Series(c).shift(N).values)
        ruido = cs - np.roll(cs, N); ruido = pd.Series(ruido).shift(1).values
        er = mov / ruido
        ok = (ancho <= ANCHO_MAX) & (ancho >= ANCHO_MIN) & (er <= ER_MAX)
        for k, v in [('N', N), ('techo', H), ('suelo', L), ('ancho', ancho), ('er', er)]:
            out[k] = np.where(ok, v, out[k])  # la ventana más larga sobrescribe
    R = pd.DataFrame(out, index=d.index)
    # visitas a los extremos dentro de la ventana elegida
    q_alto = np.zeros(n); q_bajo = np.zeros(n)
    for i in np.where(~np.isnan(R['N'].values))[0]:
        N = int(R['N'].values[i]); a, b = R['suelo'].values[i], R['techo'].values[i]
        w = c[i - N:i]
        q_alto[i] = np.sum(w >= b - 0.25 * (b - a)); q_bajo[i] = np.sum(w <= a + 0.25 * (b - a))
    R['cierres_cuarto_alto'] = q_alto; R['cierres_cuarto_bajo'] = q_bajo
    valido = (R['cierres_cuarto_alto'] >= 2) & (R['cierres_cuarto_bajo'] >= 2) & (d['c'] <= R['techo']) & (d['c'] >= R['suelo'])
    R.loc[~valido, ['N', 'techo', 'suelo', 'ancho', 'er']] = np.nan
    return R

def resultado(d, R, horizonte=60, sigue=30):
    """Desde cada vela dentro de un rango: ¿qué se rompe antes (cierre de 4 h fuera)? y, si es por abajo,
    ¿cuánto sigue cayendo? (en anchos del rango) y ¿recupera el rango en 6 velas (ruptura falsa)?"""
    c, h, l = d['c'].values, d['h'].values, d['l'].values
    n = len(d)
    lado = np.full(n, np.nan); velas = np.full(n, np.nan); sigue_abajo = np.full(n, np.nan)
    falsa = np.full(n, np.nan); caida_pct = np.full(n, np.nan)
    for i in np.where(~np.isnan(R['techo'].values))[0]:
        T, S = R['techo'].values[i], R['suelo'].values[i]
        W = T - S
        for j in range(i + 1, min(i + 1 + horizonte, n)):
            if c[j] < S:
                lado[i] = -1; velas[i] = j - i
                fin = min(j + 1 + sigue, n)
                mn = l[j:fin].min()
                sigue_abajo[i] = (S - mn) / W
                caida_pct[i] = mn / S - 1
                falsa[i] = float((c[j + 1:min(j + 7, n)] > S).any())
                break
            if c[j] > T:
                lado[i] = 1; velas[i] = j - i; break
        else:
            lado[i] = 0
    return pd.DataFrame({'lado': lado, 'velas_hasta_ruptura': velas, 'sigue_abajo_anchos': sigue_abajo,
                         'falsa': falsa, 'caida_tras_ruptura': caida_pct}, index=d.index)

if __name__ == '__main__':
    d = cargar_4h()
    print('velas', len(d), d.index.min(), d.index.max(), 'con delta real:', d['taker_buy_v'].notna().mean().round(2))
    R = detectar(d)
    Y = resultado(d, R)
    D = d.join(R).join(Y)
    D.to_parquet('rangos_4h.parquet')
    Rm = detectar(d, VENTANAS=[12, 18, 24, 36], ANCHO_MAX=0.07, ANCHO_MIN=0.015, ER_MAX=0.35)
    Ym = resultado(d, Rm, horizonte=30, sigue=18)
    Dm = d.join(Rm).join(Ym); Dm.to_parquet('rangos_menores_4h.parquet')
    sm = Dm[Dm.techo.notna()]
    print('RANGO MENOR (2-6 días, ancho <= 7 %): dentro', f'{len(sm)/len(Dm)*100:.0f} % del tiempo; ancho mediano', round(sm.ancho.median()*100, 1), '%')
    print('  ¿qué se rompe antes? (5 días)', sm['lado'].map({-1: 'abajo', 1: 'arriba', 0: 'ninguno'}).value_counts(normalize=True).round(2).to_dict())
    abm = sm[sm.lado == -1]
    print('  tras romper por abajo: falsa', round(abm.falsa.mean()*100), '% | sigue >= 1 ancho', round((abm.sigue_abajo_anchos >= 1).mean()*100), '% | caída mediana 3 días', round(abm.caida_tras_ruptura.median()*100, 1), '%')
    dentro = D['techo'].notna()
    print('velas dentro de un rango:', dentro.sum(), f'({dentro.mean()*100:.0f} % del tiempo)')
    print('ancho del rango (mediana):', round(D.loc[dentro, 'ancho'].median() * 100, 1), '%   N (velas):', D.loc[dentro, 'N'].value_counts().sort_index().to_dict())
    s = D.loc[dentro]
    print('\n¿Qué se rompe antes? (60 velas = 10 días)')
    print(s['lado'].map({-1: 'abajo', 1: 'arriba', 0: 'ninguno'}).value_counts(normalize=True).round(2).to_dict())
    for e, (a, b) in {'2017-21': ('2017', '2021'), '2022-26': ('2022', '2026')}.items():
        x = s.loc[a:b]
        print(e, x['lado'].map({-1: 'abajo', 1: 'arriba', 0: 'ninguno'}).value_counts(normalize=True).round(2).to_dict(), 'n', len(x))
    ab = s[s.lado == -1]
    print('\nTras romper por abajo: sigue cayendo >= 1 ancho del rango:', round((ab.sigue_abajo_anchos >= 1).mean() * 100), '%',
          '| ruptura falsa (recupera en 24 h):', round(ab.falsa.mean() * 100), '%',
          '| caída mediana tras romper (5 días):', round(ab.caida_tras_ruptura.median() * 100, 1), '%')
