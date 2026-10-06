# VELAS-BACKTEST

Copia en la nube de la carpeta `VELAS PARA BACKTEST` del Mac de Óscar (escritorio).
Sirve para hacer backtests **sin depender de que el ordenador esté encendido**.

- Copia subida el 6 de octubre de 2026. Las velas llegan hasta el 29 de septiembre de 2026.
- 502 archivos, unos 1,3 GB. Verificada byte a byte contra el original.
- **No se actualiza sola.** Si la carpeta del Mac cambia, hay que volver a sincronizar.

## Cómo usarla desde una sesión de Claude

1. Añadir el repositorio `OSQUIR99/VELAS-BACKTEST` a la sesión.
2. Clonarlo (tarda unos minutos por el tamaño):
   `git clone --depth 1 https://github.com/OSQUIR99/VELAS-BACKTEST`
3. Cargar velas:

```python
from cargar import velas, financiacion
df = velas('BTC', '1h')
df = velas('BTC', '15m', perpetuo=True)
f  = financiacion('BTC')
```

## Qué hay dentro

- `CRIPTO/` — 52 monedas al contado, temporalidades 5m, 15m, 1h, 4h, 1d, 1w.
- `CRIPTO_PERPETUOS/` — 21 perpetuos en 15m más su tasa de financiación.
- `TRADICIONAL/` — oro, plata, Brent, Nasdaq 100, S&P 500 y DAX.
- `INDICE.csv` — qué hay, cuántas velas y entre qué fechas.
- `LEEME.md` — instrucciones y avisos originales de la carpeta.
- `ACUMULACION/`, `RENTA_FIJA/`, `RADAR_BTC/`, `LIQUIDEZ/` — datos y código de las herramientas del proyecto (termómetro de acumulación, termómetro de bonos, radar de riesgo de BTC y estudio de barridos de liquidez).
