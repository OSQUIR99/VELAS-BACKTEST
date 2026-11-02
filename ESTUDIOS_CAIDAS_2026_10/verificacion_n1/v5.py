import sys; sys.path.insert(0,'/home/claude/caidas')
import numpy as np, pandas as pd
from comun import Cartera, LISTAS_CORTOS
C=Cartera(extra=(LISTAS_CORTOS,'/home/claude/caidas/listas_nuevas'))
O=C.O; L=C.L
print('hueco' in O.columns, 'tam_R' in O.columns)
shy=L=='shy'; S=O[shy].copy()
print('SHY ops',shy.sum(), S[['entrada','sl_inicial','tam_R','r_final']+(['hueco'] if 'hueco' in O.columns else [])].describe().round(4).to_string())
print('tam_base shy', pd.Series(C.tam_base[shy]).describe().round(3).to_string())
print('short x2:',np.unique(C.tam_base[C.cortos_exentos]), 'others !=1:', ((C.tam_base!=1)&~shy&~C.cortos_exentos).sum())
nm=(L=='n1_vixvxv')&(O.t_entrada>=C.desde).values
for cfg in (False,True):
    C.usar_base_31oct=cfg
    for v in list(C.bases)[:2]:
        b=C.bases[v]; rb,eb=C.sim(b); rn,en=C.sim(b|nm)
        rf=O.r_final.values
        print(cfg,v[0],'n1 executed',(rn.s[nm]>0).sum(),'/',nm.sum(),'n1 R',(rn.s[nm]*rf[nm]).sum().round(2),'motivos', pd.Series(rn.motivo[nm]).value_counts().to_dict())
        dl=pd.Series((rn.s-rb.s)*rf,index=L)[~nm]; 
        print('   displaced others R by lista:',dl.groupby(level=0).sum().round(2)[lambda x:abs(x)>0.05].to_dict(),'changed ops',((rn.s!=rb.s)&~nm).sum())
C.usar_base_31oct=True
for v in list(C.bases)[:2]:
    b=C.bases[v]; rb,eb=C.sim(b); rn,en=C.sim(b|nm); rf=O.r_final.values
    ch=np.flatnonzero((rn.s!=rb.s)&~nm)
    X=O.iloc[ch][['lista','activo','t_entrada','r_final']].copy(); X['s_base']=rb.s[ch]; X['s_new']=rn.s[ch]; X['mot_new']=rn.motivo[ch]; X['dR']=(X.s_new-X.s_base)*X.r_final
    print(v[0]); print(X.round(3).to_string())
    # per-year contribution of n1 vs others
    print('dd episodes base vs new: maxDD dates', (eb.cummax()-eb)[eb.index>=C.desde].idxmax(), (en.cummax()-en)[en.index>=C.desde].idxmax())
