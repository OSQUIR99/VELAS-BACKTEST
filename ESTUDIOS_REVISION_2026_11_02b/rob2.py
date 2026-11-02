from fiel import *
pm=lambda p: np.select([p>=2,p==1,p==0,p==-1],[1.5,1.25,1.0,0.5],0.25)
sol=cr&(act=='SOL')
def tm2(btc_sn=False, sol_plano=True, sobre=None):
    w=tm_fiel(btc_sn=btc_sn, sobre=sobre)
    if sol_plano:
        f=1.0/pm(PT); w[sol]*=f[sol]
        w=np.where(cr,np.clip(tam*w,0.25,5.0)/np.maximum(tam,1e-9),w)
    return w
if __name__=="__main__":
  s,eF,_=run(tm=tm2()); refF=C.met3(eF); print(linea('FIEL + SOL sin nota',eF))
  s,eB,_=run(tm=tm2(btc_sn=True)); q=C.met3(eB); print(linea('  + BTC salida neta ×1,5',eB,refF))
  print('bootstrap',C.bootstrap(eF,eB,2000))
  s,eC,_=run(tm=tm2(btc_sn=True,sobre=0.75)); print(linea('  + BTC sn + sobrecal ×0,75',eC,refF))
  rng=np.random.default_rng(5); yr=pd.DatetimeIndex(O.t_entrada.values).year
  idx=np.flatnonzero(cr&(act=='BTC')&BASEV); cnt=np.zeros(3); N=200
  for it in range(N):
      sn2=sn.copy()
      for y in np.unique(yr[idx]):
          ii=idx[yr[idx]==y]; sn2[ii]=rng.permutation(sn[ii])
      w=tm2(); w[cr&(act=='BTC')&sn2]*=1.5
      w=np.where(cr,np.clip(tam*w,0.25,5.0)/np.maximum(tam,1e-9),w)
      s,e,_=run(tm=w); qq=C.met3(e); cnt+=[qq[i]['ratio']>=q[i]['ratio'] for i in range(3)]
  print('placebo BTC sn: barajado ≥ real',(cnt/N).round(3),flush=True)
