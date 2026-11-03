from ver import *
v=V(True); O=v.O; L=v.L; b=v.base
for fam in ['cripto','petroleo','x_petroleo','corto_petroleo','c10','shy','bolsa_e1','metales','corto_sector','corto_indices_credito','yt_connors_qqq']:
    m=b&(L==fam); o=O[m]
    lag=(o.t_entrada-o.t_senal).dt.total_seconds()/3600
    rb=pd.to_numeric(o.r_bruto,errors='coerce')
    cost=(rb*o.tam_R-o.r_final) if fam!='x' else None
    print(f'{fam:22s} n={m.sum():4d} entrada-señal h: min {lag.min():.1f} med {lag.median():.1f} | ent==señal {int((lag==0).sum())} | r_bruto*tam - r_final media {np.nanmean(rb*o.tam_R-o.r_final):.3f} | salida>HOY {(o.t_salida>HOY).sum()} | cols coste {[c for c in o.columns if "cost" in c.lower() or "comis" in c.lower() or "swap" in c.lower() or "financ" in c.lower()]}')
cp=O[(L=='corto_petroleo')]
print(cp[['r_bruto','tam_R','r_final']].head(8))
print('días de la semana señales corto_pet:',cp.t_senal.dt.day_name().value_counts().to_dict())
print('columnas corto_petroleo:',pd.read_parquet('/home/claude/velas-backtest/MOTOR/listas/corto_petroleo.parquet').columns.tolist())
d=pd.read_parquet('/home/claude/velas-backtest/MOTOR/listas/corto_petroleo_diario.parquet'); print(d.columns.tolist(), len(d))
# ¿el diario arranca el día de entrada o antes?
dd=d.merge(cp[['id','t_entrada','t_salida']],on='id'); dd['fecha']=pd.to_datetime(dd.fecha)
print('diario antes de entrada:',(dd.fecha.dt.normalize()<dd.t_entrada.dt.normalize()).sum(),' después de salida:',(dd.fecha.dt.normalize()>dd.t_salida.dt.normalize()).sum())
