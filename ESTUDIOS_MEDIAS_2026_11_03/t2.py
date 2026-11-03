from t1 import *
print('== tamaño menor de la propuesta 1 (BTC con stop) y de la familia lenta')
for nm in ['p1_btc_st','sectores_lentos']:
    m=(L==nm)&d
    for f in (0.5,0.25):
        tm=np.ones(len(O)); tm[m]=f; e,q=run(C,M['BASE']|m,M['EX'],tm=tm); linea(C,f'+ {nm} x{f}',e,q,e0,q0)
print('== solas (ventana may-2018 →)')
cr=(L=='cripto')&M['BASE']
def mens(mask):
    s=pd.Series(O.r_final[mask].values,index=pd.to_datetime(O.t_salida[mask]).values); return s.resample('ME').sum()
mc=mens(cr)
for nm in ['p1_btc_st','p1_6_st','sectores_lentos']:
    m=(L==nm)&d; s=O[m]; r=s.r_final; t=pd.to_datetime(s.t_salida)
    eq=pd.Series(r.values,index=t.values).sort_index().cumsum(); dd=(eq.cummax()-eq).max(); yrs=8.5
    anual=pd.Series(r.values,index=t.values).resample('YE').sum()
    mm=mens(m).reindex(mc.index).fillna(0)
    print(nm,'ops',len(s),'R/año',round(r.sum()/yrs,1),'caída',round(dd,1),'ratio',round(r.sum()/yrs/dd,2),'acierto',round((r>0).mean(),2),'peor año',round(anual.min(),1),'corr. mensual con cripto',round(mm.corr(mc),2),flush=True)
