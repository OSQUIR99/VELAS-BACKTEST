import json, pandas as pd, numpy as np
fred = pd.read_pickle('fred.pkl'); Y = pd.read_pickle('yahoo.pkl'); px = Y['px']
ev = json.load(open('bonos_fechas_eventos.json'))
D = pd.DataFrame({k: fred[k] for k in ['DGS2','DGS10','DGS30','DGS3MO']}).dropna(subset=['DGS10'])
dD = D.diff()*100  # puntos básicos
pv = px.pivot(index='fecha', columns='simbolo', values='cierre_ajustado')
rr = pv[['SHY','IEF','TLT','SPY']].pct_change(fill_method=None)*100
tgt = pd.concat([fred['DFEDTAR'], fred['DFEDTARU']]).sort_index(); tgt = tgt[~tgt.index.duplicated(keep='last')]
ff_daily = tgt.reindex(pd.bdate_range('1982-09-27','2026-10-02')).ffill()
out = {}
# --- 1) Días de evento: cuánto se mueven los bonos frente a un día normal (2003-2026)
def tag(dates): return pd.DatetimeIndex(pd.to_datetime(dates)).intersection(dD.index)
fomc = tag([d for d in ev['FOMC'] if d <= '2026-10-01'])
cpi = tag(ev['CPI']); nfp = tag(ev['NFP'])
base = dD.loc['2000':].dropna()
rows = []
for name, idx in [('Reunión Fed', fomc), ('Dato de inflación (IPC)', cpi), ('Dato de empleo', nfp)]:
    idx = idx[idx >= '2000-01-01']
    normal = base.drop(fomc.union(cpi).union(nfp), errors='ignore')
    r = {'evento': name, 'n_dias': len(idx)}
    for c in ['DGS2','DGS10','DGS30']:
        r[f'mov_medio_{c}_pb'] = base.loc[base.index.intersection(idx), c].abs().mean()
        r[f'normal_{c}_pb'] = normal[c].abs().mean()
    rr2 = rr.loc['2003':]
    r['TLT_mov_medio_%'] = rr2.loc[rr2.index.intersection(idx), 'TLT'].abs().mean(); r['TLT_normal_%'] = rr2.drop(idx, errors='ignore').TLT.abs().mean()
    rows.append(r)
E1 = pd.DataFrame(rows); out['dias_evento'] = E1
print(E1.round(2).T.to_string())
# --- 2) Reuniones Fed por tipo de decisión
dec = []
for d in fomc:
    before = ff_daily.loc[:d - pd.Timedelta(days=1)].iloc[-1] if len(ff_daily.loc[:d - pd.Timedelta(days=1)]) else np.nan
    after = ff_daily.loc[:d + pd.Timedelta(days=1)].iloc[-1]
    ch = round((after - before)*100)
    dec.append({'fecha': d, 'decision': 'subida' if ch > 0 else ('bajada' if ch < 0 else 'mantiene'), 'pb': ch})
dec = pd.DataFrame(dec).set_index('fecha')
dd = dec.join(dD).join(rr)
# reacción en el día y en las 2 semanas siguientes
def fwd_chg(s, d, n): 
    i = s.index.searchsorted(d); 
    return (s.iloc[min(i+n, len(s)-1)] - s.iloc[i-1])*100 if i>0 else np.nan
for c in ['DGS2','DGS10']:
    dd[f'{c}_10dias'] = [fwd_chg(D[c].dropna(), d, 10) for d in dd.index]
E2 = dd.loc['2000':].groupby('decision').agg(n=('pb','size'), DGS2_dia=('DGS2','mean'), DGS10_dia=('DGS10','mean'),
        DGS2_10d=('DGS2_10dias','mean'), DGS10_10d=('DGS10_10dias','mean'), TLT_dia=('TLT','mean'), SHY_dia=('SHY','mean'))
out['fed_por_decision'] = E2; print(E2.round(2).to_string())
# --- 3) Ciclos: primera bajada y primera subida de cada ciclo (desde 1982)
ch = ff_daily.diff().fillna(0); ch = ch[ch != 0]
firsts = []; last = 0
for d, v in ch.items():
    s = np.sign(v)
    if s != last: firsts.append((d, 'primera bajada' if s < 0 else 'primera subida'))
    last = s
F1 = pd.DataFrame(firsts, columns=['fecha','tipo']); print(F1.to_string())
out['primeros_movimientos'] = F1
pd.to_pickle({'dec': dec, **out}, 'eventos.pkl')
