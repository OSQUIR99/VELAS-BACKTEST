# Actualización diaria de las velas

Desde el 18 de octubre de 2026, **GitHub añade cada día las velas cerradas de todas las series de `INDICE.csv`**
(contado y perpetuos de cripto, altcoins secundarias, índices cripto, activos tradicionales; 5m, 15m, 1h, 4h, 1d y 1w,
y la financiación de los perpetuos). Lo hace `.github/workflows/actualizar_velas.yml` a las **03:30 UTC**
(05:30 en España en verano; 04:30 en invierno).

## Cómo se usa
Igual que siempre: `velas('BTC', '5m')` ya trae lo nuevo. Para repetir un backtest con los mismos datos de antes:
`velas('BTC', '5m', actualizado=False)` (la copia fija original). Haz `git pull` para tener lo último.

## Cómo se guarda
- Los `<tf>.parquet` originales **no se tocan** (reescribirlos cada día engordaría el repositorio).
- Lo nuevo va a `ACTUALIZACION/velas/<carpeta>/<activo>/<AAAA-MM>/<AAAA-MM-DD>.parquet`: un archivo por activo y día
  (día de apertura de la vela) con todas sus temporalidades (columna `tf`). Unos 1,5-2 MB al día en total.
- `estado.json`: hasta dónde está guardada cada serie. `ultimo_informe.json`: lo que hizo la última ejecución.
- `INDICE.csv` se actualiza con la nueva fecha final y el número de velas.

## Cada 6 meses
El 2 de enero y el 2 de julio, `compactar.py` (workflow `compactar_velas.yml`) junta los diarios del semestre terminado en un
solo archivo por activo (`<AAAA>-S1.parquet` o `-S2`). No cambia los datos (probado: mismas filas); solo hace que cargar sea más rápido.

## Fuentes (las mismas que el original)
- **Binance** (contado y perpetuos): archivo oficial diario `data.binance.vision`. Si aún no está publicado, el contado
  usa la API pública `data-api.binance.vision`; los perpetuos esperan al día siguiente (sin huecos: nunca se salta un día).
  La semana (1w) se construye con las velas diarias (lunes a domingo, hora UTC), igual que Binance.
- **Financiación de los perpetuos:** archivo mensual de Binance; llega a principios del mes siguiente.
- **HYPE al contado:** OKX (5m, 15m, 1h) y Hyperliquid HYPE/USDC (4h, 1d; la semana, desde el 1d). Si OKX no responde, Hyperliquid.
- **TradingView** (tradicionales, índices, dominancias): conexión pública, mismo símbolo. Oro = COMEX:GC1!, plata = COMEX:SI1!,
  Brent = TVC:UKOIL, Nasdaq 100 = NASDAQ:NDX, S&P 500 = SP:SPX, DAX = XETR:DAX. Ajustados por dividendos: `adjustment=dividends`.
- **Solo velas cerradas.** En bolsa, la vela diaria se da por cerrada cuando el mercado lleva parado más de 45 minutos.

## Comprobado el 18-oct-2026
- Las velas nuevas coinciden con las originales en los días que se solapan (0 % de diferencia en precios).
- **Corregido:** `INDICE.csv` decía «Binance futuros» en el 15m de 10 altcoins secundarias (ALGO, AVAX, BCH, ENA, ETC, ICP,
  LTC, NEAR, SUI, THETA) que en realidad son de **contado**; la actualización usa el contado (`mercado` en `estado.json`).
- **No se actualizan:** TON al contado (retirado de Binance en junio) y KGEN (sin datos que cuadren).
- **Financiación del perpetuo de TON:** Binance no publica su archivo mensual desde julio; sus velas sí se actualizan.
- Una moneda que pase más de 30 días sin datos se deja de pedir y se avisa en `ultimo_informe.json`.

## Acciones de la lista de seguimiento (desde el 26-oct-2026)
- `acciones_lista.csv`: las acciones (EE. UU. y Europa) con su símbolo de Yahoo (RACE.MI, RAND.AS, SAP.DE, SAN.MC...) y el de TradingView.
  Para añadir o quitar una, edita ese archivo.
- `acciones.py` (paso propio del workflow, después de `actualizar.py`): velas **diarias** desde Yahoo Finance.
  La primera vez baja toda la historia a `CARPETA_DE_BACKTEST/ACCIONES/<simbolo>/1d.parquet`; después solo lo nuevo,
  en `ACTUALIZACION/velas/CARPETA_DE_BACKTEST/ACCIONES/<simbolo>/...` como el resto.
- Columnas como TRADICIONAL (`fecha` = apertura de la sesión en UTC, apertura, maximo, minimo, cierre, volumen). Ajustadas por splits, no por dividendos.
- De una en una, con pausa y reintentos (Yahoo corta con 429); si una falla, sigue con las demás y lo dice en el registro de la Acción.
- Se leen con `velas('HST', '1d')`, `velas('RACE.MI', '1d')`.

Código: `actualizar.py` (y `tv.py`, la conexión a TradingView). Primera vez con el repositorio entero: `--iniciar`.
