import pandas as pd, numpy as np
fred = pd.read_pickle('fred.pkl'); YN = pd.read_pickle('yields_sin_retraso.pkl'); S = pd.read_pickle('sinteticos.pkl')
tgt = pd.concat([fred['DFEDTAR'], fred['DFEDTARU']]).sort_index(); tgt = tgt[~tgt.index.duplicated(keep='last')]
print(tgt.loc['2024-06':].loc[lambda s: s.diff()!=0].to_string())
cuts = ['1989-06-06','1995-07-06','1998-09-29','2001-01-03','2007-09-18','2019-08-01','2024-09-19']
hikes = ['1988-03-30','1994-02-04','1997-03-25','1999-06-30','2004-06-30','2015-12-16','2022-03-17']
cum = lambda r: np.log1p(r).cumsum()
lv = pd.DataFrame({'y2': YN.DGS2, 'y10': YN.DGS10, 'curva': YN.DGS10-YN.DGS2,
                   'larg': cum(S.S_10Y), 'cort': cum(S.S_2Y), 'liq': cum(S.S_CASH), 'l30': cum(S.S_30Y)})
res = {}
for name, dates in [('bajadas', cuts), ('subidas', hikes)]:
    paths = []
    for d in dates:
        i = lv.index.searchsorted(pd.Timestamp(d))
        w = lv.iloc[i-26:i+53].reset_index(drop=True); w.index = range(-26, -26+len(w))
        base = w.loc[0]
        p = pd.DataFrame({'y2': (w.y2-base.y2)*100, 'y10': (w.y10-base.y10)*100, 'curva': (w.curva-base.curva)*100,
                          'largo_vs_corto_%': ((w.larg-base.larg)-(w.cort-base.cort))*100,
                          '10a_%': (w.larg-base.larg)*100, '30a_%': (w.l30-base.l30)*100, '2a_%': (w.cort-base.cort)*100})
        p['ciclo'] = d; paths.append(p)
    A = pd.concat(paths); res[name] = A
    m = A.groupby(level=0).median(numeric_only=True)
    pos = A.groupby(level=0)['largo_vs_corto_%'].apply(lambda x: (x>0).mean())
    print(f'\n=== Alrededor de la PRIMERA {name[:-1].upper()} (mediana de {len(dates)} ciclos; pb = puntos básicos) ===')
    t = m.loc[[-26,-13,-4,0,4,13,26,52]].round(1); t['% ciclos largo>corto'] = pos.loc[[-26,-13,-4,0,4,13,26,52]].round(2)
    print(t.to_string())
    # tabla por ciclo a +26 y +52
    print(A.loc[[26, 52]].reset_index().pivot(index='ciclo', columns='index', values=['y10','largo_vs_corto_%','30a_%']).round(1).to_string())
pd.to_pickle(res, 'ciclos.pkl')
