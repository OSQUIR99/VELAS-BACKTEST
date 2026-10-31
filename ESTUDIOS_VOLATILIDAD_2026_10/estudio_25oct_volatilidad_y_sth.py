import json, numpy as np, pandas as pd, os
D='/home/claude/vol/data/'
def px(c,tf):
    d=pd.read_parquet(D+f'{c}_{tf}.parquet'); d=d.rename(columns={'fecha':'t','apertura':'open','maximo':'high','minimo':'low','cierre':'close','volumen':'vol'})
    return d.set_index('t')[['open','high','low','close','vol']]
def btc_daily():
    b=pd.DataFrame(json.load(open(D+'bci.json'))['values']); b.index=pd.to_datetime(b.x,unit='s').dt.normalize(); b=b.y[~b.index.duplicated()]
    b=b[b>0]
    bn=px('BTC','1d').close
    ok=pd.read_csv(D+'okx_btc_1d.csv',index_col=0,parse_dates=True).close if os.path.exists(D+'okx_btc_1d.csv') else pd.Series(dtype=float)
    s=pd.concat([b[b.index<bn.index[0]],bn,ok[ok.index>bn.index[-1]]])
    s=s[~s.index.duplicated()].asfreq('D').ffill()
    return s[s.index>='2011-01-01']
def fng():
    f=pd.DataFrame(json.load(open(D+'fng.json'))['data']); f.index=pd.to_datetime(f.timestamp.astype(int),unit='s').dt.normalize()
    return f.value.astype(float).sort_index()
def bg(name,key):
    d=pd.DataFrame(json.load(open(D+name))); d.index=pd.to_datetime(d.d); return d[key].astype(float).sort_index()
import sys; sys.path.insert(0,'/home/claude/vol/code'); from base import *
s=btc_daily(); lp=np.log(s); r=lp.diff(); v=r.rolling(30).std()*100
f=fng(); f30=f.rolling(30,min_periods=20).mean().reindex(s.index)
# percentil de la volatilidad: ventana móvil de 3 años (la volatilidad de BTC baja con los años)
pct3=v.rolling(1095,min_periods=730).apply(lambda x:(x<=x[-1]).mean(),raw=True)
pos90=(s-s.rolling(90).min())/(s.rolling(90).max()-s.rolling(90).min())   # sustituto del sentimiento
ret60=s/s.shift(60)-1
H=[30,60,90]
def fwd(i,h):
    w=lp.iloc[i:i+h+1]-lp.iloc[i]; return w
def first_touch(i,thr=np.log(1.10),hmax=120):
    w=lp.iloc[i+1:i+hmax+1]-lp.iloc[i]
    up=np.where(w.values>=thr)[0]; dn=np.where(w.values<=-thr)[0]
    a=up[0] if len(up) else 9999; b=dn[0] if len(dn) else 9999
    if a==b==9999: return 0,np.nan
    return (1,a+1) if a<b else (-1,b+1)
rows=[]
idx=s.index
for i in range(len(s)-1):
    if idx[i]<pd.Timestamp('2013-01-01') or np.isnan(pct3.iloc[i]): continue
    d={'t':idx[i],'v':v.iloc[i],'pct':pct3.iloc[i],'f30':f30.iloc[i],'pos90':pos90.iloc[i],'ret60':ret60.iloc[i]}
    for h in H:
        if i+h<len(s):
            w=fwd(i,h); d[f'ret{h}']=np.exp(w.iloc[-1])-1; d[f'maxabs{h}']=np.exp(np.abs(w).max())-1
            d[f'vratio{h}']=v.iloc[i+h]/v.iloc[i]
            d[f'up{h}']=np.exp(w.max())-1; d[f'dn{h}']=np.exp(w.min())-1
    d['dir10'],d['t10']=first_touch(i)
    d['dir15'],d['t15']=first_touch(i,np.log(1.15),180)
    rows.append(d)
X=pd.DataFrame(rows).set_index('t')
X.to_pickle('/home/claude/vol/data/X_vol.pkl')
def episodes(mask,gap=60,minrun=1):
    m=mask.fillna(False).astype(bool); run=m.groupby((~m).cumsum()).cumsum()
    ok=run>=minrun; out=[];last=None
    for t,val in ok.items():
        if val and (last is None or (t-last).days>gap): out.append(t)
        if val: last=t
    return out
print('Días en la muestra',len(X),X.index[0].date(),X.index[-1].date())
print('Hoy: vol30 %.2f %%, percentil 3 años %.2f, F&G30 %.1f, pos90 %.2f'%(v.iloc[-1],pct3.iloc[-1],f30.iloc[-1],pos90.iloc[-1]))
for thr in [0.05,0.10,0.20]:
  for minrun in [1,10,20]:
    ep=episodes(X.pct<=thr,60,minrun); E=X.loc[[e for e in ep if e in X.index]]
    E=E[E.index<=X.index[-1]]
    print(f'\n== vol30 en su {int(thr*100)} % bajo de 3 años, sostenida {minrun} d: {len(E)} episodios')
    for h in H:
        c=f'maxabs{h}'; ee=E[c].dropna(); bb=X[c].dropna()
        print(f'  {h} d: mayor movimiento mediano {ee.median()*100:.1f} % (todos los días {bb.median()*100:.1f} %) · P(≥15 %) {(ee>=.15).mean()*100:.0f} % vs {(bb>=.15).mean()*100:.0f} % · vol después/ahora mediana {E[f"vratio{h}"].median():.2f} (todos {X[f"vratio{h}"].median():.2f}) · ret mediano {E[f"ret{h}"].median()*100:+.1f} % (todos {X[f"ret{h}"].median()*100:+.1f})')
    print('  primer ±10 %: sube',(E.dir10==1).sum(),'baja',(E.dir10==-1).sum(),'· días mediana',E.t10.median(),'| todos: sube %.0f %%'%((X.dir10==1).mean()*100))
    if thr==0.10 and minrun==10:
        print(E[['v','pct','f30','pos90','ret60','dir10','t10','ret30','ret60','maxabs60']].round(3).to_string())
import pandas as pd, numpy as np
X=pd.read_pickle('/home/claude/vol/data/X_vol.pkl')
X['greed_f']=np.where(X.f30>=55,1,np.where(X.f30<=45,-1,0)); X.loc[X.f30.isna(),'greed_f']=np.nan
X['greed_p']=np.where(X.pos90>=0.7,1,np.where(X.pos90<=0.3,-1,0))
def tab(lowmask,label):
    for sent in ['greed_f','greed_p']:
        out=[]
        for g,name in [(1,'codicia'),(-1,'miedo')]:
            for nm,m in [('vol baja',lowmask),('resto',~lowmask)]:
                sub=X[m&(X[sent]==g)&(X.dir10!=0)]
                if len(sub)==0: continue
                contra=(sub.dir10==-g).mean()
                # bloques de 30 días para contar «casos» independientes
                nb=sub.index.to_period('M').nunique()
                out.append(f'{name}/{nm}: contra {contra*100:.0f} % (días {len(sub)}, meses {nb}); ret60 med {sub.ret60.median()*100:+.1f} %')
        print(f'  [{label} · {sent}] '+' | '.join(out))
for thr in [0.05,0.10,0.20]:
    low=X.pct<=thr
    tab(low,f'pct≤{thr}')
    tab(low&(X.index>='2018-02-01'),f'pct≤{thr} desde 2018')
import pandas as pd, numpy as np
X=pd.read_pickle('/home/claude/vol/data/X_vol.pkl')
def episodes(mask,gap=45):
    out=[];last=None
    for t,val in mask.fillna(False).items():
        if val and (last is None or (t-last).days>gap): out.append(t)
        if val: last=t
    return out
for thr in [0.05,0.10]:
  for name,m in [('miedo F&G≤45',X.f30<=45),('codicia F&G≥55',X.f30>=55),('precio bajo en 90 d (pos≤0,3)',X.pos90<=0.3),('precio alto en 90 d (pos≥0,7)',X.pos90>=0.7)]:
    ep=episodes((X.pct<=thr)&m); E=X.loc[ep]
    good=(E.dir10==1) if ('miedo' in name or 'bajo' in name) else (E.dir10==-1)
    print(f'\n== pct≤{thr} + {name}: {len(E)} episodios · contra el sentimiento {good.sum()}/{(E.dir10!=0).sum()}')
    print(E[['v','f30','pos90','dir10','t10','dir15','t15','up60','dn60','ret60']].round(2).to_string())
import sys; sys.path.insert(0,'/home/claude/vol/code'); from base import *
ema=lambda s,n: s.ewm(span=n,adjust=False).mean()
def atr(df,n=14):
    pc=df.close.shift(1); tr=pd.concat([df.high-df.low,(df.high-pc).abs(),(df.low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False).mean()
def montaje(h4,start='2018-01-01'):
    # REBOTE 4H básico (motor del 19-oct): tendencia diaria + retroceso a la EMA20 de 4 h; 1/3 en +1R y stop que sube
    h4=h4[h4.close>0].copy()
    h4['e20']=ema(h4.close,20);h4['e50']=ema(h4.close,50);h4['e200']=ema(h4.close,200);h4['atr']=atr(h4)
    dd=h4.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
    dd['e50']=ema(dd.close,50);dd['e200']=ema(dd.close,200);dd['atr']=atr(dd)
    c=[dd.close>dd.e50,dd.close>dd.e200,dd.e50>dd.e200,dd.e50>dd.e50.shift(1)]
    dd['sub']=sum(np.where(x,1,-1) for x in c)
    pl=(dd.low<dd.low.shift(1))&(dd.low<dd.low.shift(2))&(dd.low<dd.low.shift(-1))&(dd.low<dd.low.shift(-2))
    dd['lastpiv']=pd.Series(np.where(pl,dd.low,np.nan),index=dd.index).shift(2).ffill()
    dp=dd.shift(1); day=h4.index.normalize()
    sub=day.map(dp['sub']).values; datr=day.map(dp['atr']).values; dpiv=day.map(dp['lastpiv']).values
    o=h4.open.values;hi=h4.high.values;lo=h4.low.values;cl=h4.close.values
    e20=h4.e20.values;e50=h4.e50.values;e200=h4.e200.values;a4=h4.atr.values;idx=h4.index
    tr=[];i=250;n=len(h4)
    while i<n-1:
        if not (sub[i]>=2 and e50[i]>e200[i] and cl[i]>e20[i] and (lo[i]<=e20[i] or cl[i-1]<e20[i-1])): i+=1; continue
        j=i+1;ent=o[j];R=2*a4[i];stop=ent-R;part=False;mx=hi[j];k=j;res=None
        while k<n:
            if lo[k]<=stop:
                px=min(stop,o[k]); res=(1/3 if part else 0)+(2/3 if part else 1)*(px-ent)/R; break
            if not part and hi[k]>=ent+R: part=True; stop=max(stop,ent)
            mx=max(mx,hi[k])
            if part and not np.isnan(datr[k]):
                A=datr[k]; cand=dpiv[k]-0.25*A if not np.isnan(dpiv[k]) else np.nan
                if np.isnan(cand) or not (mx-3.5*A<=cand<=mx-1.5*A): cand=mx-2.5*A
                stop=max(stop,cand)
            k+=1
        if res is None: res=(1/3 if part else 0)+(2/3 if part else 1)*(cl[-1]-ent)/R
        res-=0.0005*ent/R
        tr.append((idx[j],res,R/ent)); i=k+1
    T=pd.DataFrame(tr,columns=['t','R','stop_pct']).set_index('t'); return T[T.index>=start]
if __name__=='__main__':
    TR=[]
    for c in ['BTC','ETH','SOL','ADA','ZEC','LINK']:
        T=montaje(px(c,'4h')); T['coin']=c; TR.append(T); print(c,len(T),round(T.R.mean(),2))
    TR=pd.concat(TR).sort_index()
    X=pd.read_pickle('/home/claude/vol/data/X_vol.pkl')
    s=btc_daily(); 
    # métricas del día anterior a la entrada
    F=X[['v','pct','f30','pos90']].shift(1)
    FF=F.reindex(TR.index.normalize())
    for col in F.columns: TR[col]=FF[col].values
    # volatilidad propia de cada moneda (percentil de 3 años, día anterior)
    own=[]
    for c in TR.coin.unique():
        d=px(c,'1d').close; r=np.log(d).diff(); v=r.rolling(30).std()
        p=v.rolling(1095,min_periods=365).apply(lambda x:(x<=x[-1]).mean(),raw=True).shift(1)
        sub=TR[TR.coin==c]; own.append(pd.Series(p.reindex(sub.index.normalize()).values,index=sub.index))
    TR['own_pct']=pd.concat(own).sort_index().values if False else np.nan
    for c in TR.coin.unique():
        d=px(c,'1d').close; r=np.log(d).diff(); v=r.rolling(30).std()
        p=v.rolling(1095,min_periods=365).apply(lambda x:(x<=x[-1]).mean(),raw=True).shift(1)
        m=TR.coin==c; TR.loc[m,'own_pct']=p.reindex(TR.index[m].normalize()).values
    TR.to_pickle('/home/claude/vol/data/TR.pkl')
import pandas as pd, numpy as np
TR=pd.read_pickle('/home/claude/vol/data/TR.pkl')
EP=[('2018','2019'),('2020','2021'),('2022','2023'),('2024','2026')]
def stats(R):
    s=R.sort_index(); cum=s.cumsum(); dd=(cum-cum.cummax()).min(); yrs=max((s.index[-1]-s.index[0]).days/365.25,.5); ry=s.sum()/yrs
    return ry,dd,ry/abs(dd)
def ev(name,mk,mult):
    mk=mk.fillna(False).astype(bool); a=TR[mk]; b=TR[~mk]
    ep=[]
    for x,y in EP:
        aa=a[(a.index>=x)&(a.index<=y+'-12-31')]; bb=b[(b.index>=x)&(b.index<=y+'-12-31')]
        ep.append(f'{aa.R.mean():+.2f}/{bb.R.mean():+.2f}({len(aa)})' if len(aa) else '—')
    co=sum(1 for c in TR.coin.unique() if len(a[a.coin==c])>2 and np.sign(a[a.coin==c].R.mean()-b[b.coin==c].R.mean())==np.sign(a.R.mean()-b.R.mean()))
    w=np.where(mk,mult,1.0)
    out=[]
    for lab,x,y in [('18-22','2018','2022-12-31'),('23-26','2023','2026-12-31')]:
        sel=(TR.index>=x)&(TR.index<=y); r0=stats(TR.R[sel]); r1=stats((TR.R*w)[sel])
        out.append(f'{lab} {r0[2]:.2f}→{r1[2]:.2f}')
    print(f'{name:55s} sí {len(a):4d} {a.R.mean():+.2f}R · no {b.R.mean():+.2f}R · monedas {co}/6 · épocas {" ".join(ep)} · ×{mult}: {" | ".join(out)}')
print('Total',len(TR),round(TR.R.mean(),2))
for thr in [0.05,0.10,0.20,0.30]:
    lo=TR.pct<=thr
    m='favorable' 
    ev(f'BTC vol en su {int(thr*100)} % bajo',lo,0.5)
    ev(f'BTC vol en su {int(thr*100)} % bajo + codicia (F&G30≥55)',lo&(TR.f30>=55),0.5)
    ev(f'BTC vol en su {int(thr*100)} % bajo + miedo (F&G30≤45)',lo&(TR.f30<=45),1.5)
    ev(f'BTC vol en su {int(thr*100)} % bajo + precio alto 90 d',lo&(TR.pos90>=0.7),0.5)
    ev(f'vol propia en su {int(thr*100)} % bajo',TR.own_pct<=thr,0.5)
ev('BTC vol en su 30 % alto',TR.pct>=0.7,0.5)
# Montaje cripto con la nota de puntos (versión B, aprobada el 19-oct) + franja de TOTAL2, reconstruidos para probar la volatilidad encima.
import sys; sys.path.insert(0,'/home/claude/vol/code'); from base import *
from montaje import ema, atr
COINS=['BTC','ETH','SOL','ADA','ZEC','LINK']
EST={'BTC':1.38,'ETH':1.48,'SOL':2.57,'ADA':1.74}
def trades(c,start='2018-01-01'):
    h4=px(c,'4h'); h4=h4[h4.close>0].copy()
    h4['e20']=ema(h4.close,20);h4['e50']=ema(h4.close,50);h4['e200']=ema(h4.close,200);h4['atr']=atr(h4)
    dd=h4.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
    dd['e50']=ema(dd.close,50);dd['e200']=ema(dd.close,200);dd['atr']=atr(dd)
    cnd=[dd.close>dd.e50,dd.close>dd.e200,dd.e50>dd.e200,dd.e50>dd.e50.shift(1)]
    dd['sub']=sum(np.where(x,1,-1) for x in cnd)
    pl=(dd.low<dd.low.shift(1))&(dd.low<dd.low.shift(2))&(dd.low<dd.low.shift(-1))&(dd.low<dd.low.shift(-2))
    dd['lastpiv']=pd.Series(np.where(pl,dd.low,np.nan),index=dd.index).shift(2).ffill()
    ph=pd.Series(True,index=dd.index)
    for k in range(1,6): ph&=(dd.high>dd.high.shift(k))&(dd.high>dd.high.shift(-k))
    dd['lastph']=pd.Series(np.where(ph,dd.high,np.nan),index=dd.index).shift(5).ffill()   # se conoce 5 días después
    dd['sma120r']=dd.close/dd.close.rolling(120).mean()
    dp=dd.shift(1); day=h4.index.normalize()
    sub=day.map(dp['sub']).values; datr=day.map(dp['atr']).values; dpiv=day.map(dp['lastpiv']).values
    lph=day.map(dd['lastph']).values  # máximo de giro ya confirmado (desfase de 5 días incluido)
    s120=day.map(dp['sma120r']).values
    o=h4.open.values;hi=h4.high.values;lo=h4.low.values;cl=h4.close.values
    e20=h4.e20.values;e50=h4.e50.values;e200=h4.e200.values;a4=h4.atr.values;idx=h4.index
    tr=[];i=250;n=len(h4)
    while i<n-1:
        if not (sub[i]>=2 and e50[i]>e200[i] and cl[i]>e20[i] and (lo[i]<=e20[i] or cl[i-1]<e20[i-1])): i+=1; continue
        j=i+1;ent=o[j];R=2*a4[i];stop=ent-R;part=False;mx=hi[j];k=j;res=None
        big=abs(cl[i]-o[i])>=a4[i]; broke=(not np.isnan(lph[i])) and cl[i]>lph[i]
        while k<n:
            if lo[k]<=stop:
                pxx=min(stop,o[k]); res=(1/3 if part else 0)+(2/3 if part else 1)*(pxx-ent)/R; break
            if not part and hi[k]>=ent+R: part=True; stop=max(stop,ent)
            mx=max(mx,hi[k])
            if part and not np.isnan(datr[k]):
                A=datr[k]; cand=dpiv[k]-0.25*A if not np.isnan(dpiv[k]) else np.nan
                if np.isnan(cand) or not (mx-3.5*A<=cand<=mx-1.5*A): cand=mx-2.5*A
                stop=max(stop,cand)
            k+=1
        exit_t=idx[min(k,n-1)]
        if res is None: res=(1/3 if part else 0)+(2/3 if part else 1)*(cl[-1]-ent)/R
        res-=0.0005*ent/R
        tr.append(dict(t=idx[j],exit=exit_t,R=res,big=big,broke=broke,s120=s120[i],coin=c)); i=k+1
    T=pd.DataFrame(tr).set_index('t'); return T[T.index>=start]
def build():
    TR=pd.concat([trades(c) for c in COINS]).sort_index()
    cap=px_idx('capitalizacion_total'); dom=px_idx('dominancia_btc')
    t2=(cap*(1-dom/100)).dropna(); rel=(t2/t2.rolling(20).mean()-1).shift(1)
    d=TR.index.normalize(); TR['t2rel']=rel.reindex(d).values
    s=btc_daily()
    pk=None;c=0;o=[]
    for v in s.values:
        pk=v if pk is None else max(pk,v)
        if v<=pk*0.85: c=0;pk=v
        else: c+=1
        o.append(c)
    ds15=pd.Series(o,index=s.index).shift(1); TR['ds15']=ds15.reindex(d).values
    # abiertas en otras monedas en el momento de entrar
    TR['open_other']=[((TR.index<t)&(TR.exit>t)&(TR.coin!=cc)).sum() for t,cc in zip(TR.index,TR.coin)]
    X=pd.read_pickle(D+'X_vol.pkl'); F=X[['pct','f30','pos90','v']].shift(1)
    for col in F.columns: TR['btc_'+col]=F[col].reindex(d).values
    for cc in COINS:
        dc=px(cc,'1d').close; r=np.log(dc).diff(); v=r.rolling(30).std()
        p=v.rolling(1095,min_periods=365).apply(lambda x:(x<=x[-1]).mean(),raw=True).shift(1)
        m=TR.coin==cc; TR.loc[m,'own_pct']=p.reindex(TR.index[m].normalize()).values
    # nota de puntos (versión B)
    ret=(TR.t2rel<0).astype(int)*2
    est=TR.apply(lambda r:(r.coin in EST) and ((r.ds15>=120) or (r.s120>EST[r.coin])),axis=1)
    TR['est']=est
    TR['pts']=ret-TR.big.astype(int)-est.astype(int)-TR.broke.astype(int)-(TR.open_other>=3).astype(int)
    TR['size']=TR.pts.map(lambda p:1.5 if p>=2 else 1.25 if p==1 else 1.0 if p==0 else 0.5 if p==-1 else 0.25)
    franja=(TR.t2rel>=0)&(TR.t2rel<0.06)&(TR.coin!='LINK')
    TR['size']*=np.where(franja,0.5,1.0)
    TR.to_pickle(D+'SYS.pkl'); return TR
def px_idx(name):
    d=pd.read_parquet(D+name+'.parquet'); return d.set_index(pd.to_datetime(d.fecha)).cierre
if __name__=='__main__':
    TR=build()
    print(len(TR),'operaciones; R/op',round(TR.R.mean(),2))
    print(TR.groupby('pts').R.agg(['count','mean']).round(2))
import pandas as pd, numpy as np
TR=pd.read_pickle('/home/claude/vol/data/SYS.pkl')
def ratio(R,ex):
    s=pd.Series(R.values,index=ex.values).sort_index(); cum=s.cumsum(); dd=(cum-cum.cummax()).min()
    yrs=max((s.index[-1]-s.index[0]).days/365.25,.5); return s.sum()/yrs/abs(dd) if dd<0 else np.nan, s.sum()/yrs, dd
P=[('todo','2018','2027'),('18-22','2018','2023'),('23-26','2023','2027'),('5 años','2021-10-25','2027'),('18-19','2018','2020'),('20-21','2020','2022'),('22-23','2022','2024'),('24-26','2024','2027')]
def row(size):
    out=[]
    for lab,a,b in P:
        m=(TR.index>=a)&(TR.index<b); r=ratio(TR.R[m]*size[m],TR.exit[m]); out.append(r[0])
    return out
base=row(TR['size'])
print('Sistema actual (aprox.):',' '.join(f'{l} {v:.2f}' for (l,_,_),v in zip(P,base)))
print('correlación con otras marcas (BTC vol en su 20 % bajo):')
lo=TR.btc_pct<=0.2
for c in ['est','big','broke']: print('  ',c, round(TR[c].astype(float).corr(lo.astype(float)),2))
print('   TOTAL2 en retroceso',round((TR.t2rel<0).astype(float).corr(lo.astype(float)),2),' pts',round(TR.pts.corr(lo.astype(float)),2))
def test(name,mask,how):
    mask=mask.fillna(False).values
    if how=='punto':
        p=TR.pts+mask.astype(int)
        size=p.map(lambda p:1.5 if p>=2 else 1.25 if p==1 else 1.0 if p==0 else 0.5 if p==-1 else 0.25)*np.where((TR.t2rel>=0)&(TR.t2rel<0.06)&(TR.coin!='LINK'),0.5,1.0)
    else: size=TR['size']*np.where(mask,how,1.0)
    r=row(size); better=sum(1 for x,y in zip(r[4:],base[4:]) if x>y)
    a=TR[mask]; b=TR[~mask]
    # dentro de cada nivel de puntos
    within=[]
    for p in [-2,-1,0,1,2]:
        aa=a[a.pts.clip(-2,2)==p]; bb=b[b.pts.clip(-2,2)==p]
        if len(aa)>=5: within.append(f'{p}:{aa.R.mean():+.2f}/{bb.R.mean():+.2f}({len(aa)})')
    print(f'{name:48s} n={mask.sum():3d} | '+' '.join(f'{l} {v:.2f}' for (l,_,_),v in zip(P,r))+f' | épocas mejor {better}/4 | por puntos {" ".join(within)}')
    return r
for thr in [0.1,0.2,0.3]:
    test(f'BTC vol ≤{thr} → +1 punto',TR.btc_pct<=thr,'punto')
    test(f'BTC vol ≤{thr} → ×1,5',TR.btc_pct<=thr,1.5)
    test(f'vol propia ≤{thr} → +1 punto',TR.own_pct<=thr,'punto')
    test(f'BTC vol ≤{thr} y miedo F&G≤45 → +1 punto',(TR.btc_pct<=thr)&(TR.btc_f30<=45),'punto')
    test(f'BTC vol ≤{thr} y codicia F&G≥55 → ×0,5',(TR.btc_pct<=thr)&(TR.btc_f30>=55),0.5)
test('BTC vol ≥0,7 → ×0,5',TR.btc_pct>=0.7,0.5)
import pandas as pd, numpy as np
exec(open('/home/claude/vol/code/encima.py').read().split("base=row")[0])
base=row(TR['size'])
X=pd.read_pickle('/home/claude/vol/data/X_vol.pkl'); F=X[['pct','f30']].shift(1)
import sys; sys.path.insert(0,'/home/claude/vol/code'); from base import px
def sizes(mask,how):
    if how=='punto':
        p=TR.pts+mask.astype(int)
        return p.map(lambda p:1.5 if p>=2 else 1.25 if p==1 else 1.0 if p==0 else 0.5 if p==-1 else 0.25)*np.where((TR.t2rel>=0)&(TR.t2rel<0.06)&(TR.coin!='LINK'),0.5,1.0)
    return TR['size']*np.where(mask,how,1.0)
def score(r): return r[0], r[2], sum(x>y for x,y in zip(r[4:],base[4:]))
rng=np.random.default_rng(251026)
d=TR.index.normalize()
cands={'BTC vol ≤0,1 ×1,5':(lambda sh:(F.pct.shift(sh)<=0.1),1.5),
       'BTC vol ≤0,2 y miedo +1 punto':(lambda sh:(F.pct.shift(sh)<=0.2)&(F.f30<=45),'punto'),
       'BTC vol ≤0,1 +1 punto':(lambda sh:(F.pct.shift(sh)<=0.1),'punto')}
for name,(fn,how) in cands.items():
    real=score(row(sizes(fn(0).reindex(d).fillna(False).values,how)))
    sims=[]
    for _ in range(300):
        sh=int(rng.integers(120,1500))*int(rng.choice([-1,1]))
        m=fn(sh).reindex(d).fillna(False).values
        sims.append(score(row(sizes(m,how))))
    S=np.array(sims)
    print(f'{name}: real todo {real[0]:.2f}, 23-26 {real[1]:.2f}, épocas {real[2]}/4 | placebo: todo pctl {(S[:,0]<real[0]).mean()*100:.0f}, 23-26 pctl {(S[:,1]<real[1]).mean()*100:.0f}, mediana todo {np.median(S[:,0]):.2f}, ≥ mismas épocas {(S[:,2]>=real[2]).mean()*100:.0f} %')
print('base',[round(x,2) for x in base])
import pandas as pd, numpy as np
exec(open('/home/claude/vol/code/encima.py').read().split("for thr in")[0])
print('VECINOS (+1 punto)')
for thr in [0.1,0.15,0.2,0.25,0.3]:
    for fg in [40,45,50]:
        test(f'BTC vol ≤{thr} y F&G30≤{fg}',(TR.btc_pct<=thr)&(TR.btc_f30<=fg),'punto')
for thr in [0.1,0.2,0.3]:
    test(f'BTC vol ≤{thr} y precio bajo en 90 d (pos≤0,3)',(TR.btc_pct<=thr)&(TR.btc_pos90<=0.3),'punto')
    test(f'BTC vol ≤{thr} y pos90≤0,5',(TR.btc_pct<=thr)&(TR.btc_pos90<=0.5),'punto')
import pandas as pd, numpy as np
exec(open('/home/claude/vol/code/encima.py').read().split("for thr in")[0])
test('Solo miedo F&G30≤45 (+1 punto)',TR.btc_f30<=45,'punto')
test('Miedo con vol NO baja (pct>0,2) (+1 punto)',(TR.btc_f30<=45)&(TR.btc_pct>0.2),'punto')
test('Miedo y vol baja ≤0,2 (+1 punto)',(TR.btc_f30<=45)&(TR.btc_pct<=0.2),'punto')
a=TR[(TR.btc_f30<=45)&(TR.btc_pct<=0.2)]; b=TR[(TR.btc_f30<=45)&(TR.btc_pct>0.2)]; c=TR[TR.btc_f30>45]
print('R/op: miedo+vol baja %.2f (%d) · miedo+vol normal %.2f (%d) · sin miedo %.2f (%d)'%(a.R.mean(),len(a),b.R.mean(),len(b),c.R.mean(),len(c)))
print('Por moneda (miedo+vol baja):',a.groupby('coin').R.agg(['count','mean']).round(2).to_dict('index'))
print('Por año:',a.groupby(a.index.year).R.agg(['count','mean']).round(2).to_dict('index'))
print('Mediana R %.2f, sin la mejor operación media %.2f'%(a.R.median(),a.R.drop(a.R.idxmax()).mean()))
import sys; sys.path.insert(0,'/home/claude/vol/code'); from base import *
s=btc_daily(); lp=np.log(s)
rp=pd.DataFrame(json.load(open(D+'sth_rp.json'))); rp.index=pd.to_datetime(rp.d); rp=rp.sthRealizedPrice.astype(float).reindex(s.index)
prox=s.rolling(120).mean()
real=(s-rp)/s; px_=(s-prox)/s
m=real.notna()
print('Real vs sustituto (desde nov-2022): correlación %.2f · mismo signo %.0f %% · error mediano del coste %.1f %%'%(real[m].corr(px_[m]),(np.sign(real[m])==np.sign(px_[m])).mean()*100,((prox[m]/rp[m]-1).abs().median()*100)))
N=px_.copy(); N[m]=real[m]     # serie: sustituto hasta 2022, real después
N90=N.rolling(90).mean()
sma200=s.rolling(200).mean(); bull=(sma200>sma200.shift(20))
H=[30,60,90,180]
fw={h:(s.shift(-h)/s-1) for h in H}
dn={h:(s[::-1].rolling(h,min_periods=1).min()[::-1].shift(-1)/s-1) for h in H}
def ep(mask,gap=30):
    out=[];last=None
    for t,v in mask.fillna(False).items():
        if v and (last is None or (t-last).days>gap): out.append(t)
        if v: last=t
    return out
def show(name,events,regime=None):
    E=pd.Index([e for e in events if e>=pd.Timestamp('2013-01-01')])
    base=s.index[(s.index>='2013-01-01')]
    if regime is not None: base=base[regime.reindex(base).fillna(False).values]
    print(f'\n== {name}: {len(E)} casos')
    for h in H:
        a=fw[h].reindex(E).dropna(); b=fw[h].reindex(base).dropna()
        print(f'   {h:3d} d: mediana {a.median()*100:+6.1f} % (sube {(a>0).mean()*100:3.0f} %) · referencia mismo régimen {b.median()*100:+5.1f} % (sube {(b>0).mean()*100:.0f} %) · peor caída mediana antes {dn[h].reindex(E).median()*100:+.1f} %')
    return E
cb=(N<0)&(N.shift(1)>=0); ca=(N>0)&(N.shift(1)<=0)
E1=show('Cruce a pérdidas (precio bajo el coste STH) en ciclo alcista',ep(cb&bull.shift(1)),bull)
E2=show('Cruce a pérdidas en cualquier régimen',ep(cb),None)
E3=show('Cruce a ganancias (vuelve sobre el coste STH) en ciclo alcista',ep(ca&bull.shift(1)),bull)
E4=show('Cruce a ganancias en cualquier régimen',ep(ca),None)
c90d=(N90<0)&(N90.shift(1)>=0); c90u=(N90>0)&(N90.shift(1)<=0)
E5=show('Media de 90 d cruza a pérdidas',ep(c90d,60),None)
E6=show('Media de 90 d cruza a ganancias',ep(c90u,60),None)
E7=show('Pérdidas STH de más del 10 % en ciclo alcista',ep((N<-0.10)&bull.shift(1),30),bull)
E8=show('Línea bajo su media de 90 d y en pérdidas, ciclo alcista',ep((N<N90)&(N<0)&bull.shift(1),30),bull)
pd.to_pickle(dict(N=N,N90=N90,bull=bull,E1=E1,E3=E3,E5=E5,E6=E6,E7=E7),D+'sth.pkl')
print('\nHoy: precio %.0f, coste STH real %.0f, sustituto %.0f, STH en %+.1f %%, media 90 d %+.1f %%, ciclo alcista %s'%(s.iloc[-1],rp.dropna().iloc[-1],prox.iloc[-1],N.iloc[-1]*100,N90.iloc[-1]*100,bull.iloc[-1]))
print('Casos E1:',[d.date().isoformat() for d in E1])
