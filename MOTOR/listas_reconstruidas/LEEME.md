# Listas reconstruidas (31-oct-2026)

Listas rehechas desde su definición escrita (documento 25 del proyecto) porque las originales no estaban en GitHub.
**No sustituyen a las de `MOTOR/listas/`**: el motor solo las usa si se le pasan aparte (ver `ESTUDIOS_CAIDAS_2026_10/comun.py`, clase `Cartera`).

| Archivo | Señal | Operaciones | Nota |
|---|---|---|---|
| ~~`corto_sector`~~ (movida a `referencia/corto_sector_reconstruida` el 2-nov: la vigente es `MOTOR/listas/corto_sector`, 515 operaciones; cargar las dos contaba CORTO SECTOR dos veces) | CORTO SECTOR (12 ETF de sectores; sector y S&P bajo una media de 200 que baja; RSI(2) > 90; salida primer cierre < media de 5 o 10 sesiones; stop 2,5 ATR) | 530 | Tamaño 0,5 / 0,25 R según el dólar; en la cartera de 31-oct va × 2 |
| `corto_indices_credito` | CORTO ÍNDICES CRÉDITO (S&P, Nasdaq, Dow, Russell bajo su media de 200 y HYG < media de 50) | 109 | 0,5 R; × 2 desde 31-oct |
| `n1_vixvxv` | N1 VIX/VXV: el VIX vuelve a cerrar por debajo del VIX a 3 meses → largo S&P 9 sesiones; 1 R = 2,5 ATR; stop 20 % | 80 | **NO ABRIR (vigilancia)** desde el 31-oct, 20:35: con la base exacta baja 2022-26 |
| `cripto_realista_sin_tercio_vol10` | `cripto_realista` (de `MOTOR/listas/`) con la regla «sin venta del tercio» (volatilidad de 30 días de BTC del día anterior ≤ percentil 0,10 de 3 años; no SOL) | 591 | Regla en vigor a prueba {~} desde el 26-oct. Código: `ESTUDIOS_VOLATILIDAD_2026_10/` |

Fecha de sesión: algunas velas diarias de TradingView llevan sello de la tarde anterior; se usa (sello + 6 h).normalize().

Las listas de petróleo corregidas (contrato real) y CORTO PETRÓLEO ya están en `MOTOR/listas/` (solicitud n.º 2, 31-oct).
