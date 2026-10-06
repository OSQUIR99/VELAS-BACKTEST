# Estudio de barridos de liquidez (octubre 2026)

Backtest de qué pasa cuando el precio barre un máximo o mínimo anterior frente a cuando lo deja pendiente.
Activos: BTC, S&P 500, Nasdaq 100, oro, plata y Brent. Temporalidades 1h, 4h y diario (BTC también 15m).
Datos: las velas de esta carpeta (hasta el 29-sep-2026) y el interés abierto de Binance cada 5 min (oi_btc.parquet, desde sept-2020).

## Orden de ejecución (desde esta carpeta)
1. `estudio1.py`  -> ev1.parquet   (tramo tras barrido / suelo igual / mínimo más alto)
2. `estudio2.py`  -> ev2.parquet, ctrl2.parquet (vida de niveles, giro al perforar, estrategias, control al azar)
3. `estudio3.py`  -> ev3.parquet   (desequilibrio de liquidez y prueba del "imán")
4. `estudio4.py`  -> ev4.parquet   (entrada SMC idéntica para todos los casos)
5. `vida.py`, `extra.py`, `modelo.py`, `btc_oi.py`, `btc15.py` (pruebas complementarias)
6. `agregar.py` y después `agregar2.py` -> resultados.json (cifras del informe)

`btc_oi.py` necesita oi_btc.parquet. No va incluido por tamaño: ejecuta antes `descargar_oi.py`, que lo baja de data.binance.vision (futures/um/daily/metrics/BTCUSDT) y lo limpia igual que en el estudio.

## Dependencias
python3 -m pip install pandas pyarrow numba scikit-learn

## Ajustes clave
- Giros: ZigZag causal de 2,5 ATR (repetido con 1,5 y 4).
- Comisión 0,05 % por lado; resultados en R y con 20x.
- Informe completo: informe_barridos_liquidez.html
