from ver import *
def mens(eq,v): return eq[(eq.index>=v.desde)&(eq.index<=HOY)].resample('ME').last().diff().dropna().values
def rt(x):
    c=np.cumsum(x); d=np.max(np.maximum.accumulate(np.r_[0,c])[1:]-c); return c[-1]/max(d,1e-9)
for ter in (True,False):
    v=V(ter); L=v.L; sen=v.sen
    def k8():
        t=v.mult(2,1,0.75); t[(L=='petroleo')&np.isin(sen,['L2','tras-noticia (bajada)'])]=0.5; return t
    for fz in ((4,0.5),(3,0.5),(5,0.5),(4,0.75)):
        _,e0=v.sim(v.mult(),freno=fz); q0=tres(e0,v.desde); _,e=v.sim(k8(),freno=fz); q=tres(e,v.desde)
        print('TERCIO',int(ter),'freno',fz,'K8',fmt(q),'| B0',' / '.join(f'{x[2]:.2f}' for x in q0),'PASA' if all(q[i][2]>q0[i][2] for i in range(3)) else '-')
        if fz==(4,0.5):
            ep=episodios(e,v.desde); print('   5 peores',round(np.mean(ep[:5]),2),'peor año',min(a[0] for a in anual(e,v.desde).values()),'desde 2024/2025',[round(met(e,pd.Timestamp(a))[2],2) for a in ('2024-01-01','2025-01-01')])
            m0=mens(e0,v); m=mens(e,v); rng=np.random.default_rng(11); N=len(m)
            print('   remuestreo',np.mean([rt(m[i])>rt(m0[i]) for i in [rng.integers(0,N,N) for _ in range(2000)]]))
            print('   años',{y:a[0] for y,a in anual(e,v.desde).items()})
