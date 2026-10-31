exec(open('oficial_test.py').read().split("print('Connors oficial")[0])
cn=(L=='yt_connors_qqq')&W; me=(L=='mensuales')&((O.t_entrada>=C.desde).values)
B2=BASE|me
res={}
for nom,m in (('BASE+T1/T2+N1 (vigente antes)',B2|n1),('BASE+T1/T2+Connors (sitio de N1)',B2|cn),('BASE+T1/T2+N1+Connors',B2|n1|cn)):
    r,e=C.sim(m); res[nom]=(e,C.met3(e)); print(f'{nom:36s}',C.fmt(res[nom][1]),flush=True)
e0,q0=res['BASE+T1/T2+N1 (vigente antes)']; e1,q1=res['BASE+T1/T2+Connors (sitio de N1)']
print('Connors frente a N1:', 'PASA' if all(q1[i]['ratio']>q0[i]['ratio'] for i in range(3)) else 'no','boot',round(C.bootstrap(e0,e1,500),2))
