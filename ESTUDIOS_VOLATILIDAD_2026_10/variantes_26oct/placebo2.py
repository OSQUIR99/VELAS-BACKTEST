exec(open('/home/claude/vol2/salida.py').read().split("for thr in")[0])
import io,contextlib
base=pd.Series(SYS.R.values*SYS['size'].values,index=SYS.index); r0=[rat(base,SYS.exit,a,b) for a,b in P]
def score(mask):
    T=pd.concat([trades(c,nopart=mask) for c in COINS]).sort_index()
    R=pd.Series(T.R.values*SYS['size'].values,index=T.index); r1=[rat(R,T.exit,a,b) for a,b in P]
    return r1[4],r1[5],sum(v>u for u,v in zip(r0[:4],r1[:4]))
rng=np.random.default_rng(26102026)
for thr in [0.1,0.2]:
    real=score((bp<=thr).to_dict()); S=[]
    for _ in range(150):
        sh=int(rng.integers(120,1200))*int(rng.choice([-1,1]))
        S.append(score((bp.shift(sh)<=thr).to_dict()))
    S=np.array(S)
    print(f'BTC vol ≤{thr}: real todo {real[0]:.2f}, 22-26 {real[1]:.2f}, épocas {real[2]}/4 | placebo pctl todo {(S[:,0]<real[0]).mean()*100:.0f}, 22-26 {(S[:,1]<real[1]).mean()*100:.0f}, mediana todo {np.median(S[:,0]):.2f}, placebos con ≥ mismas épocas {(S[:,2]>=real[2]).mean()*100:.0f} %')
