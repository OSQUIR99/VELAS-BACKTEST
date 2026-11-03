from lab import *
s0,e0,_=run(); ref=C.met3(e0); print(linea('base vigente',e0))
Q={'petróleo L2':(L=='petroleo')&(sen=='L2'),'petróleo L3':(L=='petroleo')&(sen=='L3'),'petróleo tras-noticia':(L=='petroleo')&np.array([str(x).startswith('tras') for x in sen]),
   'X3':(L=='x_petroleo')&(sen=='X3'),'X1':(L=='x_petroleo')&(sen=='X1'),'E1 DJI':(L=='bolsa_e1')&(act=='DJI'),'oro M2 1h':(L=='metales')&(sen=='M2 1h'),
   'oro rebote 4h':(L=='metales')&(sen=='rebote 4h'),'c10':(L=='c10'),'LINK':(L=='cripto')&(act=='LINK'),'corto_sector':(L=='corto_sector'),'corto_indices':(L=='corto_indices_credito')}
for nom,m in Q.items():
    for sz in [0.0,0.5]:
        tm=np.ones(len(O)); tm[m]=sz
        s,e,_=run(mask=BASEV&~m if sz==0 else BASEV,tm=None if sz==0 else tm); print(linea(f'{nom} {"fuera" if sz==0 else "×0,5"} (n={int((m&BASEV).sum())})',e,ref),flush=True)
