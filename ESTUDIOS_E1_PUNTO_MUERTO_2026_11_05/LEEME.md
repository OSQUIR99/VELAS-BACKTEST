# E1: stop a punto muerto (5-nov-2026)

Listas del motor (formato `MOTOR/listas`) de la E1 de índices (S&P 500, Nasdaq 100 y Dow) con cinco gestiones del stop:
`base` (vigente), `pm02` / `pm04` / `pm06` (stop a la entrada desde el día siguiente a que el máximo toque entrada + 0,2 / 0,4 / 0,6 R, es decir, +0,5 / +1 / +1,5 ATR) y `sube` (stop que sube del documento 00).

Generadas con `contexto-cartera/HERRAMIENTAS/estudios/e1-stop-punto-muerto/gen_be.py` (generador original `listas_bolsa.py`; entradas, salida, tamaño y topes sin tocar). Informe y conclusiones: `contexto-cartera/HERRAMIENTAS/estudios/e1-stop-punto-muerto/INFORME.md` (resultado: ✗, ninguna pasa el paso 1 del documento 23 desde may-2018).
