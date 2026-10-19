# -*- coding: utf-8 -*-
"""Dominancias ENCIMA del montaje común de cripto (19-oct-2026). Pruebas P-DOM-1..3 del documento 02 y combinaciones nuevas.

Montaje común (documento 06; misma aproximación que el backtest del 16-oct, que dio +0,45 R en 2017-22 y +0,24 R en 2023-26):
  - Diario (último cierre ANTERIOR): subnota ≥ 3 de 4 (cierre > EMA50, cierre > EMA200, EMA50 > EMA200, EMA50 subiendo).
  - 4 h: EMA50 > EMA200; la vela toca la EMA20 y cierra encima (o la anterior cerró debajo y esta encima). Entrada: apertura siguiente.
  - Stop inicial: 2 ATR(14) de 4 h. 1/3 fuera en +1 R y stop a la entrada. Resto: stop que sube = máximo desde la entrada − 2,5 ATR diario.
  - Una operación por moneda a la vez. Monedas: BTC, ETH, SOL, ADA, LINK, ZEC (Binance contado).
Métricas de dominancia (diarias, último cierre ANTERIOR a la entrada; sin mirar el futuro):
  ETH/BTC, dominancia de BTC, dominancia de USDT, TOTAL3, OTHERS/TOTAL, capitalización total: pendiente de su media de 20 (a 5 días),
  precio sobre/bajo su media de 50, y rotura de resistencia viva (regla del documento 12).
Cada variable se mide POR SEPARADO (documento 00): R medio con y sin la condición, t, y por épocas 2018-21 / 2022-26 / 2024-26.
"""
import sys, os
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, AQUI)
from cargar import velas

MONEDAS = ['BTC', 'ETH', 'SOL', 'ADA', 'LINK', 'ZEC']
ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
def atr(d, n=14):
    pc = d.cierre.shift()
    tr = pd.concat([d.maximo - d.minimo, (d.maximo - pc).abs(), (d.minimo - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()

def operaciones(m):
    h = velas(m, '4h')[['apertura', 'maximo', 'minimo', 'cierre']].copy()
    d = velas(m, '1d')[['apertura', 'maximo', 'minimo', 'cierre']].copy()
    d['e50'], d['e200'] = ema(d.cierre, 50), ema(d.cierre, 200)
    d['sub'] = ((d.cierre > d.e50).astype(int) + (d.cierre > d.e200) + (d.e50 > d.e200) + (d.e50 > d.e50.shift()))
    d['atrd'] = atr(d)
    # valor del último diario cerrado ANTES de cada vela de 4 h
    dd = d[['sub', 'atrd']].shift(1)
    dd.index = dd.index  # fecha de la vela diaria d (abre 00:00) -> conocida desde el día d+1 00:00
    hd = dd.reindex(h.index.floor('D')).set_axis(h.index)
    h['e20'], h['e50'], h['e200'], h['atr'] = ema(h.cierre, 20), ema(h.cierre, 50), ema(h.cierre, 200), atr(h)
    o, hi, lo, c = (h[x].values for x in ['apertura', 'maximo', 'minimo', 'cierre'])
    e20, e50, e200, a4 = h.e20.values, h.e50.values, h.e200.values, h.atr.values
    sub, ad = hd['sub'].values, hd['atrd'].values
    t = h.index
    ops, i, n = [], 300, len(h)
    while i < n - 1:
        senal = (sub[i] >= 3) and e50[i] > e200[i] and c[i] > e20[i] and (lo[i] <= e20[i] or c[i - 1] < e20[i - 1])
        if not senal or np.isnan(ad[i]):
            i += 1; continue
        ent = o[i + 1]; R = 2 * a4[i]; stop = ent - R; parcial = False; maxh = ent; res = 0.0; j = i + 1
        while j < n:
            if lo[j] <= stop:
                salida = min(stop, o[j]) if o[j] < stop else stop
                res += (2 / 3 if parcial else 1) * (salida - ent) / R; break
            if not parcial and hi[j] >= ent + R:
                res += (1 / 3) * 1.0; parcial = True; stop = max(stop, ent)
            maxh = max(maxh, hi[j])
            if parcial:
                stop = max(stop, maxh - 2.5 * ad[j])
            j += 1
        else:
            res += (2 / 3 if parcial else 1) * (c[-1] - ent) / R
        ops.append({'moneda': m, 'entrada': t[i + 1], 'salida': t[min(j, n - 1)], 'R': res})
        i = j + 1
    return pd.DataFrame(ops)

def metricas_diarias():
    c = lambda a: velas(a, '1d').cierre
    S = {'ETH_BTC': c('ETH_BTC'), 'BTC.D': c('dominancia_btc'), 'USDT.D': c('dominancia_usdt'), 'TOTAL3': c('total3_sin_btc_eth'),
         'OTHERS/TOTAL': (c('others_fuera_top10') / c('capitalizacion_total')).dropna(), 'TOTAL': c('capitalizacion_total')}
    F = {}
    for k, s in S.items():
        m20 = s.rolling(20).mean()
        F[f'{k} media20 sube'] = (m20 > m20.shift(5))
        F[f'{k} sobre media50'] = (s > s.rolling(50).mean())
    # roturas vivas (documento 12) de ETH/BTC y TOTAL3
    from dominancias import zonas_por_dia, roturas
    import dominancias as D
    for k, arch in (('ETH_BTC', 'ETH_BTC'), ('TOTAL3', 'total3_sin_btc_eth'), ('OTHERS', 'others_fuera_top10')):
        D.TOL, D.CERCA = 0.02, 0.03
        dd = velas(arch, '1d'); dd = dd[dd.index >= '2016-01-01']
        ev = roturas(dd, zonas_por_dia(dd))
        viva = pd.Series(False, dd.index)
        for f, L, _ in ev:
            fin = f + pd.Timedelta(days=28); tramo = dd.loc[f:fin]
            rotas = tramo.index[tramo.cierre < L * 0.96]
            if len(rotas): fin = min(fin, rotas[0])
            viva.loc[f:fin] = True
        F[f'{k} rotura viva'] = viva
    F = pd.DataFrame(F).astype(float)
    return F.shift(0)   # valor al cierre del día d; se usa desde d+1 (ver más abajo)

def t_stat(a, b):
    if len(a) < 5 or len(b) < 5: return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))

if __name__ == '__main__':
    ops = pd.concat([operaciones(m) for m in MONEDAS], ignore_index=True)
    F = metricas_diarias()
    dia = ops.entrada.dt.floor('D') - pd.Timedelta(days=1)          # último cierre diario anterior a la entrada
    X = pd.concat([ops, F.reindex(dia).reset_index(drop=True)], axis=1)
    X['epoca'] = np.where(X.entrada < '2022', '2018-21', '2022-26')
    X = X[X.entrada >= '2018-01-01'].reset_index(drop=True)
    X.to_csv(os.path.join(AQUI, 'montaje_dominancias_ops.csv'), index=False)
    print('MONTAJE (comprobación): operaciones', len(X))
    for ep, g in [('2018-22', X[X.entrada < '2023']), ('2023-26', X[X.entrada >= '2023'])]:
        print(f'  {ep}: n={len(g)}  R medio={g.R.mean():+.2f}  acierto={(g.R > 0).mean():.0%}')
    filas = []
    grupos = {'todas': X.moneda.notna(), 'BTC': X.moneda == 'BTC', 'ETH': X.moneda == 'ETH',
              'altcoins': X.moneda.isin(['SOL', 'ADA', 'LINK', 'ZEC'])}
    for gnom, gm in grupos.items():
        for var in F.columns:
            G = X[gm & X[var].notna()]
            si, no = G[G[var] == 1].R, G[G[var] == 0].R
            fila = {'grupo': gnom, 'variable': var, 'n_si': len(si), 'R_si': si.mean(), 'n_no': len(no), 'R_no': no.mean(),
                    'dif': si.mean() - no.mean(), 't': t_stat(si, no)}
            for ep, a, b in (('18-21', '2018', '2022'), ('22-26', '2022', '2027'), ('24-26', '2024', '2027')):
                E = G[(G.entrada >= a) & (G.entrada < b)]
                fila[f'dif_{ep}'] = E[E[var] == 1].R.mean() - E[E[var] == 0].R.mean()
            fila['mismo_signo_3'] = all(np.sign(fila[f'dif_{e}']) == np.sign(fila['dif']) for e in ('18-21', '22-26', '24-26'))
            filas.append(fila)
    T = pd.DataFrame(filas)
    T.to_csv(os.path.join(AQUI, 'montaje_dominancias_variables.csv'), index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
    print(T.round(2).sort_values(['grupo', 't'], ascending=[True, False]).to_string(index=False))
