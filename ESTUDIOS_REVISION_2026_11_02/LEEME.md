# Backtest: E1 de índices y Connors fuera del freno de racha (2-nov-2026)

Origen: `backtests/2026-11-02-bolsa-fuera-del-freno.md`. Óscar (2-nov, 19:44) pidió buscar mejoras nuevas con lo medido. Viene de un backtest positivo, verificado por un agente independiente con su propio código, así que se aplica sin otro «sí» (documento 00, punto 10).

## Qué se aplica
1. **La E1 de índices (S&P, Nasdaq, Dow) y Connors+ADX QQQ quedan fuera del freno de racha.** Es decir:
   - no se reducen a × 0,5 cuando la cartera está 4 R por debajo de su máximo;
   - sus ganancias y pérdidas no cuentan para activar el freno.
   - Es lo mismo que ya pasa con SHY y con los cortos de bolsa.
2. **Siguen contando** en el tope de 20 R, en el bloque de bolsa de EE. UU. (unos 10 R) y en el tamaño por puntos de la E1 (con su tope de 3 R al día).
3. **Connors+ADX QQQ vuelve a operar {~}.** Regla:
   - **Señal:** al cierre, QQQ sobre su media de 250 sesiones, RSI(2) < 20 y ADX(14) > 20.
   - **Entrada:** largo en la apertura siguiente.
   - **Tamaño:** 1 R = 2,5 × ATR(14) diario. Stop inicial: entrada − 1 R.
   - **Salida:** en la apertura siguiente al primer cierre con RSI(2) > 75.
   - Una a la vez.
4. **N1 VIX/VXV sigue en vigilancia** (NO ABRIR). Fuera del freno sumaría algo más, pero solo tiene 30 operaciones desde 2018.

## Por qué
La E1 y Connors compran caídas de los índices, así que **ganan más justo cuando la cartera está en caída** y el freno está activo:
- E1 con el freno activo: **+0,10 R** de media por operación; sin freno activo: +0,04 R.
- Connors con el freno activo: +0,42 R; sin freno: +0,27 R.
- Partirlas por la mitad tiraba las mejores operaciones.
- En el resto de la cartera pasa lo contrario (+0,37 R con freno frente a +0,45 R sin él): **allí el freno sí protege** y se mantiene.

## Cifras (ratio R/año ÷ peor caída: todo / 2018-21 / 2022-26)
| Montaje | Ratio | R/año | Caída |
|---|---|---|---|
| Base vigente | 6,14 / 5,61 / 7,04 | 57,0 | −9,3 R |
| E1 fuera del freno | 6,25 / 5,72 / 7,07 | 58,8 | −9,4 R |
| **E1 y Connors fuera del freno (lo aplicado)** | **6,26 / 5,73 / 7,17** | **61,3** | −9,8 R |
| E1, Connors y N1 fuera | 6,36 / 5,83 / 7,20 | 62,3 | −9,8 R |

- Últimos años: 2024-26 9,91 → 10,06; 2025-26 12,44 → 13,19.
- Remuestreo mensual: gana a la base en el 94 % de las pruebas.
- **Pasa con 4 de 5 frenos** (3 R, 4 R y 5 R a × 0,5, y 4 R a × 0,75). Con 4 R a × 0,25 no pasa.
- **Placebo:** sacar del freno el petróleo o el oro empeora mucho (4,56 y 3,94).
- Aviso: la peor caída sube un poco (−9,3 → −9,8 R), pero sube más la ganancia.

## Seguimiento
- Alarma de deterioro a las 15 señales reales de Connors (documento 10, apartado 12).
- El sábado se compara la E1 real abierta con freno activo frente a su backtest.

## Otras ideas probadas en esta tanda (no pasan)
- Freno solo para cripto: 4,17 / 3,63 / 6,45 (la caída sube a −14,4 R).
- Tamaño según la volatilidad de toda la cartera, de 60 días, sin mirar al futuro: 4,39 / 4,28 / 5,75 (baja mucho la ganancia).
- Familia a × 0,5 si sus 10 últimas operaciones suman negativo: 5,13 / 4,69 / 5,49.
- N1 solo fuera del freno: 6,24 / 5,71 / 6,70 (baja en 2022-26).

## Código y verificación
- Código: `ESTUDIOS_REVISION_2026_11_02/` de `VELAS-BACKTEST` (`base2.py`, `r1.py`, `r2.py`, `r3.py`).
- Verificación independiente: `/home/claude/verif_freno/v.py`; cifras iguales con dos decimales.
- Matiz del verificador: «fuera del freno» hace dos cosas a la vez (no reduce esas operaciones y no las cuenta para activar el freno). Es igual que con SHY y los cortos; no se han separado los dos efectos.
