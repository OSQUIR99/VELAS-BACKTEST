"""Fases objetivas para el panel (6.2 y 6.3): caja de Wyckoff, máquina de estados A-E, posición calibrada
en la caja y retroceso de Elliott medido. Solo numpy y pandas. Reglas congeladas tal como se probaron (13-oct-2026).

Entrada: un DataFrame de velas YA CERRADAS con columnas open, high, low, close, volume e índice de fechas UTC.
Para la máquina de 4h conviene dar al menos 2.000 velas (la máquina depende del camino y necesita arrancar de lejos).

Qué devuelve cada función está en su docstring. Las probabilidades salen de BTC, ETH y 10 altcoins (Binance, 2017-2026);
«2023-26» es el periodo fuera de muestra, el que cuenta.
"""
import numpy as np
import pandas as pd

# =====================================================================================================
# Tablas medidas (no tocar sin repetir el backtest)
# =====================================================================================================
# Máquina de estados, cajas de 4h, 2023-26: probabilidad del siguiente estado al entrar en cada uno (%)
TRANSICION_4H = {
    'B':  {'C+': 29.5, 'C-': 29.8, 'D+': 21.8, 'D-': 18.5},
    'C+': {'D+': 21.9, 'D-': 2.9, 'B': 75.2},
    'C-': {'D+': 1.9, 'D-': 21.2, 'B': 76.8},
    'D+': {'E+': 65.9, 'B': 34.0},
    'D-': {'E-': 62.1, 'B': 37.6},
}
# P(el rango acaba saliendo por arriba, E+) al entrar en cada estado (%), 2023-26
SALIDA_FINAL_ALCISTA = {
    '4h': {'B': 53.6, 'C+': 31.7, 'C-': 74.3, 'D+': 83.0, 'D-': 19.0},
    '1d': {'B': 53.0, 'C+': 35.7, 'C-': 65.9, 'D+': 82.7, 'D-': 18.0},
}
# Casos parecidos (4h, 2023-26; una observación por rango)
CASOS_4H = {
    # dentro de la caja: P(salida final alcista) según dónde visita el precio
    'B tercio inferior': 38.0, 'B tercio medio': 52.3, 'B tercio superior': 67.7,
    'B tercio inferior con caja de 90 velas o más': 35.0,
    # tras una ruptura confirmada: P(la ruptura aguanta y llega a E)
    'D- con Spring fallido antes': 72.4, 'D- sin Spring fallido antes': 46.2,
    'D+ con UTAD fallido antes': 74.7, 'D+ sin UTAD fallido antes': 54.1,
    'D- que sigue en D- tras 20 velas': 63.8, 'D+ que sigue en D+ tras 20 velas': 46.7,
}
# Posición calibrada en la caja: P(rompe primero por arriba) = 1/(1+exp(-(a + b·logit(pos)))), pos acotada a [0,02; 0,98]
CALIBRACION = {('WS02', '4h'): (0.299, 1.308), ('MV10', '1d'): (0.682, 0.985), ('WS02', '1d'): (0.901, 1.223),
               ('MV10', '4h'): (0.188, 1.018), ('ASM10', '4h'): (-0.035, 0.881)}
CALIBRACION_ALTS = {('WS02', '4h'): (0.033, 1.354), ('MV10', '1d'): (0.222, 1.412), ('WS02', '1d'): (0.307, 1.124),
                    ('MV10', '4h'): (-0.020, 1.402), ('ASM10', '4h'): (0.001, 0.928)}
# Retroceso de Elliott medido: cuantiles de r = tramo 2 / tramo 1 (en logaritmos), 4h (en 1d casi igual)
RETROCESO_CUANTILES = {10: 0.46, 25: 0.64, 50: 0.93, 75: 1.48, 90: 2.34}
# Calidad de la ruptura v2 (14-oct, t8_wyckoff W1d). Se fija al entrar en D+ / D-. Prioridad: tipo de entrada > trampa propia > tendencia > volumen.
#   «sin ruptura de precio»: la máquina entró en D por SOS/SOW o por dos mínimos crecientes / máximos decrecientes tras su Spring/UTAD,
#       sin cierre fuera de la caja (el precio sigue dentro): leer como «sigue en la caja con sesgo», no como ruptura.
#   «tras su propio Spring/UTAD»: ruptura de precio en un rango que tuvo antes un Spring (si D+) o un UTAD (si D-).
#   «tendencia a favor»: cierre por encima de su SMA200 de 4h si D+ (por debajo si D-); en 1d, la SMA50 diaria.
#   «volumen ≥ 1,5»: la vela de ruptura (la que cerró fuera por primera vez) movió 1,5 veces o más la media de sus 90 velas anteriores.
#   aguanta = llega a E; objetivo = toca borde ± 1 altura antes de volver a la mitad (7 días en 4h, 20 días en 1d); mitad = vuelve antes a la mitad.
# 4h: BTC, ETH y 10 altcoins, 2023-26 (sin HYPE; en HYPE coincide con 68 entradas). Hasta 2022, dentro de ±5 puntos.
CALIDAD_RUPTURA_4H = {
    'entró en D sin ruptura de precio': dict(n=310, aguanta=11.9, objetivo_1_altura=4.8, vuelve_a_la_mitad=91.3),
    'ruptura de precio tras su propio Spring/UTAD': dict(n=298, aguanta=79.5, objetivo_1_altura=43.3, vuelve_a_la_mitad=23.8),
    'tendencia en contra': dict(n=108, aguanta=71.3, objetivo_1_altura=33.3, vuelve_a_la_mitad=42.6),
    'tendencia a favor y volumen ≥ 1,5': dict(n=422, aguanta=84.1, objetivo_1_altura=48.6, vuelve_a_la_mitad=21.8),
    'tendencia a favor y volumen < 1,5': dict(n=315, aguanta=73.0, objetivo_1_altura=36.5, vuelve_a_la_mitad=24.1),
}
# 1d: universo amplio de altcoins (71 monedas, incluidas deslistadas), 2023-26. En BTC+ETH 1d solo hay 43 casos: se usa esta con nota.
CALIDAD_RUPTURA_1D = {
    'entró en D sin ruptura de precio': dict(n=267, aguanta=10.5, objetivo_1_altura=4.5, vuelve_a_la_mitad=88.0),
    'ruptura de precio tras su propio Spring/UTAD': dict(n=242, aguanta=81.4, objetivo_1_altura=35.1, vuelve_a_la_mitad=8.3),
    'tendencia a favor y volumen ≥ 1,5': dict(n=329, aguanta=83.6, objetivo_1_altura=42.6, vuelve_a_la_mitad=14.3),
    'tendencia a favor y volumen < 1,5': dict(n=445, aguanta=78.9, objetivo_1_altura=18.2, vuelve_a_la_mitad=14.6),
}
# Fibonacci como regla de medir: P(el tramo en curso llega a r) con r = tramo en curso / tramo anterior (log), rejilla 0,10-3,00 cada 0,05.
# Sale de los tramos confirmados del zigzag 2017-26. Las series sustitutas (azar con la misma volatilidad) dan casi lo mismo:
# es geometría de la volatilidad, no un imán. Los números de Fibonacci no frenan más que otros cercanos (0,45 / 0,56 / 0,70).
FIB_NIVELES = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618]
SUPERVIVENCIA_R = {
    ('BTC+ETH', '4h'): [1.0, 0.999, 0.997, 0.991, 0.982, 0.963, 0.933, 0.9, 0.866, 0.822, 0.784, 0.738, 0.701, 0.651, 0.613, 0.569, 0.524, 0.487, 0.454, 0.437, 0.414, 0.389, 0.363, 0.341, 0.322, 0.297, 0.276, 0.254, 0.241, 0.226, 0.206, 0.196, 0.187, 0.177, 0.169, 0.16, 0.154, 0.145, 0.138, 0.131, 0.126, 0.12, 0.113, 0.109, 0.106, 0.102, 0.099, 0.094, 0.091, 0.088, 0.084, 0.08, 0.074, 0.072, 0.069, 0.067, 0.064, 0.062, 0.06],
    ('BTC+ETH', '1d'): [1.0, 1.0, 0.997, 0.99, 0.966, 0.942, 0.911, 0.881, 0.836, 0.812, 0.771, 0.734, 0.686, 0.645, 0.614, 0.573, 0.539, 0.502, 0.481, 0.457, 0.43, 0.396, 0.379, 0.352, 0.331, 0.297, 0.283, 0.27, 0.256, 0.242, 0.235, 0.232, 0.222, 0.215, 0.212, 0.205, 0.188, 0.174, 0.167, 0.164, 0.15, 0.14, 0.14, 0.13, 0.126, 0.119, 0.116, 0.113, 0.102, 0.099, 0.096, 0.092, 0.089, 0.082, 0.078, 0.075, 0.068, 0.068, 0.065],
    ('altcoins', '4h'): [1.0, 1.0, 0.998, 0.996, 0.986, 0.972, 0.945, 0.911, 0.869, 0.827, 0.784, 0.739, 0.693, 0.646, 0.605, 0.566, 0.525, 0.491, 0.459, 0.435, 0.409, 0.385, 0.361, 0.336, 0.313, 0.295, 0.278, 0.261, 0.246, 0.231, 0.216, 0.204, 0.191, 0.181, 0.17, 0.161, 0.152, 0.144, 0.136, 0.13, 0.125, 0.119, 0.114, 0.109, 0.103, 0.099, 0.096, 0.092, 0.089, 0.084, 0.08, 0.076, 0.072, 0.069, 0.067, 0.062, 0.06, 0.056, 0.054],
    ('altcoins', '1d'): [0.999, 0.998, 0.995, 0.986, 0.974, 0.961, 0.933, 0.901, 0.86, 0.822, 0.771, 0.729, 0.679, 0.631, 0.593, 0.565, 0.538, 0.502, 0.47, 0.443, 0.417, 0.389, 0.366, 0.347, 0.328, 0.309, 0.291, 0.281, 0.268, 0.253, 0.238, 0.224, 0.214, 0.199, 0.187, 0.175, 0.169, 0.161, 0.151, 0.143, 0.139, 0.13, 0.125, 0.123, 0.118, 0.111, 0.106, 0.101, 0.092, 0.089, 0.087, 0.085, 0.083, 0.08, 0.073, 0.07, 0.065, 0.06, 0.058],
}
_REJILLA_R = np.round(np.arange(0.10, 3.001, 0.05), 2)

def p_llega(r, grupo='BTC+ETH', tf='4h'):
    """P(r_final >= r) interpolada en la rejilla (fuera de 0,10-3,00 se recorta)."""
    s = SUPERVIVENCIA_R[(grupo, tf)]
    return float(np.interp(np.clip(r, 0.10, 3.0), _REJILLA_R, s))

# =====================================================================================================
# Indicadores
# =====================================================================================================
def _wilder(x, n):
    return x.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()

def atr(df, n=14):
    pc = df['close'].shift(1)
    tr = pd.concat([df['high'] - df['low'], (df['high'] - pc).abs(), (df['low'] - pc).abs()], axis=1).max(axis=1)
    return _wilder(tr, n)

def _pivotes(h, l, k=3):
    """Índice del pivote alto/bajo (máximo/mínimo único de i-k..i+k) que se confirma en la vela i+k; -1 si no hay."""
    n = len(h); pht = np.full(n, -1); plt = np.full(n, -1)
    for i in range(k, n - k):
        w = h[i - k:i + k + 1]
        if h[i] == w.max() and (w == h[i]).sum() == 1: pht[i + k] = i
        w = l[i - k:i + k + 1]
        if l[i] == w.min() and (w == l[i]).sum() == 1: plt[i + k] = i
    return pht, plt

def _runs(mask):
    m = np.asarray(mask, bool)
    if len(m) == 0: return 0
    return int(m[0]) + int(np.sum(m[1:] & ~m[:-1]))

# =====================================================================================================
# Máquina de estados de Wyckoff con la caja WS-02 (30 velas, altura de 3 a 8 ATR, 2 toques o más en cada 15 % extremo)
# =====================================================================================================
def maquina_wyckoff(df, bw=30):
    """Recorre las velas y devuelve (rangos, transiciones). Cada transición: (id_rango, vela, de, a, motivo).
    Estados: B (dentro de la caja), C+ (tras un Spring), C- (tras un UTAD), D+ / D- (ruptura confirmada arriba / abajo),
    E+ / E- (la ruptura aguantó: fin del rango). FIN = rango de más de 500 velas."""
    o = df['open'].values.astype(float); h = df['high'].values.astype(float); l = df['low'].values.astype(float)
    c = df['close'].values.astype(float); v = df['volume'].values.astype(float); n = len(df)
    a = atr(df).values; A = np.r_[np.nan, a[:-1]]                  # ATR de la vela anterior
    vs = pd.Series(v); m20 = vs.rolling(20, min_periods=20).mean().shift(1).values
    with np.errstate(divide='ignore', invalid='ignore'):
        rv20 = np.where(m20 > 0, v / m20, np.nan)
    rng = h - l
    clv = np.where(rng > 0, (c - l) / np.where(rng > 0, rng, 1.0), 0.5)
    hmax30 = pd.Series(h).rolling(bw, min_periods=bw).max().values; lmin30 = pd.Series(l).rolling(bw, min_periods=bw).min().values
    phc, plc = _pivotes(h, l, 3)
    ranges = []; trans = []; st = 'NADA'; R = None; rid = -1; pend = None

    def box_ok(i, Ai):
        if np.isnan(hmax30[i]): return False
        Tt = hmax30[i]; Ss = lmin30[i]; Wd = Tt - Ss
        if not (3 * Ai <= Wd <= 8 * Ai): return False
        return _runs(h[i - bw + 1:i + 1] >= Tt - 0.15 * Wd) >= 2 and _runs(l[i - bw + 1:i + 1] <= Ss + 0.15 * Wd) >= 2

    for i in range(60, n):
        Ai = A[i]
        if not (Ai > 0): continue
        if st == 'NADA':
            if box_ok(i, Ai):
                rid += 1
                R = dict(rid=rid, t_start=i - bw + 1, t_valid=i, S=lmin30[i], T=hmax30[i], A_val=Ai)
                R.update(W=R['T'] - R['S'], M=(R['T'] + R['S']) / 2, mature_from=i)
                st = 'B'; trans.append((rid, i, 'NADA', 'B', 'caja'))
                pend = dict(brd=-1, bru=-1, jp=-1, bp=-1, jc=-1, bc=-1, sp=None, ut=None, pl_last=None, ph_last=None,
                            t_state=i, below=0, above=0, first_break=None)
            continue
        S = R['S']; T = R['T']; W = R['W']; M = R['M']; tau = 0.25 * Ai; pd_ = pend
        new_st = None; why = None
        if st == 'B':
            # Spring: mínimo < S - 0,1 ATR viniendo de un cierre >= S, y vuelta a cerrar >= S en 3 velas; profundidad <= 3 ATR y <= W/2
            if pd_['brd'] < 0 and l[i] < S - 0.1 * Ai and c[i - 1] >= S:
                pd_['brd'] = i
            if pd_['brd'] >= 0:
                b = pd_['brd']
                if c[i] >= S:
                    seg = l[b:i + 1]; k = int(np.argmin(seg)); lsp = seg[k]; s_ = b + k
                    ok = (S - lsp) / Ai <= 3 and (S - lsp) <= 0.5 * W
                    if ok and i >= R['mature_from']:
                        new_st = 'C+'; why = 'spring'; pd_['sp'] = dict(r=i, s=s_, Lsp=lsp); pd_['pl_last'] = None
                    pd_['brd'] = -1
                elif i - b >= 3:
                    pd_['brd'] = -1
            if new_st is None:
                # UTAD: el espejo arriba
                if pd_['bru'] < 0 and h[i] > T + 0.1 * Ai and c[i - 1] <= T:
                    pd_['bru'] = i
                if pd_['bru'] >= 0:
                    b = pd_['bru']
                    if c[i] <= T:
                        seg = h[b:i + 1]; k = int(np.argmax(seg)); hut = seg[k]; s_ = b + k
                        ok = (hut - T) / Ai <= 3 and (hut - T) <= 0.5 * W
                        if ok and i >= R['mature_from']:
                            new_st = 'C-'; why = 'utad'; pd_['ut'] = dict(r=i, s=s_, Hut=hut); pd_['ph_last'] = None
                        pd_['bru'] = -1
                    elif i - b >= 3:
                        pd_['bru'] = -1
        # Rupturas: cierre > T + 0,25 ATR (o < S - 0,25 ATR) que no vuelve dentro en 5 velas = ruptura confirmada
        if pd_['jp'] >= 0:
            tb = pd_['jp']
            if c[i] <= T:
                pd_['jp'] = -1
            elif i - tb >= 5:
                pd_['jp'] = -1; pd_['jc'] = tb
                if pd_['first_break'] is None: pd_['first_break'] = ('arriba', tb, i, st)
                if st != 'D+' and new_st is None: new_st = 'D+'; why = 'ruptura_alcista'
        elif pd_['jc'] < 0 and c[i] > T + tau:
            pd_['jp'] = i
        if pd_['bp'] >= 0:
            td = pd_['bp']
            if c[i] >= S:
                pd_['bp'] = -1
            elif i - td >= 5:
                pd_['bp'] = -1; pd_['bc'] = td
                if pd_['first_break'] is None: pd_['first_break'] = ('abajo', td, i, st)
                if st != 'D-' and new_st is None: new_st = 'D-'; why = 'ruptura_bajista'
        elif pd_['bc'] < 0 and c[i] < S - tau:
            pd_['bp'] = i
        if new_st is None:
            if st == 'C+':
                sp = pd_['sp']
                if c[i] < sp['Lsp']:
                    new_st = 'B'; why = 'spring_fallido'
                else:
                    p_ = plc[i]
                    if p_ >= 0 and p_ > sp['s'] and l[p_] > sp['Lsp']:
                        if pd_['pl_last'] is not None and l[p_] > pd_['pl_last'][1]:
                            new_st = 'D+'; why = 'dos_minimos_crecientes'
                        pd_['pl_last'] = (p_, l[p_])
                    if new_st is None and pd_['pl_last'] is not None and rng[i] >= Ai and clv[i] >= 0.67 and rv20[i] >= 1 and c[i] > o[i]:
                        new_st = 'D+'; why = 'SOS'
                    if new_st is None and i - sp['r'] > 20:
                        new_st = 'B'; why = 'tiempo_agotado'
            elif st == 'C-':
                ut = pd_['ut']
                if c[i] > ut['Hut']:
                    new_st = 'B'; why = 'utad_fallido'
                else:
                    p_ = phc[i]
                    if p_ >= 0 and p_ > ut['s'] and h[p_] < ut['Hut']:
                        if pd_['ph_last'] is not None and h[p_] < pd_['ph_last'][1]:
                            new_st = 'D-'; why = 'dos_maximos_decrecientes'
                        pd_['ph_last'] = (p_, h[p_])
                    if new_st is None and pd_['ph_last'] is not None and rng[i] >= Ai and clv[i] <= 0.33 and rv20[i] >= 1 and c[i] < o[i]:
                        new_st = 'D-'; why = 'SOW'
                    if new_st is None and i - ut['r'] > 20:
                        new_st = 'B'; why = 'tiempo_agotado'
            elif st == 'D+':
                jc = pd_['jc']
                if jc < 0:
                    if c[i] < M: new_st = 'B'; why = 'pierde_la_mitad'
                else:
                    pd_['below'] = pd_['below'] + 1 if c[i] < T - tau else 0
                    if pd_['below'] >= 2:
                        new_st = 'B'; why = 'ruptura_fallida'; pd_['jc'] = -1; pd_['below'] = 0
                    else:
                        p_ = plc[i]
                        if p_ >= 0 and p_ > jc and T - 0.5 * Ai <= l[p_] <= T + 1.0 * Ai and min(c[jc:i + 1]) >= T - 0.5 * Ai:
                            new_st = 'E+'; why = 'BU'
                        elif c[i] > T + 0.5 * W: new_st = 'E+'; why = 'extension'
                        elif i - pd_['t_state'] > 60: new_st = 'E+'; why = 'tiempo'
            elif st == 'D-':
                bc = pd_['bc']
                if bc < 0:
                    if c[i] > M: new_st = 'B'; why = 'pierde_la_mitad'
                else:
                    pd_['above'] = pd_['above'] + 1 if c[i] > S + tau else 0
                    if pd_['above'] >= 2:
                        new_st = 'B'; why = 'ruptura_fallida'; pd_['bc'] = -1; pd_['above'] = 0
                    else:
                        p_ = phc[i]
                        if p_ >= 0 and p_ > bc and S - 1.0 * Ai <= h[p_] <= S + 0.5 * Ai and max(c[bc:i + 1]) <= S + 0.5 * Ai:
                            new_st = 'E-'; why = 'LPSY'
                        elif c[i] < S - 0.5 * W: new_st = 'E-'; why = 'extension'
                        elif i - pd_['t_state'] > 60: new_st = 'E-'; why = 'tiempo'
        if new_st is None and i - R['t_valid'] > 500:
            new_st = 'FIN'; why = 'viejo'
        if new_st is not None:
            trans.append((rid, i, st, new_st, why))
            if new_st in ('E+', 'E-', 'FIN'):
                R.update(t_end=i, end=new_st, end_why=why, first_break=pd_['first_break'])
                ranges.append(R); st = 'NADA'; R = None; pend = None
                continue
            st = new_st; pd_['t_state'] = i
            if new_st == 'B':
                pd_['sp'] = None; pd_['ut'] = None
    if R is not None and st not in ('A', 'NADA'):
        R.update(t_end=n - 1, end='abierto', end_why='fin_datos', first_break=pend['first_break'], state_now=st, t_state=pend['t_state'])
        ranges.append(R)
    return ranges, trans

def estado_wyckoff(df, tf='4h'):
    """Estado de la caja al cierre de la última vela, con niveles, historial y probabilidades medidas."""
    ranges, trans = maquina_wyckoff(df)
    idx = df.index; c = float(df['close'].iloc[-1])
    if not ranges or ranges[-1].get('end') != 'abierto':
        ult = trans[-1] if trans else None
        return dict(estado='sin caja activa', ultima_transicion=(str(idx[ult[1]]), ult[2], ult[3], ult[4]) if ult else None)
    R = ranges[-1]; st = R['state_now']
    hist = [(str(idx[t]), a, b, why) for rid, t, a, b, why in trans if rid == R['rid']]
    previos = [b for _, a, b, why in hist[:-1]] if len(hist) > 1 else []
    spring_fallido = (st == 'D-') and ('C+' in previos)        # hubo un Spring antes de romper abajo
    utad_fallido = (st == 'D+') and ('C-' in previos)          # hubo un UTAD antes de romper arriba
    S, T, W = R['S'], R['T'], R['W']
    out = dict(estado=st, suelo=round(S, 6), techo=round(T, 6), altura=round(W, 6), mitad=round(R['M'], 6), caja_desde=str(idx[R['t_valid']]),
               velas_en_la_caja=int(len(df) - 1 - R['t_valid']), velas_en_el_estado=int(len(df) - 1 - R['t_state']), cierre=c,
               posicion=round((c - S) / W, 3), historial=hist, spring_fallido=spring_fallido, utad_fallido=utad_fallido,
               extension_bajista=round(S - 0.5 * W, 6), extension_alcista=round(T + 0.5 * W, 6))
    out['P_salida_final_alcista'] = SALIDA_FINAL_ALCISTA.get(tf, {}).get(st)
    if st in ('D+', 'D-'):
        out['objetivo_1_altura'] = round(T + W, 6) if st == 'D+' else round(S - W, 6)
        if tf in ('4h', '1d'):
            sg = 1 if st == 'D+' else -1
            por_ruptura = hist[-1][3].startswith('ruptura')
            propia = (st == 'D+' and 'C+' in previos) or (st == 'D-' and 'C-' in previos)
            t_d = int(idx.get_loc(pd.Timestamp(hist[-1][0])))
            cc = df['close']; sma = cc.rolling(200 if tf == '4h' else 50).mean().values
            tend = bool(np.sign(cc.values[t_d] - sma[t_d]) == sg) if not np.isnan(sma[t_d]) else None
            tb = t_d - 5 if por_ruptura else t_d
            vv = df['volume'].values; vm = pd.Series(vv).rolling(90, min_periods=60).mean().shift(1).values
            vr = float(vv[tb] / vm[tb]) if vm[tb] > 0 else np.nan
            if not por_ruptura: celda = 'entró en D sin ruptura de precio'
            elif propia: celda = 'ruptura de precio tras su propio Spring/UTAD'
            elif tend is False: celda = 'tendencia en contra'
            else: celda = 'tendencia a favor y volumen ≥ 1,5' if vr >= 1.5 else 'tendencia a favor y volumen < 1,5'
            tabla = CALIDAD_RUPTURA_4H if tf == '4h' else CALIDAD_RUPTURA_1D
            fila = tabla.get(celda)
            out['calidad_ruptura'] = dict(celda=celda, tendencia_a_favor=tend, volumen_vela_ruptura=round(vr, 2) if vr == vr else None,
                                          vela_ruptura=str(idx[tb]), **(fila or dict(nota='celda sin muestra en 1d')))
            if tf == '1d': out['calidad_ruptura']['nota_tabla'] = 'tabla medida en 71 altcoins; en BTC y ETH diario solo hay 43 casos'
            if not por_ruptura: out['calidad_ruptura']['lectura'] = 'no es una ruptura: el precio sigue en el centro de la caja (por eso casi siempre toca la mitad). Operar en contra tampoco funciona: -0,21 R por operación en 2023-26'
    if tf == '4h':
        out['P_siguiente_estado'] = TRANSICION_4H.get(st)
        if st == 'B':
            p = out['posicion']
            ter = 'B tercio inferior' if p < 1 / 3 else ('B tercio superior' if p > 2 / 3 else 'B tercio medio')
            out['casos_parecidos'] = {ter: CASOS_4H[ter]}
            if p < 1 / 3 and out['velas_en_la_caja'] >= 90:
                out['casos_parecidos']['B tercio inferior con caja de 90 velas o más'] = CASOS_4H['B tercio inferior con caja de 90 velas o más']
        elif st == 'D-':
            k = 'D- con Spring fallido antes' if spring_fallido else 'D- sin Spring fallido antes'
            out['casos_parecidos'] = {k: CASOS_4H[k]}
            if out['velas_en_el_estado'] >= 20: out['casos_parecidos']['D- que sigue en D- tras 20 velas'] = CASOS_4H['D- que sigue en D- tras 20 velas']
        elif st == 'D+':
            k = 'D+ con UTAD fallido antes' if utad_fallido else 'D+ sin UTAD fallido antes'
            out['casos_parecidos'] = {k: CASOS_4H[k]}
            if out['velas_en_el_estado'] >= 20: out['casos_parecidos']['D+ que sigue en D+ tras 20 velas'] = CASOS_4H['D+ que sigue en D+ tras 20 velas']
    return out

# =====================================================================================================
# Cajas para la posición calibrada (detectores de la sección 6.3)
# =====================================================================================================
def _roll_pct(x, n):
    return x.rolling(n, min_periods=n).apply(lambda a: (a[:-1] < a[-1]).mean() * 100 if len(a) > 1 else np.nan, raw=True)

def caja_activa(df, kind='WS02', tf='4h'):
    """Caja activa al cierre de la última vela y su posición entre los niveles de ruptura (suelo - 0,1 ATR y techo + 0,1 ATR).
    WS02: 30 velas, altura de 3 a 8 ATR, 2 toques o más en cada 15 % extremo. MV10: rango de 20 velas en su percentil 30 del año."""
    H = df['high'].values; L = df['low'].values; C = df['close'].values
    A = atr(df, 14).values; n = len(df)
    if kind == 'WS02':
        win = 30
        topw = pd.Series(H).rolling(win).max().values; botw = pd.Series(L).rolling(win).min().values
        hh = topw - botw; cond = (hh >= 3 * A) & (hh <= 8 * A)
    elif kind == 'MV10':
        win = 20
        topw = pd.Series(H).rolling(win).max().values; botw = pd.Series(L).rolling(win).min().values
        pct = _roll_pct(pd.Series((topw - botw) / A), 365 if tf == '1d' else 2190).values
        cond = pct <= 30
    else:
        raise ValueError(kind)
    cond = np.where(np.isnan(A) | np.isnan(topw), False, cond)
    last_break = -1; i = win; activa = None
    while i < n:
        if cond[i] and (i - win + 1) > last_break:
            top, bot, a0 = topw[i], botw[i], A[i]
            if kind == 'WS02':
                h_ = top - bot
                if _runs(H[i - win + 1:i + 1] >= top - 0.15 * h_) < 2 or _runs(L[i - win + 1:i + 1] <= bot + 0.15 * h_) < 2:
                    i += 1; continue
            up, dn = top + 0.1 * a0, bot - 0.1 * a0
            tb = None
            for j in range(i + 1, n):
                if C[j] > up or C[j] < dn: tb = j; break
            if tb is None:
                activa = dict(desde=str(df.index[i - win + 1]), validada=str(df.index[i]), suelo=float(bot), techo=float(top),
                              nivel_ruptura_abajo=float(dn), nivel_ruptura_arriba=float(up),
                              posicion=float(np.clip((C[-1] - dn) / (up - dn), 0, 1)), altura_atr=float((top - bot) / a0), velas=int(n - (i - win + 1)))
                break
            last_break = tb; i = tb + 1
        else:
            i += 1
    return activa

def p_rompe_arriba(posicion, kind='WS02', tf='4h', altcoin=False):
    a, b = (CALIBRACION_ALTS if altcoin else CALIBRACION)[(kind, tf)]
    p = min(max(posicion, 0.02), 0.98)
    return float(1 / (1 + np.exp(-(a + b * np.log(p / (1 - p))))))

# =====================================================================================================
# Elliott: solo etiqueta medible (zigzag y retroceso), sin probabilidad propia
# =====================================================================================================
def theta(df, sym, tf, k=3.0):
    """Umbral del zigzag: máx(p_TF, 3·ATR/cierre) en BTC (p_TF = 4 % en 4h y 10 % en 1d); 3·ATR/cierre en el resto."""
    th = k * atr(df) / df['close']
    if sym == 'BTC' and tf in ('4h', '1d'):
        th = np.maximum({'4h': 0.04, '1d': 0.10}[tf], th)
    return th

def zigzag(df, th):
    h = df['high'].values; l = df['low'].values; n = len(df); th = np.asarray(th, float)
    piv = []; d = 0; ext = None; ext_t = 0
    for i in range(n):
        if np.isnan(th[i]): continue
        if d == 0:
            if ext is None:
                ext_hi, ext_lo, t_hi, t_lo = h[i], l[i], i, i; ext = 1; continue
            if h[i] > ext_hi: ext_hi, t_hi = h[i], i
            if l[i] < ext_lo: ext_lo, t_lo = l[i], i
            if np.log(ext_hi / ext_lo) >= th[i]:
                if t_lo < t_hi:
                    piv.append(dict(tipo='L', t=t_lo, t_conf=i, precio=ext_lo)); d = 1; ext, ext_t = ext_hi, t_hi
                else:
                    piv.append(dict(tipo='H', t=t_hi, t_conf=i, precio=ext_hi)); d = -1; ext, ext_t = ext_lo, t_lo
            continue
        if d == 1:
            if h[i] > ext: ext, ext_t = h[i], i
            elif np.log(ext / l[i]) >= th[i]:
                piv.append(dict(tipo='H', t=ext_t, t_conf=i, precio=ext)); d = -1; ext, ext_t = l[i], i
        else:
            if l[i] < ext: ext, ext_t = l[i], i
            elif np.log(h[i] / ext) >= th[i]:
                piv.append(dict(tipo='L', t=ext_t, t_conf=i, precio=ext)); d = 1; ext, ext_t = h[i], i
    return piv, (d, ext, ext_t)

def retroceso_elliott(df, sym, tf):
    """Último tramo confirmado del zigzag y retroceso actual medido (r = tramo en curso / tramo anterior, en logaritmos),
    con los precios a los que el retroceso llegaría a sus cuantiles históricos 25/50/75 (0,64 / 0,93 / 1,48)."""
    th = theta(df, sym, tf).values
    piv, (d, ext, ext_t) = zigzag(df, th)
    if len(piv) < 2: return None
    p0, p1 = piv[-2], piv[-1]
    L1 = abs(np.log(p1['precio'] / p0['precio']))
    c = float(df['close'].iloc[-1])
    r_now = abs(np.log(c / p1['precio'])) / L1 if L1 > 0 else np.nan
    sgn = 1 if p1['tipo'] == 'L' else -1                     # tras un mínimo, el tramo en curso es alcista
    niveles = {q: float(p1['precio'] * np.exp(sgn * r * L1)) for q, r in [(25, 0.64), (50, 0.93), (75, 1.48)]}
    # Fibonacci medido: precio de cada nivel y P(llega | lo que ya ha recorrido el tramo en curso, medido con su extremo)
    grupo = 'BTC+ETH' if sym in ('BTC', 'ETH') else 'altcoins'
    tfk = '1d' if tf == '1d' else '4h'
    r_ext = abs(np.log(ext / p1['precio'])) / L1 if (L1 > 0 and ext is not None and d == sgn) else r_now
    s_ext = p_llega(r_ext, grupo, tfk)
    fib = {}
    for lv in FIB_NIVELES:
        precio = float(p1['precio'] * np.exp(sgn * lv * L1))
        if lv <= r_ext:
            fib[lv] = dict(precio=precio, P_llega=None, estado='ya alcanzado')
        else:
            fib[lv] = dict(precio=precio, P_llega=round(100 * p_llega(lv, grupo, tfk) / s_ext, 1) if s_ext > 0 else None, estado='pendiente')
    return dict(ultimo_pivote=p1['tipo'], fecha_pivote=str(df.index[p1['t']]), precio_pivote=float(p1['precio']),
                pivote_anterior=float(p0['precio']), tramo_anterior_pct=float((np.exp(L1) - 1) * 100), theta_pct=float(th[-1] * 100),
                r_actual=float(r_now), r_extremo=float(r_ext), extremo_del_tramo=float(ext) if ext is not None else None,
                niveles_cuantiles=niveles, fibonacci=fib,
                nota_fibonacci='P_llega = probabilidad de que el tramo en curso llegue a ese nivel, dado lo que ya ha recorrido. '
                               'Los niveles de Fibonacci no frenan más que otros cercanos; la zona 0,45-0,70 frena algo más que el azar '
                               '(22 % frente a 20 % en BTC y ETH, 24 % frente a 21 % en altcoins) y el nivel 1,0 (el extremo anterior) frena menos: '
                               'si llega a 0,97, sigue más allá de 1,03 el 95 % de las veces frente al 93 % del azar.',
                invalidacion=float(p1['precio']), nota='Etiqueta descriptiva: el estado de onda no mejora ninguna probabilidad.')
