# RADAR_BTC — radar de riesgo de caída fuerte de bitcoin

Creado el 2-3 de octubre de 2026.

## Qué hay aquí
- `herramienta/` — copia de la herramienta tal y como se publicó (página `radar.html`, programas `radar_nucleo.py` y `radar_diario.py`, datos `estado.csv`, `historial.json`, `calibracion.json`, `eventos.json`, y `PROCEDIMIENTO.md`).
  La versión viva está en el artefacto "Radar de riesgo BTC" y la actualiza cada mañana la tarea programada "Radar de riesgo BTC (diario)" (7:58 de Madrid). Esta carpeta NO se actualiza sola.
- `estudio/` — programas y resultados del estudio 2017-2026:
  - `catalizadores_todos.csv`: 123 grandes movimientos y giros con su catalizador, categoría y fuente.
  - `episodios_caidas.csv`: las 13 grandes caídas desde 2019 y cuándo avisó el radar.
  - `tramos_zigzag25.csv` y `movimientos_rapidos.csv`: los movimientos detectados.
  - `lectura_tecnica_por_regimen.csv`: soportes y rupturas según el entorno macro.
  - `auc_desplome_relvol.csv`: qué variable anticipaba los desplomes en cada época.
  - Los `.py` leen la carpeta de velas y `brutos/` (para consulta).
- `brutos/` — descargas: Binance con volumen comprador agresivo, Coinbase, stablecoins.
- `descargar_liquidez.py` — baja lo que falta de liquidez de la Fed. Ejecútalo en la Terminal:
      cd "$HOME/Desktop/VELAS PARA BACKTEST/RADAR_BTC" && python3 descargar_liquidez.py --solo-fred
  y avisa a Claude para recalibrar.

## Cómo se lee
Nota 0-100. Verde < 40 · Amarillo 40-52 · Naranja 52-62 · Rojo ≥ 62.
Bloques: macro (30-45 %), liquidez (20 %), estructura y flujo (25 %), catalizadores (10 %).
