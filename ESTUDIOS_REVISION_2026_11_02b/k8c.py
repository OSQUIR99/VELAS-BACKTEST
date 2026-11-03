
from fiel import *
pm=lambda p: np.select([p>=2,p==1,p==0,p==-1],[1.5,1.25,1.0,0.5],0.25)
sol=cr&(act=='SOL')
k8=np.ones(len(O)); k8[L=='corto_petroleo']=2.0; k8[SUB=='petroleo:L2']=0.5
k8[SUB=='petroleo:tras-noticia (bajada)']=0.5; k8[np.isin(SUB,['x_petroleo:X1','x_petroleo:X3'])]=0.75
def tmf(btc=1.0, piso=True, snv=None):
    snv=sn if snv is None else snv
    w=np.ones(len(O)); w[cr&(act=='BTC')&sn]/=1.5; w[cr&(act=='BTC')&snv]*=btc
    w[cr&(lm>1)]/=lm[cr&(lm>1)]; w[cr&fragil]*=0.5
    f=1.0/pm(PT); w[sol]*=f[sol]
    nt=np.where(cr,tam*w,tam); fuera=cr&(nt<0.25-1e-9)
    if piso: nt=np.where(cr,np.clip(nt,0.25,5.0),nt); fuera[:]=False
    else: nt=np.where(cr,np.clip(nt,0,5.0),nt)
    return np.where(tam>0,nt/np.maximum(tam,1e-9),1.0), fuera
def go(btc=1.0,piso=True,kk=True,snv=None,exv=EXV,mask=BASEV):
    tf,f=tmf(btc,piso,snv); s,e,_=run(mask=mask&~f,exv=exv,tm=tf*(k8 if kk else 1)); return e
def ep(e): return ' · '.join(f"{met_eq(e,pd.Timestamp(a),pd.Timestamp(b))['ratio']:.2f}" for a,b in [('2018-01-01','2020-01-01'),('2020-01-01','2022-01-01'),('2022-01-01','2024-01-01'),('2024-01-01','2026-10-21')])
print(linea('chequeo: fiel+SOL plano, piso, sin K8 (6,41/5,09/7,79)',go(1.0,True,False)),flush=True)
for piso in [True,False]:
  for btc in [1.0,1.5]:
    e0=go(btc,piso,False); e1=go(btc,piso,True)
    print(linea(f'piso={int(piso)} btc={btc} sin K8',e0),'| ép',ep(e0))
    print(linea(f'piso={int(piso)} btc={btc} con K8',e1,C.met3(e0)),'| ép',ep(e1),flush=True)
# piso con K8 y BTC 1.5
r=C.met3(go(1.5,True,True)); print(linea('K8 btc1.5: quitar piso frente a piso',go(1.5,False,True),r),flush=True)
# vecinos BTC sobre K8 sin piso
e0=go(1.0,False,True); r0=C.met3(e0); print(linea('BASE FIEL VIGENTE (K8, sin piso, BTC ×1)',e0),'| ép',ep(e0))
for b in [1.25,1.5,1.75,2.0]:
    e=go(b,False,True); print(linea(f'  + BTC sn ×{b}',e,r0),'| ép',ep(e),flush=True)
e1=go(1.5,False,True); print('bootstrap',C.bootstrap(e0,e1,2000),flush=True)
# E1/Connors fuera del freno sobre fiel vigente
eD=go(1.5,False,True,exv=ex); print(linea('E1 y Connors DENTRO del freno',eD)); print(linea('  … FUERA (vigente)',e1,C.met3(eD)),flush=True)
# placebo
R1=[x['ratio'] for x in C.met3(e1)]
rng=np.random.default_rng(7); mb=cr&(act=='BTC'); yr=pd.DatetimeIndex(O.t_entrada.values).year.values
cnt=np.zeros(3); N=100
for i in range(N):
    s2=sn.copy()
    for y in np.unique(yr[mb]):
        idx=np.flatnonzero(mb&(yr==y)); s2[idx]=rng.permutation(sn[idx])
    cnt+=np.array([x['ratio'] for x in C.met3(go(1.5,False,True,snv=s2))])>=np.array(R1)
print('placebo barajado >= real (todo/18-21/22-26):',cnt/N,flush=True)
