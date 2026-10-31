exec(open('evaluar.py').read().split("filas=[]")[0])
rng=np.random.default_rng(11); res={'LINK':[], 'E1 S&P':[]}
real={}
for nb,b0 in list(C.bases.items())[:2]:
    base=b0|n1; rb,eqb=C.sim(base); qb=C.met3(eqb)
    for f in res:
        m=FAM[f]; rr,eq=C.sim(base,tam_mult=np.where(m&alta,1.5,1.0)); q=C.met3(eq); real.setdefault(f,[]).append(q[0]['ratio']-qb[0]['ratio'])
    for k in range(40):
        sh=int(rng.integers(52,len(LQ)-52)); LS=LQ.linea.copy(); LS[:]=np.roll(LQ.linea.values,sh)
        l2=LS.reindex(vie,method='ffill').values; dd=(LS-LS.shift(13)).reindex(vie,method='ffill').values; al=(l2>50)&(dd>0)
        for f in res:
            rr,eq=C.sim(base,tam_mult=np.where(FAM[f]&al,1.5,1.0)); q=C.met3(eq)
            res[f].append((q[0]['ratio']-qb[0]['ratio'], all(q[i]['ratio']>qb[i]['ratio'] for i in range(3))))
for f in res:
    a=np.array([x[0] for x in res[f]]); p=np.array([x[1] for x in res[f]])
    print(f,'real',np.round(real[f],3),'placebo: mejora media',a.mean().round(3),'| placebos con mejora >= real',(a>=np.mean(real[f])).mean().round(2),'| placebos que pasan',p.mean().round(2))
