import sys; sys.path.insert(0,'/home/claude/velas-backtest')
import numpy as np, pandas as pd, os
from cargar import velas
C=lambda a: velas(a,'1d')['cierre']
btc=C('BTC'); oth=C('others_fuera_top10'); t3=C('total3_sin_btc_eth')
core=['ETH','BNB','XRP','ADA','LINK','SOL']
alts=pd.concat([C(a).pct_change() for a in core],axis=1).mean(axis=1)
# timing check: corr of OTHERS returns with ALTS same day vs lag
ro=oth.pct_change()
print('corr OTHERS vs ALTS lag -1/0/+1:',[round(ro.corr(alts.shift(k)),3) for k in (-1,0,1)])
# broad basket: core + secundarias available (needs >=30d history)
sec=sorted(os.listdir('/home/claude/velas-backtest/ALTCOINS_SECUNDARIAS/CONTADO'))
br=[]
for a in core+sec:
    try:
        c=C(a); r=c.pct_change(); r[c.index<c.index[0]+pd.Timedelta(days=30)]=np.nan; br.append(r.rename(a))
    except Exception as e: pass
broad=pd.concat(br,axis=1).clip(-0.9,5).mean(axis=1)  # clip guards bad ticks
print('broad basket members:',[s.name for s in br])
idx=btc.pct_change().dropna().index; idx=idx[idx>='2018-01-01']
def sim(rA,rB,w,fee=0.001):
    w=w.reindex(idx).ffill().fillna(0.5).shift(2).fillna(0.5)  # independent: signal t -> hold from t+2 return
    rA=rA.reindex(idx).fillna(0); rB=rB.reindex(idx).fillna(0)
    eq=1.0;cur=None;out=[]
    for d,a,b,t in zip(idx,rA.values,rB.values,w.values):
        if cur is None: cur=t
        if t!=cur or d.weekday()==0: eq*=1-abs(t-cur)*fee*2; cur=t
        g=cur*(1+a)+(1-cur)*(1+b); eq*=g; cur=cur*(1+a)/g; out.append(eq)
    return pd.Series(out,idx)
def stats(eq,a=None,b=None):
    e=eq[a:b]; e=e/e.iloc[0]; return f"{(e.iloc[-1]-1)*100:,.0f}% / {((e/e.cummax()-1).min())*100:.0f}%"
def rule(c,n=50): m=c.rolling(n).mean(); return (0.5+0.5*np.sign(c-m)).where(m.notna(),0.5)
rB=btc.pct_change()
alts_idx=(1+alts.fillna(0)).cumprod()
cases={
 'H1 OTHERS>MA50 -> ALTS (claim)':(alts,rule(oth)),
 'OTHERS>MA50 -> OTHERS index':(ro,rule(oth)),
 'OTHERS>MA50 -> TOTAL3 index':(t3.pct_change(),rule(oth)),
 'OTHERS>MA50 -> broad basket':(broad,rule(oth)),
 'ALTS own price>MA50 -> ALTS':(alts,rule(alts_idx)),
 'OTHERS>MA50 -> ALTS, signal lag+1 extra':(alts,rule(oth).shift(1)),
}
eb=C('ETH').pct_change(); r=C('ETH')/btc; m=r.rolling(20).mean()
cases['H2 ETHBTC slope MA20 -> ETH (claim)']=(eb,(0.5+0.5*np.sign(m-m.shift(5))).where(m.notna(),0.5))
rows=[]
for k,(rA,w) in cases.items():
  for fee in (0.001,0.003):
    eq=sim(rA,rB,w,fee); base=sim(rA,rB,pd.Series(0.5,idx),fee)
    rows.append([k,fee]+[f"{stats(eq,a,b)} | base {stats(base,a,b)}" for a,b in ((None,None),('2018','2021'),('2022','2026'),('2024','2026'))])
pd.set_option('display.width',400); pd.set_option('display.max_colwidth',60)
print(pd.DataFrame(rows,columns=['case','fee','full','2018-21','2022-26','2024-26']).to_string(index=False))
