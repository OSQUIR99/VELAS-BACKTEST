from base import *
cs=(L=='corto_sector')&W; ci=(L=='corto_indices_credito')&W; cp=(L=='corto_petroleo')&W
cr24=(L=='cripto_24h')&(O.t_entrada>=C.desde).values&O.en_cartera.values
cri=(L=='cripto')&W
filas=[]
for tope in (True,False):
  for x2 in (True,False):
    for ind in (True,False):
      for cripto in ('realista','24h'):
        nuc=nucleo.copy()
        if cripto=='24h': nuc=(nuc&~cri)|cr24
        ex_=cs|(ci if ind else False)
        base=nuc|ex_
        C.usar_base_31oct=tope
        tb=C.tam_base.copy()
        if not x2: C.tam_base[cs|ci]=1.0
        r0,e0=C.sim(base,exentas=ex_); q0=C.met3(e0)
        r1,e1=C.sim(base|n1,exentas=ex_); q1=C.met3(e1)
        C.tam_base=tb
        filas.append(dict(tope=tope,x2=x2,indices=ind,cripto=cripto,base=round(q0[0]['ratio'],2),b1821=round(q0[1]['ratio'],2),b2226=round(q0[2]['ratio'],2),
                          n1=round(q1[0]['ratio'],2),n1_1821=round(q1[1]['ratio'],2),n1_2226=round(q1[2]['ratio'],2),pasa=all(q1[i]['ratio']>q0[i]['ratio'] for i in range(3))))
        print(filas[-1],flush=True)
pd.DataFrame(filas).to_csv('rejilla_n1.csv',index=False)
