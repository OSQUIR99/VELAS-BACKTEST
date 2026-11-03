# Verificador B (2-nov-2026): base fiel vigente = vol10 + reescalado cripto fiel + K8 + sin piso. Reutiliza /home/claude/verif_2nov (vc, fiel).
import sys; sys.path.insert(0,'/home/claude/verif_2nov')
import numpy as np, pandas as pd, vc, fiel
C = vc.montar(True); O = C.O; L = C.L; act = C.act; sen = C.senal; W = C.W
d = (O.t_entrada >= C.desde).values
W2 = W | (d & np.isin(L, ['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq']))
E1 = (L=='bolsa_e1') & np.isin(act,['SPX','DJI','NDX']) & W2
ex = np.isin(L,['corto_sector','corto_indices_credito']) & W2
cn = (L=='yt_connors_qqq') & W2
EXV = {'vigente (ex|E1|cn)': ex|E1|cn, 'dentro (solo ex)': ex, 'solo E1 fuera (ex|E1)': ex|E1, 'solo Connors fuera (ex|cn)': ex|cn}

def k8():
    k = np.ones(len(O))
    k[L=='corto_petroleo'] = 2.0
    k[(L=='petroleo') & np.isin(sen, ['L2','tras-noticia (bajada)'])] = 0.5
    k[(L=='x_petroleo') & np.isin(sen, ['X1','X3'])] = 0.75
    return k

def tam_cripto(flujo=1.0, flag=None):
    """Copia de fiel.factores SIN suelo (con tope 5). Devuelve tm = nuevo/viejo (1 fuera de cripto)."""
    n = len(O); tm = np.ones(n); idx = np.flatnonzero(C.cri); g = O.iloc[idx]
    a = g.activo.astype(str).values; old = g.tam_R.values.astype(float); new = old.copy()
    sn0 = g.salida_neta.astype(bool).values
    sn = sn0 if flag is None else np.asarray(flag, bool)[idx]
    btc = a == 'BTC'
    new = np.where(btc & sn0, new / 1.5, new)
    new = np.where(btc & sn, new * flujo, new)
    lm = g.linea_mult.values.astype(float)
    new = np.where(lm > 1, new / lm, new)
    fr = np.zeros(len(g), bool)
    for x in ('BTC','ETH','ADA'):
        m = a == x
        fr[m] = fiel.sobre_sma40(x, g.t_entrada.values[m]) & (lm[m] <= 1 + 1e-12)
    new = np.where(fr, new * 0.5, new)
    sol = a == 'SOL'
    new = np.where(sol, new / fiel.nota_mult(g.puntos.values), new)
    new = np.minimum(new, 5.0)
    tm[idx] = new / old
    return tm

def montaje(K8=True, piso=False, flujo=1.0, flag=None, exv='vigente (ex|E1|cn)', cfg=None, devolver=False):
    tm = tam_cripto(flujo, flag)
    new = O.tam_R.values * tm
    bajo = C.cri & (new < 0.25 - 1e-9)
    mask = C.mask.copy()
    if piso:
        tm = np.where(bajo, 0.25 / O.tam_R.values, tm)
    else:
        mask = mask & ~bajo
    if K8: tm = tm * k8()
    rr, eq = C.sim(mask, cfg=cfg, exentas=EXV[exv], tam_mult=tm)
    q = C.met3(eq)
    return (q, eq, rr, dict(bajo=int((bajo & C.mask).sum()))) if devolver else q
