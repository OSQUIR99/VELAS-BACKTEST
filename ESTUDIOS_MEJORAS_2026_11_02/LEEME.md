# Mejoras con lo ya medido (2-nov-2026): tamaño del petróleo

Informe: `backtests/2026-11-02-tamano-petroleo.md` del proyecto. Instrucción: `instrucciones-importadas/2026-11-02-tamano-petroleo.md`.

- `base.py`: base vigente real = E1 y Connors fuera del freno + regla «sin venta del tercio» de cripto (la lista `referencia/cripto_realista_sin_tercio_vol10` entra EN LUGAR de `MOTOR/listas/cripto_realista`, mediante una carpeta de enlaces `/home/claude/mej/gh`; con TERCIO=0 se usa la cripto normal). Da 6,35 / 5,69 / 7,36 (TERCIO=0: 6,26 / 5,73 / 7,17).
- `exp1.py`: otras familias fuera del freno y «contra-freno» de E1/Connors (no pasan).
- `exp2.py`: pesos por familia por búsqueda de coordenadas, entrenando en un periodo y probando en el otro.
- `exp3.py`: cada familia × 0,5…× 2 por separado. `exp4.py`: combinaciones K1–K6 con remuestreo y otros frenos. `exp5.py`: placebo y explicación.
- `k7.py`: K2, K7 y **K8 (la aplicada)**.
- `verificacion/`: código del agente independiente (`ver.py`, `r1.py`…`r10.py`).
