# Listas de referencia (NO se cargan junto a las demás)

`cripto_realista_sin_tercio_vol10` (y su diaria) es el REBOTE 4H cripto con la regla «sin venta del tercio con la volatilidad de BTC en su 10 % más bajo». **Repite los `id` de `MOTOR/listas/cripto_realista`** (que el motor rebautiza como `cripto` al cargarla; la `cripto.parquet` original pasa a llamarse `cripto_24h`): si se cargan las dos a la vez, el motor no valora bien la cripto y la base no da 6,14 / 5,61 / 7,04.

Se movió aquí el 1-nov-2026 para que ningún cargador que lea `MOTOR/listas_reconstruidas/*.parquet` la meta por error. Úsala solo **en lugar de `cripto_realista`** (quitando esa del cargador), nunca a la vez. Ejemplo: `ESTUDIOS_MEJORAS_2026_11_02/base.py`. **Ojo:** las cifras de base del registro (6,14 y 6,26) NO llevan esta regla; con ella, la base vigente del 2-nov es 6,35 / 5,69 / 7,36.

`corto_sector_reconstruida`: CORTO SECTOR rehecho el 28-oct (530 operaciones). Solo referencia; la vigente es `MOTOR/listas/corto_sector`.
