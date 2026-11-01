# Listas de petróleo con el contrato real y cortos (27-oct-2026)

Origen: `backtests/2026-10-27-cortos-y-correccion-petroleo.md` (proyecto «1. GESTIÓN INTEGRAL CARTERA»). Generadas con `arnes.py` (`backtests/codigo/2026-10-27-cortos-arnes.py.txt`).

| Archivo | Qué es |
|---|---|
| `petroleo` | Petróleo (L1, L2, L3) medido con el **contrato real**, sin S1 (la S1 la sustituye el CORTO PETRÓLEO desde el 27-oct). Es la lista vigente. |
| `referencia/petroleo_con_s1` | Lo mismo con la S1, solo como referencia. **Movida a `referencia/` el 1-nov: no se carga.** |
| `mensuales` | T1/T2 con el petróleo corregido. |
| `corto_petroleo` | CORTO PETRÓLEO (en el arnés, `mm02f`): nota de escasez ≤ 1 y precio bajo la media de 200; dentro del freno. |
| `corto_sector` | CORTO SECTOR (en el arnés, `veric502`): fuera del freno. Tamaños del 27-oct (0,5 R); desde el 31-oct se opera a × 2. |

Las listas anteriores de `petroleo` y `mensuales` usaban el continuo sin ajustar y daban una base de 5,32 en vez de la corregida (6,13 con la cartera del 31-oct).
