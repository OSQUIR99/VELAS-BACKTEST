from ev import *
from p34 import oro_invalidado
EXTRA=tuple(f'/home/claude/med/{d}' for d in ['l_p1_btc_st','l_p1_6_st','l_p1_btc_ns','l_p1_6_ns','l_e1r_200','l_e1r_200m','l_e1r_20s','l_sectores_lentos','l_sectores_lentos_d3','l_sectores_lentos_d7','l_sectores_lentos_d11'])
C=cartera(extra=EXTRA); M=mascaras(C); O=C.O; L=C.L; act=C.act; d=M['d']
e0,q0=run(C,M['BASE'],M['EX']); print('BASE',C.fmt(q0),'24-26',round(m24(e0),2),flush=True)
print('== Propuesta 1: ruptura EMA 20 diaria en cripto, 40 velas')
for nm in ['p1_btc_st','p1_6_st','p1_btc_ns','p1_6_ns']:
    m=(L==nm)&d; e,q=run(C,M['BASE']|m,M['EX']); linea(C,f'+ {nm} ({m.sum()} op.)',e,q,e0,q0)
print('== Propuesta 3: permiso de índices')
# A: margen 0,9 % sobre la media de 200 (filtro de la lista oficial)
from cortos import diario
IDX={'SPX':'sp500','NDX':'nasdaq100','DJI':'dowjones'}; keep=np.ones(len(O),bool)
for a,nom in IDX.items():
    c=diario(nom).cierre; m200=c.rolling(200).mean(); okm=(c>=m200*1.009)
    s=(M['E1']&(act==a)); fe=pd.to_datetime(O.t_senal[s]).dt.normalize()
    keep[np.flatnonzero(s)]=okm.reindex(fe.values,method='ffill').fillna(False).values
e,q=run(C,M['BASE']&~(M['E1']&~keep),M['EX']); linea(C,f'E1 oficial con margen 0,9 % (quita {int((M["E1"]&~keep).sum())})',e,q,e0,q0)
# B: lista regenerada (tamaño plano) con permiso 200 frente a 20 semanas, en lugar de la E1 oficial
for nm in ['e1r_200','e1r_200m','e1r_20s']:
    m=(L==nm)&d; b=(M['BASE']&~M['E1'])|m; e,q=run(C,b,M['EX']&~M['E1']|m); globals()['q_'+nm]=q; globals()['e_'+nm]=e
    linea(C,f'E1 regenerada {nm} ({m.sum()} op.) en lugar de la oficial',e,q,e0,q0)
print('  20 semanas frente a 200 (las dos regeneradas):','PASA' if ok(q_e1r_20s,q_e1r_200) else '-','| margen frente a 200:','PASA' if ok(q_e1r_200m,q_e1r_200) else '-')
print('== Propuesta 4: oro, soporte de la media de 50 semanas (sin largos nuevos con cierre semanal < 0,972 × media; vuelve al cerrar encima)')
inv=oro_invalidado(); go=(L=='metales')&(act=='oro')&M['W']; fe=pd.to_datetime(O.t_senal[go])
# semana conocida: la del último viernes cerrado antes de la señal
v=inv.copy(); v.index=v.index+pd.Timedelta(days=5)   # lunes -> viernes de cierre
val=v.reindex(fe.values,method='ffill').fillna(0).values
quita=np.zeros(len(O),bool); quita[np.flatnonzero(go)]=val>0.5
e,q=run(C,M['BASE']&~quita,M['EX']); linea(C,f'oro sin largos con el soporte perdido (quita {quita.sum()})',e,q,e0,q0)
print('== Sectores · prueba 1: CORTO SECTOR, regla del dólar solo en los muy expuestos (XLK, SMH, XLB, XLE)')
cs=(L=='corto_sector'); muy=np.isin(act,['XLK','SMH','XLB','XLE']); tR=O.tam_R.values
for nom,grupo in (('VARIANTE poco expuestos siempre 1 R',~muy),('PLACEBO muy expuestos siempre 1 R',muy)):
    tm=np.ones(len(O)); tm[cs&grupo&(np.isclose(tR,0.25))]=2.0
    e,q=run(C,M['BASE'],M['EX'],tm=tm); linea(C,nom+f' ({int((cs&grupo&np.isclose(tR,0.25)&M["W"]).sum())} op. tocadas)',e,q,e0,q0)
    globals()['e_'+nom.split()[0]]=e
print('== Sectores · prueba 2: familia lenta (12 meses, top 3)')
for nm in ['sectores_lentos','sectores_lentos_d3','sectores_lentos_d7','sectores_lentos_d11']:
    m=(L==nm)&d; e,q=run(C,M['BASE']|m,M['EX']); linea(C,f'+ {nm} ({m.sum()} op.)',e,q,e0,q0)
