# -*- coding: utf-8 -*-
"""Segunda tanda (alternativas sobre lo mismo, punto 5 del documento 23):
  PS · «seguro de la ganancia abierta»: si la cartera valorada cae x R desde su máximo, se cierran las operaciones abiertas
       que van ganando más de +1 R por unidad (se cobra lo ganado) al cierre de ese día. x = 5 y 7 R.
  E1f · E1 × 1,5 cuando la línea con impulso está ≥ 50 (dar más a las buenas en vez de quitar a las malas).
  P6 · petróleo largo × 1,5 si el dólar no sube y la línea está ≥ 33.
Mismas reglas de juicio que reglas.py."""
import copy
import numpy as np, pandas as pd
import reglas as R
from comun import HOY

C, M, O = R.C, R.M, R.O


def seguro_ganancia(base, x, umbral_u=1.0, iteraciones=20):
    """Cierra al cierre del día t las operaciones con latente ≥ umbral (por unidad) si la cartera valorada está ≥ x R bajo su máximo.
    Se repite hasta que el conjunto de cierres no cambia (convergencia; corrección de la verificación del 28-oct)."""
    Mx = M
    previo = None
    for _ in range(iteraciones):
        rr, eq = C.sim(base, M=Mx)
        s = rr.s
        e = eq.values; pk = np.maximum.accumulate(e); dd = pk - e
        dias_disparo = set(np.flatnonzero(dd >= x))
        M2 = copy.copy(M); M2.rf = M.rf.copy(); M2.sal_dia = M.sal_dia.copy(); M2.t_sal = M.t_sal.copy()
        d0 = pd.Timestamp(M.dia0)
        cambios = 0
        for k in np.flatnonzero(s > 0):
            if k not in M.lat:
                continue
            d, v, _ = M.lat[k]
            m = d < M.sal_dia[k]
            d, v = d[m], v[m]
            u = v / max(M.tam[k], 1e-9)
            for i in range(len(d)):
                if d[i] in dias_disparo and u[i] >= umbral_u:
                    M2.sal_dia[k] = d[i]; M2.rf[k] = v[i]
                    M2.t_sal[k] = np.datetime64(d0 + pd.Timedelta(days=int(d[i]), hours=23)); cambios += 1
                    break
        firma = tuple(np.flatnonzero(M2.sal_dia != M.sal_dia))
        Mx = M2
        if firma == previo:
            break
        previo = firma
    return Mx, cambios


if __name__ == '__main__':
    F = R.F
    filas = []
    for nb, base in C.bases.items():
        rb, eqb = C.sim(base); qb = C.met3(eqb); m5b, _ = C.media5(eqb)
        print(f'\n{nb} BASE', C.fmt(qb), '| media5', round(m5b, 1), flush=True)
        V = {}
        for x in (5, 7):
            V[f'PS seguro de la ganancia abierta: cartera −{x} R → cobrar lo que gana > +1 R'] = dict(prot=x)
        V['E1f E1 × 1,5 con la línea con impulso ≥ 50'] = dict(tam=np.where(R.E1 & ~R.on_at_entry('liquidez_impulso_bajo50'), 1.5, 1.0))
        buena = R.PET_L & ~R.on_at_entry('dolar_sube') & ~R.on_at_entry('liquidez_baja')
        V['P6 petróleo largo × 1,5 sin dólar al alza y con línea ≥ 33'] = dict(tam=np.where(buena, 1.5, 1.0))
        for nr, v in V.items():
            MM = M; extra = ''
            if 'prot' in v:
                MM, nc = seguro_ganancia(base, v['prot']); extra = f' ({nc} cerradas antes)'
            rr, eq = C.sim(base, tam_mult=v.get('tam'), M=MM)
            q = C.met3(eq); m5, _ = C.media5(eq); ok = C.pasa(q, qb); bt = C.bootstrap(eqb, eq, n=500)
            esc = q[0]['R_ano'] * qb[0]['caida'] / q[0]['caida']
            filas.append(dict(base=nb, regla=nr, r=q[0]['ratio'], r1821=q[1]['ratio'], r2226=q[2]['ratio'], Ra=q[0]['R_ano'],
                              Ra1821=q[1]['R_ano'], Ra2226=q[2]['R_ano'], caida=q[0]['caida'], media5=m5, pasa=ok, boot=bt, Ra_misma_caida=esc))
            print(f'  {nr[:70]:70s}', C.fmt(q), f'| media5 {m5:.1f} | escalada {esc:.1f}', '| PASA' if ok else '| no', f'| boot {bt:.2f}{extra}', flush=True)
    pd.DataFrame(filas).to_csv('/home/claude/caidas/reglas2.csv', index=False)
