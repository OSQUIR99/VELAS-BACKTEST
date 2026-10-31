exec(open('/home/claude/vol2/salida.py').read().split("for thr in")[0])
for thr in [0.05,0.075,0.1,0.125,0.15]:
    evaluar(f'BTC vol ≤{thr}: sin venta de 1/3',lambda c,thr=thr:(bp<=thr).to_dict())
# solo «sin venta» pero manteniendo el stop a la entrada: ya es así. Variante: vender 1/3 en +2R en vez de +1R
