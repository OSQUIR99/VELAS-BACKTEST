from b import *
import sys, time
seed = int(sys.argv[1]); N = int(sys.argv[2])
real = [x['ratio'] for x in montaje(flujo=1.5)]
flag = O.salida_neta.astype(bool).values.copy()
btc = C.cri & (act=='BTC'); yrs = O.t_entrada.dt.year.values
rng = np.random.default_rng(seed); cnt=np.zeros(3); vals=[]
t=time.time()
for it in range(N):
    f2 = flag.copy()
    for y in np.unique(yrs[btc]):
        ii = np.flatnonzero(btc & (yrs==y)); f2[ii] = rng.permutation(flag[ii])
    v = [x['ratio'] for x in montaje(flujo=1.5, flag=f2)]; vals.append(v); cnt += np.array([v[i] >= real[i] for i in range(3)])
print(f'semilla {seed} N={N}: real', np.round(real,2), '% barajado>=real', np.round(100*cnt/N,1), 'mediana', np.round(np.median(vals,0),2), f'{time.time()-t:.0f}s')
