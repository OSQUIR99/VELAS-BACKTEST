from h import *
import sys
C,M,r0,e0,q0=base_nueva(); print('BASE',C.fmt(q0),f'| 24-26 {met24(C,e0):.2f}',flush=True)
dia=pd.to_datetime(O0.t_entrada).dt.normalize()
cb=cond_base(O0)
def pctvol(a):
    c=px(a,'1d').close; c=c[~c.index.duplicated()].asfreq('D').ffill()
    v=np.log(c).diff().rolling(30).std()
    return v.rolling(1095,min_periods=365).apply(lambda x:(x<=x[-1]).mean(),raw=True).shift(1)
own=np.zeros(len(O0),bool); PV={}
for a in O0.activo.unique():
    PV[a]=pctvol(a); m=(O0.activo==a).values; own[m]=PV[a].reindex(dia[m]).values<=0.10
btc=px('BTC','1d').close; btc=btc[~btc.index.duplicated()]; s200=btc.rolling(200).mean()
fuerte=((btc>s200)&(s200>s200.shift(20))).shift(1)
tr=fuerte.reindex(dia).fillna(False).values.astype(bool)
def run(nom,O,D):
    C2=cartera(O,D); M2=mascaras(C2); _,e,q=evalua(C2,M2['BASE'],M2['EX']); informe(C2,nom,q,q0,e,e0)
for nom,c in [('sin tercio: BTC ≤0,10 o propia ≤0,10',cb|own),('sin tercio: solo propia ≤0,10',own),
              ('sin tercio: BTC ≤0,10 o puntos ≥2',cb|(O0.puntos.fillna(-9).values>=2)),
              ('sin tercio: BTC ≤0,10 o tendencia fuerte BTC',cb|tr),
              ('sin tercio: BTC ≤0,15 y tendencia fuerte',cb|((PCT.reindex(dia).values<=0.15)&tr))]:
    O,D,n=sin_tercio(O0,D0,c); print(nom,'modificadas',n,flush=True); run(nom,O,D)
# salida por tiempo: si tras k velas de 4 h no ha llegado a +m R y cierra bajo la entrada, fuera al cierre de esa vela
Ob,Db,_=sin_tercio(O0,D0,cb)
def stop_tiempo(k,m,bajo=0.0):
    O=Ob.copy(); D=Db.copy(); n=0; drop=[]
    for i in range(len(O)):
        o=O.iloc[i]
        if o.activo=='SOL' or (o.n_promedios or 0)>0: continue
        R=o.entrada-o.sl_inicial; h=h4(o.activo); seg=h[(h.index>=o.t_entrada)&(h.index<=o.t_salida)]
        if len(seg)<=k: continue
        pre=seg.iloc[:k]
        if pre.high.max()>=o.entrada+m*R or pre.low.min()<=o.sl_inicial: continue
        cl=seg.close.iloc[k-1]
        if cl>=o.entrada+bajo*R: continue
        x=(cl-o.entrada)/R; tx=seg.index[k-1]+pd.Timedelta(hours=4)
        O.iat[i,O.columns.get_loc('r_bruto')]=x; O.iat[i,O.columns.get_loc('r_final')]=x*o.tam_R
        O.iat[i,O.columns.get_loc('t_salida')]=tx; O.iat[i,O.columns.get_loc('salida')]=cl
        md=(D.id==o.id); f=pd.to_datetime(D.fecha)
        drop+=list(D.index[md&(f>tx.normalize())])
        j=D.index[md&(f==tx.normalize())]
        if len(j)==0:
            D=pd.concat([D,pd.DataFrame({'id':[o.id],'fecha':[D.fecha.iloc[0].__class__(tx.normalize()) if not isinstance(D.fecha.iloc[0],str) else str(tx.date())],'r_latente':[x*o.tam_R],'r_latente_unidad':[x]})],ignore_index=True)
        else:
            D.loc[j,'r_latente_unidad']=x; D.loc[j,'r_latente']=x*o.tam_R
        n+=1
    D=D.drop(index=drop); return O,D,n
for k,m,b in [(6,0.5,0.0),(12,0.5,0.0),(18,0.5,0.0),(12,1.0,0.0),(12,0.5,-0.25),(24,0.5,0.0)]:
    O,D,n=stop_tiempo(k,m,b); nom=f'tiempo: {k} velas sin +{m} R y cierre < entrada{"" if b==0 else f"{b:+} R"}'; print(nom,'cortadas',n,flush=True); run(nom,O,D)
