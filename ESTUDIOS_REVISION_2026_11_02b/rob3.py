from rob2 import tm2, run, linea, C, cr, act, sn, tam, np, met_eq, pd, O, BASEV
s,eF,_=run(tm=tm2()); refF=C.met3(eF)
for k in [1.25,1.5,1.75,2.0]:
    w=tm2(); w[cr&(act=='BTC')&sn]*=k; w=np.where(cr,np.clip(tam*w,0.25,5.0)/np.maximum(tam,1e-9),w)
    s,e,_=run(tm=w); print(linea(f'BTC salida neta ×{k}',e,refF),flush=True)
    if k==1.5:
        print('épocas', ' · '.join(f"{a[:4]} {met_eq(e,pd.Timestamp(a),pd.Timestamp(b))['ratio']:.2f}/{met_eq(eF,pd.Timestamp(a),pd.Timestamp(b))['ratio']:.2f}" for a,b in [('2018-05-01','2020-01-01'),('2020-01-01','2022-01-01'),('2022-01-01','2024-01-01'),('2024-01-01','2026-10-21')]))
        x=(cr&(act=='BTC')&sn&(s>0)); print('ops BTC sn en cartera',int(x.sum()),'peso medio',round(float(s[x].mean()),2))
