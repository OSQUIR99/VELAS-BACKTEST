exec(open('/home/claude/vol2/var.py').read().split("if __name__")[0])
for c in COINS: CACHE[c]=prep(c)
def collect(fn,side=1):
    out=[]
    for c in COINS:
        T=run(CACHE[c],fn(CACHE[c]).fillna(False),side); T['coin']=c; out.append(T)
    T=pd.concat(out).sort_index(); return T[T.index>='2018-01-01']
brk=lambda d:d.close>d.hi20
V1=collect(lambda d:brk(d)&d.comp); NO=collect(lambda d:brk(d)&~d.comp)
diff=V1.R.mean()-NO.R.mean()
# placebo: compresión desplazada en el tiempo (misma proporción de días), por moneda
rng=np.random.default_rng(261026); sims=[]
for _ in range(200):
    sh=int(rng.integers(90,900))*int(rng.choice([-1,1]))
    a=collect(lambda d:brk(d)&d.comp.shift(sh).fillna(False).astype(bool)); b=collect(lambda d:brk(d)&~d.comp.shift(sh).fillna(False).astype(bool))
    sims.append(a.R.mean()-b.R.mean())
sims=np.array(sims)
print(f'Diferencia real V1 − sin compresión: {diff:+.2f} R · placebo: mediana {np.median(sims):+.2f}, percentil {(sims<diff).mean()*100:.0f}')
print('Mediana R V1 %.2f vs sin %.2f; sin las 5 mejores V1 %.2f'%(V1.R.median(),NO.R.median(),V1.R.drop(V1.R.nlargest(5).index).mean()))
# meses distintos
print('V1 meses distintos',V1.index.to_period('M').nunique(),'de',len(V1))
# vecinos: umbral de compresión y ventana
for thr in [0.1,0.15,0.2,0.3]:
    for win in [5,10,20]:
        fa=lambda d,thr=thr,win=win:brk(d)&(d.pct<=thr).rolling(win).max().astype(bool)
        a=collect(fa); b=collect(lambda d,thr=thr,win=win:brk(d)&~(d.pct<=thr).rolling(win).max().astype(bool))
        e=lambda T,x,y:T[(T.index>=x)&(T.index<y)].R.mean()
        print(f' ≤{thr} en {win} d: n{len(a)} {a.R.mean():+.2f} vs {b.R.mean():+.2f} | 18-21 {e(a,"2018","2022"):+.2f}/{e(b,"2018","2022"):+.2f} 22-26 {e(a,"2022","2027"):+.2f}/{e(b,"2022","2027"):+.2f}')
pd.to_pickle(V1,'/home/claude/vol2/V1.pkl')
