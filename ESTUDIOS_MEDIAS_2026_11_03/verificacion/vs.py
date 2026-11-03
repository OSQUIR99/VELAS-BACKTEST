import sys; sys.path.insert(0,'/home/claude/caidas'); sys.path.insert(0,'/home/claude/velas-backtest'); sys.path.insert(0,'/home/claude/med')
import numpy as np, pandas as pd
from cortos import diario, atr_wilder, SECTORES
from p34 import sectores_lentos, SEC
spx=diario('sp500').cierre; m=spx.rolling(200).mean(); permS=((spx>m)&(m>m.shift(20)))
A={s:diario(SECTORES[s],ajustado=True).cierre for s in SEC}; P={s:diario(SECTORES[s]) for s in SEC}
cal=pd.DataFrame(A).index
# independiente: recorre día a día
mes=pd.Series(cal,index=cal).groupby(cal.to_period('M')).max()
fin=set(mes.values)
held={}; trades=[]
def atrw(s,f):
    W=P[s][P[s].index<=f].resample('W-FRI').agg({'apertura':'first','maximo':'max','minimo':'min','cierre':'last'}).dropna()
    # sólo semanas cerradas a fecha f: la última semana incluida termina en viernes <= f
    W=W[W.index<=f]
    return atr_wilder(W).iloc[-1]
pend_open=[]; pend_close=[]
cl=pd.DataFrame(A)
for t in cal[cal>='1999-06-01']:
    # ejecuciones en la apertura de t
    for s in pend_close:
        if s in held and t in P[s].index:
            h=held.pop(s); trades.append((s,h['te'],t,h['e'],P[s].apertura[t],h['R'],'regla'))
    pend_close=[]
    for s,R in pend_open:
        if t in P[s].index:
            e=P[s].apertura[t]; held[s]=dict(te=t,e=e,R=R,sl=e-R)
    pend_open=[]
    # stops durante el día
    for s in list(held):
        if t in P[s].index and P[s].minimo[t]<=held[s]['sl']:
            h=held.pop(s); trades.append((s,h['te'],t,h['e'],min(h['sl'],P[s].apertura[t]),h['R'],'stop'))
    if t in fin:
        i=cal.get_loc(t)
        if i<252: continue
        ret=(cl.iloc[i]/cl.iloc[i-252]-1).dropna(); rank=list(ret.sort_values(ascending=False).index)
        perm=bool(permS.get(t,False)) if t in permS.index else False
        keep=[s for s in held if perm and s in rank[:5]]
        for s in held:
            if s not in keep: pend_close.append(s)
        if perm:
            n=len(keep)
            for s in rank:
                if n>=3: break
                if s not in keep: pend_open.append((s,2.5*atrw(s,t))); n+=1
rows=[]
for s,te,ts,e,x,R,mo in trades: rows.append(dict(activo=s,te=te,ts=ts,r=(x-e-0.0002*e)/R,mot=mo))
T=pd.DataFrame(rows); O,D=sectores_lentos()
O['te']=O.t_entrada.dt.normalize(); O['ts']=O.t_salida.dt.normalize()
print('mío',len(T),round(T.r.sum(),2),'| suyo',len(O),round(O.r_bruto.sum(),2))
k=['activo','te']; mg=T.merge(O[['activo','te','ts','r_bruto','motivo_salida']],on=k,how='outer',indicator=True)
print(mg._merge.value_counts().to_dict())
d=mg[(mg._merge=='both')]; print('dif r máx',float((d.r-d.r_bruto).abs().max()), 'ts distinto',int((d.ts_x!=d.ts_y).sum()))
print(mg[mg._merge!='both'].to_string())
print(d[(d.ts_x!=d.ts_y)|((d.r-d.r_bruto).abs()>1e-6)].head(20).to_string())
# concurrencia
ev=[]
for _,r in O.iterrows(): ev+= [(r.t_entrada,1),(r.t_salida,-1)]
ev.sort(); c=0; mx=0
for _,x in ev: c+=x; mx=max(mx,c)
print('máx simultáneas suyas',mx, '| solapes mismo sector', sum(((g.t_entrada.values[1:]<g.t_salida.values[:-1]).sum()) for _,g in O.sort_values('t_entrada').groupby('activo')))
print('abiertas al final (mías)', held.keys())
for s,h in held.items():
    c=P[s].cierre.iloc[-1]; print(s,h['te'].date(),'latente R (x0,5)',round((c-h['e'])/h['R']*0.5,2), 'última fecha',P[s].index[-1].date())
