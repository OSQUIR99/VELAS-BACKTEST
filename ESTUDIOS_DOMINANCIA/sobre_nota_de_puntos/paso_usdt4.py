import pandas as pd, numpy as np
exec(open('paso_usdt3.py').read().split("\nV = {")[0])
c = (eth & (M.ethbtc == 1))
V = {'0': mapa(pts0) * F, 'C': mapa(pts0 - c) * F,
     'A+C': mapa(pts0 - c) * F * np.where(M.usdt == 1, 1.5, 1),
     'F': mapa(pts0 + M.usdt * (1 - t2) - c) * F}
for k, wm in V.items():
    w = peso(np.asarray(wm, float)); p = mtm(X, w); out = [k]
    for nm, a, b in PERIODOS:
        Rt, dd, ra = medir(p, a, b); out.append(f'{nm} {Rt:+.0f}/{dd:.1f}→{ra:.2f}')
    for e0, e1 in EPOCAS_C: out.append(f'{e0} {medir(p, e0, e1)[2]:.2f}')
    print(' | '.join(out), flush=True)
