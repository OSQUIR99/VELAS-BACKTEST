from base import *
import json
if __name__=="__main__": r0,e0,q0=run(); print('B0',C.fmt(q0),flush=True)
FAM={'cripto':(L=='cripto'),'petroleo':(L=='petroleo'),'x_petroleo':(L=='x_petroleo'),'c10':(L=='c10'),'shy':(L=='shy'),
     'E1':E1,'connors':(L=='yt_connors_qqq'),'oro':(L=='metales')&(act=='oro'),'corto_sector':(L=='corto_sector'),
     'corto_ind':(L=='corto_indices_credito'),'corto_pet':(L=='corto_petroleo')}
VAL=[0.5,0.75,1.0,1.25,1.5,2.0]
def tm_of(w):
    t=np.ones(len(O))
    for f,m in FAM.items(): t[m]=w[f]
    return t
def score(w,idx):
    r,e,q=run(tm=tm_of(w)); return q[idx]['ratio'],q
if __name__=="__main__":
    for train,test in ((1,2),(2,1)):
      w={f:1.0 for f in FAM}; best,_=score(w,train)
      for it in range(3):
          cambio=False
          for f in FAM:
              for v in VAL:
                  if v==w[f]: continue
                  w2=dict(w); w2[f]=v; s,_=score(w2,train)
                  if s>best+0.01: best,w,cambio=s,w2,True
          if not cambio: break
      s,q=score(w,train)
      print('ENTRENA', ['','2018-21','2022-26'][train], {k:v for k,v in w.items() if v!=1}, '| entrena',round(q[train]['ratio'],2),'prueba',round(q[test]['ratio'],2),'(base',round(q0[test]['ratio'],2),')', C.fmt(q), 'PASA' if ok(q,q0) else '-',flush=True)
      json.dump(w,open(f'pesos_{train}.json','w'))
