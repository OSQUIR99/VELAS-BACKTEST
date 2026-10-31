import sys; sys.path.insert(0,'/home/claude/vol/code'); from base import *
from montaje import atr
COINS=['BTC','ETH','SOL','ADA','ZEC','LINK']
F=fng(); F30=F.rolling(30,min_periods=20).mean()
def prep(c):
    d=px(c,'1d'); d=d[d.close>0].copy()
    if c=='BTC':
        ok=pd.read_csv(D+'okx_btc_1d.csv',index_col=0,parse_dates=True)[['open','high','low','close']]
        d=pd.concat([d,ok[ok.index>d.index[-1]]])
    r=np.log(d.close).diff(); d['v30']=r.rolling(30).std()
    d['pct']=d.v30.rolling(1095,min_periods=365).apply(lambda x:(x<=x[-1]).mean(),raw=True)
    d['atr']=atr(d); d['hi20']=d.close.rolling(20).max().shift(1); d['lo20']=d.close.rolling(20).min().shift(1)
    d['sma200']=d.close.rolling(200).mean(); d['f30']=F30.reindex(d.index)
    d['comp']=(d.pct<=0.20).rolling(10).max().astype(bool)   # compresión en los últimos 10 días
    return d
def run(d,sig,side=1,cost=0.0005):
    # sig: serie booleana al cierre del día t → entrada en la apertura de t+1. Salida estilo proyecto.
    o,h,l,c,a=[d[x].values for x in ['open','high','low','close','atr']]; idx=d.index; n=len(d); S=sig.values
    out=[];i=0
    while i<n-1:
        if not S[i] or np.isnan(a[i]): i+=1; continue
        j=i+1; ent=o[j]; R=2*a[i]; stop=ent-side*R; part=False; ext=h[j] if side==1 else l[j]; k=j; res=None
        while k<n:
            hit=(l[k]<=stop) if side==1 else (h[k]>=stop)
            if hit:
                px_=min(stop,o[k]) if side==1 else max(stop,o[k]); g=side*(px_-ent)/R
                res=(1/3 if part else 0)+(2/3 if part else 1)*g; break
            if not part and side*((h[k] if side==1 else l[k])-ent)>=R: part=True; stop=ent
            ext=max(ext,h[k]) if side==1 else min(ext,l[k])
            if part: stop=max(stop,ext-2.5*a[k]) if side==1 else min(stop,ext+2.5*a[k])
            k+=1
        if res is None: res=(1/3 if part else 0)+(2/3 if part else 1)*side*(c[-1]-ent)/R
        res-=cost*ent/R*2
        out.append((idx[j],idx[min(k,n-1)],res)); i=k+1
    return pd.DataFrame(out,columns=['t','exit','R']).set_index('t')
def ratio(T):
    if len(T)<3: return np.nan,np.nan,np.nan
    s=pd.Series(T.R.values,index=T.exit.values).sort_index(); cum=s.cumsum(); dd=(cum-cum.cummax()).min()
    yrs=max((s.index[-1]-s.index[0]).days/365.25,.5); ry=s.sum()/yrs
    return ry,dd,(ry/abs(dd) if dd<0 else np.inf)
def report(name,fn,side=1):
    allT=[]
    for c in COINS:
        d=prep(c) if c not in CACHE else CACHE[c]; CACHE[c]=d
        T=run(d,fn(d).fillna(False),side); T['coin']=c; allT.append(T)
    T=pd.concat(allT).sort_index(); T=T[T.index>='2018-01-01']
    parts=[]
    for lab,a,b in [('18-21','2018','2022'),('22-26','2022','2027')]:
        s=T[(T.index>=a)&(T.index<b)]; r=ratio(s); parts.append(f'{lab}: n{len(s)} {s.R.mean():+.2f}R ac{(s.R>0).mean()*100:.0f}% R/a÷caída {r[2]:.2f}')
    ep=' '.join(f'{T[(T.index>=a)&(T.index<b)].R.mean():+.2f}' for a,b in [('2018','2020'),('2020','2022'),('2022','2024'),('2024','2027')])
    co=' '.join(f'{c}{T[T.coin==c].R.mean():+.2f}({(T.coin==c).sum()})' for c in COINS)
    print(f'{name:58s} | '+' | '.join(parts)+f' | épocas {ep} | {co}')
    return T
CACHE={}
if __name__=='__main__':
    brk=lambda d:d.close>d.hi20; brkd=lambda d:d.close<d.lo20
    up=lambda d:d.close>d.sma200
    R={}
    print('— RUPTURA AL ALZA (cierre sobre el máximo de 20 días) —')
    R['ctrl']=report('Control: todas las rupturas al alza',brk)
    R['ctrl_up']=report('Control: rupturas al alza sobre la media de 200',lambda d:brk(d)&up(d))
    R['v1']=report('V1: ruptura al alza tras compresión (vol ≤20 % en 10 d)',lambda d:brk(d)&d.comp)
    R['v1b']=report('V1b: V1 + sobre la media de 200',lambda d:brk(d)&d.comp&up(d))
    R['v1n']=report('Contraste: ruptura al alza SIN compresión',lambda d:brk(d)&~d.comp)
    print('— RUPTURA A LA BAJA (corto) —')
    report('Control: todas las rupturas a la baja',brkd,-1)
    report('V2: ruptura a la baja tras compresión',lambda d:brkd(d)&d.comp,-1)
    report('V2b: V2 bajo la media de 200',lambda d:brkd(d)&d.comp&~up(d),-1)
    print('— TRAMPA Y GIRO (la idea del autor) —')
    def trap_up(d):  # rompe abajo tras compresión y vuelve dentro en ≤3 días → largo
        b=(d.close<d.lo20)&d.comp; back=d.close>d.lo20.shift(0)
        m=pd.Series(False,index=d.index)
        for k in range(1,4): m|=b.shift(k).fillna(False)&back
        return m&~m.shift(1).fillna(False)
    def trap_dn(d):
        b=(d.close>d.hi20)&d.comp; back=d.close<d.hi20
        m=pd.Series(False,index=d.index)
        for k in range(1,4): m|=b.shift(k).fillna(False)&back
        return m&~m.shift(1).fillna(False)
    report('V3: falsa rotura bajista tras compresión → largo',trap_up)
    report('V3b: falsa rotura alcista tras compresión → corto',trap_dn,-1)
    print('— CONTRA EL SENTIMIENTO —')
    first=lambda m:m&~m.shift(1).fillna(False)
    report('V4: compresión (≤10 %) + miedo F&G30≤45 → largo',lambda d:first((d.pct<=0.10)&(d.f30<=45)))
    report('V4b: compresión (≤10 %) + codicia ≥55 → corto',lambda d:first((d.pct<=0.10)&(d.f30>=55)),-1)
    report('V5: compresión (≤10 %) + sobre la media 200 → largo',lambda d:first((d.pct<=0.10)&up(d)))
    pd.to_pickle(R,'/home/claude/vol2/R.pkl')
