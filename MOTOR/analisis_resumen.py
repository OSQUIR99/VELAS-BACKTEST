import sys, json, time, itertools; sys.path.insert(0,'/home/claude/drive-pendiente/motor-de-cartera/codigo')
import recomendacion as RC, analisis as A, numpy as np, pandas as pd
from motor import metricas, HOY
O,D,M=RC.preparar('/home/claude/motor/listas')
desde=A.inicio_ventana(O); CORTE=pd.Timestamp('2022-01-01')
EC=O.en_cartera.values; T=(O.t_entrada>=desde).values; W=EC&T
L=O.lista.values; S=O.senal.astype(str).values; act=O.activo.astype(str).values
IDX={'SPX','DJI','NDX','RUT'}
uni={'REBOTE 4H cripto':L=='cripto','Petróleo L/S/noticia':L=='petroleo','Petróleo X1/X3 (bolsa)':L=='x_petroleo',
 'E1 índices':(L=='bolsa_e1')&np.isin(act,list(IDX)),'E1 sectores':(L=='bolsa_e1')&~np.isin(act,list(IDX)),
 'CORRECCIÓN NASDAQ (c10)':L=='c10','Oro':(L=='metales')&(act=='oro'),'Plata':(L=='metales')&(act=='plata'),
 'Materias primas T1/T2':L=='mensuales','SHY tres tercios':L=='shy'}
REF={'SOPORTE ACCIÓN / v2 acciones (solo contexto)':L=='acciones_v2'}
FL=dict(freno=(4,0.5),freno_modo='latente',prioridad='descorr')
def stats(rr,m,d0=desde,h=None):
    mt=metricas(M,rr.s,d0,h,mascara=m,eq=M.curva(rr.s,m))
    return mt
def peor(eq,d0,h=None):
    e=eq[(eq.index>=d0)&(eq.index<=(h or HOY))]; y=e.resample('YE').last().diff(); y.iloc[0]=e.resample('YE').last().iloc[0]-e.iloc[0]
    return float(y.min()), int(y.idxmin().year)
filas=[]
def fila(nombre,fam,m,sub=''):
    if (m&W).sum()==0: print('VACIO',nombre); return None
    rr=M.simular(A.SIN_TOPES,mascara=m&EC)
    eq=M.curva(rr.s,m&EC)
    mv=stats(rr,m&EC); pv=peor(eq,desde)
    d0=pd.Timestamp(O.t_entrada[m&EC].min()).normalize()
    mh=stats(rr,m&EC,d0); 
    filas.append(dict(familia=fam,senal=nombre,n_vent=mv['n'],R_ano=round(mv['R_ano'],2),caida_R=round(mv['caida'],2),
      ratio=round(mv['Rano_caida'],2) if mv['caida']>0 else None,acierto=round(100*mv['acierto'],1),R_op=round(mv['R_op'],3),
      peor_ano_R=round(pv[0],2),peor_ano=pv[1],desde_hist=str(d0.date()),n_hist=mh['n'],R_ano_hist=round(mh['R_ano'],2),
      caida_hist=round(mh['caida'],2),ratio_hist=round(mh['Rano_caida'],2) if mh['caida']>0 else None,nivel=sub))
    return eq
EQ={}
for k,m in {**uni,**REF}.items():
    EQ[k]=fila(k,k,m,'FAMILIA')
# desglose por activo/señal
def sub(fam,mask,col):
    for v in sorted(set(col[mask&W])):
        fila(f'{fam} · {v}',fam,mask&(col==v),'detalle')
sub('REBOTE 4H cripto',uni['REBOTE 4H cripto'],act)
sub('Petróleo L/S/noticia',uni['Petróleo L/S/noticia'],S)
sub('Petróleo X1/X3 (bolsa)',uni['Petróleo X1/X3 (bolsa)'],S)
sub('E1 índices',uni['E1 índices'],act); 
sub('Oro',uni['Oro'],S); sub('Plata',uni['Plata'],S)
sub('Materias primas T1/T2',uni['Materias primas T1/T2'],S); sub('Materias primas T1/T2',uni['Materias primas T1/T2'],act)
# SOL pirámide
if 'n_piramide' in O:
    np_=O.n_piramide.fillna(0).values>0
    fila('REBOTE 4H cripto · SOL con pirámide','REBOTE 4H cripto',uni['REBOTE 4H cripto']&(act=='SOL')&np_,'detalle')
F=pd.DataFrame(filas); F.to_csv('tabla_senales.csv',index=False)
print(F.to_string())
# correlación mensual
mon=pd.DataFrame({k:e[(e.index>=desde)&(e.index<=HOY)].resample('ME').last().diff() for k,e in EQ.items()}).dropna()
C=mon.corr().round(2); C.to_csv('correlacion_mensual.csv'); print(C.to_string())
# cartera actual
Wc=W&~REF['SOPORTE ACCIÓN / v2 acciones (solo contexto)']
def run(mask,cfg=FL,d0=desde,h=None,mult=1.0):
    c=dict(cfg); c['mult']=mult; rr=M.simular(c,mascara=mask); return rr,metricas(M,rr.s,d0,h,mascara=mask,eq=rr.eq)
t=time.time(); rr0,m0=run(Wc); print('tiempo sim',time.time()-t); print('ACTUAL',m0)
contrib=[]
for k,m in {**uni}.items():
    sel=(rr0.s>0)&m&Wc; eqk=M.curva(rr0.s,m&Wc)
    e=eqk[(eqk.index>=desde)&(eqk.index<=HOY)]
    cand=(m&Wc).sum(); motiv=pd.Series(rr0.motivo[m&Wc]).value_counts().to_dict()
    contrib.append(dict(familia=k,cand=int(cand),tomadas=int(sel.sum()),R_total=round(float(e.iloc[-1]-e.iloc[0]),1),
      R_ano=round(float(e.iloc[-1]-e.iloc[0])/((HOY-desde).days/365.25),2),tam_medio=round(float(rr0.s[sel].mean()),2) if sel.sum() else 0,motivos=motiv))
Cb=pd.DataFrame(contrib); print(Cb.to_string()); Cb.to_csv('contribucion.csv',index=False)
pv0=peor(rr0.eq,desde)
# también todas sin topes y vigente simple
rrT,mT=run(Wc,A.SIN_TOPES); rrV,mV=run(Wc,{})
# selección
keys=list(uni)
def mask_of(ks): 
    m=np.zeros(len(O),bool)
    for k in ks: m|=uni[k]
    return m&Wc
cache={}
def score(ks,d0=desde,h=None):
    key=(tuple(sorted(ks)),str(d0),str(h))
    if key not in cache:
        _,mm=run(mask_of(ks),d0=d0,h=h); cache[key]=mm
    return cache[key]
loo=[]
for k in keys:
    mm=score([x for x in keys if x!=k]); loo.append(dict(quitar=k,R_ano=round(mm['R_ano'],2),caida=round(mm['caida'],2),ratio=round(mm['Rano_caida'],2)))
LOO=pd.DataFrame(loo); print(LOO.to_string()); LOO.to_csv('quitar_una.csv',index=False)
def greedy_fwd(d0,h):
    sel=[];best=-1;hist=[]
    while True:
        cands=[(score(sel+[k],d0,h)['Rano_caida'],k) for k in keys if k not in sel]
        cands=[c for c in cands if c[0]==c[0]]
        if not cands: break
        v,k=max(cands)
        if v<=best: break
        sel.append(k);best=v;hist.append((k,round(v,2)))
    return sel,hist
def greedy_bwd(d0,h):
    sel=list(keys);best=score(sel,d0,h)['Rano_caida'];hist=[]
    while len(sel)>1:
        v,k=max((score([x for x in sel if x!=k],d0,h)['Rano_caida'],k) for k in sel)
        if v<=best: break
        sel.remove(k);best=v;hist.append(('-'+k,round(v,2)))
    return sel,hist
res={}
for nom,(d0,h) in {'completa':(desde,None),'IS_2018_21':(desde,CORTE),'IS_2022_26':(CORTE,None)}.items():
    f=greedy_fwd(d0,h); b=greedy_bwd(d0,h); res[nom]=dict(fwd=f,bwd=b); print(nom,f,b)
def ev(ks):
    a=score(ks); i=score(ks,desde,CORTE); o=score(ks,CORTE,None)
    return dict(R_ano=round(a['R_ano'],2),caida=round(a['caida'],2),ratio=round(a['Rano_caida'],2),n=a['n'],acierto=round(a['acierto'],3),R_op=round(a['R_op'],3),
      ratio_18_21=round(i['Rano_caida'],2),R_ano_18_21=round(i['R_ano'],2),caida_18_21=round(i['caida'],2),ratio_22_26=round(o['Rano_caida'],2),R_ano_22_26=round(o['R_ano'],2),caida_22_26=round(o['caida'],2))
combos={'Actual (todas)':keys}
for nom,r in res.items():
    combos[f'voraz adelante elegida en {nom}']=r['fwd'][0]; combos[f'voraz atrás elegida en {nom}']=r['bwd'][0]
EV={}
for n,ks in combos.items(): EV[n]=dict(fam=sorted(ks),**ev(ks)); print(n,EV[n])
# escalado a igual caída que la actual
def escala(ks,obj):
    lo,hi=0.5,4.0
    for _ in range(18):
        mid=(lo+hi)/2; _,mm=run(mask_of(ks),mult=mid)
        if mm['caida']<=obj: lo=mid
        else: hi=mid
    _,mm=run(mask_of(ks),mult=lo); return lo,mm
ESC={}
for n,ks in combos.items():
    if n=='Actual (todas)': continue
    k=tuple(sorted(ks))
    if k in [tuple(sorted(x)) for x in ESC.values()]: continue
    lo,mm=escala(ks,m0['caida']); EV[n]['escala']=round(lo,2); EV[n]['R_ano_escalado']=round(mm['R_ano'],2); EV[n]['caida_escalado']=round(mm['caida'],2)
    ESC[n]=ks
json.dump(dict(actual=dict(R_ano=m0['R_ano'],caida=m0['caida'],ratio=m0['Rano_caida'],n=m0['n'],acierto=m0['acierto'],R_op=m0['R_op'],peor_ano=pv0,
   sin_topes=dict(R_ano=mT['R_ano'],caida=mT['caida'],ratio=mT['Rano_caida']),vigente_simple=dict(R_ano=mV['R_ano'],caida=mV['caida'],ratio=mV['Rano_caida']),
   ratio_18_21=score(keys,desde,CORTE)['Rano_caida'],ratio_22_26=score(keys,CORTE,None)['Rano_caida']),
   seleccion=res,evaluacion=EV),open('resultados.json','w'),ensure_ascii=False,indent=1,default=str)
