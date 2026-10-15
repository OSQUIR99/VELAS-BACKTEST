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

## Tercera parte (15-oct-2026, noche)
- `sr_diario.py`: zonas de pivote diarias + 0-3 velas diarias de confirmación. Rebotes: no funcionan.
  Roturas de resistencia (seguir la ruptura): OTHERS mejora en 96 % de combinaciones (92 % en ambos tramos); ETH/BTC en 94 %.
- `eth_btc_intradia.py`: confirmación en 4 h y 12 h. Rebote sigue sin funcionar; rotura de resistencia mejora en ~77 % (54 % en ambos tramos).
- `soportes_alts.py`: soportes de OTHERS, TOTAL3 y altcoins, con y sin el bajista 2022. Solo BNB rebota más que al azar.
- `indicadores.py`: medias, pendientes, rupturas de rango, RSI, separando lado alcista/bajista.
- `auditoria_others.py` (agente independiente): OTHERS > media 50 sin fallos ni mirar el futuro, pero inflado
  (cesta con supervivientes; casi todo en 2018-21; desde 2024 pierde contra 50/50). Lo más sólido: ETH/BTC con pendiente
  de la media de 20 días -> ETH o BTC; gana al 50/50 en 2018-21, 2022-26 y 2024-26, también con comisión del 0,3 %.
