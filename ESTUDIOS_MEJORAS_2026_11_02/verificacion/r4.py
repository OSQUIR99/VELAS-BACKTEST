from ver import *
v=V(True); O=v.O; L=v.L
s0=np.load('s_B0.npy')
for fam in ('petroleo','x_petroleo','corto_petroleo'):
    m=(L==fam)&v.base&(s0>0)
    d=pd.DataFrame(dict(sen=v.sen[m],y=O.t_entrada[m].dt.year.values,r=O.r_final.values[m],rs=s0[m]*O.r_final.values[m],tam=O.tam_R.values[m]))
    d['ep']=np.where(d.y<2022,'18-21','22-26')
    print('==',fam); print(d.groupby(['sen','ep']).agg(n=('r','size'),Rop=('r','mean'),Rtot=('rs','sum'),tam=('tam','mean')).round(3).unstack().to_string())
