import sys; sys.path.insert(0,'/home/claude/velas-backtest/ESTUDIOS_MEDIAS_2026_11_03')
from ev import *
C=cartera(extra=('/home/claude/estudios/vix-mejora/listas',)); M=mascaras(C); L=C.L; d=M['d']
e0,q0=run(C,M['BASE'],M['EX']); print('BASE',C.fmt(q0),flush=True)
def go(nom,fams):
    mk=np.zeros(len(L),bool); tm=np.ones(len(L)); n=0
    for f,t in fams: m=(L==f)&d; n+=m.sum(); mk|=m; tm=np.where(m,t,tm)
    e,q=run(C,M['BASE']|mk,M['EX'],tm=tm); print(f'n={n:4d}',end=' '); linea(C,nom,e,q,e0,q0,boot=True)
B28,B30,F28='m_b28_m1','m_b30_m1','m_b28_spx_sobre200_m1'
CN,CNF='n_cn_p25_l10_r100','n_cn_p25_l10_r100_spx200'
go('1 VIX>=28 0.5',[(B28,.5)])
go('2 VIX>=30 0.5',[(B30,.5)])
go('3 VIX>=28 filtro200 0.5',[(F28,.5)])
go('4 curva sola 0.75',[(CN,.75)])
go('5 curva filtro200 0.75',[(CNF,.75)])
go('6 >=28 0.5 + curva 0.75',[(B28,.5),(CN,.75)])
go('7 >=28f 0.5 + curva 0.75',[(F28,.5),(CN,.75)])
go('8 >=28f 0.5 + curva 0.5',[(F28,.5),(CN,.5)])
go('9 >=28f 0.5 + curvaf 0.75',[(F28,.5),(CNF,.75)])
go('10 >=28f 0.5 + curvaf 0.5',[(F28,.5),(CNF,.5)])
