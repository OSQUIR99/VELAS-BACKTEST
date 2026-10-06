import pandas as pd, numpy as np
P = pd.read_pickle('precios_semanales.pkl'); S = pd.read_pickle('sinteticos.pkl'); SC = pd.read_pickle('scores.pkl')
R = P[['BIL','SHY','IEI','IEF','TLH','TLT','AGG','SPY','TIP','LQD','HYG']].pct_change(fill_method=None)
R['CASH'] = R.BIL.fillna(S.S_CASH)
start, end = '2003-05-02', '2026-10-02'
R = R.loc[start:end]; SC = SC.loc[start:end]
COST = 0.0005
def run(W, retraso=0, cada=1):
    W = W.reindex(R.index).ffill()
    if cada > 1:
        keep = np.arange(len(W)) % cada == 0; W = W.where(pd.Series(keep, index=W.index), np.nan).ffill()
    W = W.shift(1 + retraso).fillna(0)  # pesos decididos al cierre de t, aplicados a la semana t->t+1
    ret = (W * R[W.columns].fillna(0)).sum(axis=1)
    to = W.diff().abs().sum(axis=1).fillna(0)
    return ret - to*COST, to
def stats(r, to=None):
    r = r.dropna(); eq = (1+r).cumprod(); yrs = len(r)/52
    cagr = eq.iloc[-1]**(1/yrs)-1; vol = r.std()*np.sqrt(52)
    ex = r - R.CASH.reindex(r.index).fillna(0)
    sh = ex.mean()/ex.std()*np.sqrt(52); dd = (eq/eq.cummax()-1).min()
    d = {'Rent. anual %': cagr*100, 'Volatilidad %': vol*100, 'Sharpe': sh, 'Peor caída %': dd*100, 'Rent/caída': cagr/abs(dd)}
    if to is not None: d['Rotación anual'] = to.sum()/yrs
    return d
def w_const(**k): return pd.DataFrame({a: pd.Series(v, index=R.index) for a, v in k.items()})
D = SC.score_duracion; B = SC.score_bonos_vs_acciones
def escalon(D, alto=65, bajo=35):
    w = pd.DataFrame(0.0, index=D.index, columns=['TLT','IEF','SHY'])
    w.loc[D >= alto, 'TLT'] = 1; w.loc[(D < alto) & (D >= bajo), 'IEF'] = 1; w.loc[D < bajo, 'SHY'] = 1
    return w
def prop(D): return pd.DataFrame({'TLT': D/100, 'SHY': 1 - D/100})
estr = {}
estr['Solo SHY (1-3 años)'] = w_const(SHY=1); estr['Solo IEF (7-10 años)'] = w_const(IEF=1); estr['Solo TLT (+20 años)'] = w_const(TLT=1)
estr['AGG (mezcla de mercado)'] = w_const(AGG=1)
m = (D/100).mean(); estr[f'Fijo {m:.0%} TLT / resto SHY'] = w_const(TLT=m, SHY=1-m)
estr['Puntuación: escalón TLT/IEF/SHY'] = escalon(D)
estr['Puntuación: proporcional TLT/SHY'] = prop(D)
eq = (0.6 + 0.2*(50 - B)/50).clip(0.4, 0.8)
estr['60/40 fijo (SPY/IEF)'] = w_const(SPY=0.6, IEF=0.4)
estr['Puntuación B: % acciones 40-80 (resto IEF)'] = pd.DataFrame({'SPY': eq, 'IEF': 1-eq})
eD = escalon(D)
estr['Combinado: B decide acciones, D decide plazo'] = pd.concat([eq.rename('SPY'), eD.mul(1-eq, axis=0)], axis=1)
estr['60/40 con plazo según D'] = pd.concat([pd.Series(0.6, index=D.index, name='SPY'), eD*0.4], axis=1)
rows = {}; series = {}
for k, w in estr.items():
    for etiqueta, kw in [('semanal', {}), ('mensual', {'cada': 4}), ('mensual+1sem retraso', {'cada': 4, 'retraso': 1})]:
        r, to = run(w, **kw); rows[(k, etiqueta)] = stats(r, to); series[(k, etiqueta)] = r
T = pd.DataFrame(rows).T
pd.set_option('display.width', 250)
print(T.xs('mensual', level=1).round(2).to_string())
print('\n-- Sensibilidad a la frecuencia / retraso --')
print(T.loc[[k for k in T.index if 'Puntuación' in k[0] or 'Combinado' in k[0] or '60/40 con' in k[0]]].round(2).to_string())
# por subperiodos
print('\n-- Subperiodos (mensual) --')
sub = {}
for k in estr:
    r = series[(k, 'mensual')]
    for a, b in [('2003','2008'), ('2009','2015'), ('2016','2021'), ('2022','2026')]:
        x = r.loc[a:b]; sub[(k, f'{a}-{b}')] = ((1+x).prod()**(52/len(x))-1)*100
print(pd.Series(sub).unstack().round(1).to_string())
pd.to_pickle({'tabla': T, 'series': series, 'pesos': estr}, 'backtest.pkl')
