# Ideas de rotación 2, 3 y 4 re-simuladas con el código ORIGINAL (regla vigente: sin venta del tercio con nota 2)
import sys
sys.path.insert(0,'/home/claude/contexto-cartera/BOT/codigo/estudios')
import origen_util as U, numpy as np, pandas as pd
MC=U.MC; DC=U.DC
src=open(MC.__file__).read()
a1="parts = list(P['partial']); pdone = 0"; assert a1 in src
src=src.replace(a1,"parts = ([(1.0, 0.0)] if (P.get('st') is not None and P['st'](P, idx[k0], i)) else list(P['partial'])); pdone = 0")
a2="    T = sim(X, P, sig=sig, permitir=perm)"; assert a2 in src
src=src.replace(a2,"    P = dict(P); P['a'] = a; P['pts'] = (lambda i: tam_i(i)[0]); P['st'] = ST.get('f'); P['sal50'] = ST.get('sal50')\n    T = sim(X, P, sig=sig, permitir=perm)")
# idea 3: salida al cierre diario si el cierre queda un 2 % bajo la EMA 50 diaria (valor en vivo)
a3="            if guardar_camino and es_cierre_dia[j]:"; assert a3 in src
src=src.replace(a3,"            if P.get('sal50') and es_cierre_dia[j] and C[j] < X['e50d_vivo'][j] * 0.98:\n                px = C[j]; motivo = 'pierde_ema50'; break\n"+a3,1)
ST={'f':None,'sal50':None}; MC.__dict__['ST']=ST
exec(compile(src,MC.__file__,'exec'),MC.__dict__)
ST['f']=lambda P,t,i: P['a']!='SOL' and P['pts'](i)>=2
O0=pd.read_parquet('/home/claude/velas-backtest/MOTOR/listas/cripto_realista.parquet')
def ema(x,n): return pd.Series(x).ewm(span=n,adjust=False).mean()
def adx(d,n=14):
    up=d.h.diff(); dn=-d.l.diff(); pdm=((up>dn)&(up>0))*up; ndm=((dn>up)&(dn>0))*dn
    tr=pd.concat([d.h-d.l,(d.h-d.c.shift()).abs(),(d.l-d.c.shift()).abs()],axis=1).max(axis=1)
    w=lambda s: s.ewm(alpha=1/n,adjust=False).mean(); a=w(tr)
    pdi=100*w(pdm)/a; ndi=100*w(ndm)/a; dx=100*(pdi-ndi).abs()/(pdi+ndi); return w(dx)
Xbase={}; ORIG_SEN=MC.señales
def prep(a):
    if a not in Xbase:
        X=dict(DC.preparar(a)); d=DC.ld(a,'1d'); tc=X['tc']
        e50=ema(d.c,50); prev=DC.al_diario(e50,tc); al=2/51
        X['e50d_vivo']=prev*(1-al)+X['C']*al
        X['adx_d']=DC.al_diario(adx(d),tc)
        e50h,e200h=X['e50'],X['e200']; C=X['C']
        nota4=(C>e50h).astype(int)+(C>e200h)+(e50h>e200h)+(np.r_[False,e50h[1:]>e50h[:-1]])
        X['lateral4h']=(nota4==2)
        Xbase[a]=X
    return Xbase[a]
def idea4_sig(X):
    """Espera al cierre: señal de la mañana (vela que cierra 06-12 UTC) tras una caída nocturna > 0,5 ATR diario
    desde el cierre de las 20:00 UTC → se pasa a la vela siguiente solo si esa vela también cierra sobre la media."""
    s=ORIG_SEN(X,'e20').copy(); idx=X['idx']; tc=X['tc']; C=X['C']; L=X['L']; m=X['e20']; AD=X['AD']; n=len(C)
    hcl=pd.DatetimeIndex(tc).hour; ref=None; cambios=0
    for i in range(n):
        if pd.Timestamp(tc[i]).hour==20: ref=i
        if not s[i] or ref is None or not (6<=hcl[i]<=12) or i+1>=n: continue
        caida=C[ref]-L[ref+1:i+1].min()
        if np.isfinite(AD[i]) and caida>0.5*AD[i]:
            s[i]=False; cambios+=1
            if C[i+1]>m[i+1]: s[i+1]=True
    return s,cambios
nom=sys.argv[1]
Xc={a:prep(a) for a in MC.COINS}
if nom=='i3': ST['sal50']=True
if nom=='i2':
    viejo=U.permitir_realista
    def nuevo(X):
        p=viejo(X)
        if X['a']!='BTC': return p
        lat=X['lateral4h']; ad=X['adx_d']
        return lambda i: p(i) and not (lat[i] and np.nan_to_num(ad[i])>20)
    U.permitir_realista=nuevo
if nom=='i4':
    # se sustituye la función de señales por la versión con espera
    orig=MC.señales; cache={}
    def señ(X,ma='e20'):
        k=X['a']
        if k not in cache: cache[k]=idea4_sig(X); print('  espera al cierre',k,'señales movidas',cache[k][1],flush=True)
        return cache[k][0]
    MC.señales=señ
TT=U.listas(realista=True,Xc=Xc); T=U.todas(TT)
O,D=U.a_lista(T,plantilla=O0)
O.to_parquet(f'C_{nom}.parquet'); D.to_parquet(f'C_{nom}_diario.parquet')
print(nom,len(O),'R',round(O.r_final.sum(),1),'motivos',O.motivo_salida.value_counts().head(6).to_dict(),flush=True)
