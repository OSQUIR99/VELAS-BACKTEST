from ver import *
import itertools
print('=== TERCIO=0')
w=V(False)
assert (w.L=='cripto').sum()>0
qb=None
for n,tm in (('B0',w.mult()),('K6',w.mult(corto_pet=2)),('K2',w.mult(2,0.75,0.75)),('K7',w.mult(2,1,0.75,pet_no_L1=0.5))):
    for fz in ((4,0.5),(3,0.5),(5,0.5),(4,0.75)):
        _,e=w.sim(tm,freno=fz); q=tres(e,w.desde)
        if n=='B0': globals()['b'+str(fz)]=q
        ref=globals()['b'+str(fz)]
        print(f'{n} freno {fz}',fmt(q),'PASA' if n!='B0' and all(q[i][2]>ref[i][2] for i in range(3)) else '')
print('=== prueba justa K7 (TERCIO=1): elegir recortes del petróleo por señal mirando solo 2018-21')
v=V(True); L=v.L; sen=v.sen
_,e0=v.sim(v.mult()); q0=tres(e0,v.desde)
SEN=['L1','L2','L3','tras-noticia (bajada)','tras-noticia (subida)']
def tm_of(ws):
    t=v.mult(2,1,0.75)
    for s_,x in ws.items(): t[(L=='petroleo')&(sen==s_)]=x
    return t
# (a) regla simple: recortar a 0,5 las señales con R/op < 0,25 en 2018-21 (L2 0,15; tras-noticia bajada -0,14); subida sin datos -> 1
ws={'L2':0.5,'tras-noticia (bajada)':0.5}
_,e=v.sim(tm_of(ws)); q=tres(e,v.desde); print('K7-justa (L2 y tras-noticia bajada x0,5; L1 y L3 x1)',fmt(q),'PASA' if all(q[i][2]>q0[i][2] for i in range(3)) else '-')
ws2={'L2':0.5,'tras-noticia (bajada)':0.5,'tras-noticia (subida)':0.5}
_,e=v.sim(tm_of(ws2)); q=tres(e,v.desde); print('K7-justa + subida x0,5',fmt(q),'PASA' if all(q[i][2]>q0[i][2] for i in range(3)) else '-')
# (b) búsqueda por coordenadas por señal entrenada en 2018-21
VAL=[0.5,0.75,1.0,1.25]
ws={s_:1.0 for s_ in SEN[:4]}
def sc(ws): _,e=v.sim(tm_of(ws)); return tres(e,v.desde)
best=sc(ws)[1][2]
for it in range(3):
    cam=False
    for s_ in ws:
        for x in VAL:
            if x==ws[s_]: continue
            w2=dict(ws); w2[s_]=x; r=sc(w2)[1][2]
            if r>best+0.01: best,ws,cam=r,w2,True
    if not cam: break
q=sc(ws); print('búsqueda 2018-21 por señal ->',ws,fmt(q),'PASA' if all(q[i][2]>q0[i][2] for i in range(3)) else '-')
# K2 frente a la versión x_pet sola / pet solo
for nom,tm in (('corto x2 + pet x0,75 (K1)',v.mult(2,0.75,1)),('corto x2 + x_pet x0,75',v.mult(2,1,0.75)),('K2',v.mult(2,0.75,0.75)),('corto x2 + pet x0,5 + x_pet x0,75 (lo que dio la búsqueda)',v.mult(2,0.5,0.75)),('K7',v.mult(2,1,0.75,pet_no_L1=0.5))):
    _,e=v.sim(tm); q=tres(e,v.desde); print(f'{nom:60s}',fmt(q),'PASA' if all(q[i][2]>q0[i][2] for i in range(3)) else '-')
# pesos_1 completos (entrenados 2018-21) fuera de muestra
import json
p=json.load(open('/home/claude/mej/pesos_1.json'))
t=np.ones(len(v.O)); act=v.act
FAM={'cripto':(L=='cripto'),'petroleo':(L=='petroleo'),'x_petroleo':(L=='x_petroleo'),'c10':(L=='c10'),'shy':(L=='shy'),'E1':(L=='bolsa_e1')&np.isin(act,['SPX','DJI','NDX']),'connors':(L=='yt_connors_qqq'),'oro':(L=='metales')&(act=='oro'),'corto_sector':(L=='corto_sector'),'corto_ind':(L=='corto_indices_credito'),'corto_pet':(L=='corto_petroleo')}
for f,m in FAM.items(): t[m]=p[f]
_,e=v.sim(t); q=tres(e,v.desde); print('pesos_1 completos (entrenados 2018-21)',fmt(q))
