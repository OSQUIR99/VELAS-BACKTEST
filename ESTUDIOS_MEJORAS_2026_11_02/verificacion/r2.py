from ver import *
v=V(True); O=v.O; L=v.L
s0=np.load('s_B0.npy'); s6=np.load('s_K6.npy'); m6=np.load('mot_K6.npy',allow_pickle=True); m0=np.load('mot_B0.npy',allow_pickle=True)
cp=np.flatnonzero((L=='corto_petroleo')&v.base)
print('corto_petroleo total en lista',(L=='corto_petroleo').sum(),'en ventana',len(cp))
pd.set_option('display.width',250)
T=O.loc[cp,['id','activo','senal','direccion','t_senal','t_entrada','t_salida','tam_R','riesgo_inicial_R','r_final','mae_R','motivo_salida','bloque']].copy()
T['s_B0']=s0[cp];T['s_K6']=s6[cp];T['mot_B0']=m0[cp];T['mot_K6']=m6[cp]
T['R_B0']=s0[cp]*O.r_final.values[cp]; T['R_K6']=s6[cp]*O.r_final.values[cp]; T['riesgoR_K6']=s6[cp]*O.riesgo_inicial_R.values[cp]
print(T.to_string())
print('suma R B0',T.R_B0.sum().round(2),'K6',T.R_K6.sum().round(2))
# lista completa: estadísticas
c=O[L=='corto_petroleo']; print('lista completa desde',c.t_entrada.min(),'n',len(c),'R/op',c.r_final.mean().round(3))
print(c.groupby(c.t_entrada.dt.year).r_final.agg(['count','sum']).round(2).T)
