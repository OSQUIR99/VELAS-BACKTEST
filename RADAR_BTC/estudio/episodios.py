# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
D = pd.read_parquet('radar_historico.parquet')
T = pd.read_csv('tramos_zigzag25.csv', parse_dates=['inicio', 'fin'])
c = D['precio']
filas = []
for _, t in T[T.tipo == 'CAIDA'].iterrows():
    a, b = t.inicio, t.fin
    if a < pd.Timestamp('2018-08-20'): continue
    antes = D.loc[a - pd.Timedelta(days=30):a]
    tramo = D.loc[a:b]
    aviso = tramo[tramo.total >= 52]
    if len(aviso):
        d0 = aviso.index[0]
        hecho = (c.loc[d0] / c.loc[a] - 1) / (t.hasta / t.desde - 1)
        dias = (d0 - a).days
    else:
        d0, hecho, dias = None, np.nan, np.nan
    pre = antes.total.max()
    filas.append(dict(techo=a.date(), suelo=b.date(), caida_pct=t.cambio_pct, radar_max_30d_antes=round(pre),
                      macro_en_techo=round(D.loc[a, 'macro']), liquidez_en_techo=round(D.loc[a, 'liquidez']),
                      primer_aviso_naranja=d0.date() if d0 is not None else '-', dias_tras_techo=dias,
                      caida_ya_hecha_al_avisar=f'{hecho*100:.0f} %' if not np.isnan(hecho) else '-',
                      radar_max_en_caida=round(tramo.total.max())))
E = pd.DataFrame(filas)
print(E.to_string(index=False))
E.to_csv('episodios_caidas.csv', index=False)
# falsas alarmas: episodios ROJO (>=62) cuyo precio no cae >=15 % en los 30 días siguientes
rojo = D.total >= 62
ini = rojo & ~rojo.shift(1, fill_value=False).rolling(15).max().astype(bool)
res = []
for d in ini[ini].index:
    if d > D.index.max() - pd.Timedelta(days=30): continue
    res.append(D.loc[d, 'dd'])
res = pd.Series(res)
print(f'\nEpisodios ROJO: {len(res)}; con caída >=15 % en 30 d: {(res<=-0.15).mean()*100:.0f} %; >=10 %: {(res<=-0.10).mean()*100:.0f} %; caída máx mediana {res.median()*100:.1f} %')
nar = (D.total >= 52)
ini = nar & ~nar.shift(1, fill_value=False).rolling(15).max().astype(bool)
res = pd.Series([D.loc[d, 'dd'] for d in ini[ini].index if d <= D.index.max() - pd.Timedelta(days=30)])
print(f'Episodios NARANJA o más: {len(res)}; con caída >=15 % en 30 d: {(res<=-0.15).mean()*100:.0f} %; >=10 %: {(res<=-0.10).mean()*100:.0f} %; caída máx mediana {res.median()*100:.1f} %')
base = D['dd'].dropna()
print(f'Cualquier día al azar: caída >=15 % en 30 d: {(base<=-0.15).mean()*100:.0f} %; >=10 %: {(base<=-0.10).mean()*100:.0f} %; mediana {base.median()*100:.1f} %')
