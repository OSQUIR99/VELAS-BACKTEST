# Acciones de la lista de seguimiento (velas diarias)

393 acciones de la lista de Óscar (EE. UU. y Europa), velas **diarias ajustadas por dividendos**, desde 2002 (o desde que cotizan) hasta el **23-oct-2026**.
Bajadas el 25-oct-2026 con la conexión pública de TradingView (`ACTUALIZACION/tv.py`). **No se actualizan solas.**

- `velas/<BOLSA>_<TICKER>.parquet`: columnas `fecha`, `apertura`, `maximo`, `minimo`, `cierre`, `volumen`.
- `lista.csv`: símbolos usados. `bajar.py`: para volver a bajarlas o ampliarlas (`python3 bajar.py lista.csv`, cambiando la carpeta de salida).
- Uso: `pd.read_parquet('ACCIONES_LISTA/velas/NYSE_SLB.parquet')`.
- Estudios que las usan: proyecto, `backtests/2026-10-25-filtros-video-ema21.md` y `backtests/2026-10-26-acciones-b-en-cartera.md`.
