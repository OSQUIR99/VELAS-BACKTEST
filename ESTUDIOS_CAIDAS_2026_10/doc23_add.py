import sys
txt = open('doc23_actual.md').read()
viejo = "Versión 1.2 · 27 de octubre de 2026, 09:00 (base del backtest corregida a 4,83 y cortos aceptados, documento 25)"
nuevo = "Versión 1.3 · 28 de octubre de 2026, 02:30 (B21 suspendida; reglas para bajar la caída, ninguna pasa) · " + viejo
assert viejo in txt
txt = txt.replace(viejo, nuevo, 1)
add = """- **28-oct · B21 (aplicada el 27-oct) → solo aviso** (`backtests/2026-10-28-causas-caidas-e1-y-b21.md`): con los cortos en la base ya no pasa (versión más parecida a la real: 6,63 → 6,32; R/año 62,9 → 60,0; la caída no baja). Se repite el sábado con las listas de petróleo corregidas. Ojo de método: B21 ya bajaba el R/año el 27-oct; se aceptó solo por el ratio. **A partir de ahora se aplica la regla completa del apartado 2.3 (sube el ratio Y sube el R/año).**
- **28-oct · Bajar la caída:** 27 reglas (frenos de E1, filtros de petróleo, topes de cripto en racimo, freno a 3 o 6 R, proteger la ganancia abierta, seguro de la cartera) y IBS en SPY: **ninguna pasa en las tres versiones de la base** (documento 22, v1.3). Las caídas llegan tras rachas muy buenas y son, a partes casi iguales, ganancia abierta devuelta y entradas nuevas que salen mal. **Con estas señales, unos 9-10 R de caída es el suelo:** para bajarlo hacen falta señales nuevas que no se muevan con la cripto.
- **Aviso de datos (28-oct):** las listas corregidas del petróleo y las de los cortos no están en GitHub ni en Drive; el estudio del 28-oct rehízo los cortos de bolsa con su definición escrita y midió con tres versiones de la parte del petróleo. Pendiente: subirlas a `MOTOR/listas` de VELAS-BACKTEST.
"""
txt = txt.rstrip('\n') + '\n' + add
open('doc23_nuevo.md', 'w').write(txt)
print('ok', len(txt))
