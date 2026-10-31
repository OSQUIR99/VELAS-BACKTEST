import sys
sys.argv=[sys.argv[0]]
exec(open('base.py').read().replace("('/home/claude/velas-backtest/MOTOR/listas_reconstruidas','/home/claude/liq31/listas_nuevas','/home/claude/exacta/listas_extra')","('/home/claude/velas-backtest/MOTOR/listas_reconstruidas','/home/claude/liq31/listas_nuevas','/home/claude/exacta/oficial')").replace("'connors_qqq'","'yt_connors_qqq'").replace("if __name__=='__main__':","if False:"))
cn=(L=='yt_connors_qqq')&W; me=(L=='mensuales')&((O.t_entrada>=C.desde).values)
print('Connors oficial desde 2018:',int(cn.sum()),'ops, R',round(float(O.r_final[cn].sum()),1),'| mensuales',int(me.sum()))
r0,e0=C.sim(BASE); q0=C.met3(e0); print(f"{'BASE (sin N1)':34s}",C.fmt(q0))
for nom,m,ref in (('Connors en lugar de E1',(BASE&~E1)|cn,q0),('Connors encima (sitio de N1)',BASE|cn,q0),('N1 encima',BASE|n1,q0)):
    r,e=C.sim(m); q=C.met3(e); ok=all(q[i]['ratio']>ref[i]['ratio'] for i in range(3))
    print(f'{nom:34s}',C.fmt(q),'PASA' if ok else 'no','boot',round(C.bootstrap(e0,e,500),2),flush=True)
B2=BASE|me; r2,e2=C.sim(B2); q2=C.met3(e2); print(f"{'BASE + T1/T2':34s}",C.fmt(q2))
for nom,m in (('+T1/T2 Connors encima',B2|cn),('+T1/T2 Connors en lugar de E1',(B2&~E1)|cn)):
    r,e=C.sim(m); q=C.met3(e); ok=all(q[i]['ratio']>q2[i]['ratio'] for i in range(3))
    print(f'{nom:34s}',C.fmt(q),'PASA' if ok else 'no','boot',round(C.bootstrap(e2,e,500),2),flush=True)
