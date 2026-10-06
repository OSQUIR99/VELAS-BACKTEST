import pandas as pd, numpy as np
F = pd.read_pickle('features.pkl'); T = pd.read_pickle('targets.pkl')
def ic(f, t, h):
    df = pd.concat([f, t], axis=1).dropna()
    if len(df) < 3*h + 20: return np.nan, np.nan, 0
    vals = []
    for o in range(h):
        sub = df.iloc[o::h]
        if len(sub) > 8: vals.append(sub.iloc[:,0].rank().corr(sub.iloc[:,1].rank()))
    n = len(df)//h
    m = np.nanmean(vals); return m, m*np.sqrt(n), n
periods = {'1977-94':('1977','1994'), '1995-09':('1995','2009'), '2010-26':('2010','2026')}
rows = []
for tgt, sign in [('syn_larg_vs_cort', 1), ('dY10', -1), ('TLT_vs_SHY', 1), ('syn10_vs_SPY', 1)]:
    for h in [4, 13, 26]:
        t = T[f'{tgt}_{h}'] * sign
        for c in F:
            r = {'objetivo': tgt, 'h': h, 'indicador': c}
            m, ts, n = ic(F[c], t, h); r.update(IC_total=m, t=ts, n=n)
            for p, (a, b) in periods.items():
                r[p] = ic(F[c].loc[a:b], t.loc[a:b], h)[0]
            rows.append(r)
R = pd.DataFrame(rows); R.to_pickle('ic.pkl')
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
for tgt in ['syn_larg_vs_cort', 'TLT_vs_SHY', 'syn10_vs_SPY']:
    sub = R[(R.objetivo == tgt) & (R.h == 13)].copy()
    sub['mismo_signo'] = sub[list(periods)].apply(lambda x: (np.sign(x.dropna()) == np.sign(x.dropna().mean())).all() and x.notna().sum() >= 2, axis=1)
    print(f'\n==== {tgt}  h=13 semanas ====')
    print(sub.sort_values('IC_total', ascending=False)[['indicador','IC_total','t','n','1977-94','1995-09','2010-26','mismo_signo']].round(3).to_string(index=False))
