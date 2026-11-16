# ESTUDIOS_E1_SALIDAS_2026_11_05

E1 de índices (S&P 500, Nasdaq 100, Dow) con salidas más largas, conviviendo con la cartera base vigente fiel (7,28 / 6,55 / 8,23). Informe: `contexto-cartera/HERRAMIENTAS/estudios/e1-salida-convivencia/INFORME.md`. **Ninguna pasa; la regla no cambia.** Solo mide el pasado.

- `gen_e1.py`: generador original de `MOTOR/listas/bolsa_e1` (`drive-pendiente/bolsa-gestion/listas_bolsa.py`) con la salida de los índices parcheada. Con `base` reproduce la lista del motor exacta.
- `listas/bolsa_e1_<salida>.parquet` (+ `_diario`): base, seguir5, rsi90, minant, seguir5_max10, mitad. **No son listas vigentes**: para probarlas, cargar una en lugar de `bolsa_e1`, nunca junto a ella (comparten los `id`).
- `solo.py` (E1 sola), `cartera.py` (motor real con el montaje de `contexto-cartera/HERRAMIENTAS/estudios/ruptura-maximos-cartera/harness.py`), `tabla.py` (resumen), `datos_cripto.py` (datos del código original del REBOTE 4H).
