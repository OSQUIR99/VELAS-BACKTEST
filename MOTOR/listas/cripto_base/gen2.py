# Lista cripto re-simulada con el código ORIGINAL (regla vigente: sin venta del tercio con nota de puntos 2) y variantes de medias
import sys, os, copy
sys.path.insert(0,'/home/claude/contexto-cartera/BOT/codigo/estudios')
import origen_util as U, numpy as np, pandas as pd
MC=U.MC
src=open(MC.__file__).read()
a1="parts = list(P['partial']); pdone = 0"; assert a1 in src
src=src.replace(a1,"parts = ([(1.0, 0.0)] if (P.get('st') is not None and P['st'](P, idx[k0], i)) else list(P['partial'])); pdone = 0")
a2="    T = sim(X, P, sig=sig, permitir=perm)"; assert a2 in src
src=src.replace(a2,"    P = dict(P); P['a'] = a; P['pts'] = (lambda i: tam_i(i)[0]); P['st'] = ST.get('f')\n    T = sim(X, P, sig=sig, permitir=perm)")
ST={'f':None}; MC.__dict__['ST']=ST
exec(compile(src,MC.__file__,'exec'),MC.__dict__)
def c_pts(P,t,i): return P['a']!='SOL' and P['pts'](i)>=2
ST['f']=c_pts
O0=pd.read_parquet('/home/claude/velas-backtest/MOTOR/listas/cripto_realista.parquet')
def ema(x,n): return pd.Series(x).ewm(span=n,adjust=False).mean().values
VAR={'base':{}, 'm18':{'e20':18}, 'm22':{'e20':22}, 'm16':{'e20':16}, 'm25':{'e20':25}, 'm40':{'e50':40}, 'm62':{'e50':62}}
Xbase={}
for nom in sys.argv[1:]:
    Xc={}
    for a in MC.COINS:
        if a not in Xbase: Xbase[a]=U.DC.preparar(a)
        X=dict(Xbase[a])
        for k,n in VAR[nom].items(): X[k]=ema(X['C'],n)
        Xc[a]=X
    TT=U.listas(realista=True,Xc=Xc); T=U.todas(TT)
    O,D=U.a_lista(T,plantilla=O0)
    O.to_parquet(f'C_{nom}.parquet'); D.to_parquet(f'C_{nom}_diario.parquet')
    print(nom,len(O),'sin parcial',int((~O.parcial.astype(bool)).sum()) if 'parcial' in O else '','R',round(O.r_final.sum(),1),flush=True)
