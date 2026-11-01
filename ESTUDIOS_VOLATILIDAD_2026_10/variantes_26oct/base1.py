exec(open('/home/claude/vol2/salida.py').read().split("def evaluar")[0])
def rat1(T,a,b):
    m=(T.index>=a)&(T.index<b); s=pd.Series(T.R[m].values,index=T.exit[m].values).sort_index(); cum=s.cumsum(); dd=(cum-cum.cummax()).min()
    yrs=(pd.Timestamp(min(b,'2026-10-25'))-pd.Timestamp(a)).days/365.25; return s.sum()/yrs/abs(dd)
T0=pd.concat([trades(c) for c in COINS]).sort_index()
T1=pd.concat([trades(c,nopart=(bp<=0.1).to_dict()) for c in COINS]).sort_index()
print('Tamaño 1 (sin nota):', ' | '.join(f'{a}-{b} {rat1(T0,a,b):.2f}→{rat1(T1,a,b):.2f}' for a,b in P), '| R/op',round(T0.R.mean(),3),round(T1.R.mean(),3))
