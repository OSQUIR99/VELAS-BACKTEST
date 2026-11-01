# Código de los estudios del 26-oct-2026: punto dulce tras caídas y caídas de mercado + fundamental
# Datos: velas de ~258 acciones (yfinance, carpeta rezagadas/) y companyfacts de la SEC.

######## p.py
import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
D='/tmp/claude-0/-home-claude-velas-backtest/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/rezagadas'
C=pd.read_parquet(f'{D}/Close.parquet'); H=pd.read_parquet(f'{D}/High.parquet'); L=pd.read_parquet(f'{D}/Low.parquet')
U=json.load(open(f'{D}/universo.json')); sec={s:e for e,l in U.items() for s in l}
etfs=list(U); mkt=C[etfs].pct_change().mean(axis=1).fillna(0).add(1).cumprod()
HZ=120; DROP=0.25
rows=[]
for s,e in sec.items():
    if s not in C or e not in C: continue
    c=C[s].dropna(); 
    if len(c)<400: continue
    h=H[s].reindex(c.index); l=L[s].reindex(c.index); se=C[e].reindex(c.index).ffill(); m=mkt.reindex(c.index).ffill()
    hi60=c.rolling(60).max(); dd=c/hi60-1
    ema=c.ewm(span=20,adjust=False).mean(); sma200=c.rolling(200).mean()
    lo10=l.rolling(10).min(); hi10=h.rolling(10).max().shift(1)
    vol10=c.pct_change().rolling(10).std(); vol20=c.pct_change().rolling(40).std()
    rs20=c.pct_change(20)-se.pct_change(20)
    cv=c.values; n=len(c); i=200; idx=c.index
    while i<n-HZ-1:
        if dd.iloc[i]<=-DROP:
            ev=i
            # tipo de caída (60 sesiones)
            r_s=cv[ev]/cv[ev-60]-1; r_e=se.iloc[ev]/se.iloc[ev-60]-1; r_m=m.iloc[ev]/m.iloc[ev-60]-1
            fin=ev+HZ
            def entra(cond):
                for j in range(ev+1,fin):
                    if cond(j): return j
                return None
            s2=entra(lambda j: l.iloc[j-5:j+1].min()>lo10.iloc[j-6] and vol10.iloc[j]<vol20.iloc[j])
            s3=entra(lambda j: cv[j]>ema.iloc[j] and ema.iloc[j]>ema.iloc[j-3] and cv[j]>hi10.iloc[j] and rs20.iloc[j]>0)
            s200=entra(lambda j: cv[j]>sma200.iloc[j])
            def res(j):
                if j is None: return (np.nan,np.nan)
                ret=cv[fin]/cv[j]-1; mae=l.iloc[j+1:fin+1].min()/cv[j]-1; return ret,mae
            r={'tk':s,'fecha':idx[ev],'r_s':r_s,'r_e':r_e,'r_m':r_m,'ultra':cv[ev]>sma200.iloc[ev-60] if not np.isnan(sma200.iloc[ev-60]) else False}
            for k,j in [('M0',ev),('S2',s2),('S3',s3),('SMA200',s200)]:
                a,b=res(j); r[k+'_ret']=a; r[k+'_mae']=b; r[k+'_d']=None if j is None else j-ev
            # control: el sector en esa ventana
            r['sec_ret']=se.iloc[fin]/se.iloc[ev]-1
            rows.append(r); i=fin   # una por caída, espera a que acabe el horizonte
        else: i+=1
R=pd.DataFrame(rows); R.to_parquet('/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto/ev.parquet')
print(len(R))

######## a.py
import pandas as pd, numpy as np
R=pd.read_parquet('/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto/ev.parquet')
R['tipo']=np.select([R.r_m<=-0.10,(R.r_e<=-0.15)],['A sistémica','B sectorial'],np.where(R.r_s-R.r_e<-0.20,'C propia','mixta'))
for k in ['M0','S2','S3','SMA200']: R[k+'_ex']=(1+R[k+'_ret'])/(1+R.sec_ret*0)-1
R['ESC_ret']=0.25*R.M0_ret+0.35*R.S2_ret.fillna(0)+0.40*R.S3_ret.fillna(0)
R['ESC_mae']=0.25*R.M0_mae+0.35*R.S2_mae.fillna(0)+0.40*R.S3_mae.fillna(0)
R['ESC_inv']=0.25+0.35*R.S2_ret.notna()+0.40*R.S3_ret.notna()
def t(x): x=x.dropna(); return x.mean()/(x.std()/np.sqrt(len(x)))
def tabla(X,tit):
    print(f'\n== {tit} ({len(X)} caídas ≥25% desde máx. de 60 sesiones; resultado hasta 120 sesiones tras la caída)')
    for k in ['M0','S2','S3','SMA200','ESC']:
        r=X[k+'_ret']; m=X[k+'_mae']; ent=r.notna().mean() if k!='ESC' else X.ESC_inv.mean()
        u=(r+m)
        print(f' {k:6s} entra {100*ent:4.0f}% · ret medio {100*r.mean():+5.1f}% · mediana {100*r.median():+5.1f}% · peor bajada media {100*m.mean():+5.1f}% · ret/|bajada| {r.mean()/abs(m.mean()):.2f} · % ganadoras {100*(r>0).mean():.0f}' + (f' · días {X[k+"_d"].median():.0f}' if k+'_d' in X else ''))
    d=(X.S3_ret-X.M0_ret).dropna(); print(f'   S3 − M0 (mismas caídas con S3): {100*d.mean():+.1f} pts, t {t(d):.1f}')
    d=(X.S2_ret-X.M0_ret).dropna(); print(f'   S2 − M0: {100*d.mean():+.1f} pts, t {t(d):.1f}')
tabla(R,'todas')
for a,b in [(1999,2008),(2009,2017),(2018,2026)]: tabla(R[(R.fecha.dt.year>=a)&(R.fecha.dt.year<=b)],f'{a}-{b}')
for ty in ['A sistémica','B sectorial','C propia','mixta']: tabla(R[R.tipo==ty],ty)
tabla(R[R.ultra],'venía de tendencia alcista (sobre su media de 200 hace 60 sesiones)')
print('\nsector mismo periodo (desde la caída):',f"{100*R.sec_ret.mean():+.1f}%")

######## bajar_sec.py
import json, time, os, urllib.request, pandas as pd
S='/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto'
t=json.load(open(f'{S}/tickers.json')); m={v['ticker']:v['cik_str'] for v in t.values()}
C=pd.read_parquet('/tmp/claude-0/-home-claude-velas-backtest/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/rezagadas/Close.parquet')
ok=0
for tk in C.columns:
    f=f'{S}/sec/{tk}.json'
    if os.path.exists(f): ok+=1; continue
    cik=m.get(tk.replace('.','-')) or m.get(tk)
    if not cik: continue
    req=urllib.request.Request(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json',headers={'User-Agent':'Backtest Research research@example.org'})
    try:
        open(f,'wb').write(urllib.request.urlopen(req,timeout=30).read()); ok+=1
    except Exception as e: print(tk,e)
    time.sleep(0.15)
print('ok',ok,'de',len(C.columns))

######## fund.py
import json, glob, os, pandas as pd, numpy as np
S='/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto'
REV=['Revenues','RevenueFromContractWithCustomerExcludingAssessedTax','SalesRevenueNet','RevenueFromContractWithCustomerIncludingAssessedTax','RevenuesNetOfInterestExpense']
GP=['GrossProfit']; COGS=['CostOfRevenue','CostOfGoodsAndServicesSold','CostOfGoodsSold']
OI=['OperatingIncomeLoss']
DEBT=['LongTermDebt','LongTermDebtNoncurrent','LongTermDebtCurrent','DebtCurrent','ShortTermBorrowings','CommercialPaper']
CASH=['CashAndCashEquivalentsAtCarryingValue','CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']
def facts(j,names,anual):
    out=[]
    g=j.get('facts',{}).get('us-gaap',{})
    for nm in names:
        if nm not in g: continue
        for u,lst in g[nm]['units'].items():
            if u!='USD': continue
            for f in lst:
                if anual:
                    if 'start' not in f: continue
                    d=(pd.Timestamp(f['end'])-pd.Timestamp(f['start'])).days
                    if not 350<=d<=380: continue
                out.append((nm,pd.Timestamp(f['end']),pd.Timestamp(f['filed']),f['val']))
    return pd.DataFrame(out,columns=['c','end','filed','val'])
def serie(df):  # primer valor publicado de cada fecha de fin; preferir primer concepto disponible por periodo
    if df.empty: return df
    df=df.sort_values('filed').drop_duplicates(['c','end'],keep='first')
    return df
rows=[]
for f in glob.glob(f'{S}/sec/*.json'):
    tk=os.path.basename(f)[:-5]; j=json.load(open(f))
    rv=serie(facts(j,REV,True)); gp=serie(facts(j,GP,True)); cg=serie(facts(j,COGS,True)); oi=serie(facts(j,OI,True))
    db=serie(facts(j,DEBT,False)); ca=serie(facts(j,CASH,False))
    rows.append((tk,rv,gp,cg,oi,db,ca))
import pickle; pickle.dump(rows,open(f'{S}/fund.pkl','wb')); print(len(rows))

######## e1acc.py
import pickle, json, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
S='/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto'
D='/tmp/claude-0/-home-claude-velas-backtest/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/rezagadas'
C=pd.read_parquet(f'{D}/Close.parquet'); H=pd.read_parquet(f'{D}/High.parquet'); L=pd.read_parquet(f'{D}/Low.parquet'); O=pd.read_parquet(f'{D}/Open.parquet')
U=json.load(open(f'{D}/universo.json')); etfs=list(U); sec={s:e for e,l in U.items() for s in l}
FUND={r[0]:r[1:] for r in pickle.load(open(f'{S}/fund.pkl','rb'))}
mk=C[etfs].pct_change().mean(axis=1).fillna(0).add(1).cumprod(); mdd=mk/mk.rolling(60).max()-1
def rsi(c,n=2):
    d=c.diff(); u=d.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); v=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean(); return 100-100/(1+u/v)
# fracción de acciones con E1 cada día
E1={}; IND={}
for s in sec:
    if s not in C: continue
    c=C[s].dropna()
    if len(c)<300: continue
    h,l,o=H[s].reindex(c.index),L[s].reindex(c.index),O[s].reindex(c.index)
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1); atr=tr.ewm(alpha=1/14,adjust=False).mean()
    s200=c.rolling(200).mean(); perm=(c>s200)&(s200>s200.shift(20)); r2=rsi(c)
    E1[s]=perm&(r2<10); IND[s]=(c,h,l,o,atr,c.rolling(5).mean(),r2)
frac=pd.DataFrame(E1).reindex(C.index).fillna(False).mean(axis=1)
def last_two(df):
    return df
def calidad(tk,fecha):
    if tk not in FUND: return np.nan,np.nan
    rv,gp,cg,oi,db,ca=FUND[tk]
    def known(df): return df[df.filed<=fecha] if len(df) else df
    r=known(rv)
    if len(r)==0: return np.nan,np.nan
    r=r.groupby('end').val.first().sort_index()
    if len(r)<2: return np.nan,np.nan
    e1,e0=r.index[-1],r.index[-1]-pd.Timedelta(days=365)
    prev=r[(r.index>e0-pd.Timedelta(days=40))&(r.index<e0+pd.Timedelta(days=40))]
    if len(prev)==0 or (fecha-e1).days>500: return np.nan,np.nan
    crece=r.iloc[-1]>prev.iloc[-1]
    g=known(gp)
    if len(g): bruto=g.sort_values('end').val.iloc[-1]
    else:
        cc=known(cg); bruto=r.iloc[-1]-cc.sort_values('end').val.iloc[-1] if len(cc) else (known(oi).sort_values('end').val.iloc[-1] if len(known(oi)) else np.nan)
    d=known(db)
    if len(d):
        ult=d.end.max(); dd=d[d.end==ult].groupby('c').val.first()
        debt=max(dd.get('LongTermDebt',0), dd.get('LongTermDebtNoncurrent',0)+dd.get('LongTermDebtCurrent',0))+dd.get('DebtCurrent',0)*0+dd.get('ShortTermBorrowings',0)+dd.get('CommercialPaper',0)
    else: debt=0
    k=known(ca); cash=k.sort_values('end').val.iloc[-1] if len(k) else 0
    deuda_ok=(debt-cash)<3*bruto if bruto and bruto>0 else False
    return float(crece), float(deuda_ok)
ops=[]
for s,(c,h,l,o,atr,s5,r2) in IND.items():
    ent=E1[s].values; cv,hv,lv,ov,av,s5v=c.values,h.values,l.values,o.values,atr.values,s5.values; idx=c.index; i=0; n=len(c)
    while i<n-1:
        if not ent[i] or idx[i].year<2010: i+=1; continue
        e=cv[i]; R=2.5*av[i]; st=e-R; px=None
        for j in range(i+1,n):
            if lv[j]<=st: px=min(ov[j],st) if not np.isnan(ov[j]) else st; break
            if cv[j]>s5v[j] or j-i>=10: px=cv[j]; break
        if px is None: break
        q=calidad(s,idx[i])
        ops.append({'tk':s,'entrada':idx[i],'salida':idx[j],'dias':j-i,'R':(px-e)/R-0.0005*e/R,'mdd':mdd.get(idx[i],np.nan),'frac':frac.get(idx[i],np.nan),'ventas':q[0],'deuda':q[1],'rsi':r2.iloc[i]})
        i=j+1
P=pd.DataFrame(ops); P.to_parquet(f'{S}/ops_acc.parquet'); print(len(P), P.ventas.notna().mean())

######## an2.py
import pandas as pd, numpy as np
P=pd.read_parquet('/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto/ops_acc.parquet')
def tcl(x,d):  # t agrupado por día de entrada
    g=x.groupby(d).mean(); return g.mean()/(g.std()/np.sqrt(len(g)))
def ep(q): return ' '.join(f"{q[(q.entrada.dt.year>=a)&(q.entrada.dt.year<=b)].R.mean():+.3f}" for a,b in [(2010,2014),(2015,2019),(2020,2026)])
print(f'TODAS {len(P)} R/op {P.R.mean():+.3f} acierto {100*(P.R>0).mean():.0f}% t(día) {tcl(P.R,P.entrada):.1f} | épocas {ep(P)}')
P['sist']=P.mdd<=-0.07; P['masivo']=P.frac>=0.15; P['cal']=(P.ventas==1)&(P.deuda==1); P['sindato']=P.ventas.isna()
for nom,m in [('mercado −7 % o más desde su máx. 60',P.sist),('≥15 % de las acciones con E1 ese día',P.masivo),('calidad (ventas crecen y deuda<3× bruto)',P.cal),('ventas crecen',P.ventas==1),('deuda ok',P.deuda==1),('sin dato fundamental',P.sindato),('RSI2<5',P.rsi<5)]:
    a,b=P[m],P[~m]
    print(f'{nom:45s} sí n {len(a):5d} {a.R.mean():+.3f} [{ep(a)}] | no {b.R.mean():+.3f} [{ep(b)}] | t sí {tcl(a.R,a.entrada):.1f}')
print()
for s_ in [False,True]:
    for c_ in [False,True]:
        q=P[(P.sist==s_)&(P.cal==c_)]; print(f'sistémica={s_!s:5} calidad={c_!s:5}: n {len(q):5d} R/op {q.R.mean():+.3f} [{ep(q)}]')

######## an3.py
import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto')
import pandas as pd, numpy as np
from calidad import calidad
R=pd.read_parquet('/tmp/claude-0/-home-claude/01b16d49-2df4-534b-8cb2-14c2e0917fd8/scratchpad/punto/ev.parquet'); R=R[R.fecha.dt.year>=2010].copy()
q=[calidad(t,f) for t,f in zip(R.tk,R.fecha)]; R['ventas']=[a for a,b in q]; R['deuda']=[b for a,b in q]
R['cal']=(R.ventas==1)&(R.deuda==1); R['sist']=R.r_m<=-0.10
def t(x): x=x.dropna(); return x.mean()/(x.std()/np.sqrt(len(x)))
for s_ in [False,True]:
  for c_ in [False,True]:
    z=R[(R.sist==s_)&(R.cal==c_)]
    print(f'sistémica={s_!s:5} calidad={c_!s:5} n {len(z):4d} comprar en la caída {100*z.M0_ret.mean():+5.1f}% (mediana {100*z.M0_ret.median():+5.1f}) peor bajada {100*z.M0_mae.mean():+5.1f}% | esperar S3 {100*z.S3_ret.mean():+5.1f}% | ret/bajada M0 {z.M0_ret.mean()/abs(z.M0_mae.mean()):.2f}')
a=R[R.cal].M0_ret; b=R[~R.cal].M0_ret; print('calidad sí−no', f'{100*(a.mean()-b.mean()):+.1f} pts', 'n',len(a),len(b))
for y1,y2 in [(2010,2016),(2017,2026)]:
    z=R[(R.fecha.dt.year>=y1)&(R.fecha.dt.year<=y2)]; print(y1,y2,'cal',f"{100*z[z.cal].M0_ret.mean():+.1f}",'no',f"{100*z[~z.cal].M0_ret.mean():+.1f}",'sist',f"{100*z[z.sist].M0_ret.mean():+.1f}",'no sist',f"{100*z[~z.sist].M0_ret.mean():+.1f}")
print()
z=R[R.sist].copy(); z['mes']=z.fecha.dt.to_period('Q')
g=z.groupby('mes').agg(n=('tk','size'),acc=('M0_ret','mean'),fondo=('sec_ret','mean'))
print(g.round(3).to_string())
print('episodios',len(g),'acción − su fondo (media por episodio):',f"{100*(g.acc-g.fondo).mean():+.1f} pts", 'positivos',int(((g.acc-g.fondo)>0).sum()))
w=R[~R.sist]; print('no sistémicas: acción − fondo', f"{100*(w.M0_ret-w.sec_ret).mean():+.1f} pts")
