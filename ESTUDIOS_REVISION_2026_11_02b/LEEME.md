# ESTUDIOS_REVISION_2026_11_02b

Código del estudio del 2-nov (noche): base fiel a las reglas vigentes del REBOTE 4H cripto, K8, piso, salida neta de BTC y freno.

- `base.py`: monta la base vigente (máscara `BASE|cn`, exentas `ex|E1|cn`) con la lista `cripto_realista_sin_tercio_vol10` (de `MOTOR/listas_reconstruidas/referencia/`) en lugar de `cripto_realista`. `VOL10=0` usa la lista del motor sin cambiar.
- `sim2.py`: copia de `Motor.simular` con ganchos (freno continuo, factor por operación). Sin ganchos da lo mismo que el motor.
- `lab.py`, `fiel.py`, `rob2.py`: reescalado de los tamaños cripto (`tam_mult` = nuevo ÷ viejo).
- `k8c.py`: rejilla final (K8, piso, BTC salida neta, E1 y Connors dentro o fuera del freno, placebo).
- Resto: pruebas descartadas (freno multinivel, histéresis, pesos por subseñal, enfriamiento, correlación, 24 h, diversificadores).
- `verificacion_b/`: código del segundo verificador independiente.

Ejecutar desde esta carpeta: `python3 k8c.py`.
