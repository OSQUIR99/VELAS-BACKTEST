# Base del estudio del 2-nov (noche). Ejecutar desde esta carpeta dentro de velas-backtest.
# VOL10=1 (por defecto) usa la lista cripto realista con la regla «sin venta del tercio» (referencia/).
import sys,warnings,os,tempfile; warnings.filterwarnings('ignore')
RAIZ=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,os.path.join(RAIZ,'ESTUDIOS_CAIDAS_2026_10')); import comun
if os.environ.get('VOL10','1')=='1':
    d=tempfile.mkdtemp(prefix='listas_v_'); src=os.path.join(RAIZ,'MOTOR','listas'); ref=os.path.join(RAIZ,'MOTOR','listas_reconstruidas','referencia')
    for f in os.listdir(src):
        if f.endswith('.parquet'): os.symlink(os.path.join(src,f),os.path.join(d,f))
    for suf in ['','_diario']:
        p=os.path.join(d,f'cripto_realista{suf}.parquet'); os.remove(p)
        os.symlink(os.path.join(ref,f'cripto_realista_sin_tercio_vol10{suf}.parquet'),p)
    comun.LISTAS_GH=d
sys.path.insert(0,os.path.join(RAIZ,'ESTUDIOS_REVISION_2026_11_02'))
from base2 import *
from comun import met_eq
BASEV=BASE|cn; EXV=ex|E1|cn   # base vigente 2-nov: E1 y Connors fuera del freno
def corre(m=BASEV,x=EXV,**kw):
    r,e=C.sim(m,exentas=x,**kw); return r,e
def resumen(e,nom=''):
    q=C.met3(e); q2=[met_eq(e,pd.Timestamp(a)) for a in ['2024-01-01','2025-01-01']]
    return f"{nom:40s} {C.fmt(q)} | 24-26 {q2[0]['ratio']:.2f} 25-26 {q2[1]['ratio']:.2f}"
if __name__=='__main__':
    r,e=corre(); print(resumen(e,'base vigente'))
