from ver import *
import itertools
v=V(True); L=v.L; act=v.act
_,e0=v.sim(v.mult()); q0=tres(e0,v.desde)
FAM={'cripto':(L=='cripto'),'c10':(L=='c10'),'E1':(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX']),'connors':(L=='yt_connors_qqq'),'oro':(L=='metales')&(act=='oro'),'corto_sector':(L=='corto_sector'),'corto_ind':(L=='corto_indices_credito')}
_,e=v.sim(v.mult(2,0.75,0.75)); qk=tres(e,v.desde); dk=np.mean([qk[i][2]-q0[i][2] for i in range(3)])
res=[]
for a,b in itertools.combinations(FAM,2):
    t=v.mult(corto_pet=2); t[FAM[a]]*=0.75; t[FAM[b]]*=0.75; _,e=v.sim(t); q=tres(e,v.desde)
    res.append((a,b,np.mean([q[i][2]-q0[i][2] for i in range(3)]),all(q[i][2]>q0[i][2] for i in range(3))))
print('K2 mejora media',round(dk,3),'| placebos',len(res),'>=K2:',sum(r[2]>=dk for r in res),'pasan:',sum(r[3] for r in res))
for r in sorted(res,key=lambda x:-x[2])[:3]: print(' ',r)
# placebo aleatorio: x0,5 a una fracción aleatoria de operaciones de petróleo largo del mismo tamaño que L2+L3+tras-noticia
rng=np.random.default_rng(3); pet=np.flatnonzero((L=='petroleo')&v.base); nk=int(((L=='petroleo')&v.base&(v.sen!='L1')).sum())
_,e=v.sim(v.mult(2,1,0.75,pet_no_L1=0.5)); q7=tres(e,v.desde); d7=np.mean([q7[i][2]-q0[i][2] for i in range(3)])
r2=[]
for _ in range(100):
    t=v.mult(2,1,0.75); t[rng.choice(pet,nk,replace=False)]=0.5; _,e=v.sim(t); q=tres(e,v.desde); r2.append(np.mean([q[i][2]-q0[i][2] for i in range(3)]))
r2=np.array(r2); print('K7 mejora media',round(d7,3),'| aleatorio (mismo nº de ops de petróleo a x0,5): media',round(r2.mean(),3),'p95',round(np.percentile(r2,95),3),'>=K7',(r2>=d7).mean())
