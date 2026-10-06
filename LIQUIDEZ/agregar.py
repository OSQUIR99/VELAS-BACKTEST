# -*- coding: utf-8 -*-
"""Reúne todas las cifras del informe en resultados.json."""
import pandas as pd, numpy as np, json
from core import HORAS_TF

R = {}
ACT = ['BTC', 'sp500', 'nasdaq100', 'oro', 'plata', 'brent']
TFS = ['1h', '4h', '1d']
ev1 = pd.read_parquet('ev1.parquet'); ev1 = ev1[ev1.k == 2.5]
ev2 = pd.read_parquet('ev2.parquet'); c2 = pd.read_parquet('ctrl2.parquet')
ev4 = pd.read_parquet('ev4.parquet'); vida = pd.read_parquet('ev_vida.parquet')
ev3 = pd.read_parquet('ev3.parquet')
b15 = pd.read_parquet('ev2_btc15.parquet'); c15 = pd.read_parquet('ctrl2_btc15.parquet'); f15 = pd.read_parquet('ev4_btc15.parquet')


def r3(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


# ---------- 1. Distancia al extremo contrario: P(llegar) por categoría (todos los activos) ----------
e = ev1.copy(); e['dist'] = e.leg_atr / e.ext
bins = [0, 3, 4, 5, 6, 8]; lab = ['<3', '3–4', '4–5', '5–6', '6–8']
e['bin'] = pd.cut(e.dist, bins, labels=lab)
t = e.pivot_table(index='bin', columns='cat', values='rompe', aggfunc='mean', observed=False) * 100
nn = e.pivot_table(index='bin', columns='cat', values='rompe', aggfunc='size', observed=False)
R['distancia'] = {'bins': lab, 'cats': {c: [r3(v) if nn.loc[b, c] >= 40 else None for b, v in zip(lab, t[c].values)] for c in t.columns}}
R['dist_mediana'] = {c: r3(v) for c, v in e.groupby('cat').dist.median().items()}

# ---------- 2. Tramo y tendencia por activo/tf/categoría ----------
orden = ['ruptura', 'barrido', 'doble', 'ml_extremo', 'ml_alto']
w = ev1[ev1.res.isin([1, -1])].copy(); w['p0'] = 1 / (1 + w.R_obj); w['exc'] = (w.res == 1) - w.p0
tab = {}
for a in ACT:
    tab[a] = {}
    for tf in TFS:
        g = ev1[(ev1.activo == a) & (ev1.tf == tf)]; gw = w[(w.activo == a) & (w.tf == tf)]
        h = HORAS_TF[tf]
        tab[a][tf] = {}
        for c in orden:
            x = g[g.cat == c]; xw = gw[gw.cat == c]
            if len(x) < 10:
                continue
            se = xw.exc.std() / np.sqrt(len(xw)) if len(xw) > 2 else np.nan
            tab[a][tf][c] = dict(n=int(len(x)), tramo_pct=r3(100 * x.leg_pct.median()), tramo_h=r3(x.leg_bars.median() * h),
                                 tend_pct=r3(100 * x.tend_pct.median()), tend_h=r3(x.tend_bars.median() * h),
                                 rompe=r3(100 * x.rompe.mean()), er=r3(x.er.median()), hh=r3(x.hh_seguidos.mean()),
                                 ventaja=r3(100 * xw.exc.mean()), z=r3(xw.exc.mean() / se) if se and se > 0 else None)
R['tramos'] = tab
# global por categoría
g = {}
for c in orden:
    x = ev1[ev1.cat == c]; xw = w[w.cat == c]
    g[c] = dict(n=int(len(x)), tramo_atr=r3(x.leg_atr.median()), er=r3(x.er.median()), rompe=r3(100 * x.rompe.mean()),
                ventaja=r3(100 * xw.exc.mean()), z=r3(xw.exc.mean() / (xw.exc.std() / np.sqrt(len(xw)))), hh=r3(x.hh_seguidos.mean()),
                tend_atr=r3(x.tend_atr.median()))
R['tramos_global'] = g

# ---------- 3. Vida de los niveles pendientes vs precio cualquiera ----------
v = vida.pivot_table(index=['activo', 'tf', 'H'], columns='tipo', values='barrido', aggfunc='mean') * 100
R['vida'] = {}
for (a, tf, H), row in v.iterrows():
    R['vida'].setdefault(a, {}).setdefault(tf, []).append(dict(H=int(H), real=r3(row['nivel pendiente']), azar=r3(row['precio cualquiera'])))
vg = vida.pivot_table(index=['tf', 'H'], columns='tipo', values='barrido', aggfunc='mean') * 100
R['vida_global'] = {tf: [dict(H=int(H), real=r3(vg.loc[(tf, H), 'nivel pendiente']), azar=r3(vg.loc[(tf, H), 'precio cualquiera'])) for H in vg.loc[tf].index] for tf in TFS}
e2 = ev2[ev2.k == 2.5]
dej = e2[e2.dejado]
R['dejados_alguna_vez'] = {a: r3(100 * dej[dej.activo == a].roto.mean()) for a in ACT}
R['dejados_espera_mediana_h'] = {a: {tf: r3(dej[(dej.activo == a) & (dej.tf == tf) & dej.roto].espera.median() * HORAS_TF[tf]) for tf in TFS} for a in ACT}

# ---------- 4. Giro al perforar: real vs azar ----------
r = e2[e2.res.isin([1, -1])]; c = c2[(c2.k == 2.5) & c2.res.isin([1, -1])]
R['giro'] = {a: {tf: dict(real=r3(100 * (r[(r.activo == a) & (r.tf == tf)].res == 1).mean()),
                          azar=r3(100 * (c[(c.activo == a) & (c.tf == tf)].res == 1).mean()),
                          n=int(((r.activo == a) & (r.tf == tf)).sum())) for tf in TFS} for a in ACT}
R['giro']['BTC']['15m'] = dict(real=r3(100 * (b15[b15.res.isin([1, -1])].res == 1).mean()),
                               azar=r3(100 * (c15[c15.res.isin([1, -1])].res == 1).mean()), n=int(b15.res.isin([1, -1]).sum()))
R['giro_global'] = dict(real=r3(100 * (r.res == 1).mean()), azar=r3(100 * (c.res == 1).mean()))
R['giro_cierre'] = {str(k): dict(real=r3(100 * (r[r.cierra_dentro == k].res == 1).mean()), azar=r3(100 * (c[c.cierra_dentro == k].res == 1).mean()),
                                 n=int((r.cierra_dentro == k).sum())) for k in [True, False]}

# ---------- 5. Qué anticipa giro o ruptura (univariante, todos los activos) ----------
rr = r.copy(); rr['giro'] = (rr.res == 1) * 100
feat = {}
for col, nom in [('compr', 'Volatilidad reciente / volatilidad de fondo'), ('rsi', 'RSI al llegar al nivel'),
                 ('vel', 'Velocidad de llegada (ATR en 10 velas)'), ('edad', 'Antigüedad del nivel (velas)'),
                 ('dist_sig', 'Distancia al siguiente nivel pendiente (ATR)')]:
    q = pd.qcut(rr[col], 4, duplicates='drop')
    gg = rr.groupby(q, observed=True).giro.agg(['mean', 'size'])
    feat[nom] = [dict(tramo=f'{iv.left:.2f} a {iv.right:.2f}', giro=r3(m), n=int(s)) for iv, (m, s) in zip(gg.index, gg.values)]
tq = rr.groupby(rr.n_toques.clip(upper=3)).giro.agg(['mean', 'size'])
feat['Toques del mismo nivel (suelos/techos iguales)'] = [dict(tramo={1: '1 (nivel simple)', 2: '2 (doble)', 3: '3 o más'}[int(k)], giro=r3(m), n=int(s)) for k, (m, s) in tq.iterrows()]
pq = pd.cut(rr.prof, [-0.01, 0.3, 0.7, 1.2, 99], labels=['<0,3 ATR', '0,3–0,7', '0,7–1,2', '>1,2'])
gg = rr.groupby(pq, observed=True).giro.agg(['mean', 'size'])
feat['Profundidad de la perforación (vela de rotura)'] = [dict(tramo=str(k), giro=r3(m), n=int(s)) for k, (m, s) in gg.iterrows()]
R['rasgos'] = feat

# ---------- 6. Estrategias (R neto y 20x) ----------
def st(s):
    s = s.dropna()
    return dict(n=int(len(s)), R=r3(s.mean()), z=r3(s.mean() / (s.std() / np.sqrt(len(s)))) if len(s) > 2 else None)

estr = {}
for tf in TFS:
    g2 = e2[e2.tf == tf]; g4 = ev4[ev4.tf == tf]
    estr[tf] = {
        'Anticipar: orden límite en el nivel': st(g2.E1_R),
        'Confirmar: cierre de vuelta dentro (2R)': st(g2.E2_R),
        'Confirmar en niveles al azar (control)': st(c2[(c2.k == 2.5) & (c2.tf == tf)].E2_R),
        'SMC tras barrido → liquidez opuesta': st(g4[g4.cat == 'barrido'].op),
        'SMC en mínimo más alto → liquidez opuesta': st(g4[g4.cat == 'ml_cerca'].op),
        'SMC en suelo/techo igual → liquidez opuesta': st(g4[g4.cat == 'doble'].op),
        'Ruptura de máximo → largo (2R)': st(g2[g2.lado == 'corto'].E3_R),
        'Ruptura de mínimo → corto (2R)': st(g2[g2.lado == 'largo'].E3_R),
    }
estr['15m'] = {
    'Anticipar: orden límite en el nivel': st(b15.E1_R),
    'Confirmar: cierre de vuelta dentro (2R)': st(b15.E2_R),
    'Confirmar en niveles al azar (control)': st(c15.E2_R),
    'SMC tras barrido → liquidez opuesta': st(f15[f15.cat == 'barrido'].op),
    'SMC en mínimo más alto → liquidez opuesta': st(f15[f15.cat == 'ml_cerca'].op),
    'SMC en suelo/techo igual → liquidez opuesta': st(f15[f15.cat == 'doble'].op),
    'Ruptura de máximo → largo (2R)': st(b15[b15.lado == 'corto'].E3_R),
    'Ruptura de mínimo → corto (2R)': st(b15[b15.lado == 'largo'].E3_R),
}
R['estrategias'] = estr
# por activo: las 4 claves
pa = {}
for a in ACT:
    pa[a] = {}
    for tf in TFS:
        g2 = e2[(e2.activo == a) & (e2.tf == tf)]; g4 = ev4[(ev4.activo == a) & (ev4.tf == tf)]
        pa[a][tf] = {
            'confirmar': st(g2.E2_R), 'smc_barrido': st(g4[g4.cat == 'barrido'].op), 'smc_ml': st(g4[g4.cat == 'ml_cerca'].op),
            'smc_doble': st(g4[g4.cat == 'doble'].op),
            'rup_max_largo': st(g2[g2.lado == 'corto'].E3_R), 'rup_min_corto': st(g2[g2.lado == 'largo'].E3_R),
            'm20_rup_max': r3(100 * g2[g2.lado == 'corto'].E3_m.mean()), 'liq_rup_max': r3(100 * (g2[g2.lado == 'corto'].E3_m <= -0.999).mean()),
            'm20_confirmar': r3(100 * g2.E2_m.mean()), 'stop_confirmar': r3(100 * g2.E2_stop_pct.median()),
        }
R['por_activo'] = pa
# estabilidad temporal SMC
x = ev4.copy(); x['mitad'] = x.groupby(['activo', 'tf']).fecha.transform(lambda s: np.where(s <= s.median(), '1a', '2a'))
R['mitades_smc'] = {c: {m: r3(x[(x.cat == c) & (x.mitad == m)].op.mean()) for m in ['1a', '2a']} for c in ['barrido', 'ml_cerca', 'doble', 'sin_nivel']}
R['mitades_fechas'] = {f'{a} {tf}': str(x[(x.activo == a) & (x.tf == tf)].fecha.median().date()) for a in ACT for tf in TFS}
x2 = e2.copy(); x2['mitad'] = x2.groupby(['activo', 'tf']).fecha.transform(lambda s: np.where(s <= s.median(), '1a', '2a'))
R['mitades_rup'] = {tf: {m: r3(x2[(x2.tf == tf) & (x2.mitad == m) & (x2.lado == 'corto')].E3_R.mean()) for m in ['1a', '2a']} for tf in TFS}

# ---------- 7. Desequilibrio / imán ----------
m = ev3[ev3.res.isin([1, -1])].copy(); m['arriba'] = (m.res == 1) * 100.0; m['esp'] = m.p_azar * 100
m['ratio'] = pd.cut(m.du / (m.du + m.dd), [0, 0.2, 0.4, 0.6, 0.8, 1])
gg = m.groupby('ratio', observed=True)[['arriba', 'esp']].mean()
R['iman_dist'] = [dict(tramo=f'{iv.left:.1f}–{iv.right:.1f}', real=r3(row.arriba), azar=r3(row.esp)) for iv, row in gg.iterrows()]
m['deseq'] = (m.nu5 - m.nd5).clip(-3, 3)
gg = m.groupby('deseq')[['arriba', 'esp', 'f50']].mean(); ns = m.groupby('deseq').size()
R['iman_deseq'] = [dict(deseq=int(k), real=r3(row.arriba), azar=r3(row.esp), f50=r3(row.f50), n=int(ns[k])) for k, row in gg.iterrows()]
m['rac'] = np.sign(m.cu - m.cd)
R['iman_racimo'] = {str(int(k)): dict(exc=r3((g.arriba - g.esp).mean()), n=int(len(g))) for k, g in m.groupby('rac')}

# ---------- 8. BTC interés abierto ----------
b = pd.read_parquet('ev2_btc.parquet'); b = b[b.res.isin([1, -1]) & b.oi_vela.notna() & (b.k == 2.5)].copy(); b['giro'] = (b.res == 1) * 100
b['oi_q'] = b.groupby('tf').oi_vela.transform(lambda s: pd.qcut(s, 4, labels=['Cae mucho', 'Cae algo', 'Sube algo', 'Sube mucho']))
b['prof_q'] = pd.cut(b.prof, [-0.01, 0.3, 0.7, 1.2, 99], labels=['<0,3 ATR', '0,3–0,7', '0,7–1,2', '>1,2'])
t = b.pivot_table(index='oi_q', columns='prof_q', values='giro', aggfunc='mean', observed=False)
nn = b.pivot_table(index='oi_q', columns='prof_q', values='giro', aggfunc='size', observed=False)
R['btc_oi'] = {'filas': list(t.index.astype(str)), 'cols': list(t.columns.astype(str)), 'giro': [[r3(v) for v in row] for row in t.values], 'n': nn.values.tolist(),
               'umbral': {tf: r3(b[b.tf == tf].oi_vela.quantile(0.25)) for tf in TFS},
               'E2': {q: r3(b[b.oi_q == q].E2_R.mean()) for q in ['Cae mucho', 'Cae algo', 'Sube algo', 'Sube mucho']}}

# ---------- 9. Muestras y periodos ----------
R['muestras'] = {a: {tf: int(((e2.activo == a) & (e2.tf == tf)).sum()) for tf in TFS} for a in ACT}
json.dump(R, open('resultados.json', 'w'), ensure_ascii=False)
print('ok', len(json.dumps(R)))

# ---------- 10. Sensibilidad a comisiones (SMC con entrada y objetivo límite: 0,02 %; stop a mercado: 0,05 %) ----------
R = json.load(open('resultados.json'))
x = ev4.copy()
x['bruto'] = x['op'] + 0.001 / x.riesgo_pct
x['maker'] = x.bruto - np.where(x['op'] > 0, 0.0004, 0.0007) / x.riesgo_pct
com = {}
for tf in TFS:
    com[tf] = {c: dict(bruto=r3(x[(x.tf == tf) & (x.cat == c)].bruto.mean()), taker=r3(x[(x.tf == tf) & (x.cat == c)]['op'].mean()),
                       maker=r3(x[(x.tf == tf) & (x.cat == c)].maker.mean()), riesgo=r3(100 * x[(x.tf == tf) & (x.cat == c)].riesgo_pct.median()))
               for c in ['barrido', 'ml_cerca', 'doble', 'sin_nivel']}
y = f15.copy(); y['bruto'] = y['op'] + 0.001 / y.riesgo_pct; y['maker'] = y.bruto - np.where(y['op'] > 0, 0.0004, 0.0007) / y.riesgo_pct
com['15m'] = {c: dict(bruto=r3(y[y.cat == c].bruto.mean()), taker=r3(y[y.cat == c]['op'].mean()), maker=r3(y[y.cat == c].maker.mean()), riesgo=r3(100 * y[y.cat == c].riesgo_pct.median())) for c in ['barrido', 'ml_cerca', 'doble', 'sin_nivel']}
R['comisiones_smc'] = com
# SMC 20x: rentabilidad media por operación sobre margen y % liquidadas (taker)
R['smc_20x'] = {tf: {c: dict(m=r3(100 * x[(x.tf == tf) & (x.cat == c)].op_m.mean()), liq=r3(100 * (x[(x.tf == tf) & (x.cat == c)].op_m <= -0.999).mean()))
                     for c in ['barrido', 'ml_cerca', 'doble']} for tf in TFS}
json.dump(R, open('resultados.json', 'w'), ensure_ascii=False)
print(json.dumps(com, ensure_ascii=False)); print(json.dumps(R['smc_20x']))
