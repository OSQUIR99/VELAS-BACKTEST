> **Desde el 18-oct-2026 las velas se actualizan solas cada día** (todas las series y temporalidades). Mira `ACTUALIZACION/LEEME.md`. `velas(..., actualizado=False)` da la copia fija original.

# VELAS-BACKTEST

Archivo de velas de Óscar para hacer backtests **sin depender de que el Mac esté encendido**.
Nació como copia de la carpeta `VELAS PARA BACKTEST` del escritorio (6-oct-2026) y se reorganizó el 13-oct-2026.

**No se actualiza solo.** Cada archivo dice hasta cuándo llega en `INDICE.csv`.

## Cómo está ordenado (desde el 13-oct-2026)

```
CARPETA_DE_BACKTEST/                 lo que se usa en el proyecto de gestión integral
  CRIPTO/<moneda>/<tf>.parquet           BTC, ETH, HYPE, SOL, XRP, ADA, LINK, ZEC, BNB, UNI, HBAR, ONDO, AAVE y ETH_BTC
  CRIPTO_PERPETUOS/<moneda>/<tf>.parquet los mismos 13 perpetuos (Binance), en las 6 temporalidades
  CRIPTO_PERPETUOS/<moneda>/financiacion.parquet
  TRADICIONAL/<activo>/<tf>.parquet      41 activos: índices, sectores, bonos, tipos, dólar, volatilidad, metales, energía, grano
  INDICES_CRIPTO/<indice>/<tf>.parquet   dominancia de BTC, ETH y USDT; capitalización total, TOTAL3 y OTHERS
ALTCOINS_SECUNDARIAS/                 el resto de monedas, tal como estaban (hasta el 29-sep-2026)
  CONTADO/<moneda>/<tf>.parquet          38 monedas
  PERPETUOS/<moneda>/15m.parquet         14 perpetuos y su financiación
ACUMULACION/, RENTA_FIJA/, RADAR_BTC/, LIQUIDEZ/   datos y código de las herramientas
PANEL_CRIPTO/                        panel cripto con fuentes públicas: script y su histórico diario (lo guarda GitHub Actions cada día a las 00:20 UTC)
INDICE.csv                            qué hay, cuántas velas, desde y hasta cuándo, y de dónde sale
cargar.py                             carga cualquier archivo con una línea
```

Temporalidades: `5m`, `15m`, `1h`, `4h`, `1d`, `1w`. Horas en UTC (hora de apertura de la vela). La última vela de cada archivo está cerrada.

## Cómo usarlo desde una sesión de Claude

1. Añadir el repositorio `OSQUIR99/VELAS-BACKTEST` a la sesión y clonarlo (tarda unos minutos):
   `git clone --depth 1 https://github.com/OSQUIR99/VELAS-BACKTEST`
2. Cargar velas:

```python
from cargar import velas, financiacion
df = velas('BTC', '1h')
df = velas('SOL', '5m', perpetuo=True)
df = velas('tlt', '1d', ajustado=True)   # con dividendos reinvertidos
f  = financiacion('BTC')
```

## Columnas

- Todos: `fecha`, `apertura`, `maximo`, `minimo`, `cierre`, `volumen`.
- **Cripto de interés (contado y perpetuos, Binance): además `volumen_comprador`**, es decir, el volumen que compró a mercado. Delta = `2*volumen_comprador - volumen`.
- Financiación: `fecha`, `tasa` (por periodo de cobro, normalmente cada 8 horas).

## De dónde sale cada cosa

- **Cripto de interés:** archivo oficial de Binance (data.binance.vision), velas de 5 minutos agregadas al resto de temporalidades. Hasta el 12-oct-2026.
  Se rehicieron porque la copia anterior tenía velas guardadas a medias (por ejemplo, BTC el 21-sep, el 23-ago y varias horas de agosto y septiembre). Coinciden con las anteriores en más del 99,99 % de las velas.
- **HYPE al contado:** 5m, 15m y 1h de OKX (desde nov-2025); 4h, 1d y 1w de Hyperliquid, su mercado de origen (desde el 29-nov-2024). Diferencia de precio entre ambos: 0,06 % de media. Sin `volumen_comprador`.
- **Perpetuos de interés:** Binance futuros, desde 2020 (o desde que se listaron). Financiación hasta el 30-sep-2026.
- **Tradicional nuevo e índices cripto:** TradingView sin sesión iniciada, sesión regular. Unas 5.000 velas por gráfico: décadas en diario y semanal, pocas semanas o meses en 5 y 15 minutos. Hasta el 12-13 de octubre de 2026.
  Los fondos cotizados tienen además `1d_ajustado_dividendos` y `1w_ajustado_dividendos`.
- **Tradicional antiguo** (oro, plata, Brent, Nasdaq 100, S&P 500, DAX): TradingView, hasta el 29-sep-2026, sin cambios.
- **Altcoins secundarias:** sin cambios, hasta el 29-sep-2026.

## Avisos

- El volumen de los índices (S&P 500, Nasdaq 100, Dow Jones, Russell 2000, DAX) no es el volumen real del mercado.
- `sp500_pct_sobre_media200` (porcentaje de acciones del S&P 500 por encima de su media de 200) solo existe en diario y semanal.
- `move` (volatilidad de los bonos) solo en diario y semanal: el intradía de TradingView venía con huecos de días.
- Las criptos se miden en Binance y se operan en Quantfury, OKX o BitUnix: la diferencia de precio es mínima, pero existe.
- Las herramientas de `RADAR_BTC/` leen las velas desde otra ruta (`datos/...`): son copias para consulta.
