import pandas as pd, numpy as np
from scipy.stats import norm
F = pd.read_pickle('features.pkl'); M = pd.read_pickle('macro_semanal.pkl')
VENT = 520; MINP = 156
def z(s, win=VENT):
    m = s.rolling(win, min_periods=MINP).mean(); sd = s.rolling(win, min_periods=MINP).std()
    return ((s - m) / sd).clip(-3, 3)
X = pd.DataFrame(index=F.index)
# componentes (signo ya orientado: + = favorable)
X['prima_plazo'] = z(F.valor_prima_plazo.fillna(F.valor_real_10a_subyacente*np.nan))
X['tipo_real'] = z(F.valor_real_10a_subyacente)
X['pend_10a_3m'] = z(F.curva_10a_3m)
X['carry_10a_ff'] = z(F.carry_10a_menos_ff)
X['tramo_corto_2a_ff'] = z(-F.fed_2a_menos_ff)      # 2 años por encima del tipo Fed
X['cond_financieras'] = z(-F.riesgo_nfci)
X['y10_vs_media5a'] = z(F.valor_y10_vs_media5a)
X['dolar_13s'] = z(F.dolar_13s)
BLOQ_D = {'Valoración': (['prima_plazo','tipo_real'], 0.40),
          'Pendiente y carry': (['pend_10a_3m','carry_10a_ff','tramo_corto_2a_ff'], 0.45),
          'Condiciones financieras': (['cond_financieras'], 0.15)}
BLOQ_B = {'Valoración bonos': (['y10_vs_media5a','prima_plazo'], 0.45),
          'Pendiente': (['pend_10a_3m'], 0.30),
          'Dólar': (['dolar_13s'], 0.25)}
def build(bloques):
    parts = {}; tot = 0; wsum = 0
    for b, (cols, w) in bloques.items():
        v = X[cols].mean(axis=1, skipna=True); parts[b] = v
        tot = tot + v.fillna(0)*w; wsum = wsum + v.notna()*w
    comp = tot / wsum.replace(0, np.nan)
    sd = comp.expanding(MINP).std()
    sc = pd.Series(100*norm.cdf(comp / sd), index=comp.index)
    return sc, pd.DataFrame(parts)
SD, PD_ = build(BLOQ_D); SB, PB = build(BLOQ_B)
out = pd.DataFrame({'score_duracion': SD, 'score_bonos_vs_acciones': SB})
out.to_pickle('scores.pkl'); X.to_pickle('componentes_z.pkl'); PD_.to_pickle('bloques_D.pkl'); PB.to_pickle('bloques_B.pkl')
print(out.dropna().iloc[::260].round(0).to_string()); print(out.tail(6).round(1).to_string())
print(X.tail(1).T.round(2).to_string())
