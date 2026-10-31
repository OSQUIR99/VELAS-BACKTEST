exec(open('pruebas.py').read().split("filas=[]")[0])
cfg=dict(freno=(999,1.0),freno_modo='latente',prioridad='descorr')
for nb,base in (('con N1',BASE|n1),('sin N1',BASE)):
    r0,e0=C.sim(base,cfg=cfg); q0=C.met3(e0)
    for nr,v in (('B21 mitad',dict(tam=np.where(resto&b21,0.5,1.0))),('E1e',dict(mask=base&e1_una(base))),('BTC semanal impulso',dict(mask=base|((L=='btc_sem_impulso')&W))),
                 ('LINK x0,5 baja',dict(tam=np.where(FAM['LINK']&baja,0.5,1.0))),('C10 x1,5 alta',dict(tam=np.where(FAM['C10']&alta,1.5,1.0)))):
        r,e=C.sim(v.get('mask',base),cfg=cfg,tam_mult=v.get('tam')); q=C.met3(e)
        print(nb,f'{nr:22s}',' / '.join(f"{q[i]['ratio']-q0[i]['ratio']:+.2f}" for i in range(3)),'pasa' if all(q[i]['ratio']>q0[i]['ratio'] for i in range(3)) else 'no',flush=True)
