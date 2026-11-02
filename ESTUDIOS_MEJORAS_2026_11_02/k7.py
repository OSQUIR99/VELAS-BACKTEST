from base import *
from exp2 import FAM
def tm_k2():
    t=np.ones(len(O)); t[FAM['corto_pet']]=2; t[FAM['petroleo']]=0.75; t[FAM['x_petroleo']]=0.75; return t
def tm_k7():
    s=O['senal'].astype(str).values
    t=np.ones(len(O)); t[FAM['corto_pet']]=2; t[FAM['x_petroleo']]=0.75; t[(L=='petroleo')&(s!='L1')]=0.5; return t
def tm_k8():
    """APLICADA (2-nov-2026): corto petróleo x2, X1/X3 x0,75, petróleo L2 y tras-noticia (bajada) x0,5; L1 y L3 x1.
    Elegida solo con 2018-21 (verificador independiente)."""
    s=O['senal'].astype(str).values
    t=np.ones(len(O)); t[FAM['corto_pet']]=2; t[FAM['x_petroleo']]=0.75
    t[(L=='petroleo')&np.isin(s,['L2','tras-noticia (bajada)'])]=0.5; return t
