# Panel cripto · histórico diario

Cada día a las 00:20 UTC, GitHub ejecuta `PANEL_CRIPTO/panel/panel_cripto_publico.py` con fuentes gratuitas (Binance público, OKX, Coinbase,
CoinMetrics, Deribit, BGeometrics, DefiLlama, alternative.me) y guarda:

- `historial/json/AAAA-MM-DD.json`: la salida completa del día (con la fecha del cierre diario).
- `historial/panel_diario.csv`: una fila por día con las cifras clave, para seguir umbrales y probabilidades en el tiempo.
- `historial/ultimo_resumen.txt`: el resumen en texto del último día.

Para lanzarlo a mano: pestaña **Actions** → «Panel cripto · histórico diario» → **Run workflow**.

Las reglas y tablas vienen de la Sección 6 (backtests 2017-2026, periodo de comprobación 2023-26). No cambiar umbrales sin repetir la prueba.

El programa del día está en `.github/workflows/panel_cripto_diario.yml` (GitHub solo acepta los programas en esa carpeta de la raíz).
El primer día guardado (`2026-10-12.json`) se generó a mano el 13-oct a las 23:10 UTC con el mismo script.
