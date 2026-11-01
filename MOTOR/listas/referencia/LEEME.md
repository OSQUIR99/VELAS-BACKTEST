# Listas de referencia (NO se cargan en el motor)

`petroleo_con_s1` y `petroleo_con_s1_diario` son el petróleo con la entrada corta S1, que desde el 27-oct-2026 sustituye el CORTO PETRÓLEO. Comparten los `id` con `MOTOR/listas/petroleo`: si se cargan a la vez, el motor no valora el petróleo día a día (la base da 5,76 en vez de 6,14).

Se movieron aquí el 1-nov-2026 para que ningún cargador que lea `MOTOR/listas/*.parquet` las meta por error. Solo para comparar.
