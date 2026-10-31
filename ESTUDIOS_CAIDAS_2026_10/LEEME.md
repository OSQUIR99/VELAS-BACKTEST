# Estudio «causas de las caídas» y señales nuevas (28-31 oct 2026)

Código del estudio. Informes en el proyecto: `backtests/2026-10-28-causas-caidas-e1-y-b21.md` y `backtests/2026-10-31-revision-ratio-y-vix-vxv.md`.

- `comun.py`: monta el motor con las listas de GitHub + las reconstruidas; base del 31-oct (tope de 10.000 $ en SHY, cortos × 2).
- `cortos.py`: rehace CORTO SECTOR y CORTO ÍNDICES CRÉDITO.
- `linea.py`: rehace la línea de liquidez (Reserva Federal + TradingView) → `LIQUIDEZ/linea_reconstruida_2026_10.parquet`.
- `factores.py`, `escaneo.py`: 25 métricas conocidas al empezar el día y su relación con las pérdidas.
- `reglas.py`, `reglas2.py`, `revisar31.py`: reglas para bajar la caída y su revisión con el criterio «solo ratio».
- `nuevas.py`, `evalua_nuevas.py`, `placebo_n1.py`, `vecinos_n1.py`: señales nuevas y las pruebas de N1 VIX/VXV.
