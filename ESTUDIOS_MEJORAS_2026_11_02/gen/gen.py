# Re-simulación vela a vela del REBOTE 4H con el código ORIGINAL, quitando la venta del tercio según una condición
import sys, os, pickle, re
sys.path.insert(0,'/home/claude/contexto-cartera/BOT/codigo/estudios')
import origen_util as U, numpy as np, pandas as pd
MC=U.MC
src=open(MC.__file__).read()
a1="parts = list(P['partial']); pdone = 0"
assert a1 in src
src=src.replace(a1,"parts = ([(1.0, 0.0)] if (P.get('st') is not None and P['st'](P, idx[k0], i)) else list(P['partial'])); pdone = 0")
a2="    T = sim(X, P, sig=sig, permitir=perm)"
assert a2 in src
src=src.replace(a2,"    P = dict(P); P['a'] = a; P['pts'] = (lambda i: tam_i(i)[0]); P['st'] = ST.get('f')\n    T = sim(X, P, sig=sig, permitir=perm)")
ST={'f':None}; MC.__dict__['ST']=ST
exec(compile(src,MC.__file__,'exec'),MC.__dict__)
X=pd.read_pickle('/home/claude/vol/data/X_vol.pkl'); PCT=X.pct.shift(1)
def c_vol(P,t,i):   return P['a']!='SOL' and (PCT.get(pd.Timestamp(t).normalize(),1.0)<=0.10)
def c_pts(P,t,i):   return P['a']!='SOL' and P['pts'](i)>=2
def c_both(P,t,i):  return c_vol(P,t,i) or c_pts(P,t,i)
VAR={'v0':None,'vol':c_vol,'vol_o_puntos':c_both,'puntos':c_pts}
O0=pd.read_parquet('/home/claude/velas-backtest/MOTOR/listas/cripto_realista.parquet')
Xc={}
for nom in sys.argv[1:]:
    ST['f']=VAR[nom]
    TT=U.listas(realista=True,Xc=Xc); T=U.todas(TT)
    O,D=U.a_lista(T,plantilla=O0)
    O.to_parquet(f'B_{nom}.parquet'); D.to_parquet(f'B_{nom}_diario.parquet')
    print(nom,len(O),'sin parcial',int((~O.parcial).sum()),'R',round(O.r_final.sum(),1),flush=True)
