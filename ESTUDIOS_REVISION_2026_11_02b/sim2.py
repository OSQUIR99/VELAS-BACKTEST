"""Copia del Motor.simular con ganchos: freno continuo, factor de freno por operación y registro del estado."""
import heapq, numpy as np
from collections import defaultdict
import sys; import os; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','MOTOR'))
import motor as MO
def simular2(M, cfg, mascara, f_freno_fn=None, freno_op=None, log=False):
    cfg=dict(cfg); tope_t=cfg.get('tope_total',MO.TOPE_TOTAL); tope_b=cfg.get('tope_bloque',MO.TOPE_BLOQUE)
    umbral=cfg.get('umbral_bloque',MO.UMBRAL_BLOQUE); max_op=cfg.get('max_op',MO.MAX_OP); freno=cfg.get('freno',MO.FRENO)
    mult=cfg.get('mult',1.0); tam_mult=cfg.get('tam_mult'); prioridad=cfg.get('prioridad','llegada')
    n=len(M.rf); cand=np.asarray(mascara,bool).copy(); idxs=np.flatnonzero(cand)
    s=np.zeros(n); motivo=np.array(['']*n,dtype=object); abiertas={}; salidas=[]; cerrado=0.0; pico_l=0.0
    ddlog=np.full(n,np.nan)
    claves=(M.t_ent[idxs].astype('datetime64[h]')).astype(np.int64); pos=0; N=len(idxs)
    while pos<N:
        q=pos
        while q<N and claves[q]==claves[pos]: q+=1
        grupo=list(idxs[pos:q]); pos=q; t=M.t_ent[grupo[0]]; dia=M.ent_dia[grupo[0]]
        while salidas and salidas[0][0]<=t:
            ts,k=heapq.heappop(salidas)
            if k in abiertas:
                sz=abiertas.pop(k)
                if not M.sin_freno[k]: cerrado+=sz*M.rf[k]
        eq_l=cerrado+sum(abiertas[j]*M.latente(j,dia) for j in abiertas if not M.sin_freno[j])
        pico_l=max(pico_l,eq_l); dd=pico_l-eq_l
        if f_freno_fn is not None: f_fr=f_freno_fn(dd)
        else: f_fr=freno[1] if (freno and dd>=freno[0]) else 1.0
        if len(grupo)>1 and prioridad!='llegada': grupo=M._ordenar(grupo,abiertas,prioridad,M.tb[grupo[0]])
        for k in grupo:
            ddlog[k]=dd
            base=mult*(tam_mult[k] if tam_mult is not None else 1.0)
            ff=f_fr
            if freno_op is not None and f_fr<1.0: ff=freno_op(k,f_fr)
            sz=base*(ff if not M.sin_freno[k] else 1.0)
            if max_op and sz*M.tam[k]>max_op: sz=max_op/M.tam[k]
            if sz<=0: motivo[k]='tamaño 0'; continue
            r_new=sz*M.r0[k]
            if tope_t is not None:
                usado=sum(abiertas[j]*M.riesgo(j,dia) for j in abiertas)
                if r_new>tope_t-usado+1e-9: motivo[k]='tope 20 R'; continue
            if tope_b is not None and abiertas:
                if M._riesgo_bloque(k,sz,abiertas,M.tb[k],dia,umbral)>tope_b+1e-9: motivo[k]='tope bloque'; continue
            s[k]=sz; abiertas[k]=sz; heapq.heappush(salidas,(M.t_sal[k],k))
    return s,motivo,ddlog
