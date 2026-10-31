# Entradas tras caídas bruscas y fundamental (26-oct-2026)

Código de dos estudios de bolsa, ambos verificados por un agente independiente y **descartados** (documento 22 del contexto):
- «Punto dulce»: esperar estabilización (S2) o reversión temprana (S3) tras una caída ≥ 25 % desde el máximo de 60 sesiones.
- Caídas de todo el mercado frente a sectoriales o propias, E1 en acciones sueltas y fundamental (ventas que crecen y deuda neta < 3 × beneficio bruto) como filtro.

Lo único que queda es contexto ~: las caídas de todo el mercado rebotan más que las de un sector o una empresa.

- `codigo_punto_dulce_y_caidas.py`: los scripts `p.py`, `a.py`, `bajar_sec.py`, `fund.py`, `e1acc.py`, `an2.py` y `an3.py` juntos.
- Datos: velas de unas 258 acciones (yfinance) y `companyfacts` de la SEC (no se suben). Rutas absolutas de la sesión que lo hizo.
- Informes en el proyecto: `backtests/2026-10-26-punto-dulce-tras-caidas.md` y `backtests/2026-10-26-caidas-de-mercado-y-fundamental.md`.

Solo mide el pasado. No es asesoramiento.
