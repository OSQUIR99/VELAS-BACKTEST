exec(open('/home/claude/vol2/var.py').read().split("if __name__")[0])
for c in COINS: CACHE[c]=prep(c)
SYS=pd.read_pickle('/home/claude/vol/data/SYS.pkl'); SYS['Rw']=SYS.R*SYS['size']
def collect(fn):
    out=[]
    for c in COINS:
        T=run(CACHE[c],fn(CACHE[c]).fillna(False)); T['coin']=c; out.append(T)
    T=pd.concat(out).sort_index(); return T[T.index>='2018-01-01']
brk=lambda d:d.close>d.hi20
V1=collect(lambda d:brk(d)&d.comp); ALL=collect(brk); NO=collect(lambda d:brk(d)&~d.comp)
def rat(R,ex,a,b):
    m=(R.index>=a)&(R.index<b); s=pd.Series(R[m].values,index=ex[m].values).sort_index(); cum=s.cumsum(); dd=(cum-cum.cummax()).min()
    yrs=(pd.Timestamp(b if b<'2027' else '2026-10-25')-pd.Timestamp(a)).days/365.25; return s.sum()/yrs/abs(dd), s.sum()/yrs, dd
P=[('2018','2020'),('2020','2022'),('2022','2024'),('2024','2027'),('2018','2022'),('2022','2027'),('2018','2027')]
def show(name,extra,w=1.0):
    R=pd.concat([SYS.Rw,extra.R*w]); ex=pd.concat([SYS.exit,extra.exit])
    out=[rat(R,ex,a,b) for a,b in P]
    print(f'{name:45s} '+' | '.join(f'{a[2:4]}-{b[2:4]} {o[0]:.2f}' for (a,b),o in zip(P,out))+f' || todo R/año {out[-1][1]:+.1f} caída {out[-1][2]:.1f}')
show('Solo sistema actual (aprox.)',SYS.iloc[0:0][['R','exit']])
show('+ ruptura tras compresión (V1), 1 R',V1)
show('+ ruptura tras compresión (V1), 0,5 R',V1,0.5)
show('+ todas las rupturas, 1 R',ALL)
show('+ rupturas sin compresión, 1 R',NO)
