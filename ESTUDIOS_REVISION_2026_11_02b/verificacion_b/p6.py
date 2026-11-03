from b import *
a,b_ = pd.Timestamp('2021-05-09'), pd.Timestamp('2021-07-19')
grp = {'cripto':L=='cripto','petróleo(3)':np.isin(L,['petroleo','corto_petroleo','x_petroleo']),'E1':E1,'Connors':cn,'cortos ex':ex,'c10':L=='c10','oro':L=='metales','shy':L=='shy'}
for k in ('vigente (ex|E1|cn)','dentro (solo ex)'):
    q,e,rr,_ = montaje(flujo=1.5, exv=k, devolver=True); s = rr.s
    out={}
    for g,m in grp.items():
        cu = C.M.curva(np.where(m, s, 0)); out[g]=round(float(cu.asof(b_)-cu.asof(a)),2)
    out['TOTAL']=round(float(e.asof(b_)-e.asof(a)),2)
    print(k, out)
    # nº operaciones tomadas en la ventana por grupo y tamaño medio
    t = O.t_entrada
    print('   abiertas en ventana (s>0):', {g:int(((s>0)&m&(t>=a)&(t<=b_)).sum()) for g,m in grp.items()})
