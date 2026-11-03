from ver import *
v=V(True); O=v.O; L=v.L; M=v.M
for nom in ('K6','K2','K7'):
    s=np.load(f's_{nom}.npy'); mo=np.load(f'mot_{nom}.npy',allow_pickle=True)
    cp=np.flatnonzero((L=='corto_petroleo')&(s>0))
    lg=np.flatnonzero(np.isin(L,['petroleo','x_petroleo','mensuales','c10'])&(s>0)&(O.bloque.values=='energia'))
    print('==',nom,'cortos abiertos',len(cp),'max tamaño R/op',round((s[cp]*O.tam_R.values[cp]).max(),2),'max riesgo',round((s[cp]*O.riesgo_inicial_R.values[cp]).max(),2))
    for k in cp:
        a,b=O.t_entrada[k],O.t_salida[k]
        ov=[j for j in lg if O.t_entrada[j]<b and O.t_salida[j]>a]
        if ov:
            for j in ov: print('  solapa',O.id[k],O.activo[k],a.date(),'corto',round(s[k]*O.tam_R[k],2),'R  con',O.lista[j],O.senal[j],O.activo[j],O.t_entrada[j].date(),'->',O.t_salida[j].date(),'largo',round(s[j]*O.tam_R[j],2),'R r_final',round(s[j]*O.r_final[j],2))
    # riesgo energía neto/bruto máximo en días con corto abierto
    # rechazos por topes vs B0
    m0=np.load('mot_B0.npy',allow_pickle=True)
    print('  motivos',pd.Series(mo[v.base]).value_counts().to_dict(),'| B0',pd.Series(m0[v.base]).value_counts().to_dict())
    s0=np.load('s_B0.npy'); ch=np.flatnonzero(v.base&((s0>0)!=(s>0)))
    print('  ops que entran/salen respecto a B0:',len(ch), pd.Series(L[ch]).value_counts().to_dict())
# riesgo diario bruto máximo de la cartera con K7 (sumando riesgo inicial de lo abierto)
for nom in ('B0','K2','K7'):
    s=np.load(f's_{nom}.npy'); sel=np.flatnonzero(s>0)
    ev=[]
    for k in sel: ev+= [(O.t_entrada[k],s[k]*O.riesgo_inicial_R[k],L[k]),(O.t_salida[k],-s[k]*O.riesgo_inicial_R[k],L[k])]
    ev.sort(key=lambda x:(x[0],x[1])); cur=0;mx=0;en=0;mxe=0
    for t,r,l in ev:
        cur+=r; mx=max(mx,cur)
        if l in('petroleo','x_petroleo','corto_petroleo'): en+=r; mxe=max(mxe,en)
    print(nom,'riesgo inicial abierto máx (bruto, sin bajar stops)',round(mx,1),'| petróleo bruto máx',round(mxe,1))
