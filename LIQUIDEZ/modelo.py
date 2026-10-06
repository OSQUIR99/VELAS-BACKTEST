import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
pd.set_option('display.width',250)
ev=pd.read_parquet('ev2.parquet')
e=ev[(ev.k==2.5)&ev.res.isin([1,-1])].copy()
e['giro']=(e.res==1).astype(int)
print('giro por n_toques'); print(e.groupby(e.n_toques.clip(upper=4)).giro.agg(['size','mean']).round(3))
e['log_edad']=np.log1p(e.edad); e['log_aprox_b']=np.log1p(e.aprox_barras)
e['dist_sig_c']=e.dist_sig.clip(upper=10); e['dist_op_c']=e.dist_opuesto.clip(upper=15).fillna(15)
e['apil_c']=e.apilados.clip(upper=10)
ANT=['n_toques','apil_c','log_edad','vel','aprox_tramo','log_aprox_b','presion','compr','tend','rsi','dist_sig_c','dist_op_c']
CONF=ANT+['prof','cierra_dentro']
e['fecha']=pd.to_datetime(e.fecha)
res=[]
for tf in ['1h','4h','1d','todas']:
    g=e if tf=='todas' else e[e.tf==tf]
    g=g.dropna(subset=ANT+['prof'])
    # partición temporal dentro de cada serie: 60% primero entrena, 40% final prueba
    corte=g.groupby(['activo','tf']).fecha.transform(lambda s: s.quantile(0.6))
    tr, te = g[g.fecha<=corte], g[g.fecha>corte]
    for nom,cols in [('anticipar',ANT),('con vela de rotura',CONF)]:
        for mn,m in [('logistica',make_pipeline(StandardScaler(),LogisticRegression(max_iter=500))),('arboles',HistGradientBoostingClassifier(max_depth=3,max_iter=150,learning_rate=0.05))]:
            m.fit(tr[cols].astype(float),tr.giro)
            p=m.predict_proba(te[cols].astype(float))[:,1]
            auc=roc_auc_score(te.giro,p)
            # rentabilidad: tomar E2 solo en el quintil superior de prob de giro
            te2=te.assign(p=p)
            top=te2[te2.p>=te2.p.quantile(0.8)]
            bot=te2[te2.p<=te2.p.quantile(0.2)]
            res.append(dict(tf=tf,info=nom,modelo=mn,n_prueba=len(te),AUC=round(auc,3),
                giro_top20=round(100*top.giro.mean(),1),giro_bot20=round(100*bot.giro.mean(),1),
                E2_top20=round(top.E2_R.mean(),3),E3_bot20=round(bot.E3_R.mean(),3),E2_todos=round(te.E2_R.mean(),3)))
print(pd.DataFrame(res).to_string())
# importancia: coeficientes logistica anticipar, todas
g=e.dropna(subset=ANT)
m=make_pipeline(StandardScaler(),LogisticRegression(max_iter=500)).fit(g[ANT].astype(float),g.giro)
print(pd.Series(m[-1].coef_[0],index=ANT).sort_values().round(3))
