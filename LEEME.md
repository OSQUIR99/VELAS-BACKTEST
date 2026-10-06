# Velas para backtest

Copia fija del archivo de precios, tomada el 30 de septiembre de 2026. Los datos llegan
hasta el 29 de septiembre de 2026. **No se actualiza sola**, así que un backtest dará el
mismo resultado hoy que dentro de un año.

## Cómo está ordenado

```
CRIPTO/<moneda>/<temporalidad>.parquet            52 monedas al contado (Binance; HYPE de OKX)
CRIPTO_PERPETUOS/<moneda>/15m.parquet             21 perpetuos (Binance futuros)
CRIPTO_PERPETUOS/<moneda>/financiacion.parquet    tasa de financiación de cada perpetuo
TRADICIONAL/<activo>/<temporalidad>.parquet       oro, plata, petroleo_brent, nasdaq100, sp500, dax (TradingView)
INDICE.csv                                        qué hay, cuántas velas, desde y hasta cuándo
cargar.py                                         carga cualquier archivo con una línea
```

Temporalidades: `5m`, `15m`, `1h`, `4h`, `1d`, `1w`.

**Todos los archivos tienen las mismas columnas**: `fecha` (hora UTC de apertura de la vela),
`apertura`, `maximo`, `minimo`, `cierre` y `volumen`. Una sola fuente por activo, sin
duplicados. La última vela de cada archivo está siempre cerrada.

## Cómo se usa

```python
from cargar import velas
df = velas('BTC', '1h')
```

## Avisos

- **Intradía tradicional corto**: TradingView da unas 10.000 velas por gráfico. En 5 minutos
  eso son de 2 a 7 meses; en 1 hora, de 1 a 6 años; en diario, décadas. Mira `INDICE.csv`.
- La plata en diario solo llega a 2009 (en semanal, a 1970).
- El volumen de los índices (S&P 500, Nasdaq 100, DAX) no es el volumen real de mercado.
- En criptomonedas, cada moneda empieza cuando se listó. Bitcoin, en agosto de 2017.
- KGEN solo tiene velas de 1 hora y se detienen el 29 de junio de 2026.
- Los datos se miden en Binance y se opera en OKX o BitUnix. La diferencia de precio es mínima,
  pero existe.

## Si hay que instalar algo

En Mac el comando `pip` suelto no existe. Se usa:

```
python3 -m pip install pandas pyarrow
```

En este ordenador ya está instalado.
