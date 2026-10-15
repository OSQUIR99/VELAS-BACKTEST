# Rotación por extremos de dominancia (15-oct-2026)

Hipótesis: cuando ETH/BTC, la dominancia de BTC o la de USDT están muy estiradas, rotar al lado contrario.
Velas: `CARPETA_DE_BACKTEST/INDICES_CRIPTO` (TradingView, hasta 12-oct-2026) y contado de Binance.
Script: `rotacion_dominancia.py` (rejilla de 18 combinaciones por prueba). Resultados: `rejilla_resultados.csv`, `resumen.json`.
Verificado por un agente independiente (datos correctos; corregidos dos fallos de calendario/comisión).

Conclusión: la rotación a la contra NO funciona en ninguna de las tres. Lo único con algo de señal es seguir
la tendencia de ETH/BTC (al revés de la hipótesis), y solo de forma inestable.
Aviso: la cesta de altcoins (ETH, BNB, XRP, ADA, LINK, SOL) tiene sesgo de supervivientes.

## Soportes y resistencias (15-oct-2026, segunda parte)
Scripts: `soportes_resistencias.py` (eventos y rotación con ambos lados), `sr_un_lado.py` (cada lado por separado),
`sr_confirmacion_diaria.py` (zonas de pivote semanales + confirmación con vela diaria).
- Único candidato: resistencia en la dominancia de BTC (sin confirmación diaria) -> pasar a altcoins unas semanas.
  Mejora la rentabilidad por unidad de riesgo en 12 de 12 combinaciones; gana en 2018-21 y 2022-26 en 7 de 12.
  Pocos casos (4-16) y cesta de altcoins con sesgo de supervivientes: pendiente de auditoría.
- Soportes: no funcionan en ningún indicador. En OTHERS, los soportes se rompen el 80-90 % de las veces.
- Confirmación diaria: da tan pocas señales (0-7 en ocho años) que no se puede sacar conclusión.
