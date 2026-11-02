from lab import *
sys.path.insert(0,RAIZ); from cargar import velas
cr=(L=='cripto')
tam=O.tam_R.values.astype(float)
lm=O.linea_mult.values.astype(float) if 'linea_mult' in O else np.ones(len(O))
sn=O.salida_neta.fillna(False).values.astype(bool); niv=O.nivel.fillna(True).values.astype(bool)
sob=O.sobrecalentamiento.fillna(False).values.astype(bool)
# tendencia frágil: cierre semanal (semana cerrada anterior) > media de 40 semanas y línea con impulso ≤ 50 (linea_mult ≤ 1)
fragil=np.zeros(len(O),bool)
for a in ['BTC','ETH','ADA']:
    dd=velas(a,'1d').cierre; w=dd.resample('W-SUN').last(); sma=w.rolling(40).mean(); enc=(w>sma)
    enc.index=enc.index+pd.Timedelta(days=1)   # usable desde el lunes siguiente
    m=cr&(act==a); te=pd.DatetimeIndex(O.t_entrada.values[m]).tz_localize(None) if pd.DatetimeIndex(O.t_entrada.values[m]).tz is not None else pd.DatetimeIndex(O.t_entrada.values[m])
    v=enc.reindex(enc.index.union(te)).ffill().reindex(te).fillna(False).values.astype(bool)
    fragil[np.flatnonzero(m)]=v&(lm[m]<=1.0)
def tm_fiel(btc_sn=False, solo_reduce=True, con_fragil=True, quitar_nivel_btc=False, sobre=None):
    w=np.ones(len(O))
    m=cr&(act=='BTC')&sn
    if not btc_sn: w[m]/=1.5
    if solo_reduce: w[cr&(lm>1)]/=lm[cr&(lm>1)]
    if con_fragil: w[cr&fragil]*=0.5
    if quitar_nivel_btc: w[cr&(act=='BTC')&~niv]*=2.0
    if sobre is not None: w[cr&sob]*=sobre
    # piso 1/4 R y techo 5 R sobre el tamaño nuevo
    nt=np.where(cr,tam*w,tam); nt=np.where(cr,np.clip(nt,0.25,5.0),nt)
    return np.where(tam>0,nt/np.maximum(tam,1e-9),1.0)
if __name__=='__main__':
    print('frágil en cripto',int((cr&fragil&BASEV).sum()),'de',int((cr&BASEV).sum()))
    s0,e0,_=run(); print(linea('lista del motor (BTC sn ×1,5, línea hasta ×2, sin frágil)',e0))
    tf=tm_fiel(); s,e,_=run(tm=tf); ref=C.met3(e); print(linea('FIEL a las reglas de hoy',e)); 
    V={'fiel + BTC salida neta ×1,5 (reactivar)':tm_fiel(btc_sn=True),
       'fiel + línea hasta ×2 (como antes)':tm_fiel(solo_reduce=False),
       'fiel sin tendencia frágil':tm_fiel(con_fragil=False),
       'fiel + BTC sin nivel a ×1 (quitar ×0,5)':tm_fiel(quitar_nivel_btc=True),
       'fiel + sobrecalentamiento ×0,5':tm_fiel(sobre=0.5),
       'fiel + sobrecalentamiento ×0,75':tm_fiel(sobre=0.75),
       'fiel + BTC sn ×1,5 + sobrecal ×0,5':tm_fiel(btc_sn=True,sobre=0.5),
       'fiel + BTC sn ×1,5 + sin nivel ×1':tm_fiel(btc_sn=True,quitar_nivel_btc=True),
       'fiel + BTC sn + sin nivel ×1 + sobrecal ×0,5':tm_fiel(btc_sn=True,quitar_nivel_btc=True,sobre=0.5)}
    for k,w in V.items():
        s,e,_=run(tm=w); print(linea(k,e,ref),flush=True)
