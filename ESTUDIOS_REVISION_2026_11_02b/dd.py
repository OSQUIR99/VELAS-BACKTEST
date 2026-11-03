from lab import *
s0,e0,_=run()
e=e0[(e0.index>=C.desde)&(e0.index<=pd.Timestamp('2026-10-20'))]
pk=e.cummax(); d=pk-e
# episodios
eps=[];i=0;v=d.values;idx=d.index
while i<len(v):
    if v[i]>0:
        j=i
        while j<len(v) and v[j]>0: j+=1
        k=i+int(np.argmax(v[i:j])); eps.append((v[k],idx[i-1] if i>0 else idx[i],idx[k],idx[j-1])); i=j
    else: i+=1
eps=sorted(eps,reverse=True)[:6]
# contribución por familia en cada episodio: curvas por familia
fams=['cripto','metales','petroleo','x_petroleo','corto_petroleo','bolsa_e1','yt_connors_qqq','shy','c10','corto_sector','corto_indices_credito']
cur={f:M.curva(s0,mascara=(L==f)) for f in fams}
for dd_,a,b,c in eps:
    contr={f:round(float(cur[f].loc[b]-cur[f].loc[a]),1) for f in fams}
    print(f'caída {dd_:.1f} R  {a.date()} → {b.date()} (fin {c.date()})',{k:v for k,v in contr.items() if abs(v)>=0.3})
