from lab import *
s0,e0,_=run(); ref=C.met3(e0); print(linea('base vigente (cripto horario real)',e0))
W2=(O.t_entrada>=C.desde).values
c24=(L=='cripto_24h')&W2&O.operable.values if 'operable' in O else (L=='cripto_24h')&W2
cr=(L=='cripto')&BASEV
print('ops cripto',cr.sum(),'cripto_24h',c24.sum())
s,e,_=run(mask=(BASEV&~cr)|c24); print(linea('cripto 24 h (bot)',e,ref),flush=True)
sr=O['sin_revision'].fillna(False).astype(bool).values
print('24h con sin_revision',(c24&sr).sum())
