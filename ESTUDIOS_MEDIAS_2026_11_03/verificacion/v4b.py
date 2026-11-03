import sys; sys.path.insert(0,'/home/claude/med')
from ev import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',20)
for v,(a,b) in [('C_m22',('2020-12-18','2020-12-24')),('C_base',('2020-12-18','2020-12-24')),('C_m18',('2020-06-01','2020-06-22')),('C_base',('2020-06-01','2020-06-22')),('C_base',('2020-09-01','2020-09-24'))]:
    C=cartera(cripto=v); M=mascaras(C); rr,e=C.sim(M['BASE'],exentas=M['EX'],tam_mult=k8(C)); O=C.O
    sel=(rr.s>0)&(O.t_salida>=a).values&(O.t_salida<b).values
    x=O[sel][['lista','activo','t_entrada','t_salida','r_final','motivo_salida']].copy(); x['s']=rr.s[sel]; x['contrib']=x.s*x.r_final
    print('==',v,a,b,'suma',round(x.contrib.sum(),2)); print(x.groupby('lista').contrib.agg(['sum','count']).round(2))
    print(x[x.lista=='cripto'].sort_values('t_salida').to_string()[:2500])
