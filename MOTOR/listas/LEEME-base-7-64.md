# Base de cartera 7,28 → 7,64 (reglas del VIX, 6-nov-2026)

Para reproducir exacta la base del motor de cartera:

- **Cripto vigente:** `cripto_base/C_base.parquet` (+ `_diario`). Generada con `cripto_base/gen2.py` (código original, sin venta del tercio con nota de puntos 2), a partir de `cripto_realista.parquet`. Sustituye a `cripto_realista.parquet` en la base 7,28.
- **VIX 28 ALCISTA** (VIX ≥ 28 y S&P sobre su media de 200; 0,5 R): `vix/m_b28_spx_sobre200_m1.parquet` (+ `_diario`).
- **VIX CURVA** (pico ≥ 25 en 10 sesiones y cruce del VIX bajo el VIX a 3 meses; 0,75 R): `vix/n_cn_p25_l10_r100.parquet` (+ `_diario`).
- Combinación aprobada (opción 7): `vix/final_opcion7.py`, línea `go('7 >=28f 0.5 + curva 0.75', ...)`. Listón 7,28 sin VIX → 7,64 con las dos reglas.
- El resto de listas de la base: los demás archivos de esta carpeta (bolsa_e1, c10, petroleo, metales, shy, mensuales, x_petroleo, corto_*…).
