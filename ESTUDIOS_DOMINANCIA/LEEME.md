# Rotación por extremos de dominancia (15-oct-2026)

Hipótesis: cuando ETH/BTC, la dominancia de BTC o la de USDT están muy estiradas, rotar al lado contrario.
Velas: `CARPETA_DE_BACKTEST/INDICES_CRIPTO` (TradingView, hasta 12-oct-2026) y contado de Binance.
Script: `rotacion_dominancia.py` (rejilla de 18 combinaciones por prueba). Resultados: `rejilla_resultados.csv`, `resumen.json`.
Verificado por un agente independiente (datos correctos; corregidos dos fallos de calendario/comisión).

Conclusión: la rotación a la contra NO funciona en ninguna de las tres. Lo único con algo de señal es seguir
la tendencia de ETH/BTC (al revés de la hipótesis), y solo de forma inestable.
Aviso: la cesta de altcoins (ETH, BNB, XRP, ADA, LINK, SOL) tiene sesgo de supervivientes.
