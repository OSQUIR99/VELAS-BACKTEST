# Rotación BTC–altcoins: (1) altcoins a media posición con el termómetro ≥ 70; (5) etiqueta apoya/neutral/en contra
from ev import *
import sys; sys.path.insert(0,'/home/claude/velas-backtest')
from cargar import velas
LISTA=['ETH','AAVE','ADA','BNB','HBAR','HYPE','LINK','ONDO','SOL','UNI','XRP','ZEC']
def dia(a):
    d=velas(a,'1d').cierre; d=d[~d.index.duplicated()]; return d
# termómetro: % de la lista con cierre diario sobre su media de 50 (día anterior; solo monedas con 50 días de historia)
cl=pd.DataFrame({a:dia(a) for a in LISTA}); ma=cl.rolling(50).mean()
sobre=(cl>ma).astype(float).where(ma.notna()); nn=sobre.notna().sum(axis=1).astype(float); term=(sobre.sum(axis=1)/nn.replace(0,np.nan)*100).where(nn>=4)
term_prev=term.shift(1)
# sesgo de rotación (doc 12): pendiente de la media de 20 de ETH/BTC (5 días) y de la dominancia de BTC
eb=dia('ETH')/dia('BTC'); m=eb.rolling(20).mean(); peb=(m/m.shift(5)-1).shift(1)
dom=velas('dominancia_btc','1d').cierre; dom=dom[~dom.index.duplicated()]; md=dom.rolling(20).mean(); pdm=(md/md.shift(5)-1).shift(1)
C=cartera(); M=mascaras(C); O=C.O; L=C.L; act=C.act
e0,q0=run(C,M['BASE'],M['EX']); print('BASE',C.fmt(q0),'24-26',round(m24(e0),2),flush=True)
cr=(L=='cripto')&M['BASE']; fe=pd.to_datetime(O.t_senal).dt.normalize()
T=term_prev.reindex(fe.values,method='ffill').values
alts=cr&np.isin(act,['SOL','ADA','LINK','ZEC'])
print('termómetro: media',round(term.dropna().mean(),1),'% de días >= 70:',round((term.dropna()>=70).mean()*100,1))
for nom,grupo in (('SOL, ADA, LINK, ZEC',alts),('las 5 menos BTC (con ETH)',cr&(act!='BTC'))):
    for um in (70,):
        tm=np.ones(len(O)); toc=grupo&(T>=um); tm[toc]=0.5
        e,q=run(C,M['BASE'],M['EX'],tm=tm); linea(C,f'idea 1: {nom} x0,5 con termómetro >= {um} ({toc.sum()} op.)',e,q,e0,q0)
# placebo: mismo número de operaciones al azar
rng=np.random.default_rng(3); n=int((alts&(T>=70)).sum()); res=[]
for k in range(20):
    tm=np.ones(len(O)); idx=rng.choice(np.flatnonzero(alts),n,replace=False); tm[idx]=0.5
    _,q=run(C,M['BASE'],M['EX'],tm=tm); res.append([q[i]['ratio'] for i in range(3)])
res=np.array(res); print('placebo (20 sorteos, mismas op. al azar a x0,5): media',res.mean(0).round(2),'máximo',res.max(0).round(2))
# por qué: R por operación de las altcoins según el termómetro
t=pd.to_datetime(O.t_entrada)
for a,b,nm in (('2018-05','2022','2018-21'),('2022','2027','2022-26')):
    s=alts&(t>=a).values&(t<b).values
    for cond,lab in ((T>=70,'>=70'),(T<70,'<70')):
        u=O.r_bruto[s&cond]; print(f'  altcoins {nm} termómetro {lab}: {len(u)} op., R/op {u.mean():+.2f}')
# idea 5: etiqueta por señal
def etiqueta(a,f):
    x=(peb if a in ('ETH','BTC') else -pdm).reindex([f],method='ffill').iloc[0]
    if a=='BTC': x=-x
    if pd.isna(x) or abs(x)<0.0025: return 'neutral'
    return 'apoya' if x>0 else 'en contra'
lab=np.array(['']*len(O),dtype=object)
for i in np.flatnonzero(cr): lab[i]=etiqueta(act[i],fe.iloc[i])
print('idea 5: R por operación del REBOTE 4H según la etiqueta (ETH y BTC: pendiente ETH/BTC; altcoins: pendiente de la dominancia de BTC al revés)')
for a,b,nm in (('2018-05','2022','2018-21'),('2022','2027','2022-26'),('2024','2027','2024-26')):
    s=cr&(t>=a).values&(t<b).values
    print('  ',nm,' · '.join(f'{k}: {int((s&(lab==k)).sum())} op. {O.r_bruto[s&(lab==k)].mean():+.2f}' for k in ('apoya','neutral','en contra')))
