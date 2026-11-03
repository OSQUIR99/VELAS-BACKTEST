from ver import *
import itertools, json
v=V(True); O=v.O; L=v.L; sen=v.sen
def K(nom):
    return {'B0':v.mult(),'K6':v.mult(corto_pet=2),'K2':v.mult(2,0.75,0.75),'K7':v.mult(2,1,0.75,pet_no_L1=0.5),
            'K2b (pet x0,75 + x_pet x0,75, sin corto)':v.mult(1,0.75,0.75)}[nom]
noms=['B0','K6','K2','K7','K2b (pet x0,75 + x_pet x0,75, sin corto)']
print('--- frenos')
for fz in ((4,0.5),(3,0.5),(5,0.5),(4,0.75),None):
    qb=None
    for n in noms:
        _,eq=v.sim(K(n),freno=fz); q=tres(eq,v.desde)
        if n=='B0': qb=q
        ok=all(q[i][2]>qb[i][2] for i in range(3))
        print(f'freno {str(fz):10s} {n:42s}',fmt(q),'PASA' if (ok and n!='B0') else '')
# bootstrap pareado mensual propio y bloques de 3 meses
def mens(eq): return eq[(eq.index>=v.desde)&(eq.index<=HOY)].resample('ME').last().diff().dropna()
def rt(x):
    c=np.cumsum(x); d=np.max(np.maximum.accumulate(np.r_[0,c])[1:]-c); return c[-1]/max(d,1e-9)
_,e0=v.sim(K('B0')); m0=mens(e0).values
rng=np.random.default_rng(11)
print('--- remuestreo (fracción en que gana a B0): meses sueltos / bloques de 6 meses')
for n in noms[1:]:
    _,e=v.sim(K(n)); m=mens(e).values; N=len(m)
    g1=np.mean([rt(m[i])>rt(m0[i]) for i in [rng.integers(0,N,N) for _ in range(2000)]])
    g2=[]
    for _ in range(2000):
        st=rng.integers(0,N-6,N//6+1); i=np.concatenate([np.arange(a,a+6) for a in st])[:N]; g2.append(rt(m[i])>rt(m0[i]))
    print(f'{n:42s} {g1:.2f} / {np.mean(g2):.2f}')
print('--- por años (R, caída dentro del año)')
A_={}
for n in noms[:4]:
    _,e=v.sim(K(n)); A_[n]=anual(e,v.desde)
    ep=episodios(e,v.desde)
    print(n,'| peor año R',min(x[0] for x in A_[n].values()),'| media 5 peores caídas',round(np.mean(ep[:5]),2),[round(x,1) for x in ep[:5]])
print(pd.DataFrame({n:{y:f'{a[0]:+.1f} ({a[1]:.1f})' for y,a in A_[n].items()} for n in A_}).to_string())
# últimos años
print('--- ratio desde 2024 / desde 2025')
for n in noms[:4]:
    _,e=v.sim(K(n)); print(n,[round(met(e,pd.Timestamp(a))[2],2) for a in ('2024-01-01','2025-01-01')],[round(met(e,pd.Timestamp(a))[0],1) for a in ('2024-01-01','2025-01-01')])
