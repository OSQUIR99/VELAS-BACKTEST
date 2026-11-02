from base import *
from exp2 import FAM
from exp4 import tmw
import itertools
r0,e0,q0=run()
_,eK,qK=run(tm=tmw(corto_pet=2,petroleo=0.75,x_petroleo=0.75)); dK=np.mean([qK[i]['ratio']-q0[i]['ratio'] for i in range(3)])
print('TERCIO',TERCIO,'B0',C.fmt(q0),'| K2',C.fmt(qK),'PASA' if ok(qK,q0) else '-',flush=True)
if TERCIO:
    # placebo: corto_pet x2 + otras dos familias (no petróleo) a x0,75
    fams=[f for f in FAM if f not in ('shy','corto_pet','petroleo','x_petroleo')]
    res=[]
    for a,b in itertools.combinations(fams,2):
        _,e,q=run(tm=tmw(corto_pet=2,**{a:0.75,b:0.75})); res.append((a,b,ok(q,q0),np.mean([q[i]['ratio']-q0[i]['ratio'] for i in range(3)])))
    print('placebo: pasan',sum(r[2] for r in res),'de',len(res),'| mejora media K2',round(dK,3),'| placebos con mejora >= K2',sum(r[3]>=dK for r in res))
    for r in sorted(res,key=lambda x:-x[3])[:4]: print('  ',r)
    # por qué: petróleo largo solo, por épocas, y su peso en las caídas
    for nm,m in (('petroleo',FAM['petroleo']),('x_petroleo',FAM['x_petroleo']),('corto_pet',FAM['corto_pet'])):
        t=pd.to_datetime(O.t_entrada); mm=m&BASE
        for a,b in (('2018-05','2022'),('2022','2027')):
            s=mm&(t>=a).values&(t<b).values
            print(nm,a,b,'ops',s.sum(),'R/op',round(O.r_final[s].mean(),3),'acierto',round((O.r_final[s]>0).mean(),2))
