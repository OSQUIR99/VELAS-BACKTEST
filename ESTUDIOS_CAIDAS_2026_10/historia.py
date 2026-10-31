import numpy as np, pandas as pd
F=pd.read_parquet('factores.parquet')
L='/home/claude/velas-backtest/MOTOR/listas/'
def welch(a,b):
    va,vb=a.var(ddof=1)/len(a),b.var(ddof=1)/len(b); return (a.mean()-b.mean())/np.sqrt(va+vb)
def tabla(o, factores, nombre):
    o=o.copy(); o['u']=o.r_final/o.tam_R; d0=pd.to_datetime(o.t_entrada).dt.normalize()
    for c in factores: o[c]=F[c].reindex(d0).values
    print('\n==', nombre, len(o), 'operaciones', o.t_entrada.min().date(), '→', o.t_entrada.max().date())
    eps=[('antes de 2010',None,'2010-01-01'),('2010-2018',  '2010-01-01','2018-05-01'),('2018-2021','2018-05-01','2022-01-01'),('2022-2026','2022-01-01',None)]
    for c in factores:
        txt=[]
        for nm,a,b in eps:
            g=o[o[c].notna()]
            if a: g=g[g.t_entrada>=a]
            if b: g=g[g.t_entrada<b]
            on=g[g[c]==1].u; off=g[g[c]==0].u
            if len(on)>=5 and len(off)>=5: txt.append(f'{nm}: {on.mean():+.2f} ({len(on)}) vs {off.mean():+.2f} ({len(off)})  t {welch(on,off):+.1f}')
            else: txt.append(f'{nm}: pocos ({len(on)})')
        print(f'  {c:26s}', ' | '.join(txt))
p=pd.read_parquet(L+'petroleo.parquet'); p=p[p.direccion==1]
tabla(p,['tipos_suben','dolar_sube','liquidez_baja','liquidez_cae13','liquidez_impulso_bajo50','btc_bajo200','spx_bajo200','vix_alto'],'PETRÓLEO LARGO (L1, L2, L3, tras noticia)')
for s_ in ['L1','L2','L3']:
    tabla(p[p.senal==s_],['tipos_suben','dolar_sube','liquidez_baja'],f'petróleo {s_}')
e=pd.read_parquet(L+'bolsa_e1.parquet'); e=e[e.activo.isin(['SPX','NDX','DJI'])]
tabla(e,['liquidez_impulso_bajo50','liquidez_baja','liquidez_cae13','tipos_suben','dolar_sube','vix_alto','B21_semis_flojos','credito_flojo','amplitud_baja','FOMC_cerca','CPI_cerca','btc_cae7','spx_cae5','vix_salto'],'E1 ÍNDICES (S&P, Nasdaq, Dow)')
m=pd.read_parquet(L+'metales.parquet'); m=m[m.activo=='oro']
tabla(m,['liquidez_impulso_bajo50','liquidez_baja','tipos_suben','dolar_sube','financiacion_alta'],'ORO')
c=pd.read_parquet(L+'cripto_realista.parquet')
tabla(c,['liquidez_impulso_bajo50','liquidez_baja','tipos_suben','dolar_sube','vix_alto','spx_bajo200','financiacion_alta','btc_bajo200','FOMC_cerca','CPI_cerca'],'CRIPTO REBOTE 4H')
