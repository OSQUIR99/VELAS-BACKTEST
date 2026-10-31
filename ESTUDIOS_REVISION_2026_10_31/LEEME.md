# Revisión del 31-oct-2026: liquidez en la cartera, base exacta con el petróleo corregido, Connors y MSTR

Informes en el proyecto «1. GESTIÓN INTEGRAL CARTERA»:
- `backtests/2026-10-31-liquidez-en-la-cartera-repeticion.md`
- `backtests/2026-10-31-base-exacta-petroleo-corregido.md`
- `backtests/2026-10-26-mstr-mineras-y-bitcoin-retraso.md`

## Arreglo en `ESTUDIOS_CAIDAS_2026_10/comun.py`
- **El fallo:** `MOTOR/listas/petroleo` y `petroleo_con_s1` tienen los mismos `id`. El motor guarda el latente diario por `id`, así que, cargando las dos, el petróleo de la base no se valoraba día a día.
- **El efecto:** la base daba 5,76 / 5,56 / 7,18 en vez de 6,14 / 5,61 / 7,04.
- **El arreglo:** `comun.mezclar` ya no carga `petroleo_con_s1` (conjunto `EXCLUIR`).
- **Lo encontró** un verificador independiente.

## Carpetas
- `liquidez/`: 47 variantes de la línea de liquidez en la cartera (`evaluar.py`), placebo (`placebo.py`) y las listas de la señal semanal de BTC (`senal_btc.py`; necesita el BTC diario de `mstr/datos.py`).
- `base_exacta/`:
  - base del 31-oct (`base.py`);
  - N1, B21, E1e y liquidez sobre la base exacta (`pruebas.py`);
  - la rejilla de montajes (`rejilla.py`);
  - el efecto sin freno (`sinfreno*.py`);
  - **una réplica propia de Connors+ADX QQQ** (`connors.py`, salida en la apertura siguiente; `connors_cierre.py`, salida al cierre) y su prueba (`connors_test.py`).
  - Ojo: es una réplica, no la lista oficial `yt_connors_qqq`.
- `mstr/`: MSTR y mineras frente a Bitcoin (adelanto y retraso, diario y horario). Descartado.

## Resultados principales (base corregida 6,14 / 5,61 / 7,04)
- **N1 VIX/VXV:** baja el ratio de 2022-26 (7,04 → 6,97). No pasa el criterio.
- **B21:** solo pasa con N1 dentro. Sigue como aviso.
- **E1e:** descartada.
- **Liquidez:** nada fiable. Lo que pasa son mejoras de centésimas o efectos del freno.
- **Largo semanal de BTC con la línea:** no pasa.
- **Connors (réplica) en lugar de la E1:** 5,81 / 5,53 / 6,72. Encima de la E1: 5,83 / 5,38 / 6,53. No pasa. Hay que repetirlo con la lista oficial `yt_connors_qqq` cuando esté en `MOTOR/`.
