import pandas as pd, numpy as np, json
from core import cargar
R=json.load(open('resultados.json'))
ev1=pd.read_parquet('ev1.parquet'); ev1=ev1[ev1.k==2.5]
ev2=pd.read_parquet('ev2.parquet'); ev2=ev2[ev2.k==2.5]
c2=pd.read_parquet('ctrl2.parquet'); c2=c2[c2.k==2.5]
ACT=['BTC','sp500','nasdaq100','oro','plata','brent']; TFS=['1h','4h','1d']
def r3(x): return None if pd.isna(x) else round(float(x),4)
for a in ACT:
    for tf in TFS:
        f=cargar(a,tf).fecha.values; n=len(f)
        g=ev1[(ev1.activo==a)&(ev1.tf==tf)].copy()
        j=g.j.values.astype(int)
        e1=np.clip(j+g.leg_bars.values.astype(int),0,n-1); e2=np.clip(j+g.tend_bars.values.astype(int),0,n-1)
        g['leg_h']=(f[e1]-f[j])/np.timedelta64(1,'h'); g['tend_h']=(f[e2]-f[j])/np.timedelta64(1,'h')
        for c,x in g.groupby('cat'):
            if c in R['tramos'][a][tf]:
                R['tramos'][a][tf][c]['tramo_h']=r3(x.leg_h.median()); R['tramos'][a][tf][c]['tend_h']=r3(x.tend_h.median())
        d=ev2[(ev2.activo==a)&(ev2.tf==tf)&ev2.dejado&ev2.roto]
        cf=d.cf.values.astype(int); en=np.clip(cf+d.espera.values.astype(int),0,n-1)
        R['dejados_espera_mediana_h'][a][tf]=r3(np.median((f[en]-f[cf])/np.timedelta64(1,'h')))
# giro agrupado por activo
r=ev2[ev2.res.isin([1,-1])]; c=c2[c2.res.isin([1,-1])]
R['giro_activo']={a:dict(real=r3(100*(r[r.activo==a].res==1).mean()),azar=r3(100*(c[c.activo==a].res==1).mean()),n=int((r.activo==a).sum()),nc=int((c.activo==a).sum())) for a in ACT}
b15=pd.read_parquet('ev2_btc15.parquet'); c15=pd.read_parquet('ctrl2_btc15.parquet')
R['giro_activo']['BTC15']=dict(real=r3(100*(b15[b15.res.isin([1,-1])].res==1).mean()),azar=r3(100*(c15[c15.res.isin([1,-1])].res==1).mean()),n=int(b15.res.isin([1,-1]).sum()),nc=int(c15.res.isin([1,-1]).sum()))
# tramos 4h globales por activo para la tabla resumen ya estan en R['tramos']
# periodos
per={}
for a in ACT:
    per[a]={tf:[str(pd.Timestamp(x).date()) for x in (cargar(a,tf).fecha.iloc[[0,-1]].values)] for tf in TFS}
R['periodos']=per
json.dump(R,open('resultados.json','w'),ensure_ascii=False)
print(json.dumps(R['giro_activo'])); print(json.dumps(R['dejados_espera_mediana_h'])); print(json.dumps(R['periodos']))
print(json.dumps({a:{c:(R['tramos'][a]['4h'][c]['tramo_pct'],R['tramos'][a]['4h'][c]['tramo_h']) for c in R['tramos'][a]['4h']} for a in ACT}))
e4=pd.read_parquet('ev4.parquet')
for a in ACT:
    for tf in TFS:
        R['por_activo'][a][tf]['riesgo_smc']=round(float(100*e4[(e4.activo==a)&(e4.tf==tf)].riesgo_pct.median()),2)
json.dump(R,open('resultados.json','w'),ensure_ascii=False)
