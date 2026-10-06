# ACUMULACION — una puntuación de 0 a 100 por activo y un cambio entre metales

Creado el 2-3 de octubre de 2026; ampliado el 4 de octubre con el estudio «dentro de la fase alcista» y el cambio oro ↔ plata. Datos hasta el cierre del 2 de octubre de 2026 (Bitcoin, hasta el 1 de octubre).
Activos: Bitcoin, S&P 500, Nasdaq 100, oro y plata, al contado.

## Para usarlo cada semana

    cd "$HOME/Desktop/VELAS PARA BACKTEST/ACUMULACION"
    python3 termometro.py --descargar   # actualiza datos y da la lectura (solo desde la Terminal normal del Mac)
    python3 termometro.py               # sin internet, con lo guardado en datos/

Con mirar una vez por semana basta. Mira a diario solo si la puntuación de Bitcoin baja de 35.
Si una puntuación sale como «NO FIABLE: datos caducados», no la uses hasta actualizar.

## Qué significa la puntuación en cada activo

Cada activo tiene sus propios ingredientes y sus propios tramos. Lectura del 2-oct-2026: Bitcoin 54, S&P 500 50, Nasdaq 100 40, oro 30, plata 30.

| Activo | Ingredientes (puntos) | Cómo leerla |
|---|---|---|
| Bitcoin | Liquidez, 7 luces (3) · reloj del halving (3) · regla tendencia + liquidez apagada (2) · sin sobrecalentamiento (1) · zona de valor (1) | 25 o menos: vender por tramos; recomprar al volver a 50. 25-40: sin dinero extra. 75 o más: dinero extra |
| S&P 500 | Liquidez, 6 luces (3) · tendencia (2) · sin recesión con tendencia rota (2) · miedo aprovechable (3) | Solo destaca 75 o más (dinero extra). No se vende por puntuación |
| Nasdaq 100 | Dólar bajando (1,5) · bono a 10 años bajando (1,5) · dólar sin dispararse (1) · miedo aprovechable (3) · sin sobrecalentamiento (1) · sin recesión con tendencia rota (2) | 75 o más: dinero extra. 25 o menos: aviso serio, no regla de venta |
| Oro | Tendencia (3) · media de 200 subiendo (2) · sin caída del 10 % (2) · dólar bajando (1) · sin subida parabólica (1) · volatilidad extrema (1) | 75 o más: tendencia a favor. Por debajo: sin dinero extra. No se vende por puntuación |
| Plata | Tendencia (2) · media de 200 subiendo (1) · oro en tendencia alcista (2) · sin caída del 10 % (2) · sin subida parabólica (2) · no cara frente al oro (1) | Igual que el oro. Aparte, el aviso de subida parabólica (tramo pequeño) |

Las compras periódicas no se retrasan nunca: esperar caídas, o comprar más con puntuación alta y menos con baja, no dio más unidades.

## Dentro de una fase alcista: vender y recomprar no funcionó

Fase alcista de fondo = precio por encima de su media de 200 sesiones y esa media subiendo.
Probé ahí 14.790 combinaciones (126 señales de venta x 17 formas de recomprar, por activo): sobrecompra, agotamiento, pérdida de impulso, divergencias, datos externos.

| Activo | Pruebas | Acabaron con más unidades | Media por operación | Vendiendo un día cualquiera | Eligiendo cada año las 5 mejores hasta entonces |
|---|---|---|---|---|---|
| Bitcoin | 2.877 | 10,6 % | -6,0 % | -5,2 % | x0,91 |
| S&P 500 | 3.338 | 8,7 % | -0,8 % | -0,8 % | x0,63 |
| Nasdaq 100 | 3.265 | 9,7 % | -1,2 % | -1,2 % | x0,86 |
| Oro | 3.044 | 15,4 % | -0,9 % | -1,2 % | x0,92 |
| Plata | 2.266 | 20,6 % | -1,5 % | -1,5 % | x0,74 |

Las señales no aportan nada: se pierde lo mismo que vendiendo al azar, es decir, la subida que te pierdes mientras esperas fuera.
En Bitcoin la fuerza llama a más fuerza (tras RSI de 70 o más: +31 % y +10 % en 20 días, frente a +13 % y +3,5 % de un día cualquiera).
Tampoco aguantaron: varias señales a la vez, filtros de liquidez, cambios de volatilidad, calendario, ni rotar entre otros pares de activos.

## Ideas probadas el 4 de octubre: al revés, divergencias de ida y vuelta y rotaciones

- **Señales al revés** (sobreventa, divergencia alcista, miedo... usadas para vender): pierden algo menos que vender al azar, pero pierden. Con más unidades: BTC 30,8 %, S&P 13,5 %, Nasdaq 17,9 %, oro 19,2 %, plata 22,0 % de las variantes.
- **Vender en divergencia bajista y recomprar en la siguiente alcista** (diario; RSI, MACD, delta; 144 variantes por activo): con más unidades BTC 14 %, ETH 6 %, S&P 0 %, Nasdaq 0 %, oro 0 %, plata 12 %. Te deja fuera del mercado entre un tercio y la mitad del tiempo.
- **Rotar por fuerza relativa**: BTC/ETH gana casi todo en 2016-2017 y desde 2019 va a rachas (×1,1-1,2 frente a BTC; la mitad frente al mejor en 2021-2023). BTC/ETH/HYPE (22 meses): ×0,2-0,6 frente a mantener HYPE. S&P/Nasdaq desde 1985: ×0,5 frente al Nasdaq.
- **Candidata sin confirmar**: divergencia bajista del delta de volumen de 90 días en Bitcoin, en fase alcista, recomprando al tocar la media de 20 sesiones. 23 operaciones en nueve años, ×1,6; ganan las 28 variantes con picos de 5 u 8 sesiones; en ETH, SOL, XRP, BNB y LTC no funcionó (44 % de variantes, típica ×0,96). La herramienta no la calcula. Última señal: julio de 2025.

## Cambio oro ↔ plata (la asimetría que sí aguantó)

Ratio oro/plata = onzas de plata que vale una de oro. Se compara, con cierres semanales, con su media de 5 años (260 semanas).

- **Tienes plata**: medio tramo a oro cuando el ratio baja 1,5 desviaciones típicas de su media; el otro medio en 2. Vuelta a plata cuando el ratio recupera la media.
- **Tienes oro** (lado flojo, no lo recomiendo como regla): a plata cuando el ratio sube 1,5 / 2 desviaciones; vuelta a oro en la media.
- La herramienta da el ratio, la media, los niveles de esta semana y el estado de la regla. Se decide con la semana cerrada.

Respaldo (velas semanales 1975-2026, comisión del 0,125 % por operación, ejecución una semana después):
- Lado de la plata: 10 cambios; 8 ganaron, 1 perdió un 6 %, 1 sigue abierto. Las 24 variantes probadas ganan (típica x2,9; peor x1,7; la central x4,1). Desde 1985: x2,8; desde 2000: x2,2; desde 2010: x1,5.
- Lado del oro: 7 de 9; típica x1,7; una variante pierde; un cambio duró ocho años y perdió un 30 %.
- Ojo: son unas 7 decisiones independientes en 51 años; cuatro cambios llegaron a ir entre un 24 % y un 33 % por detrás; el de 1979-80 aporta la cuarta parte del resultado y sus precios son dudosos; no hay tope de pérdida si el ratio tarda años en volver.
- Solo con productos cotizados: con metal físico los márgenes y el IVA de la plata se comen la ventaja. Cada cambio con ganancia adelanta impuestos (no incluidos).

Lectura del 2-oct-2026: ratio 68,1; media de 5 años 80,6. La regla cambió plata por oro en diciembre de 2025 (65,0 y 59,0) y sigue en oro; vuelta a plata con cierre semanal en 80,6 o más. Nueva señal solo por debajo de 66,5.

## Lo que respalda cada una

- **Bitcoin** (la más útil). Vender por tramos con 25 o menos y recomprar con 50: x3,35 (2011-2019) y x2,29 (2020-2026) en unidades frente a no hacer nada; x1,04 desde 2023. Siete ventas: cinco ganaron con claridad, una empató, una perdió un 12 %. Tras 25 o menos, -17 % y -25 % a tres meses; tras 75 o más, +94 % y +40 %.
  OJO: es sobre todo una apuesta por el ciclo de cuatro años. Con el reloj en fase favorable la puntuación no puede bajar de 30: desde el 20-oct-2026 hasta la primavera de 2029 no puede haber venta por puntuación. La alternativa sin reloj es la regla «precio bajo su media de 200 días con 2 luces verdes o menos» (x3,0 y x1,9; x0,87 desde 2023; 9 falsas alarmas de 18): la herramienta la enseña también.
- **Nasdaq 100.** Tras 75 o más: +10 % y +12,5 % a tres meses. Tras 25 o menos: -15 % y -32 %, pero casi todos los casos son de 2001 y 2008. Vender a 25 dio x1,25 y x1,08 y con el umbral en 30 pierde: no es fiable.
- **S&P 500** (la menos útil). Tras 75 o más: +10 % y +7 % a tres meses, con 11 y 15 semanas de muestra (el 1 % del tiempo). Por debajo no separa bien.
- **Oro.** Tras 75 o más: +21 % y +17 % a doce meses; tras 25 o menos: -2 % y +5 %. Vender con puntuación baja dejó la mitad de las unidades en 2006-2026.
- **Plata** (poco respaldo). Con velas semanales desde 1970, tras 75 o más: +33 % y +27 % a doce meses; por debajo, entre 0 % y 6 %. Aviso parabólico (extensión de 1,7 o más; recomprar al volver a la media de 200): 6 de 6 desde 1970, pero frágil.

Lo que NO funcionó para vender, en ninguno: RSI alto, bandas de Bollinger, precio lejos de sus medias, máximos de 52 semanas, divergencias (RSI, MACD, delta), delta de volumen, codicia extrema, interés abierto alto, especuladores muy comprados, salir bajo la media sin más, «vender en mayo».

## Las siete luces de liquidez (verde = a favor; cambio en 13 semanas)

Dólar (baja) · condiciones financieras NFCI (baja) · bono a 10 años (baja) · diferencial de crédito Baa (baja) · Fed + BCE + Banco de Japón en dólares (sube) · liquidez neta de la Fed (sube) · monedas estables (+2 %, solo Bitcoin).
Hostil: 2 verdes o menos. Favorable: 4 o más. Lectura del 2-oct-2026: 2 de 7.

## Ficheros

- `termometro.py` — la herramienta (pandas + numpy; Python 3.9 o superior).
- `datos/precios_diarios.csv` — cierres diarios de los cinco activos.
- `datos/series/*.csv` — dólar, VIX, tipos, crédito, balances de bancos centrales, monedas estables, miedo y codicia, peticiones de paro.
- `lectura_actual.json` e `historial_lecturas.csv` — la última lectura y el registro de todas.
- `informe_termometro_acumulacion.html` — copia del informe (ábrelo con el navegador).
- `estudio.zip` — los programas, datos públicos y resultados del estudio, para consulta (incluye `swing.py`, `swing_wf.py`, `gsr.py`, `inv.py`, `div_rt.py`, `btc_delta_div.py`, `rot.py` y las auditorías del 4 de octubre).

## Ojo

- **No hay prueba con datos nuevos.** Ingredientes, pesos y umbrales se eligieron mirando toda la historia. Con otros pesos razonables, la regla de Bitcoin dio de media x1,8 y x1,7: espera menos que lo que muestra la prueba.
- Pocas muestras: Bitcoin tiene tres ciclos completos y siete ventas; la zona alta del S&P 500 son 26 semanas en 59 años.
- La fecha del siguiente halving (15-abr-2028) es una estimación: cámbiala en `termometro.py` (HALVINGS) cuando ocurra.
- Yahoo, FRED, Binance y demás están bloqueados desde la consola de Claude: la descarga funciona desde la Terminal normal del Mac y no se pudo probar desde aquí. Si una fuente falla, el programa lo dice y marca la puntuación como no fiable cuando el dato caduca.
- Las pruebas no incluyen impuestos, dividendos ni el interés del efectivo. Cada venta con ganancia adelanta el pago a Hacienda.
- El índice NFCI y las peticiones de paro se revisan con el tiempo; se usa la versión actual.
- En tu base de velas, la vela diaria de BTC del 21-sep-2026 quedó guardada a medias (cierre 85.710 en vez de 86.620). Aquí está corregida; en la base original no la he tocado.
- No es asesoramiento financiero ni fiscal.
