# Medias móviles, sectores y rotación BTC–altcoins (3-nov-2026)

Solo mide el pasado. No es asesoramiento. Propuestas de la conversación «BACKTEST + HERRAMIENTAS + BOT» (`claude/medias-moviles-limpieza.md`, `claude/rotacion-btc-alts.md`, `claude/rotacion-traspaso.md`) y la instrucción `instruccion-2026-11-03-dos-pruebas-sectores.md`. Verificado por un agente independiente con su propio código (cifras idénticas).

**Cifra a batir: base vigente fiel 7,28 / 6,55 / 8,23** (ratio R/año ÷ peor caída en todo desde may-2018, 2018-21 y 2022-26), 65,6 R/año, −9,0 R. Reproducida exacta con la lista cripto re-simulada con el código original (`velas-backtest/ESTUDIOS_MEDIAS_2026_11_03/gen/gen2.py`).

**En resumen:** ninguna de las 9 pruebas pasa. No cambia ninguna regla. Hallazgo de método: comparar parámetros del REBOTE 4H con el ratio es muy inestable (ver punto 5).

## 1. Ruptura de la EMA 20 diaria en cripto, solo largos, 40 velas
| Variante | Ratio en la cartera | R/año | Caída | 2024-26 |
|---|---|---|---|---|
| Base | 7,28 / 6,55 / 8,23 | 65,6 | −9,0 | 12,58 |
| + BTC con stop 2,5 ATR (1 R) | 6,43 / 6,03 / 7,79 | 69,0 | −10,7 | 11,20 |
| + BTC con stop, a 0,25 R | 7,11 / 6,43 / 8,38 | 67,1 | −9,4 | 12,73 |
| + 6 monedas con stop (0,5 R) | 4,67 / 4,90 / 6,20 | 74,8 | −16,0 | 8,84 |
| + BTC sin stop / 6 sin stop | 5,82 / 5,99 / 7,74 · 4,49 / 4,50 / 5,80 | | | |
- Sola: BTC con stop +0,52 R por operación (2023-26 +0,49), 3,7 R/año, caída −8,4 R, 41 % de aciertos; **se mueve con la cripto** (correlación mensual 0,22-0,25). Gana dinero, pero añade caída justo cuando la cartera ya la tiene. **✗** No se probó «junto a la Ruptura B» porque la Ruptura B no está en el motor (sigue sin decidir, documento 22).

## 2. Medias que no deben contar como confluencia
En las reglas vigentes **ninguna media cuenta como confluencia de un nivel** (los niveles objetivos salen de pivotes y volumen). Las medias se usan como filtro de tendencia (subnota diaria con las EMA 50/200, EMA 50 > 200 de 4 h) y como toque del montaje (EMA 20 de 4 h). **Sin choque.** Se aplica solo al texto del panel: no presentar la EMA 200 diaria de BTC ni las medias de 1 h y 4 h como «confluencia», y no contar dos veces la 200 de 1 h y la 50 de 4 h. Sin backtest de cartera (no cambia ninguna orden).

## 3. Permiso de los índices (E1)
| Variante | Ratio | Nota |
|---|---|---|
| Margen de 0,9 % sobre la media de 200 (lista oficial) | 7,27 / 6,48 / 8,26 | quita 15 operaciones |
| E1 regenerada con permiso de 200 / con margen / con 20 semanas | 7,07 / 7,06 / 7,01 | 20 semanas (sin retraso) 7,01 / 6,35 / 7,98 |
**✗** El permiso actual se queda.

## 4. Oro: soporte de la media de 50 semanas
Sin largos nuevos con el cierre semanal un 2,8 % bajo la media (hasta que cierre encima): quita 31 operaciones → 7,17 / 6,41 / 8,14. **✗** como filtro. Puede quedar como **contexto** del panel (hoy activo: el 30-oct cerró un 8,4 % bajo la media).

## 5. Medias vecinas del REBOTE 4H (re-simulado con el original)
| Media | Ratio | R/año (2018-21) | 2024-26 | Peor caída 2018-21 |
|---|---|---|---|---|
| **20 y 50 (vigente)** | **7,28 / 6,55 / 8,23** | 59,0 | 12,58 | 9,0 (sep-2020, mezcla) |
| 16 | 7,58 / 7,17 / 8,42 | 65,7 | 11,78 | 9,2 (may-jul 2021) |
| 18 | 4,70 / 4,35 / 7,91 | 62,9 | 11,85 | 14,5 (jun-2020: ETH devuelve beneficio) |
| 22 | 5,23 / 4,67 / 9,09 | 60,8 | 13,11 | 13,0 (dic-2020: BTC devuelve beneficio) |
| 25 | 5,18 / 4,70 / 8,20 | 58,5 | 11,67 | 12,4 |
| 50 → 40 / 62 | 6,44 · 6,47 | | | |
- **La 16 pasa en las tres ventanas, pero no se aplica:** empeora 2024-26 (11,78 frente a 12,58) y el remuestreo no la confirma (0,33). Su mejora está en 2018-21 (gana un 11 % más); con la media de las 5 peores caídas mejora en 2018-21 y empata en 2022-26. En observación.
- **Hallazgo de método:** con tamaños de hasta 4,5 R, la peor caída de la cartera puede ser el beneficio que devuelve **una sola operación ganadora** (18 y 22). El ratio castiga entonces a la variante por tener una operación mejor. **Para cambiar parámetros del REBOTE 4H, mirar también la media de las 5 peores caídas y la caída con operaciones cerradas.**
- RETROCESO 1H (bot sombra, no está en la cartera) y RETROCESO PETRÓLEO 20/50 (sin generador en GitHub): no medidos.

## 6. CORTO SECTOR: la regla del dólar solo en los sectores que venden fuera
- Grupos fijados **antes de mirar**: muy expuestos XLK, SMH, XLB y XLE. Fuentes: S&P Dow Jones Indices, «S&P 500 Global Sales» (último público con sectores: 2018; tecnología 58 %, energía 51 %) y FactSet vía First Trust (sep-2026, fuera de Norteamérica: tecnología 51,6 %, materiales 46,5 %, comunicación 36,8 %, energía 31,1 %). XLC queda fuera (36,8 %).
- Variante (poco expuestos siempre a tamaño completo): **6,85 / 6,13 / 8,24** (sube la caída de 2018-21 a −9,6 R). Placebo (al revés): 7,27 / 6,54 / 8,22. **✗**

## 7. Familia lenta de sectores (12 meses, top 3)
- Paso 0: lo descartado antes era otra cosa (26 semanas a 13 semanas; y top 3 de 6 meses el 25-oct). Se hizo la prueba.
- Sola: 117 operaciones desde 1999 (47 en la ventana), +0,47 R por operación, 0,9 R/año, caída −1,2 R, peor año −1,0 R, correlación mensual con la cripto 0,03 (sí es descorrelacionada).
- En la cartera (0,5 R): **6,63 / 5,93 / 8,81**, caída −10,0 R; a 0,25 R 7,19 / 6,47 / 8,68. Sube 2022-26 pero baja 2018-21. Con 3, 7 y 11 sesiones de desplazamiento sale lo mismo (el impulso de 12 meses casi no cambia con unos días: no sirve de placebo). **✗** Al documento 22: «Familia lenta de sectores por impulso de 12 meses ✗; no se vuelve a probar con otros plazos».

## 8. Ideas de rotación BTC–altcoins (sin backtest; qué chocaría y qué haría falta)
| Idea | ¿Choca con lo vigente? | Backtest necesario (montaje de 4 h) |
|---|---|---|
| 1. Peso de altcoins = mitad del termómetro 2; media posición con 70 o más | Sí: el tamaño del REBOTE 4H lo da la nota de puntos y sus multiplicadores por operación; no hay peso global de altcoins. Ya se descartó un multiplicador de dominancia (USDT.D × 1,5) y ETH lleva −1 punto con ETH/BTC subiendo (doc 12/13) | Multiplicador por operación de SOL, ADA, LINK, ZEC (y ETH) según el termómetro del día anterior, re-simulando con el original (el tamaño cambia topes y freno). Una variante, con placebo |
| 2. Largos de BTC en lateral con empuje solo con ADX ≤ 20 | Choca con doc 25, punto 6 (en lateral las señales siguen igual) y con doc 22 («quitar o reducir en lateral: 0 de 20 mejoran»). El ADX bajo ya da +1 ★ con retroceso corto (doc 11, capa A) | Filtro de entrada del REBOTE 4H de BTC con régimen lateral y ADX diario > 20 → NO ABRIR; re-simulado |
| 3. Rupturas de medias con su fuerza; perder la media de 50 por un 2 % como sesgo vendedor | Las rupturas como entrada: no pasan (punto 1 de este informe). Como sesgo de contexto, no choca (capa C, doc 11) | Si se quisiera como salida del REBOTE 4H: re-simulación con salida al perder la EMA 50 diaria un 2 %. Como aviso: medir su coletilla (R a 5-20 días) |
| 4. «Espera al cierre» tras una caída nocturna > 0,5 ATR | Roza la regla del 3-nov (velas de 4 h de la 1:00 y las 5:00 → NO ABRIR en Quantfury y Bitunix) y la entrada a mercado del montaje | Retrasar la entrada al cierre de la vela siguiente cuando la noche cayó > 0,5 ATR; re-simulado con el original (cambia precio de entrada y operaciones) |
| 5. Etiqueta «apoya / neutral / en contra» por señal | No choca si es solo texto (capas A/C del doc 11). Chocaría si moviera estrellas o tamaño sin estar medida (±1 ★ como mucho entre todo) | R por operación de las señales de la lista por etiqueta, en 2018-21 y 2022-26; solo si separa bien pasa a ±1 ★ |

## Código y verificación
`velas-backtest/ESTUDIOS_MEDIAS_2026_11_03/` (p1.py, p34.py, ev.py, t1.py, t2.py, gen/gen2.py; verificación en `verificacion/`).

## 9. Ideas de rotación medidas (3-nov, 22:00; Óscar: «sí»)
**Definiciones fijadas antes de mirar** (la definición exacta del «termómetro 2» está en el otro proyecto; si es distinta, se repite):
- **Termómetro:** % de la lista de cripto de Óscar (ETH, AAVE, ADA, BNB, HBAR, HYPE, LINK, ONDO, SOL, UNI, XRP, ZEC) con el cierre diario sobre su media de 50, el día anterior. Media 47 %; ≥ 70 el 37 % de los días.
- **Etiqueta:** con el sesgo de rotación del documento 12 (pendiente de 5 días de la media de 20): ETH y BTC con ETH/BTC; las altcoins con la dominancia de BTC al revés. Neutral si el cambio es menor del 0,25 %.

**Idea 1 · altcoins a media posición con el termómetro ≥ 70**
| Variante | Ratio en la cartera | R/año | Caída | 2024-26 |
|---|---|---|---|---|
| Base | 7,28 / 6,55 / 8,23 | 65,6 | −9,0 | 12,58 |
| SOL, ADA, LINK, ZEC × 0,5 (263 op.) | 6,47 / 5,57 / 8,93 | 62,3 | −9,6 | 12,61 |
| Las 5 sin BTC (con ETH) × 0,5 (316 op.) | 7,09 / 6,47 / 8,92 | 64,5 | −9,1 | 12,64 |
- **Sola, la señal es fuerte:** las altcoins del REBOTE 4H ganan mucho menos con el termómetro ≥ 70 (2018-21: +0,52 frente a +1,07 R por operación; 2022-26: +0,15 frente a +0,92). Encaja con lo del 14-oct: comprar el retroceso de una altcoin cuando todo el mercado de altcoins está eufórico sale peor.
- **En la cartera no pasa:** sube 2022-26 (8,93, por encima del máximo de 20 sorteos al azar, 8,64), pero baja 2018-21 porque esas operaciones, aun ganando menos, ganaban. **✗ como tamaño.**
- **Queda como aviso de contexto {~}** (no mueve estrellas ni tamaño): «Altcoin del REBOTE 4H con el termómetro de la lista ≥ 70 %: en el pasado ganó +0,15 R por operación desde 2022 (119 casos), frente a +0,92 R con el termómetro bajo 70».

**Idea 5 · etiqueta «apoya / neutral / en contra»** (R por operación del REBOTE 4H)
| Periodo | Apoya | Neutral | En contra |
|---|---|---|---|
| 2018-21 | +0,56 (163) | +1,32 (36) | +0,96 (84) |
| 2022-26 | +0,56 (121) | +0,40 (75) | +0,75 (108) |
| 2024-26 | +0,79 (83) | +0,72 (52) | +0,68 (71) |
- **No separa:** «en contra» gana igual o más que «apoya». **✗** No se pone etiqueta en las señales.

Pendientes de la lista de rotación: ideas 2 (ADX ≤ 20 en lateral), 3 (perder la media de 50 como salida) y 4 (esperar al cierre tras caída nocturna), que necesitan re-simular con el original.
