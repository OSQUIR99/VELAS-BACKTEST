from base import *
cs=(L=='corto_sector')&W; ci=(L=='corto_indices_credito')&W
def run(nom,mask,exentas,tb31,x2):
    C.usar_base_31oct=tb31
    tb=C.tam_base.copy()
    if not x2: C.tam_base[cs|ci]=1.0
    rr,eq=C.sim(mask,exentas=exentas); print(f'{nom:60s}',C.fmt(C.met3(eq)),flush=True)
    C.tam_base=tb
run('27-oct: núcleo + corto_sector exento, sin tope SHY, x1',nucleo|cs,cs,False,False)
run('27-oct + corto índices exento (x1)',nucleo|cs|ci,cs|ci,False,False)
run('31-oct: tope SHY + cortos x2 (sin índices)',nucleo|cs,cs,True,True)
run('31-oct: tope SHY + cortos x2 + índices',nucleo|cs|ci,cs|ci,True,True)
run('31-oct completa + N1',nucleo|cs|ci|n1,cs|ci,True,True)
