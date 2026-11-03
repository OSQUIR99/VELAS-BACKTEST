from ev import *
res={}
for nm in ['C_base','C_i2','C_i3','C_i4']:
    C=cartera(nm); M=mascaras(C); e,q=run(C,M['BASE'],M['EX'])
    if nm=='C_base': e0,q0,C0=e,q,C
    linea(C,nm,e,q,e0,q0,boot=(nm!='C_base'))
    try: print('   media5',C.media5(e))
    except Exception as x: print('   media5 err',x)
    res[nm]=(C,e,q)
