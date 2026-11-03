from ver import *
t=time.time(); v=V(True); print('carga',round(time.time()-t),'s desde',v.desde)
print(pd.Series(v.L[v.base]).value_counts().to_string())
for nom,tm in (('B0',None),('K6',v.mult(corto_pet=2)),('K2',v.mult(2,0.75,0.75)),('K7',v.mult(2,1,0.75,pet_no_L1=0.5))):
    t=time.time(); rr,eq=v.sim(tm); q=tres(eq,v.desde); print(nom,fmt(q),'5peores',round(np.mean(episodios(eq,v.desde)[:5]),2),round(time.time()-t),'s',flush=True)
    eq.to_pickle(f'eq_{nom}.pkl'); np.save(f's_{nom}.npy',rr.s); np.save(f'mot_{nom}.npy',rr.motivo.astype(str))
