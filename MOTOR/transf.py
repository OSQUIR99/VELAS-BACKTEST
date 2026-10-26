exec(open('/home/claude/resumen-senales/analisis_resumen.py').read().split('# selección')[0].split('filas=[]')[0])
C='/home/claude/motor/cache/'
def px(n):
    d=pd.read_parquet(C+'cierre_'+n+'.parquet'); s=d.iloc[:,0]; s.index=pd.to_datetime(s.index); return s.sort_index()
Wc=W&~(L=='acciones_v2')
te=pd.to_datetime(O.t_entrada).values; ts=pd.to_datetime(O.t_salida).values; dia=pd.to_datetime(O.t_entrada).dt.normalize()
def asof(s,t):  # valor a cierre anterior a t
    s=s[~s.index.duplicated()].dropna(); t=pd.DatetimeIndex(t); k=s.index.searchsorted(t,side='left')-1
    v=s.values[np.clip(k,0,None)].astype(float); v[k<0]=np.nan; return v
quit3=['Materias primas T1/T2','E1 sectores','Plata']
basek=[k for k in uni if k not in quit3]
def mk(ks,extra=None):
    m=np.zeros(len(O),bool)
    for k in ks: m|=uni[k]
    if extra is not None: m|=extra
    return m&Wc
def ev(mask,tam=None):
    c=dict(FL)
    if tam is not None: c['tam_mult']=tam
    rr=M.simular(c,mascara=mask)
    f=lambda a,b=None: metricas(M,rr.s,a,b,mascara=mask,eq=rr.eq)
    return [f(desde),f(desde,CORTE),f(CORTE)]
def sola(mask,tam=None):
    c=dict(A.SIN_TOPES); 
    if tam is not None: c['tam_mult']=tam
    rr=M.simular(c,mascara=mask); return metricas(M,rr.s,desde,mascara=mask,eq=rr.eq)
rows=[]; B=ev(mk(basek))
def reg(nombre,extra,quita=None,tam=None,familia=''):
    ks=[k for k in basek if k!=quita]; m=mk(ks,extra); r=ev(m,tam); so=sola(extra&Wc,tam) if extra is not None and (extra&Wc).sum() else None
    ok=all(r[i]['Rano_caida']>B[i]['Rano_caida'] and r[i]['R_ano']>B[i]['R_ano'] for i in range(3))
    rows.append(dict(familia=familia,variante=nombre,ops_sola=int((extra&Wc).sum()) if extra is not None else 0,
      sola_Ra=so and round(so['R_ano'],2),sola_caida=so and round(so['caida'],2),sola_ratio=so and round(so['Rano_caida'],2),
      Ra=round(r[0]['R_ano'],2),caida=round(r[0]['caida'],2),ratio=round(r[0]['Rano_caida'],3),
      IS_Ra=round(r[1]['R_ano'],2),IS_ratio=round(r[1]['Rano_caida'],3),OOS_Ra=round(r[2]['R_ano'],2),OOS_ratio=round(r[2]['Rano_caida'],3),pasa=ok))
    print(rows[-1],flush=True)
rows.append(dict(familia='BASE',variante='sin las tres',Ra=round(B[0]['R_ano'],2),caida=round(B[0]['caida'],2),ratio=round(B[0]['Rano_caida'],3),
  IS_Ra=round(B[1]['R_ano'],2),IS_ratio=round(B[1]['Rano_caida'],3),OOS_Ra=round(B[2]['R_ano'],2),OOS_ratio=round(B[2]['Rano_caida'],3))); print(rows[-1])
# ---- E1 sectores
sec=uni['E1 sectores']; idx=uni['E1 índices']
dias_idx=set(dia[idx&Wc])
S1=sec&~dia.isin(dias_idx).values
reg('S1 sectores solo sin E1 índices ese día',S1,familia='E1 sectores')
MAP={'XLC':'comunicaciones','XLP':'consumo_basico','XLY':'consumo_ciclico','XLE':'energia','XLF':'financieras','XLI':'industria','XLRE':'inmobiliario','XLB':'materiales','XLV':'salud','XLU':'servicios_publicos','XLK':'tecnologia'}
spx=px('SPX'); P=pd.DataFrame({k:px('sector_'+v) for k,v in MAP.items()}).reindex(spx.index).ffill()
rs=(P.pct_change(126).sub(spx.pct_change(126),axis=0)); rk=rs.rank(axis=1,ascending=False)
top=np.zeros(len(O),bool)
ii=np.flatnonzero(sec)
for i in ii:
    a=act[i]
    if a not in MAP: continue
    r=rk[a].loc[:pd.Timestamp(te[i])-pd.Timedelta(hours=1)]
    if len(r) and r.iloc[-1]<=3: top[i]=True
reg('S2 sectores top-3 fuerza relativa 6m',top,familia='E1 sectores')
sma=spx.rolling(200).mean(); bajo=asof((spx<sma).astype(float),dia)
bajo=np.nan_to_num(bajo)>0.5
S3=sec&np.isin(act,['XLP','XLU','XLV'])&bajo
reg('S3 defensivos con SPX bajo media 200',S3,familia='E1 sectores')
reg('S4 = S1 y S2 a la vez',S1&top,familia='E1 sectores')
# ---- Plata
pl=uni['Plata']; oro=uni['Oro']&Wc
oi=np.flatnonzero(oro); go_e=te[oi]; go_s=ts[oi]
abierto=np.array([((go_e<=te[i])&(go_s>te[i])).any() for i in range(len(O))]) if False else None
ab=np.zeros(len(O),bool)
for i in np.flatnonzero(pl): ab[i]=((go_e<=te[i])&(go_s>te[i])).any()
reg('P1 plata solo sin oro abierto',pl&~ab,familia='Plata')
g=px('oro'); s=px('plata'); rt=(g/s).dropna(); z=(rt-rt.rolling(252).mean())/rt.rolling(252).std()
zz=asof(z,dia); reg('P2 plata solo con ratio oro/plata z>1',pl&(np.nan_to_num(zz)>1),familia='Plata')
mom=asof(s.pct_change(63)-g.pct_change(63),dia); reg('P3 plata solo si más fuerte que oro 3m',pl&(np.nan_to_num(mom)>0),familia='Plata')
tam=np.ones(len(O)); tam[pl]=0.5; reg('P4 plata a medio tamaño',pl,tam=tam,familia='Plata')
# ---- T1/T2
mt=uni['Materias primas T1/T2']
reg('M1 T1/T2 solo metales',mt&np.isin(act,['ORO','PLATA','COBRE','PALADIO','PLATINO']),familia='T1/T2')
# M2 filtro: oro solo si T1/T2 ORO abierto en la misma dirección (sin T1/T2 en cartera)
t2o=np.flatnonzero(mt&(act=='ORO')); dirv=O.direccion.values
conf=np.zeros(len(O),bool)
for i in np.flatnonzero(uni['Oro']): conf[i]=((te[t2o]<=te[i])&(ts[t2o]>te[i])&(dirv[t2o]==dirv[i])).any()
reg('M2 oro solo si T2 oro confirma (filtro)',None if False else (uni['Oro']&conf),quita='Oro',familia='T1/T2')
# M3 pirámide: T1/T2 de metales solo si hay operación de oro abierta en ganancia
ent=O.entrada.values; gcl=asof(g,pd.DatetimeIndex(te))
pir=np.zeros(len(O),bool)
for i in np.flatnonzero(mt&np.isin(act,['ORO','PLATA'])):
    k=oi[(go_e<=te[i])&(go_s>te[i])]
    pir[i]=any(dirv[j]*(gcl[i]-ent[j])>0 for j in k)
reg('M3 T1/T2 oro/plata como pirámide sobre oro en ganancia',pir,familia='T1/T2')
pd.DataFrame(rows).to_csv('/home/claude/resumen-senales/transformaciones.csv',index=False)
