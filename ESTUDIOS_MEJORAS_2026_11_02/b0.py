from h import *
O,D,n=sin_tercio(O0,D0,cond_base(O0)); print('modificadas',n)
C=cartera(O0.copy(),D0.copy()); M=mascaras(C); _,_,q=evalua(C,M['BASE'],M['ex']); print('31-oct + Connors dentro',C.fmt(q))
_,_,q=evalua(C,M['BASE'],M['EX']); print('fuera del freno (2-nov)',C.fmt(q))
C2=cartera(O,D); M2=mascaras(C2); _,e,q=evalua(C2,M2['BASE'],M2['EX']); print('NUEVA BASE: sin tercio + fuera del freno',C2.fmt(q))
