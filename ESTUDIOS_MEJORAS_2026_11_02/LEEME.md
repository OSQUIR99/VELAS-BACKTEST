# Búsqueda de mejoras con lo medido (2-nov-2026, 21:00-23:30) · no vender el tercio por nota de puntos, re-simulado

Pedido por Óscar (2-nov, 20:21): «usa la información disponible para mejorar las estrategias… que lo revise un agente… comprueba que las señales no se pisan y que no hay fallos técnicos». Solo mide el pasado. No es asesoramiento.

**Criterio** (documento 23): sube el ratio (R/año ÷ peor caída de la curva valorada a diario) en todo, 2018-21 y 2022-26. Más peso a los años recientes.

**Base de partida:** la vigente del 2-nov (E1 de índices y Connors fuera del freno, sin venta del tercio con volatilidad baja): 6,35 / 5,69 / 7,36, R/año 62,2, caída −9,8 R.

## 1. Fallo de método encontrado (importante)
- «Sin venta del tercio» se medía cambiando la lista ya hecha con una fórmula: (r − 1/3) × 1,5.
- El verificador independiente vio que la fórmula falla en tres cosas:
  - multiplica también los tramos de promedio y los costes;
  - no tiene en cuenta que el camino de la operación cambia;
  - depende de si el freno salta o no en junio de 2020.
- **Solución:** re-simular vela a vela con el código ORIGINAL del REBOTE 4H (`contexto-cartera/BOT/codigo/origen/`). Este código reproduce la lista oficial: 591 operaciones y 362,1 R, frente a 362,6 R.
- En la re-simulación, en +1 R no se vende nada (`parts = [(1.0, 0.0)]`), pero el stop pasa a la entrada y el retroceso fallido deja de mirarse. Es justo lo que dice la regla escrita.

## 2. Resultado con la re-simulación fiel

| Lista cripto (resto de la cartera igual) | Ratio todo / 2018-21 / 2022-26 | R/año | Caída | 2024-26 |
|---|---|---|---|---|
| Sin regla de tercio (v0) | 6,26 / 5,73 / 7,16 | 61,3 | −9,8 | 10,07 |
| **Regla aprobada: volatilidad de BTC ≤ 10 %** | 6,24 / 5,68 / 7,17 | 61,1 | −9,8 | 10,03 |
| Volatilidad o puntos 2 | 6,49 / 5,71 / 7,50 | 63,5 | −9,8 | 10,66 |
| **Puntos 2 (nota máxima)** | **6,61 / 5,73 / 7,71** | **64,7** | −9,8 | **11,05** |

- **La regla de volatilidad baja aprobada el 26-oct no mejora.** Con la re-simulación fiel baja en el total y en 2018-21. Lo confirma el verificador. Su aprobación venía de la fórmula.
- **No vender el tercio con la nota de puntos máxima (2) sube el total y 2022-26** sin subir la caída. Afecta a 42 operaciones y suma +55,9 R.
- **2018-21 queda en empate:** 5,727 → 5,731 (+0,004). Técnicamente pasa el criterio, pero es ruido.

## 3. Robustez de «puntos 2»
- **Freno 3 R:** 5,85 / 5,40 / 7,37 → 6,28 / 5,62 / 8,07 (pasa). **Freno 5 R:** 4,93 / 4,54 / 6,87 → 5,05 / 4,62 / 7,56 (pasa, pero la caída sube de 12,3 a 13,2).
- **Remuestreo mensual:** 0,92.
- **Placebo** (20 sorteos marcando al azar el mismo 14 % de operaciones): media 6,20 / 5,67 / 7,05, máximo 6,44 / 6,07 / 7,34. **Ningún sorteo llega a 6,61 en total ni a 7,71 en 2022-26.** En 2018-21 varios sorteos sí superan.
- **Épocas** (2018-19 / 2020-21 / 2022-23 / 2024-26): 2,40 / 8,48 / 3,53 / 10,07 → 2,45 / 8,44 / 3,51 / 11,05. **Casi toda la ganancia está en 2024-26.**
- **Quitando una moneda cada vez:** pasa sin BTC, sin ADA y sin LINK. No pasa sin ETH (2018-21 baja) ni sin ZEC (2022-26 baja).
- **Sin las 3 mejores** (ETH-2020-12, ADA-2020-06, ZEC-2026-08): 6,36 / 5,42 / 7,49. Sigue mejor en el total y en 2022-26, pero no en 2018-21.
- **Mediana por operación −0,29 R:** 24 de 42 pierden algo. Es una apuesta de cola: pocas operaciones que corren mucho pagan muchas pequeñas.
- **Sin mirar al futuro:** la nota de puntos se calcula en la vela de señal (`tamaño_fila`, con el diario ya cerrado).
- **Lógica:** la nota máxima marca las entradas con más recorrido. Ya llevan tamaño × 1,5, y dejarlas correr aprovecha su cola.

**Veredicto del verificador:** «se sostiene con matices». Mejora el total y 2022-26; en 2018-21 empata; depende de 3 operaciones y del camino del freno. Recomienda quitar la regla de volatilidad.

**Propuesta para Óscar (no aplicada):** cambiar el paso 5 quater del documento 06. En lugar de la volatilidad baja, que la condición sea la **nota de puntos 2**: en BTC, ETH, ADA, ZEC y LINK, en +1 R no se vende el tercio y el stop pasa a la entrada. Sería a prueba {~}, con retirada a las 20 operaciones reales si no ganan más que vendiendo.

## 4. Otras ideas probadas que no pasan (sobre la base vigente)

| Idea | Resultado | Por qué no |
|---|---|---|
| Peso por familia según su Sharpe pasado (24-60 meses, sin mirar al futuro) | Sube R/año a 65-72; 2024-26 hasta 11,5 | 2018-21 baja en 18 de 20 combinaciones; inestable |
| Peso por familia inverso a su volatilidad | 4,4-6,1 | Baja la ganancia |
| Peso por familia según su ratio acumulado | 4,3-6,1 | Sube la caída |
| Freno que respeta la calidad (puntos 2 o estrellas ≥ 3 fuera del freno) | 4,5-4,7 | La caída sube a −14 R |
| Salida por tiempo (k velas sin +0,5 o +1 R y bajo la entrada) | Solo 9 velas/1 R mejora; vecinos no | No aguanta los umbrales vecinos |
| Sin tercio con la volatilidad propia de cada moneda o con tendencia fuerte de BTC | 5,1-6,4 | Sube la caída o no cambia |

*Estas pruebas usaron la fórmula; su conclusión negativa no cambia con la re-simulación porque o no tocan salidas o empeoran mucho.*

## 5. Revisión de coherencia (otro agente, solo lectura)
Fallos que pueden dar una orden mal:
1. **Piso de 1/4 R:** el registro (31-oct) dice abrir a 0,25 R. El bot v0.2 lo quitó porque empeora (6,16 → 4,85). No está escrito qué manda en lo manual.
2. **Freno de racha:** los documentos 06 (punto 2.5), 08 y 00 aún no dicen que la E1 y Connors van fuera del freno. Siguiéndolos, irían a medio tamaño.
3. **Herramientas que faltan en GitHub:** `escaner_v2.py` (documento 10, S7, solo en Drive) y el módulo `estudio_contado`, que importa `senales_contado.py` y no está.
4. **`cobertura_btc.py` no arranca sin `websocket-client`:** sin esa librería no sale la señal de cobertura. Falta el `pip install` en el arranque.

Incoherencias de texto:
- Documento 00 v1.49: Connors, capa M al 50 %, Supadata, entradas a mercado.
- Documento 09, línea 10: capa M al 50 %.
- Documento 22: Connors aún en vigilancia.
- `instruccion-2026-10-31-connors-a-vigilancia.md` y `…-youtube-supadata.md` sin marcar como sustituidas.
- `HERRAMIENTAS/yt_supadata.py` sigue en el repositorio.

Huecos sin regla escrita:
- E1 y Connors en el mismo índice el mismo día.
- Corto de índices y E1 en largo a la vez.
- Contador de la retirada de la capa T en ETH.

Solicitud n.º 7 de `velas-backtest`: ya sobra (la n.º 6 hizo lo mismo).

## Código
`velas-backtest/ESTUDIOS_MEJORAS_2026_11_02/`:
- `h.py`: arnés.
- `c1.py` a `c5.py`: pesos, freno, salidas.
- `gen/gen.py`: re-simulación con el código original.
- `gen/evB.py` y `gen/rob.py`: evaluación y robustez.

Verificación independiente: `/home/claude/verif_puntos/gen/`, con código propio. Cifras iguales al tercer decimal.
