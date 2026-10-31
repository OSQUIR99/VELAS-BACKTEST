# Volatilidad baja de BTC (vídeo de Plan BTC) · 25-31 oct 2026

Código de los estudios que dieron la regla **«sin venta del tercio»** del REBOTE 4H de cripto:
si la volatilidad de 30 días de BTC del cierre anterior está en su 10 % más bajo de 3 años,
BTC, ETH, ADA, ZEC y LINK no venden 1/3 en +1 R (SOL nunca lo vende). Estado: a prueba {~}.

Solo mide el pasado. No es asesoramiento.

## Archivos
| Archivo | Qué hace |
|---|---|
| `estudio_25oct_volatilidad_y_sth.py` | Estudio inicial: episodios de volatilidad baja, sentimiento, cruces del coste de compradores recientes (STH) y efecto sobre el REBOTE 4H |
| `variantes_26oct/` | Variantes (trampa y giro, compresión + sentimiento, ruptura tras compresión, salida sin tercio), placebo y cartera |
| `base_exacta_31oct/lista_modificada_y_motor_28oct.py` | Construye la lista de cripto modificada (`lista_modificada(thr, dst)`) y la mide con el motor real |
| `base_exacta_31oct/base_exacta_31oct.py` | Reproduce la base exacta del 31-oct (6,14 / 5,61 / 7,04) y mide los umbrales 7,5 / 10 / 12,5 % |
| `vol_btc.py` | Herramienta diaria (también en el repositorio privado de contexto): percentil de 3 años, `sin_venta_tercio`, avisos de compresión y ruptura |
| `../MOTOR/listas_reconstruidas/cripto_realista_sin_tercio_vol10*.parquet` | `cripto_realista` con la regla aplicada (umbral 0,10) |

## Cómo se modifica la lista
Para cada operación con parcial (no SOL) que entra con el percentil del día anterior ≤ 0,10 y toca +1 R:
- `r_bruto` nuevo = (`r_bruto` − 1/3) × 1,5; `r_final` = eso × `tam_R`.
- En el diario, desde el día que toca +1 R: `r_latente_unidad` = (A − 1/3) × 1,5.

## Resultados (ratio R/año ÷ peor caída: todo / 2018-21 / 2022-26)
| Montaje | Base | Con la regla |
|---|---|---|
| Motor real (28-oct) | 5,49 | 5,68 |
| Base exacta 31-oct (carga corregida, sin `petroleo_con_s1`) | 6,14 / 5,61 / 7,04 | **6,39 / 5,65 / 7,48** (R/año 57,0 → 59,2, misma caída) |
| Umbral 7,5 % | — | 6,28 / 5,64 / 7,27 |
| Umbral 12,5 % | — | 4,98 / 4,47 / 7,30 (caída −11,7 R en 2021): no |

## Notas
- Las rutas son absolutas (`/home/claude/...`) de la sesión que lo hizo: cámbialas a tu clon.
- La base exacta **no** carga `petroleo_con_s1` (repite los `id` de `petroleo`).
- Datos externos del estudio del 25-oct (no se suben): BTC diario antiguo de blockchain.info, miedo y codicia de alternative.me y coste STH de BGeometrics.
- Informes en el proyecto: `backtests/2026-10-25-volatilidad-baja-y-sth.md` y `backtests/2026-10-26-volatilidad-baja-variantes.md`.
