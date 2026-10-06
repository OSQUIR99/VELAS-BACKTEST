"""Construye el panel semanal (viernes) sin mirar al futuro."""
import json, io, pandas as pd, numpy as np
fred = pd.read_pickle('fred.pkl')
for k, t in json.load(open('bonos_fred_extra.json')).items():
    fred[k] = pd.read_csv(io.StringIO(t), na_values=['.'], parse_dates=['observation_date']).set_index('observation_date').iloc[:,0].dropna()
Y = pd.read_pickle('yahoo.pkl'); px = Y['px']
ev = json.load(open('bonos_fechas_eventos.json'))
cpi_rel = pd.to_datetime(sorted(set(ev['CPI']))); nfp_rel = pd.to_datetime(sorted(set(ev['NFP'])))

BD = pd.bdate_range('1962-01-01', '2026-10-02')

def avail_daily(s, lag_days=1):
    """dato diario disponible al cierre del día siguiente (lag de 1 día hábil)"""
    s = s.copy(); s.index = s.index + pd.offsets.BDay(lag_days); return s
def avail_monthly_by_release(s, rel):
    """valor del mes M disponible en la primera fecha de publicación posterior a fin de mes M"""
    out = {}
    for d, v in s.items():
        me = d + pd.offsets.MonthEnd(0)
        r = rel[rel > me]
        if len(r) and (r[0] - me).days < 50: out[r[0]] = v
        else: out[me + pd.Timedelta(days=45)] = v   # antes de 2000: retraso conservador
    return pd.Series(out).sort_index()
def avail_lag(s, days):
    s = s.copy(); s.index = s.index + pd.Timedelta(days=days); return s

def to_weekly(s):
    """último valor conocido a cada viernes"""
    s = s[~s.index.duplicated(keep='last')].sort_index()
    idx = pd.date_range('1962-01-05', '2026-10-02', freq='W-FRI')
    return s.reindex(s.index.union(idx)).ffill().reindex(idx)

W = {}
daily_mkt = ['DGS1MO','DGS3MO','DGS6MO','DGS1','DGS2','DGS5','DGS7','DGS10','DGS20','DGS30','T10Y2Y','T10Y3M','DFF',
             'T10YIE','T5YIE','T5YIFR','DFII10','DFII5','VIXCLS','DTWEXBGS','DTWEXM','DCOILWTICO','BAA10Y','AAA10Y','DTB3',
             'BAMLH0A0HYM2','BAMLC0A0CM','DEXUSEU','DEXJPUS']
for k in daily_mkt:
    if k in fred: W[k] = to_weekly(avail_daily(fred[k], 1))
# objetivo de la Fed: el anuncio se conoce el mismo día
tgt = pd.concat([fred['DFEDTAR'], fred['DFEDTARU']]).sort_index(); tgt = tgt[~tgt.index.duplicated(keep='last')]
W['FEDTGT'] = to_weekly(tgt)
W['TP10'] = to_weekly(avail_lag(fred['THREEFYTP10'], 7))
W['ICSA'] = to_weekly(avail_lag(fred['ICSA'], 5)); W['CCSA'] = to_weekly(avail_lag(fred['CCSA'], 12))
W['NFCI'] = to_weekly(avail_lag(fred['NFCI'], 5)); W['WALCL'] = to_weekly(avail_lag(fred['WALCL'], 1))
W['CPI'] = to_weekly(avail_monthly_by_release(fred['CPIAUCSL'], cpi_rel))
W['CORECPI'] = to_weekly(avail_monthly_by_release(fred['CPILFESL'], cpi_rel))
for k in ['UNRATE','PAYEMS','SAHMREALTIME']:
    W[k] = to_weekly(avail_monthly_by_release(fred[k], nfp_rel))
for k, lag in [('PCEPILFE',60),('INDPRO',50),('UMCSENT',30),('M2SL',60),('RSAFS',45),('PPIACO',45),('JTSJOL',70),('RECPROUSM156N',95)]:
    s = fred[k].copy(); s.index = s.index + pd.offsets.MonthEnd(0) + pd.Timedelta(days=lag); W[k] = to_weekly(s)
g = fred['GDPC1'].copy(); g.index = g.index + pd.offsets.QuarterEnd(0) + pd.Timedelta(days=35); W['GDP'] = to_weekly(g)
W['USREC'] = to_weekly(fred['USREC'].set_axis(fred['USREC'].index + pd.offsets.MonthEnd(0)))  # SOLO para etiquetar, nunca como señal
macro = pd.DataFrame(W)

# precios Yahoo (cierre ajustado = con dividendos) al viernes
pv = px.pivot(index='fecha', columns='simbolo', values='cierre_ajustado')
pc = px.pivot(index='fecha', columns='simbolo', values='cierre')
for c in ['DX-Y.NYB','^VIX','^MOVE','^TNX','^IRX','^TYX','^FVX','GC=F']: pv[c] = pc[c]
idx = pd.date_range('1962-01-05', '2026-10-02', freq='W-FRI')
pw = pv.reindex(pv.index.union(idx)).ffill(limit=5).reindex(idx)
for c in pw: pw.loc[:pv[c].first_valid_index(), c] = np.nan; pw.loc[pw.index < pv[c].first_valid_index(), c] = np.nan
pw.to_pickle('precios_semanales.pkl'); macro.to_pickle('macro_semanal.pkl')

# Bonos sintéticos a partir de rendimientos (para historia larga 1962+)
def par_bond_ret(y, n):
    """retorno semanal de un bono a la par de vencimiento n años, semestral, con rendimientos en %"""
    y = y/100; y0 = y.shift(1); c = y0/2; m = n - 1/52; k = 2*m
    p = c/(y/2)*(1-(1+y/2)**(-k)) + (1+y/2)**(-k)
    return (p - 1) + y0/52
yw = pd.DataFrame({k: to_weekly(fred[k]) for k in ['DGS1','DGS2','DGS5','DGS7','DGS10','DGS20','DGS30','DTB3']})
# rendimientos SIN retraso (son resultado, no señal)
pd.to_pickle(yw, 'yields_sin_retraso.pkl')
y30 = yw['DGS30'].fillna(yw['DGS20'])
syn = pd.DataFrame({'S_CASH': yw['DTB3'].shift(1)/100/52,
                    'S_2Y': par_bond_ret(yw['DGS2'], 2), 'S_5Y': par_bond_ret(yw['DGS5'], 5),
                    'S_10Y': par_bond_ret(yw['DGS10'], 10), 'S_30Y': par_bond_ret(y30, 30)})
syn.to_pickle('sinteticos.pkl')

r = pw[['SHY','IEF','TLT']].pct_change(fill_method=None)
cmp = pd.concat([r, syn], axis=1).dropna()
print(cmp.corr().loc[['SHY','IEF','TLT'], ['S_2Y','S_5Y','S_10Y','S_30Y']].round(3))
print((cmp[['SHY','IEF','TLT','S_2Y','S_10Y','S_30Y']].add(1).prod()**(52/len(cmp))-1).round(4))
