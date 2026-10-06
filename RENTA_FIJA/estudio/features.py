import pandas as pd, numpy as np
M = pd.read_pickle('macro_semanal.pkl'); P = pd.read_pickle('precios_semanales.pkl')
S = pd.read_pickle('sinteticos.pkl'); YN = pd.read_pickle('yields_sin_retraso.pkl')
def chg(s, n): return s - s.shift(n)
def pchg(s, n): return s / s.shift(n) - 1
def yoy_m(s): return s / s.shift(52) - 1
F = pd.DataFrame(index=M.index)
y10, y2 = M.DGS10, M.DGS2
# --- TENDENCIA de los rendimientos (signo: positivo = rendimientos bajando = bueno para bonos)
F['tend_y10_13s'] = -chg(y10, 13); F['tend_y10_26s'] = -chg(y10, 26); F['tend_y10_52s'] = -chg(y10, 52)
F['tend_y10_vs_media40'] = -(y10 - y10.rolling(40).mean())
F['tend_y2_13s'] = -chg(y2, 13)
F['tend_y30_13s'] = -chg(M.DGS30.fillna(M.DGS20), 13)
# --- FED
ff = M.DFF; tgt = M.FEDTGT.fillna(ff)
F['fed_cambio_26s'] = -chg(tgt, 26); F['fed_cambio_52s'] = -chg(tgt, 52)
F['fed_2a_menos_ff'] = -(y2 - ff)          # 2 años por debajo del tipo Fed = mercado descuenta bajadas
F['fed_3m_menos_ff'] = -(M.DGS3MO.fillna(M.DTB3) - ff)
F['fed_1a_menos_ff'] = -(M.DGS1 - ff)
# semanas desde el último movimiento y su dirección
d = tgt.diff().fillna(0); last_dir = d.replace(0, np.nan).ffill()
F['fed_ultimo_mov_bajada'] = -np.sign(last_dir)
# --- CURVA y CARRY
F['curva_10a_2a'] = y10 - y2; F['curva_10a_3m'] = y10 - M.DGS3MO.fillna(M.DTB3)
F['curva_cambio_13s'] = chg(y10 - y2, 13)
F['carry_10a_menos_ff'] = y10 - ff
# --- VALORACIÓN
cpi_y = yoy_m(M.CPI)*100; core_y = yoy_m(M.CORECPI)*100
F['valor_real_10a_ipc'] = y10 - cpi_y
F['valor_real_10a_subyacente'] = y10 - core_y
F['valor_tips10'] = M.DFII10
F['valor_y10_vs_media5a'] = y10 - y10.rolling(260).mean()
F['valor_prima_plazo'] = M.TP10
# --- INFLACIÓN (signo: inflación bajando = bueno)
F['infl_ipc_anual'] = -cpi_y
F['infl_sub_acel'] = -((M.CORECPI / M.CORECPI.shift(13))**4*100 - 100 - core_y)
F['infl_ipc_acel'] = -((M.CPI / M.CPI.shift(13))**4*100 - 100 - cpi_y)
F['infl_breakeven_13s'] = -chg(M.T10YIE, 13)
F['infl_petroleo_26s'] = -pchg(M.DCOILWTICO, 26)
F['infl_ppi_anual'] = -yoy_m(M.PPIACO)
# --- CRECIMIENTO / EMPLEO (signo: economía debilitándose = bueno para bonos)
F['crec_paro_vs_min12m'] = M.UNRATE - M.UNRATE.rolling(52).min()
F['crec_sahm'] = M.SAHMREALTIME
F['crec_subsidios_tend'] = M.ICSA.rolling(4).mean() / M.ICSA.rolling(52).mean() - 1
F['crec_empleo_3m'] = -(M.PAYEMS - M.PAYEMS.shift(13))
F['crec_indpro_anual'] = -yoy_m(M.INDPRO)
F['crec_confianza_26s'] = -chg(M.UMCSENT, 26)
F['crec_ventas_anual'] = -yoy_m(M.RSAFS)
# --- RIESGO / ESTRÉS (signo: más miedo = bueno para bonos del Tesoro)
vix = M.VIXCLS
F['riesgo_vix'] = vix; F['riesgo_vix_4s'] = chg(vix, 4)
F['riesgo_baa'] = M.BAA10Y; F['riesgo_baa_13s'] = chg(M.BAA10Y, 13)
F['riesgo_nfci'] = M.NFCI
spy = P.SPY
F['riesgo_spy_26s'] = -pchg(spy, 26)
F['riesgo_spy_caida_max52'] = -(spy / spy.rolling(52).max() - 1)
F['riesgo_move'] = P['^MOVE']
# --- DÓLAR, ORO
dxy = P['DX-Y.NYB']
F['dolar_13s'] = pchg(dxy, 13); F['oro_13s'] = pchg(P['GC=F'], 13)
F['oro_vs_bono_13s'] = -(pchg(P['GC=F'], 13) - pchg(P.TLT, 13))
# --- RÉGIMEN de correlación acciones-bonos
r_s = spy.pct_change(fill_method=None); r_b = S.S_10Y
F['regimen_corr_acc_bonos'] = -r_s.rolling(52).corr(r_b)
# --- Tendencia de precio de los propios fondos
F['precio_tlt_vs_media40'] = P.TLT / P.TLT.rolling(40).mean() - 1
F['precio_ief_vs_media40'] = P.IEF / P.IEF.rolling(40).mean() - 1
F.to_pickle('features.pkl')

# ---------- OBJETIVOS (lo que pasa DESPUÉS de t) ----------
T = pd.DataFrame(index=M.index)
yn10, yn2 = YN.DGS10, YN.DGS2
for h in [4, 13, 26]:
    T[f'dY10_{h}'] = yn10.shift(-h) - yn10
    T[f'dY2_{h}'] = yn2.shift(-h) - yn2
    T[f'dCurva_{h}'] = (yn10 - yn2).shift(-h) - (yn10 - yn2)
    def fwd(r): return np.log1p(r).rolling(h).sum().shift(-h)
    T[f'syn_larg_vs_cort_{h}'] = fwd(S.S_10Y) - fwd(S.S_2Y)
    T[f'syn_30a_vs_liq_{h}'] = fwd(S.S_30Y) - fwd(S.S_CASH)
    rt = P.pct_change(fill_method=None)
    T[f'TLT_vs_SHY_{h}'] = fwd(rt.TLT) - fwd(rt.SHY)
    T[f'IEF_vs_SHY_{h}'] = fwd(rt.IEF) - fwd(rt.SHY)
    T[f'TLT_{h}'] = fwd(rt.TLT); T[f'IEF_{h}'] = fwd(rt.IEF)
    T[f'IEF_vs_SPY_{h}'] = fwd(rt.IEF) - fwd(rt.SPY)
    T[f'syn10_vs_SPY_{h}'] = fwd(S.S_10Y) - fwd(rt.SPY)
T.to_pickle('targets.pkl')
print(F.dropna(how='all').notna().idxmax().sort_values().to_string())
