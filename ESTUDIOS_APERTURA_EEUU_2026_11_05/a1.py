import pandas as pd, numpy as np
from scipy import stats
T=pd.read_pickle('T1h.pkl'); T['año']=pd.to_datetime(T.t0).dt.year
def cond(x,y,nom):
    m=x.notna()&y.notna(); x=x[m]; y=y[m]
    up=x>0; dn=x<0
    rho=stats.spearmanr(x,y)[0]; r=np.corrcoef(x,y)[0,1]
    print(f"{nom:34s} n={len(x)} | sube 1ª: después media {y[up].mean()*100:+.3f}% baja el {(y[up]<0).mean()*100:.0f}% | baja 1ª: después {y[dn].mean()*100:+.3f}% sube el {(y[dn]>0).mean()*100:.0f}% | corr {r:+.3f} (Spearman {rho:+.3f}, p {stats.pearsonr(x,y)[1]:.3f})")
print('== Todas las sesiones 2020-2026 ==')
cond(T.r1,T.rr,'S&P 1ª hora → resto de sesión')
cond(T.b1,T.brr,'BTC 1ª hora → resto de sesión')
cond(T.b1,T.b24,'BTC 1ª hora → 24 h')
cond(T.r1,T.brr,'S&P 1ª hora → BTC resto sesión')
cond(T.b_pre,T.b1,'BTC noche (16→9:30) → 1ª hora')
cond(T.b_pre,T.brr,'BTC noche → resto sesión')
both_up=(T.r1>0)&(T.b1>0); both_dn=(T.r1<0)&(T.b1<0)
print(f"Los dos suben la 1ª hora (n={both_up.sum()}): S&P después {T.rr[both_up].mean()*100:+.3f}% (baja {(T.rr[both_up]<0).mean()*100:.0f}%), BTC después {T.brr[both_up].mean()*100:+.3f}% (baja {(T.brr[both_up]<0).mean()*100:.0f}%), BTC 24h {T.b24[both_up].mean()*100:+.3f}%")
print(f"Los dos bajan la 1ª hora (n={both_dn.sum()}): S&P después {T.rr[both_dn].mean()*100:+.3f}% (sube {(T.rr[both_dn]>0).mean()*100:.0f}%), BTC después {T.brr[both_dn].mean()*100:+.3f}% (sube {(T.brr[both_dn]>0).mean()*100:.0f}%), BTC 24h {T.b24[both_dn].mean()*100:+.3f}%")
print('base: S&P resto sube', f"{(T.rr>0).mean()*100:.0f}%", 'BTC resto sube', f"{(T.brr>0).mean()*100:.0f}%")
print('\n== Por tamaño de la 1ª hora (en desviaciones de los 60 días anteriores) ==')
for x,y,nom in [('r1','rr','S&P'),('b1','brr','BTC'),('b1','b24','BTC→24h')]:
    z=T[x]/T[x].rolling(60).std().shift(1)
    q=pd.cut(z,[-99,-2,-1,-0.5,0,0.5,1,2,99])
    g=T.groupby(q)[y].agg(['count','mean',lambda v:(v>0).mean()])
    g.columns=['n','media%','sube%']; g['media%']*=100; g['sube%']*=100
    print(nom); print(g.round(3).to_string())
print('\n== Por año (correlación 1ª hora → resto) ==')
print(T.groupby('año').apply(lambda d: pd.Series({'S&P':d.r1.corr(d.rr),'BTC':d.b1.corr(d.brr),'BTC24':d.b1.corr(d.b24),'n':len(d)})).round(3).to_string())
