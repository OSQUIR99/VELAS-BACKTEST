import pandas as pd, numpy as np
exec(open('backtest.py').read().split("rows = {}")[0])
print('Peso medio en acciones con B:', round(eq.mean(),3))
r, to = run(w_const(SPY=eq.mean(), IEF=1-eq.mean()), cada=4); print('Fijo con ese mismo peso medio:', {k: round(v,2) for k,v in stats(r,to).items()})
print('\nUmbrales del escalón (mensual):')
for alto, bajo in [(55,45),(60,40),(65,35),(70,30),(75,25),(80,20)]:
    r, to = run(escalon(D, alto, bajo), cada=4); s = stats(r, to); print(alto, bajo, {k: round(v,2) for k,v in s.items()})
print('\nEscalón usando BIL en vez de SHY abajo, e IEI en medio (desde 2007):')
def esc2(D, alto=65, bajo=35):
    w = pd.DataFrame(0.0, index=D.index, columns=['TLT','IEF','CASH'])
    w.loc[D >= alto, 'TLT'] = 1; w.loc[(D < alto) & (D >= bajo), 'IEF'] = 1; w.loc[D < bajo, 'CASH'] = 1; return w
r, to = run(esc2(D), cada=4); print({k: round(v,2) for k,v in stats(r,to).items()})
# z-score expansivo en vez de ventana 10 años
print('\nCon z-scores de ventana 5 años y expansiva:')
import importlib, score
for win in [260, 10000]:
    src = open('score.py').read().replace('VENT = 520', f'VENT = {win}').replace("out.to_pickle('scores.pkl')", "out.to_pickle(f'scores_{VENT}.pkl')").split("print(")[0]
    exec(src)
    D2 = pd.read_pickle(f'scores_{win}.pkl').score_duracion.loc[start:end]
    r, to = run(escalon(D2), cada=4); print(win, {k: round(v,2) for k,v in stats(r,to).items()})
# tiempo en cada tramo
print('\nTiempo en cada tramo (escalón 65/35):', escalon(D).mean().round(2).to_dict())
# aciertos: cuando D>=65, ¿TLT batió a SHY las 13 semanas siguientes?
Tg = pd.read_pickle('targets.pkl').loc[start:end]
for lo, hi in [(0,35),(35,65),(65,101)]:
    msk = (D>=lo)&(D<hi); x = Tg.loc[msk, 'TLT_vs_SHY_13'].dropna(); y = Tg.loc[msk, 'dY10_13'].dropna()
    print(f'D en [{lo},{hi}): semanas={msk.sum()}  TLT-SHY 13s media={x.mean()*100:.2f}%  acierto TLT>SHY={ (x>0).mean():.0%}  cambio 10a medio={y.mean()*100:.0f}pb')
Ts = pd.read_pickle('targets.pkl').loc['1977':'2002']; Dl = pd.read_pickle('scores.pkl').score_duracion.loc['1977':'2002']
print('\nHistoria larga 1977-2002 (bonos sintéticos, parte usada para elegir):')
for lo, hi in [(0,35),(35,65),(65,101)]:
    msk = (Dl>=lo)&(Dl<hi); x = Ts.loc[msk, 'syn_larg_vs_cort_13'].dropna(); y = Ts.loc[msk,'dY10_13'].dropna()
    print(f'D en [{lo},{hi}): semanas={msk.sum()}  10a-2a 13s media={x.mean()*100:.2f}%  acierto={ (x>0).mean():.0%}  cambio 10a medio={y.mean()*100:.0f}pb')
