from h import *
C,M,r0,e0,q0=base_nueva(); print('BASE',C.fmt(q0),f'| 24-26 {met24(C,e0):.2f}',flush=True)
cb=cond_base(O0); pts=O0.puntos.fillna(-9).values
def run(nom,c,cfg=None,ret=False):
    O,D,n=sin_tercio(O0,D0,c); C2=cartera(O,D); M2=mascaras(C2); _,e,q=evalua(C2,M2['BASE'],M2['EX'],cfg=cfg)
    if cfg is None: informe(C2,f'{nom} (n={n})',q,q0,e,e0)
    return C2,e,q
for nom,c in [('puntos ≥2 solo (sin la vol de BTC)',pts>=2),('BTC ≤0,10 o puntos ≥1',cb|(pts>=1)),('BTC ≤0,10 o puntos ≥2',cb|(pts>=2))]:
    run(nom,c)
for a in ['BTC','ETH','ADA','ZEC','LINK']:
    run(f'BTC≤0,10 o puntos≥2, salvo {a}',cb|((pts>=2)&(O0.activo.values!=a)))
# frenos distintos: compara base y variante con el mismo freno
for fr in [(3,0.5),(5,0.5),(4,0.75)]:
    cfg=dict(comun.FL); cfg['freno']=fr
    _,eb,qb=evalua(C,M['BASE'],M['EX'],cfg=cfg); _,ev,qv=run('x',cb|(pts>=2),cfg=cfg)
    print(f'freno {fr}: base {C.fmt(qb)} | variante {C.fmt(qv)}', 'PASA' if all(qv[i]['ratio']>qb[i]['ratio'] for i in range(3)) else '-',flush=True)
# por años
C2,e2,q2=run('x',cb|(pts>=2),cfg=dict(comun.FL))
y0=e0.resample('YE').last().diff(); y2=e2.resample('YE').last().diff()
print('diferencia por año (R):',(y2-y0).round(1).dropna().to_dict(),flush=True)
# placebo: mismas operaciones añadidas en número, elegidas al azar entre las que podrían
eleg=np.flatnonzero(~cb & (O0.activo.values!='SOL') & O0.parcial.values.astype(bool))
k=int(((pts>=2)&~cb&(O0.activo.values!='SOL')&O0.parcial.values.astype(bool)).sum()); print('placebo: añadidas',k,'de',len(eleg),flush=True)
rng=np.random.default_rng(11); res=[]
for t in range(40):
    c=cb.copy(); c[rng.choice(eleg,k,replace=False)]=True
    O,D,n=sin_tercio(O0,D0,c); Cp=cartera(O,D); Mp=mascaras(Cp); _,e,q=evalua(Cp,Mp['BASE'],Mp['EX'])
    res.append([q[0]['ratio'],q[1]['ratio'],q[2]['ratio']])
res=np.array(res); print('placebo medias',res.mean(0).round(2),'máx',res.max(0).round(2),'% ≥ variante en todo',(res[:,0]>=q2[0]['ratio']).mean(),'en 22-26',(res[:,2]>=q2[2]['ratio']).mean(),flush=True)
