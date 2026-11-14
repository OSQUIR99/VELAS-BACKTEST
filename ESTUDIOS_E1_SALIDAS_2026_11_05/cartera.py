# -*- coding: utf-8 -*-
"""Pasos 2 y 3 del documento 23: la E1 de índices con cada salida, conviviendo con la cartera base vigente fiel
(7,28 / 6,55 / 8,23; registro, 2-nov 23:45) en el motor real (velas-backtest/MOTOR vía ESTUDIOS_CAIDAS_2026_10/comun.py):
topes de 20 R y de bloque (~10 R con correlación), máximo 5 R por operación, freno de racha con la cartera valorada
(4 R → × 0,5) y prioridad por descorrelación; E1 de índices, Connors y cortos de bolsa FUERA del freno (2-nov); K8.
Montaje copiado de contexto-cartera/HERRAMIENTAS/estudios/ruptura-maximos-cartera/harness.py; solo cambia la lista
bolsa_e1 (generada con gen_e1.py: el generador original, cambiando solo la salida de los índices).
Uso: python3 cartera.py <carpeta_listas_e1> <lista_cripto_base (sin .parquet)>"""
import sys, os, glob, json, tempfile, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/velas-backtest/ESTUDIOS_CAIDAS_2026_10')
import numpy as np, pandas as pd
import comun

GH = '/home/claude/velas-backtest/MOTOR/listas'
REC = '/home/claude/velas-backtest/MOTOR/listas_reconstruidas'
LIS = sys.argv[1] if len(sys.argv) > 1 else 'listas'
CRI = sys.argv[2] if len(sys.argv) > 2 else 'base/B_puntos'
SAL = sys.argv[3].split(',') if len(sys.argv) > 3 else ['base', 'seguir5', 'rsi90', 'minant']
ETQ = sys.argv[4] if len(sys.argv) > 4 else 'principal'
IDX = ['SPX', 'DJI', 'NDX']


def cartera(e1):
    tmp = tempfile.mkdtemp(prefix='e1conv_')
    for p in glob.glob(GH + '/*.parquet'):
        b = os.path.basename(p)
        if b.startswith('cripto_realista') or b.startswith('bolsa_e1'):
            continue
        os.symlink(p, os.path.join(tmp, b))
    pd.read_parquet(CRI + '.parquet').to_parquet(tmp + '/cripto_realista.parquet')
    pd.read_parquet(CRI + '_diario.parquet').to_parquet(tmp + '/cripto_realista_diario.parquet')
    if e1 == 'oficial':
        for s in ('', '_diario'):
            os.symlink(f'{GH}/bolsa_e1{s}.parquet', f'{tmp}/bolsa_e1{s}.parquet')
    else:
        for s in ('', '_diario'):
            os.symlink(os.path.abspath(f'{LIS}/bolsa_e1_{e1}{s}.parquet'), f'{tmp}/bolsa_e1{s}.parquet')
    comun.LISTAS_GH = tmp
    return comun.Cartera(extra=(REC,))


def mascaras(C):  # = harness.mascaras
    O = C.O; L = C.L; act = C.act; d = (O.t_entrada >= C.desde).values
    W = C.W | (d & np.isin(L, ['corto_petroleo', 'n1_vixvxv', 'corto_indices_credito', 'corto_sector', 'yt_connors_qqq']))
    E1 = (L == 'bolsa_e1') & np.isin(act, IDX) & W
    nucleo = (np.isin(L, ['cripto', 'petroleo', 'corto_petroleo', 'x_petroleo', 'c10', 'shy']) | E1 | ((L == 'metales') & (act == 'oro'))) & W
    ex = np.isin(L, ['corto_sector', 'corto_indices_credito']) & W; cn = (L == 'yt_connors_qqq') & W
    C.cortos_exentos = ex
    return dict(BASE=nucleo | ex | cn, EX=ex | E1 | cn, E1=E1, cn=cn, ex=ex, W=W, d=d)


def k8(C):  # = harness.k8
    L = C.L; s = C.O['senal'].astype(str).values if 'senal' in C.O.columns else np.array([''] * len(C.O)); t = np.ones(len(L))
    t[L == 'corto_petroleo'] = 2.0; t[(L == 'petroleo') & (s == 'L2')] = 0.5
    t[(L == 'petroleo') & (s == 'tras-noticia (bajada)')] = 0.5; t[L == 'x_petroleo'] = 0.75
    return t


def tramo(e, a, b=None):
    return comun.met_eq(e, pd.Timestamp(a), pd.Timestamp(b) if b else None)


def riesgo_e1(C, r, m):
    """Riesgo abierto de la E1 de índices por día natural (stop fijo: riesgo = tamaño × tam_R mientras está abierta)."""
    Mo = C.M; k = np.flatnonzero(m & (r.s > 0)); v = np.zeros(Mo.ndias + 2); n = np.zeros(Mo.ndias + 2)
    for j in k:
        a, b = Mo.ent_dia[j], Mo.sal_dia[j]
        v[a:b] += r.s[j] * Mo.r0[j]; n[a:b] += 1
    idx = pd.date_range(pd.Timestamp(Mo.dia0), periods=len(v), freq='D')
    S = pd.DataFrame({'riesgo': v, 'n': n}, index=idx)
    return S[(S.index >= C.desde) & (S.index <= comun.HOY)]


res, eqs, ops, e1c = {}, {}, {}, {}
for s in SAL:
    C = cartera(s); M = mascaras(C); tm = k8(C)
    r, e = C.sim(M['BASE'], exentas=M['EX'], tam_mult=tm)
    q = C.met3(e)
    E1 = M['E1']; mot = np.asarray(r.motivo)
    tomadas = E1 & (r.s > 0)
    RE = riesgo_e1(C, r, E1)
    otros = M['BASE'] & ~E1
    d = dict(
        q=q, P1=tramo(e, C.desde, '2024-01-01'), P2=tramo(e, '2024-01-01'), r24=tramo(e, '2024-01-01')['ratio'],
        media5=C.media5(e)[0],
        e1_senales=int(E1.sum()), e1_tomadas=int(tomadas.sum()),
        e1_tope20=int((E1 & (mot == 'tope 20 R')).sum()), e1_bloque=int((E1 & (mot == 'tope bloque')).sum()),
        otros_tope20=int((otros & (mot == 'tope 20 R')).sum()), otros_bloque=int((otros & (mot == 'tope bloque')).sum()),
        e1_R=float((r.s * C.M.rf)[tomadas].sum()), e1_R_op=float((r.s * C.M.rf)[tomadas].mean()),
        e1_riesgo_max=float(RE.riesgo.max()), e1_riesgo_medio_abierta=float(RE.riesgo[RE.n > 0].mean()),
        e1_dias_abierta=float((RE.n > 0).mean()), e1_n_max=int(RE.n.max()), e1_dias_3omas=int((RE.n >= 3).sum()),
        e1_dias_riesgo_3R=int((RE.riesgo >= 3).sum()), e1_dias_riesgo_5R=int((RE.riesgo >= 5).sum()))
    res[s] = d; eqs[s] = e; e1c[s] = C.M.curva(r.s, E1)
    # operaciones rechazadas (para comparar qué se pierde frente a la base)
    O = C.O
    ops[s] = pd.DataFrame({'id': O.id.values, 'lista': C.L, 'activo': C.act, 't_entrada': O.t_entrada.values,
                           'r_final': C.M.rf, 's': r.s, 'motivo': mot, 'en_base': M['BASE']})[M['BASE']]
    print(f'{s:9s}', C.fmt(q), f"| 24-26 {d['r24']:.2f} | media5 {d['media5']:.2f} | E1 {d['e1_tomadas']}/{d['e1_senales']} "
          f"R {d['e1_R']:.1f} | rech E1 20R {d['e1_tope20']} bloque {d['e1_bloque']} · otros 20R {d['otros_tope20']} bloque {d['otros_bloque']}"
          f" | riesgo E1 máx {d['e1_riesgo_max']:.2f} n máx {d['e1_n_max']} días≥3 {d['e1_dias_3omas']}", flush=True)
b0 = res[SAL[0]]['q']; e0 = eqs[SAL[0]]
for s in SAL[1:]:
    res[s]['pasa'] = all(res[s]['q'][i]['ratio'] > b0[i]['ratio'] for i in range(3))
    res[s]['boot'] = C.bootstrap(e0, eqs[s], 1000)
    print(f"{s:9s} pasa {res[s]['pasa']} | remuestreo {res[s]['boot']:.2f}", flush=True)
# qué operaciones de otras familias se pierden o se ganan frente a la base
X = ops[SAL[0]].set_index('id')
cmp = []
for s in SAL[1:]:
    Y = ops[s].set_index('id'); j = X[['lista', 's', 'r_final']].join(Y[['s']], rsuffix='_v', how='inner')
    j = j[~j.lista.eq('bolsa_e1')]
    perd = j[(j.s > 0) & (j.s_v == 0)]; gan = j[(j.s == 0) & (j.s_v > 0)]
    cmp.append(dict(salida=s, otras_perdidas=len(perd), R_perdido=float((perd.s * perd.r_final).sum()),
                    otras_ganadas=len(gan), R_ganado=float((gan.s_v * gan.r_final).sum()),
                    familias_perdidas=perd.lista.value_counts().to_dict()))
    print(cmp[-1], flush=True)
# peor caída de cada montaje (todo el periodo) y lo que pone la E1 dentro; E1 en los 10 peores meses de la base
def peor(e):
    e = e[(e.index >= C.desde) & (e.index <= comun.HOY)]; pk = e.cummax(); t = (pk - e).idxmax(); p = e[:t].idxmax()
    return p, t, float(pk[t] - e[t])
mb = C.mensual(e0); peores = mb.nsmallest(10).index
for s in SAL:
    p, t, dd = peor(eqs[s]); x = e1c[s]
    res[s]['peor_caida'] = dict(desde=str(p.date()), hasta=str(t.date()), caida=dd, e1_dentro=float(x[t] - x[p]))
    m1 = x[(x.index >= C.desde) & (x.index <= comun.HOY)].resample('ME').last().diff().reindex(peores).fillna(0)
    res[s]['e1_10_peores_meses'] = float(m1.sum())
    yrs = x[(x.index >= C.desde) & (x.index <= comun.HOY)]
    res[s]['e1_por_ano'] = {str(k): float(v) for k, v in yrs.resample('YE').last().diff().fillna(yrs.resample('YE').last().iloc[0] - yrs.iloc[0]).items()}
    print(f"{s:9s} peor caída {p.date()} → {t.date()} {dd:.1f} R · E1 dentro {res[s]['peor_caida']['e1_dentro']:+.1f} R · "
          f"E1 en los 10 peores meses de la base {res[s]['e1_10_peores_meses']:+.1f} R", flush=True)
json.dump(dict(res=res, cmp=cmp), open(f'res_{ETQ}.json', 'w'), ensure_ascii=False, indent=1, default=float)
pd.DataFrame(eqs).to_parquet(f'eq_{ETQ}.parquet')
