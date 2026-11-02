import sys, hashlib
exec(open('gen.py').read().split("O0=pd.read_parquet")[0])
sys.path.insert(0,'/home/claude/mej'); from h import cartera, mascaras, evalua, met24, comun
O0=pd.read_parquet('/home/claude/velas-backtest/MOTOR/listas/cripto_realista.parquet'); Xc={}
def corre(f):
    ST['f']=f; T=U.todas(U.listas(realista=True,Xc=Xc)); O,D=U.a_lista(T,plantilla=O0)
    C=cartera(O,D); M=mascaras(C); _,e,q=evalua(C,M['BASE'],M['EX']); return C,e,q
C0,e0,q0=corre(None); print('v0',C0.fmt(q0),flush=True)
def ep(C,e): return ' '.join(f"{comun.met_eq(e,pd.Timestamp(a),pd.Timestamp(b))['ratio']:.2f}" for a,b in [('2018-01-01','2020-01-01'),('2020-01-01','2022-01-01'),('2022-01-01','2024-01-01'),('2024-01-01','2026-12-31')])
print('épocas v0', ep(C0,e0),flush=True)
C,e,q=corre(c_pts); print('puntos',C.fmt(q),'| épocas',ep(C,e),'| boot',round(C.bootstrap(e0,e,500),2),flush=True)
for a in ['BTC','ETH','ADA','ZEC','LINK']:
    C,e,q=corre(lambda P,t,i,a=a: c_pts(P,t,i) and P['a']!=a)
    print(f'puntos salvo {a}',C.fmt(q),'PASA' if all(q[k]['ratio']>q0[k]['ratio'] for k in range(3)) else '-',flush=True)
p=float(sys.argv[1]); res=[]
for s in range(20):
    def f(P,t,i,s=s):
        if P['a']=='SOL': return False
        h=int(hashlib.md5(f"{s}-{P['a']}-{t}".encode()).hexdigest(),16)%10000/10000; return h<p
    C,e,q=corre(f); res.append([q[k]['ratio'] for k in range(3)]); print('placebo',s,C.fmt(q),flush=True)
res=np.array(res); print('placebo media',res.mean(0).round(2),'máx',res.max(0).round(2),flush=True)
