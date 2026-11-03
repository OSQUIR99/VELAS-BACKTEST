import sys; sys.path.insert(0,'/home/claude/med')
from ev import *
def ddinfo(e,a,b):
    x=e[(e.index>=a)&(e.index<b)]; x=x-x.iloc[0]; pk=x.cummax(); dd=pk-x; t=dd.idxmax(); p=x[:t].idxmax()
    return p.date(),t.date(),round(dd.max(),2)
def top_eps(e,a,b,n=3):
    x=e[(e.index>=a)&(e.index<b)].values; ix=e[(e.index>=a)&(e.index<b)].index; pk=np.maximum.accumulate(x); dd=pk-x; res=[];i=0
    while i<len(x):
        if dd[i]>0:
            j=i
            while j<len(x) and dd[j]>0: j+=1
            k=i+np.argmax(dd[i:j]); res.append((round(dd[k],2),ix[i-1].date(),ix[k].date())); i=j
        else: i+=1
    return sorted(res,reverse=True)[:n]
out={}
for v in ['C_base','C_m16','C_m18','C_m22','C_m25','C_m40','C_m62']:
    C=cartera(cripto=v); M=mascaras(C); rr,e=C.sim(M['BASE'],exentas=M['EX'],tam_mult=k8(C)); q=C.met3(e)
    cr=(C.L=='cripto')&M['BASE']; ec=C.M.curva(rr.s, cr); enc=C.M.curva(rr.s, ~cr)
    a,b=C.desde,comun.CORTE
    p,t,dd=ddinfo(e,a,b)
    w=lambda s: float(s[s.index<=pd.Timestamp(t)].iloc[-1]-s[s.index<=pd.Timestamp(p)].iloc[-1])
    print(v,C.fmt(q),'| 24-26',round(m24(e),2))
    print('   peor caída 18-21',p,'->',t,dd,'| aporte cripto',round(w(ec),2),'resto',round(w(enc),2),'| top3',top_eps(e,a,b))
    print('   R total 18-21 cripto',round(float(ec[ec.index<b].iloc[-1]-ec[ec.index<a].iloc[-1]),1),'resto',round(float(enc[enc.index<b].iloc[-1]-enc[enc.index<a].iloc[-1]),1),'| ops cripto',int(((C.L=='cripto')&M['BASE']&(rr.s>0)).sum()))
    out[v]=e
import pickle; pickle.dump(out,open('eq4.pkl','wb'))
