from b import *
import vc as V
# 1) cadena: dónde aparece la inversión dentro/fuera
def par(Cx, mask, tm, exs):
    return [Cx.met3(Cx.sim(mask, exentas=e, tam_mult=tm)[1]) for e in exs]
C0 = V.montar(False); L0=C0.L; a0=C0.act; d0=(C0.O.t_entrada>=C0.desde).values
W0 = C0.W | (d0 & np.isin(L0,['corto_petroleo','n1_vixvxv','corto_indices_credito','corto_sector','yt_connors_qqq']))
ex0 = np.isin(L0,['corto_sector','corto_indices_credito'])&W0
qs = par(C0, C0.mask, None, [ex0, C0.exentas]); print('motor (listas GH)       dentro', C0.fmt(qs[0]), '| fuera', C0.fmt(qs[1]))
qs = par(C, C.mask, None, [ex, C.exentas]); print('vol10                   dentro', C.fmt(qs[0]), '| fuera', C.fmt(qs[1]))
qs = par(C, C.mask, k8(), [ex, C.exentas]); print('vol10+K8                dentro', C.fmt(qs[0]), '| fuera', C.fmt(qs[1]))
tmF,_=fiel.factores(O,C.cri)
qs = par(C, C.mask, tmF, [ex, C.exentas]); print('fiel piso sin K8        dentro', C.fmt(qs[0]), '| fuera', C.fmt(qs[1]))
for K in (False, True):
    a=montaje(K8=K, exv='dentro (solo ex)'); b_=montaje(K8=K); print(f'fiel sin piso K8={K}    dentro', C.fmt(a), '| fuera', C.fmt(b_))
# 2) episodio de la peor caída (BTC x1,5, sin piso, K8)
for k in ('vigente (ex|E1|cn)','dentro (solo ex)'):
    q,e,rr,_ = montaje(flujo=1.5, exv=k, devolver=True)
    e = e[(e.index>=C.desde)&(e.index<=vc.comun.HOY)]; e=e-e.iloc[0]; dd=e.cummax()-e
    fin=dd.idxmax(); ini=e[:fin].idxmax(); rec = e[fin:][e[fin:]>=e[ini]].index
    print(f'{k}: peor caída {dd.max():.2f} R de {ini.date()} a {fin.date()} (recupera {rec[0].date() if len(rec) else "no"})')
    # top-3 caídas distintas
    eps=[]; pk=e.cummax(); inDD=dd>0; grp=(~inDD).cumsum()
    for g_,s in dd[inDD].groupby(grp[inDD]): eps.append((s.max(), s.index[0].date(), s.idxmax().date()))
    print('   top4 episodios:', [(round(x,2),str(a),str(b)) for x,a,b in sorted(eps,reverse=True)[:4]])
    if k.startswith('vigente'): rrV, eV = rr, e
    else: rrD, eD = rr, e
# 3) en el episodio de la peor caída de la vigente: contribución por lista
q,e,rr,_ = montaje(flujo=1.5, devolver=True)
