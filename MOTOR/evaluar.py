# Evalúa las ideas de índices: sola y conviviendo con la cartera base (5,20). 25-oct-2026.
import sys, json
sys.path.insert(0, '/home/claude/drive-pendiente/motor-de-cartera/codigo')
import recomendacion as RC, analisis as A, numpy as np, pandas as pd
from motor import metricas, HOY
O, D, M = RC.preparar('/home/claude/mejora-indices/listas')
desde = A.inicio_ventana(O[~O.lista.str.startswith('ix')]); CORTE = pd.Timestamp('2022-01-01')
EC = O.en_cartera.values; T = (O.t_entrada >= desde).values; W = EC & T
L = O.lista.values; act = O.activo.astype(str).values
IDX = ['SPX', 'DJI', 'NDX', 'RUT']
uni = {'cripto': L == 'cripto', 'petroleo': L == 'petroleo', 'x_petroleo': L == 'x_petroleo',
       'E1ind': (L == 'bolsa_e1') & np.isin(act, IDX), 'c10': L == 'c10', 'oro': (L == 'metales') & (act == 'oro'), 'shy': L == 'shy'}
Wc = W & (L != 'acciones_v2')
FL = dict(freno=(4, 0.5), freno_modo='latente', prioridad='descorr')
te = pd.to_datetime(O.t_entrada).values; ts = pd.to_datetime(O.t_salida).values


def mk(ks, extra=None, quita=None):
    m = np.zeros(len(O), bool)
    for k in ks:
        m |= uni[k]
    if quita is not None:
        m &= ~quita
    if extra is not None:
        m |= extra
    return m & Wc


BASEK = list(uni)


def ev(mask, tam=None, mult=1.0):
    c = dict(FL); c['mult'] = mult
    if tam is not None:
        c['tam_mult'] = tam
    rr = M.simular(c, mascara=mask)
    f = lambda a, b=None: metricas(M, rr.s, a, b, mascara=mask, eq=rr.eq)
    return [f(desde), f(desde, CORTE), f(CORTE)], rr


def peor(eq):
    e = eq[(eq.index >= desde) & (eq.index <= HOY)]; y = e.resample('YE').last().diff()
    y.iloc[0] = e.resample('YE').last().iloc[0] - e.iloc[0]
    return round(float(y.min()), 2), int(y.idxmin().year)


def mensual(eq):
    e = eq[(eq.index >= desde) & (eq.index <= HOY)]
    return e.resample('ME').last().diff().fillna(0)


# cripto: meses sin señal o perdiendo (en la cartera base)
B, rrB = ev(mk(BASEK))
cm = uni['cripto'] & Wc
mes_cr = mensual(M.curva(rrB.s, cm))
ent_cr = pd.Series(1, index=pd.to_datetime(O.t_entrada[cm])).resample('ME').sum().reindex(mes_cr.index).fillna(0)
flojo = (ent_cr == 0) | (mes_cr <= 0)
print('meses', len(mes_cr), 'flojos', int(flojo.sum()), 'sin señal', int((ent_cr == 0).sum()))
cr_ab_i = np.flatnonzero(cm)


def cripto_abierta(mask):
    r = np.zeros(len(O), bool)
    for i in np.flatnonzero(mask):
        r[i] = ((te[cr_ab_i] <= te[i]) & (ts[cr_ab_i] > te[i])).any()
    return r


def sola(m):
    m = m & Wc
    rr = M.simular(A.SIN_TOPES, mascara=m); eq = M.curva(rr.s, m)
    a = metricas(M, rr.s, desde, mascara=m, eq=eq); i = metricas(M, rr.s, desde, CORTE, mascara=m, eq=eq); o = metricas(M, rr.s, CORTE, mascara=m, eq=eq)
    mm = mensual(eq)
    return dict(n=a['n'], R_ano=round(a['R_ano'], 2), caida=round(a['caida'], 2), ratio=round(a['Rano_caida'], 2) if a['caida'] > 0 else None,
                acierto=round(100 * a['acierto'], 1), peor=peor(eq), ratio_IS=round(i['Rano_caida'], 2), ratio_OOS=round(o['Rano_caida'], 2),
                corr_cripto=round(float(mm.corr(mes_cr)), 2), R_mes_flojo=round(float(mm[flojo].mean()), 2),
                R_mes_bueno=round(float(mm[~flojo].mean()), 2), pct_pos_flojo=round(100 * float((mm[flojo] > 0).mean()), 0),
                corr_flojo=round(float(mm[flojo].corr(mes_cr[flojo])), 2))


rows = []
R0 = dict(variante='BASE (5,20)', Ra=round(B[0]['R_ano'], 2), caida=round(B[0]['caida'], 2), ratio=round(B[0]['Rano_caida'], 3),
          IS_Ra=round(B[1]['R_ano'], 2), IS_ratio=round(B[1]['Rano_caida'], 3), OOS_Ra=round(B[2]['R_ano'], 2), OOS_ratio=round(B[2]['Rano_caida'], 3))
rows.append(R0); print(R0, flush=True)
MASKS = {}


def reg(nombre, idea, nueva, quita=None, tam=None, solo=None):
    m = mk(BASEK, nueva, quita); r, rr = ev(m, tam)
    ok = all(r[i]['Rano_caida'] > B[i]['Rano_caida'] and r[i]['R_ano'] > B[i]['R_ano'] for i in range(3))
    s = sola(solo if solo is not None else nueva) if (solo is not None or nueva is not None) else {}
    # aporte en meses flojos de cripto dentro de la cartera
    dm = mensual(rr.eq) - mensual(rrB.eq)
    row = dict(idea=idea, variante=nombre, **{'sola_' + k: v for k, v in s.items()},
               Ra=round(r[0]['R_ano'], 2), caida=round(r[0]['caida'], 2), ratio=round(r[0]['Rano_caida'], 3),
               IS_Ra=round(r[1]['R_ano'], 2), IS_ratio=round(r[1]['Rano_caida'], 3), OOS_Ra=round(r[2]['R_ano'], 2), OOS_ratio=round(r[2]['Rano_caida'], 3),
               dif_cartera_mes_flojo=round(float(dm[flojo].mean()), 2), pasa=ok)
    rows.append(row); MASKS[nombre] = (m, tam); print(row, flush=True)


ixa = (L == 'ixa') & Wc
# A2: solo los índices con E1 positiva ANTES de la ventana (1990-2017): elegido sin mirar 2018-26
pre = O[(L == 'ixa') & (O.t_entrada < desde).values].groupby('activo').r_bruto.agg(['mean', 'size'])
buenos = list(pre[pre['mean'] > 0.05].index); print('historia previa ixa', pre.round(3).to_dict(), 'elegidos', buenos)
reg('A1 E1 en 6 índices de fuera', 'A', ixa)
reg('A2 E1 fuera, solo los que ganaban antes de 2018 (' + ','.join(buenos) + ')', 'A', ixa & np.isin(act, buenos))
reg('B1 cortos bajo media 200 (S&P, Nasdaq, Dow, DAX)', 'B', (L == 'ixb') & Wc)
e1 = uni['E1ind'] & Wc
reg('C0 control: E1 EE. UU. regenerada (salida media 5)', 'C', (L == 'ixc0') & Wc, quita=uni['E1ind'])
reg('C1 E1 con stop que sube (máx − 2,5 ATR, 15 días)', 'C', (L == 'ixc1') & Wc, quita=uni['E1ind'])
reg('C2 E1 con salida media de 10 (15 días)', 'C', (L == 'ixc2') & Wc, quita=uni['E1ind'])
reg('D1 tendencia: retroceso a media 20 con 50>200', 'D', (L == 'ixd') & Wc)
ab = cripto_abierta(e1)
reg('E1 E1 EE. UU. solo sin cripto abierta', 'E', e1 & ~ab, quita=uni['E1ind'])
tam = np.ones(len(O)); tam[e1 & ~ab] = 2.0
reg('E2 E1 EE. UU. ×2 cuando no hay cripto abierta', 'E', None, tam=tam, solo=e1)
reg('F1 quitar RUT de la E1', 'F', None, quita=uni['E1ind'] & (act == 'RUT'), solo=e1 & (act == 'RUT'))
reg('F2 quitar RUT y DJI de la E1', 'F', None, quita=uni['E1ind'] & np.isin(act, ['RUT', 'DJI']), solo=e1 & np.isin(act, ['RUT', 'DJI']))
pd.DataFrame(rows).to_csv('/home/claude/mejora-indices/resultados.csv', index=False)
json.dump(dict(desde=str(desde), flojos=int(flojo.sum()), meses=len(mes_cr), sin_senal=int((ent_cr == 0).sum()),
               mes_cr_flojo=round(float(mes_cr[flojo].mean()), 2)), open('/home/claude/mejora-indices/meta.json', 'w'))


def escala(m, tam, obj=15.3):
    lo, hi = 0.5, 3.0
    for _ in range(16):
        mid = (lo + hi) / 2; r, _ = ev(m, tam, mid)
        if r[0]['caida'] <= obj: lo = mid
        else: hi = mid
    r, _ = ev(m, tam, lo); return lo, r


esc = {}
lo, r = escala(mk(BASEK), None); esc['BASE'] = (round(lo, 3), round(r[0]['R_ano'], 2), round(r[0]['caida'], 2), round(r[1]['R_ano'], 2), round(r[2]['R_ano'], 2))
for row in rows[1:]:
    if row['pasa']:
        m, t = MASKS[row['variante']]; lo, r = escala(m, t)
        esc[row['variante']] = (round(lo, 3), round(r[0]['R_ano'], 2), round(r[0]['caida'], 2), round(r[1]['R_ano'], 2), round(r[2]['R_ano'], 2))
print('ESCALADO', esc)
json.dump(esc, open('/home/claude/mejora-indices/escalado.json', 'w'), ensure_ascii=False)
