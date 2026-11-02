# Estudio «causas de las caídas» y señales nuevas (28-31 oct 2026)

Código del estudio. Informes en el proyecto: `backtests/2026-10-28-causas-caidas-e1-y-b21.md` y `backtests/2026-10-31-revision-ratio-y-vix-vxv.md`.

- `comun.py`: monta el motor con las listas de GitHub + las reconstruidas; base del 31-oct (tope de 10.000 $ en SHY, cortos × 2).
- `cortos.py`: rehace CORTO SECTOR y CORTO ÍNDICES CRÉDITO.
- `linea.py`: rehace la línea de liquidez (Reserva Federal + TradingView) → `LIQUIDEZ/linea_reconstruida_2026_10.parquet`.
- `factores.py`, `escaneo.py`: 25 métricas conocidas al empezar el día y su relación con las pérdidas.
- `reglas.py`, `reglas2.py`, `revisar31.py`: reglas para bajar la caída y su revisión con el criterio «solo ratio».
- `nuevas.py`, `evalua_nuevas.py`, `placebo_n1.py`, `vecinos_n1.py`: señales nuevas y las pruebas de N1 VIX/VXV.
- `base31.py`, `paso1_base.py`, `extra.py`, `ver_g.py`, `doc23_add.py`: pasos auxiliares (base del 31-oct, comprobaciones y edición de documentos).
- `resultados/`: tablas de salida (reglas, escaneo de factores, descomposición de caídas, revisión «solo ratio», señales nuevas, placebo y vecinos de N1).
- `verificacion_n1/`: código del agente independiente que verificó N1 (alineación de fechas, lista de operaciones, cartera, efecto del freno).

**Estado (2-nov-2026):** N1 en vigilancia (NO ABRIR); B21 solo aviso; «una sola E1 abierta» descartada. Lo vigente, en `datos/registro-cambios.md` del proyecto.
